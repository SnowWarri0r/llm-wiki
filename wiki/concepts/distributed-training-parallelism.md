---
name: distributed-training-parallelism
type: concept
sources: [krea-2, cosmos-3]
updated: 2026-07-16
---

# 分布式训练并行 · 模型、数据和长序列分别怎么切

## 一句话
显存不够时不要只说“多加几张卡”：参数、矩阵乘和 token 是三种不同的东西，要用三种切法。

## 先认清三个瓶颈

- **FSDP2 / HSDP：切模型状态。** 参数、梯度和优化器状态分散到多张卡；算某层前临时把那层参数凑齐，算完再释放。它解决“整套模型状态放不下”。
- **Tensor Parallel，简称 TP：切一层计算。** 同一个大矩阵乘拆给多张卡，每张卡算一部分输出。它解决“单层太大或单层计算太慢”。
- **Context Parallel，简称 CP：切长序列。** 同一条超长序列的 token 分给多张卡。Ulysses 是一种 CP 实现，通过 all-to-all 交换，让每张卡轮流拿到完成注意力所需的 head 或序列片段。

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

## HSDP 为什么多一个 H

全局有 16 张卡时，可以分成 4 组，每组 4 卡：组内像 FSDP 一样切成四份，组间复制一套。这样组内通信更密集，跨组通信更少。它用一些重复存储换更符合机器拓扑的通信量。

## async-TP 在做什么

普通 TP 是“先通信，再计算”；async-TP 尽量让第 N 块的通信与第 N−1 块的矩阵乘同时进行。只有计算时间足以盖住通信时间，异步才真能变快。

## 链接

- [[krea-2]] · FSDP2、Megatron TP 与 async-TP
- [[cosmos-3]] · HSDP 与 Ulysses Context Parallel
- [[gpu-interconnects-and-collectives]] · 这些切法依赖的跨卡搬运
- [[activation-checkpointing]] · 不加卡时，另一种省显存办法
