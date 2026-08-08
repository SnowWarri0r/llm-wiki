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

「倒回去」最容易卡住，把数据画成块矩阵就一目了然。整层激活可以切成 4×4 = 16 块，每块 = 一个 token 段 × 一组 head：

```text
              head组1   head组2   head组3   head组4
token段1      B₁₁      B₁₂      B₁₃      B₁₄
token段2      B₂₁      B₂₂      B₂₃      B₂₄
token段3      B₃₁      B₃₂      B₃₃      B₃₄
token段4      B₄₁      B₄₂      B₄₃      B₄₄

token 布局 = 卡 i 持有第 i 行（自己的 2000 token、全部 head）
head  布局 = 卡 g 持有第 g 列（全部 8000 token、自己的 4 个 head）
```

all-to-all 去程就是「行持有换成列持有」：每卡留下对角块（自己 token × 自己 head），把行里另外 3 块发给对应的卡，同时收下别人发来的、属于自己那列的 3 块。回程是同一个操作反着做一遍——注意力算完后卡 1 手里是第 1 列（8000 token × head 组 1），它按 token 段把这一列切成 4 块：留下 B₁₁，把 B₂₁、B₃₁、B₄₁ 分别发回卡 2、3、4；同时从卡 2、3、4 收回 B₁₂、B₁₃、B₁₄，沿 head 维一拼，第 1 行（2000 token × 16 head）就齐了。去程按 head 切、按 token 段拼；回程按 token 段切、按 head 拼，收发块数完全对称。

通信账（bf16，用上面这组数）：一份本地张量是 2000 × 2048 × 2 字节 ≈ 8.2 MB；all-to-all 每卡只发出「自己那份的 3/4」，Q、K、V 去程加输出回程共 4 次，每卡每层实际上线约 24.6 MB。all-gather 方案光收 K 和 V 就要约 49.2 MB。更关键的是伸缩方向：8 卡时 all-to-all 降到约 14.3 MB（每卡的份变小了），all-gather 反而涨到约 57.3 MB——一个越切越省，一个越切越亏。

两个边界条件：

- **并行度封顶在 head 数**：每卡至少要分到一个 head，16 个 head 最多切 16 卡；用 GQA 时封顶在更少的 KV head 数上。
- **序列太短不划算**：每卡分到的 token 太少时，kernel 启动和 all-to-all 的固定开销盖过省下的计算。wan-streamer v0.2 的 Performer 只切长的视频 latent、不照搬去切短的音频 latent，算的就是这笔账。

head 数不够切、或序列长到单卡连一组 head 的完整 K/V 都放不下时，另一族做法是 Ring Attention（见下节）。

## Ring Attention 具体怎么走

Ulysses 的前提是「head 够分、每卡放得下全序列的一组 head」。序列长到连这个都放不下、或者并行度要超过 head 数时，就换 Ring Attention 的思路：**Q 不动，K/V 沿卡环流动**。

它其实是把 [[flash-attention]] 的那套「分块扫 K/V + 在线 softmax 累加」从单卡内部搬到了卡与卡之间——FlashAttention 里数据在 HBM 和片上 SRAM 之间分块进出，这里换成在相邻 GPU 之间分块传递，累加公式一个字都不用改。

```text
4 张卡围成环（1→2→3→4→1），8000 token 均分：
卡 i 拿自己 2000 token 的 Q/K/V，16 个 head 全都在，不切 head。

          第1轮        第2轮      第3轮      第4轮
卡1手上   KV₁(自己)    KV₄        KV₃        KV₂
卡2手上   KV₂(自己)    KV₁        KV₄        KV₃
卡3手上   KV₃(自己)    KV₂        KV₁        KV₄
卡4手上   KV₄(自己)    KV₃        KV₂        KV₁

每轮做两件事，同时进行：
  算：拿手上这块 K/V 跟自己的 2000 个 Q 算一块注意力，
      每个 query 的 (m, l, a) 就地累加，算完这块 K/V 即可丢
  传：把手上这块 K/V 发给下家，同时从上家收下一块

4 轮后每个 Q 都见过全部 8000 个 key，输出 = a/l。
```

能「只看一块就累加」靠的正是在线 softmax：每个 query 只留三个数——见过的最大分 m、以 m 为基准的指数和 l、按同样权重累加的 V 值 a；新块里出现更大的分数时，把旧 l、旧 a 各乘 exp(m旧 − m新) 换个基准再加新贡献，结果和一次看全完全一样（精确，不是近似；完整手算见 [[flash-attention]]）。

三笔账：

- **通信藏进计算**：每轮收/发一块 K+V，上面这组数下是 2000 × 2048 × 2 字节 × 2 ≈ 16.4 MB；只要每轮的注意力计算时间 ≥ 传块时间，通信就完全被盖住，总耗时约等于纯计算。序列太短时块太小、算得太快，通信藏不住——和 Ulysses 一样有「短序列不划算」的下限，而且它的收发是逐轮串行依赖，藏不住时更疼。
- **显存随卡数线性扩**：每卡自始至终只放自己那块 Q 和一两块过路的 K/V，从不落整条序列——所以上下文长度可以随卡数近乎线性地涨，这是 Ulysses 给不了的。
- **因果 mask 下负载不均**：causal attention 里靠前的 token 只被少数 query 看，按顺序均分会让持有开头段的卡早早闲下来、持有结尾段的卡满负荷。常见修法是把序列按 zigzag / 条纹方式交错分给各卡，让每卡摊到的「早晚 token」大致均衡。

和 Ulysses 的取舍一句话：Ulysses 两次 all-to-all 一锤子买卖、实现轻，但并行度封顶 head 数、每卡要放全序列一组 head 的 K/V；Ring 不设 head 上限、显存随卡数扩，但要围着环转 P 轮、对「计算盖住通信」的依赖更强。两者也能叠着用：组内 Ulysses、组间 Ring。

## HSDP 为什么多一个 H

全局有 16 张卡时，可以分成 4 组，每组 4 卡：组内像 FSDP 一样切成四份，组间复制一套。这样组内通信更密集，跨组通信更少。它用一些重复存储换更符合机器拓扑的通信量。

## async-TP 在做什么

普通 TP 是“先通信，再计算”；async-TP 尽量让第 N 块的通信与第 N−1 块的矩阵乘同时进行。只有计算时间足以盖住通信时间，异步才真能变快。

## 链接

- [[flash-attention]] · 在线 softmax 的完整手算；Ring Attention 就是它的跨卡版
- [[krea-2]] · FSDP2、Megatron TP 与 async-TP
- [[cosmos-3]] · HSDP 与 Ulysses Context Parallel
- [[gpu-interconnects-and-collectives]] · 这些切法依赖的跨卡搬运
- [[activation-checkpointing]] · 不加卡时，另一种省显存办法
- [[wan-streamer-v03]] · v0.2/v0.3 的 Performer 用 Ulysses 切长视频 latent，短音频 latent 不照搬同一切法
- [[wan-streamer-v02]] · 预分片 K/V cache 与多卡 Performer 的完整部署时间线
