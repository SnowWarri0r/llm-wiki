---
name: rcm
type: paper
source: https://arxiv.org/pdf/2510.08431
upstream: https://arxiv.org/abs/2510.08431
ingested: 2026-08-12
authors: Kaiwen Zheng 等（清华大学、NVIDIA）· ICLR 2026 · arXiv v3
year: 2026
---

# rCM · 把连续时间一致性蒸馏扩到 14B 视频模型

rCM 不是一种新的生成骨干，而是一套少步扩散蒸馏配方：sCM 负责沿老师轨迹学习、保住多样性，DMD 负责纠正大模型上累积的细节与时序误差。论文同时补上 FlashAttention-2 JVP、FSDP 和上下文并行，使这套训练能落到 14B 视频 DiT。

## 一句话

**用 DMD 的长跳纠偏，修复 sCM 沿局部切线逐段累积的误差。**

## 先纠正五个容易读错的点

1. rCM 的 `r` 是 score-regularized，不是 Riemannian、rotation 或 recursive。
2. 它没有把 14B 模型缩小；推理变快来自网络调用次数从 70 次左右降到 1–4 次。
3. JVP 不是普通反向传播，也不是完整 Jacobian；它只求模型沿当前时间轨迹方向的导数。
4. DMD 项不是又训练一遍 sCM。它从学生自己生成的结果出发，用 teacher / fake 两个方向做长距离纠偏。
5. 仓库后来加入的 Causal-rCM 是后续工作；本文的 rCM 仍是双向图像 / 视频扩散蒸馏。

## 它要解决的痛点

- sCM 理论上能把多步 ODE 压成少步，却在 10B+ 视频 DiT 上出现纹理粗糙、文字破损和时序伪影。
- 误差不只来自模型容量，而来自连续时间目标里的 JVP 自反馈：早期的一点偏差会沿时间传播，低精度计算又会把它放大。
- 单独用 DMD 能修质量，但反向 KL 容易偏向少数高概率模式；单独用 sCM 多样性好，却缺一条跨长距离的纠偏信号。

## 核心贡献

1. **局部轨迹监督**：[[continuous-time-consistency]] —— 让同一去噪轨迹上的各点直接回到同一个干净终点。
2. **长跳纠偏**：[[forward-reverse-divergence-distillation]] —— sCM 保覆盖，DMD 修质量，两种方向互补。
3. **可扩展切线计算**：[[jacobian-vector-product]] —— 只算当前轨迹方向的导数，并把 attention 的原值和切线一起流式计算。
4. **时间口径统一**：[[noise-schedule-wrapping]] —— 把不同老师的原始噪声日程换到 TrigFlow 的统一时间轴。
5. **工程扩展**：[[flash-attention]] 与 [[distributed-training-parallelism]] —— 用 FSDP2 分模型状态、用 Ulysses CP 分长视频序列，让 14B JVP 训练放得下、跑得动。

## 关键结果

- Cosmos-Predict2 14B 文生图：老师 70 NFE 的 GenEval overall 为 `0.84`；rCM 4 / 2 / 1 步为 `0.83 / 0.81 / 0.82`。
- Wan2.1 14B 480p 文生视频：老师 `0.18 FPS`；rCM 4 / 2 / 1 步为 `4.5 / 8.3 / 14.4 FPS`，2 步 VBench total 为 `85.05`。
- Wan2.1 1.3B 4 步为 `14.6 FPS`，1 步为 `32.3 FPS`。FPS 包含扩散采样和 VAE 解码，测于单张 H100、batch 1。
- 1 步并非无损：小文字更差，视频更模糊；2–4 步才是论文实际推荐区间。

## 我的批注

- rCM 最重要的洞察不是“再加一个 loss”，而是把 sCM 的局部切线监督和 DMD 的长距离分布纠偏分工讲清楚。
- 论文把质量故障定位到 JVP 自反馈与低精度误差，证据比“模型大了所以难训”具体得多；但理论分析仍主要解释误差怎样传播，没有给出严格收敛界。
- `λ=0.01` 在论文任务上复用得很好，但它仍是一条质量—多样性旋钮，不应被理解成跨模型永远免调。
- 论文没有公开完整训练墙钟时间、GPU 数和数据配比，无法据此估算从零复现成本。
- 官方仓库到 2026 年已经建议更稳的分阶段流程 `dCM → sCM → DMD (+sCM)`；这是发布后的工程经验，不是原论文主实验口径。

## 跟 wiki 里其他 paper 的关系

- [[dmd]] · 提供 rCM 的长跳 score 纠偏项。
- [[dmd2]] · 同属 on-policy 分布匹配，但训练配方与本文不同。
- [[drifting-models]] · 都可理解为“目标吸引 − 学生自身排斥”。
- [[senseflow]] · 也在解决大模型 DMD 训练失稳，但修的是 fake-score 追踪、时间监督和判别器。
- [[flow-matching]] · rCM 的老师可用速度场表示，Wan / Cosmos 都属于这条生成主线。

## 历史定位

- 2023 · Consistency Models：离散相邻时间点的一致性蒸馏。
- 2024 · sCM / MeanFlow：把时间间隔压到连续极限，用 JVP 直接学切线。
- 2024 · DMD / DMD2：用 real / fake score 匹配学生生成分布。
- 2025–2026 · **rCM**：把连续时间一致性扩到 14B 视频模型，并用 DMD 修质量。
- 2026 · Causal-rCM：把同一互补关系搬到流式自回归视频；不是本文实验的一部分。
