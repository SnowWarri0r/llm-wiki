---
name: distributed-training-parallelism
type: concept
sources: [krea-2, cosmos-3, qwen3-vl-report, senseflow, wan-streamer-v02, wan-streamer-v03]
updated: 2026-08-06
---

# 分布式训练并行 · 模型、数据和长序列分别怎么切

## 一句话
显存不够时不要只说“多加几张卡”：参数、矩阵乘和 token 是三种不同的东西，要用三种切法。

## 先认清三个瓶颈

- **FSDP2 / HSDP：切模型状态。** 参数、梯度和优化器状态分散到多张卡；算某层前临时把那层参数凑齐，算完再释放。它解决“整套模型状态放不下”。
- **Tensor Parallel，简称 TP：切一层计算。** 同一个大矩阵乘拆给多张卡，每张卡算一部分输出。它解决“单层太大或单层计算太慢”。
- **Context Parallel，简称 CP：切长序列。** 同一条超长序列的 token 分给多张卡。Ulysses 是最常用的 CP 实现之一：注意力前后各做一次 all-to-all，在「按 token 切」和「按 head 切」两种布局间互倒（走法见下文专节）。

它们可以叠加：外层 HSDP 切模型状态，内层 TP 切矩阵，CP 再切 token。代价是每多切一刀，就多一种跨卡通信和故障点。

## 数字例子

假设训练状态共占 24 GB，一条视频有 8000 个 token，一层线性变换要算 4096 个输出通道，现有 4 张 GPU：

```text
普通数据并行：每卡都放完整 24 GB 状态
FSDP2：       24 ÷ 4 = 每卡常驻约 6 GB 状态

Context Parallel：8000 ÷ 4 = 每卡先处理约 2000 个 token
Tensor Parallel： 4096 ÷ 4 = 每卡先算约 1024 个输出通道
```

这不是白省：FSDP2 算某层前要 all-gather 参数；TP 算完要合并局部结果；CP 做注意力时要交换 token 或 head。若网络来不及搬数据，GPU 就会等通信。

## Ulysses 具体怎么走

CP 的难点全在注意力上。FFN、LayerNorm、QKV 投影对每个 token 都是独立的——token 切给谁就在谁那算，零通信；可 self-attention 里每个 query 要看整条序列的 K/V，token 一切开，谁手里都不全。

最笨的补法是 all-gather：每张卡把别人手里的 K/V 全收一份再算。代价是每卡都要收下几乎整条序列的 K/V，序列越长收得越多，而且这笔通信量不随卡数下降——加卡不减负。

Ulysses 的观察是：**head 之间同样互不相干**。与其把整条 K/V 搬给每张卡，不如换个切法——让每张卡拿到全部 token，但只拿一部分 head，注意力就能在卡内独立算完。前后各做一次 all-to-all，在两种布局之间互倒：

```text
4 张卡、16 个 head、8000 个 token、每 head 128 维（隐藏维 2048）：

① token 布局     每卡 2000 token × 全部 16 head
                 （FFN、归一化、QKV 投影都在这层布局零通信地算）
② 本地投影       每卡算出自己这 2000 个 token 的 Q/K/V
③ all-to-all 去  把 16 个 head 切成 4 组：每卡留 1 组、把另外 3 组发给对应的卡，
                 同时收下别的卡发来的「自己那组 head」 → 变成 8000 token × 4 head
④ 本地注意力     每卡在自己 4 个 head 上做完整 softmax 注意力，
                 序列是全的，FlashAttention 照常用，结果精确不近似
⑤ all-to-all 回  注意力输出按原路倒回 2000 token × 16 head，
                 拼回 head 维，接输出投影和 FFN，继续 token 布局
```

通信账（bf16，用上面这组数）：一份本地张量是 2000 × 2048 × 2 字节 ≈ 8.2 MB；all-to-all 每卡只发出「自己那份的 3/4」，Q、K、V 去程加输出回程共 4 次，每卡每层实际上线约 24.6 MB。all-gather 方案光收 K 和 V 就要约 49.2 MB。更关键的是伸缩方向：8 卡时 all-to-all 降到约 14.3 MB（每卡的份变小了），all-gather 反而涨到约 57.3 MB——一个越切越省，一个越切越亏。

两个边界条件：

- **并行度封顶在 head 数**：每卡至少要分到一个 head，16 个 head 最多切 16 卡；用 GQA 时封顶在更少的 KV head 数上。
- **序列太短不划算**：每卡分到的 token 太少时，kernel 启动和 all-to-all 的固定开销盖过省下的计算。wan-streamer v0.2 的 Performer 只切长的视频 latent、不照搬去切短的音频 latent，算的就是这笔账。

head 数不够切、或序列长到单卡连一组 head 的完整 K/V 都放不下时，另一族做法是 Ring Attention：K/V 分块在卡环上传一圈，边传边用 online softmax 累加，不受 head 数限制，但实现更重、通信沿环串行。

## HSDP 为什么多一个 H

全局有 16 张卡时，可以分成 4 组，每组 4 卡：组内像 FSDP 一样切成四份，组间复制一套。这样组内通信更密集，跨组通信更少。它用一些重复存储换更符合机器拓扑的通信量。

## async-TP 在做什么

普通 TP 是“先通信，再计算”；async-TP 尽量让第 N 块的通信与第 N−1 块的矩阵乘同时进行。只有计算时间足以盖住通信时间，异步才真能变快。

## 链接

- [[krea-2]] · FSDP2、Megatron TP 与 async-TP
- [[cosmos-3]] · HSDP 与 Ulysses Context Parallel
- [[gpu-interconnects-and-collectives]] · 这些切法依赖的跨卡搬运
- [[activation-checkpointing]] · 不加卡时，另一种省显存办法
- [[wan-streamer-v03]] · v0.2/v0.3 的 Performer 用 Ulysses 切长视频 latent，短音频 latent 不照搬同一切法
- [[wan-streamer-v02]] · 预分片 K/V cache 与多卡 Performer 的完整部署时间线
