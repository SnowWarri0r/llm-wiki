---
name: raven
type: paper
source: raw/raven.txt
upstream: https://arxiv.org/abs/2605.15190
ingested: 2026-09-28
authors: RAVEN 作者组（含 J. Deng，NVIDIA Academic Grant 资助）· arXiv 2605.15190 (2026-05)
year: 2026
---

# RAVEN · 把推理时的"接龙"搬进训练图，让历史也吃到梯度

实时自回归视频扩散的两块补丁：RAVEN（训练时测试）把每次 self rollout 重新拍成「干净历史块 / 带噪去噪块」交错的一条序列，让后面块的损失能反传到前面块的历史编码；CM-GRPO 把一致性采样的一步直接当高斯策略做 GRPO，不再借 Flow-GRPO 那套 Euler-Maruyama 辅助随机过程。基座 Wan2.1-T2V-1.3B，每块 3 个 latent 帧。

## 一句话

**Self Forcing 让学生在自己生成的历史上训练，但历史是 stop-gradient 的死上下文；RAVEN 把 rollout 里的干净块和带噪块交错拍平成一条因果序列、一次前向，后面块的 DMD 损失就能修前面块的历史表示——VBench 总分 84.96 → 85.15，再叠 CM-GRPO 到 85.46，动态度是最大赢面。**

## 它要解决的痛点

- **历史监督缺口**：因果视频蒸馏里，每个生成块都是后面所有块的上下文。Teacher Forcing 喂真历史（训练分布 ≠ 推理）；Diffusion Forcing / CausVid 喂各自独立加噪的真历史（还是不像推理）；Self Forcing 喂自己 rollout 的历史，分布对了，但 cache 是 `sg(·)` 的——后面块的损失到不了历史那一头。四种范式要么分布错，要么分布对了没梯度。
- **直接展开太贵**：想让梯度穿过整条自回归采样（每块又是多步去噪的终点）得把整条轨迹放进一张计算图，反传要穿过自回归递归和采样器动力学两层。
- **少步模型做 RL 的接口错位**：Flow-GRPO 把确定性 ODE 改写成 SDE 再 Euler-Maruyama 离散化，得到可算比率和 KL 的高斯核；但推理用的 ODE 采样器里根本没有这些随机转移。一致性采样器不一样——它每步天然是「预测干净端点 → 重新加噪」的高斯转移，本身就能当策略。

## 核心设计

1. **训练时测试（[[training-time-test]]）**：fake-score 步里冻结的学生做 self rollout（KV cache 复用），得到每块的完整去噪轨迹 `{ẑ_t^(τ_k)}` 和干净端点 `x̂_t`。生成器步不丢这些状态，而是取一个采样层级 `u ∈ {τ_1..τ_{K−1}}`，拍成交错序列 `I_u = (ẑ_1^(u), x̂_1, ẑ_2^(u), x̂_2, …, ẑ_{T−1}^(u), x̂_{T−1}, ẑ_T^(u))`（长 2T−1），在因果 mask 下一次前向：带噪块是被监督的去噪目标，前面的干净块 `x̂_{<t}` 是它的历史 `h_t^RAVEN = H(x̂_{<t})`——这次历史编码在图里，梯度能到。灵感来自 EAGLE-3 的 training-time test（用推测解码时自己会产生的上下文来训）。
2. **分块损失缩放（[[future-participation-loss-scaling]]）**：定义未来参与分数 `p_j = Σ_{k≥j} m_k / Σ_k m_k`（块 j 及之后的元素占比，前面大后面小），过权重函数 `g_η` 出原始权重，再归一化保证元素平均权重不变。消融里 shift 家族 `π_α(p)=αp/(1+(α−1)p)`：α=1 偏早块、α=0 均匀、α=−1（把 π_1 套在反向坐标 `p_J/p_j` 上）偏晚块——采用 α=−1，总分比均匀高 1.33。
3. **CM-GRPO（[[consistency-kernel-policy]]）**：为什么蒸馏完还要 RL——DMD 只会说"像老师"，说不出"动得更多 / 贴文字 / 别糊"，要按这些标准往上推得给视频打分；卡点是 GRPO 要"概率"而确定性 ODE 采样没有，Flow-GRPO 靠训练时硬加噪声造概率（推理不跑、还要调 σ/β）。一致性一步 `ẑ^(s) = α_s x̂_θ + σ_s ε` 就是高斯核 `π_θ(ẑ^(s)|ẑ^(u),c) = N(α_s x̂_θ, σ_s² I)`。同一 prompt 采 G 条轨迹，端点打分 → 组内归一化优势 `Â_i`，广播到轨迹上的每个转移。去掉常数后 `log π = −‖ẑ^(s) − μ‖²/(2σ_s²)`，对 `x̂_θ` 的梯度是 `−Â α_s (ẑ^(s) − μ)/σ_s²`，用 stop-gradient 回归 `‖x̂_θ − sg(x̂_θ + Â α_s/(2σ_s²)·(ẑ^(s)−μ))‖²` 实现——形式上和 DMD 的 score 梯度更新同一个模子。参考策略 KL 有闭式 `α_s²‖x̂_θ − x̂_ref‖²/(2σ_s²)`，但双向老师没法从一致性接口采样，本文没用。
4. **奖励组合**：每个奖励维度先组内归一化再加权求和（TA 文本对齐 2 / DD 动态度 0.35 / MS 运动平滑 0.75 / AQ 美学 1 / IQ 成像 1），再整体做组归一化 + clip。DD 用 RAFT 光流幅度前 5% 均值，MS 用 AMT 补帧误差，AQ 是 LAION 线性美学头，IQ 是 MUSIQ，TA 是 VideoReward（Qwen2-VL + DPO，182K 人工偏好对）。
5. **训练配置**：初始化沿用 Causal Forcing（从自回归老师 ODE 蒸馏的因果学生）；关 weight decay，TTUR critic:生成器 5→2；CM-GRPO 在 RAVEN 上加 LoRA rank 256，AdamW lr 5e-6、betas (0, 0.999)、eps 1e-10，batch 8 × group 32；只用 VidProM 的文本 prompt（按 Self Forcing 协议过滤 + LLM 扩写），需要真视频的消融用 OpenVidHD-0.4M 经 RIFE 插帧。算力 RAVEN ≈70、CM-GRPO ≈170 H200 GPU 小时。

## 关键数字

- 主表（VBench Total / Quality / Semantic + UnifiedReward-32B 动态度）：Causal Forcing 84.96/86.00/80.76/2.669 → RAVEN 85.15/86.18/81.04/2.951 → +CM-GRPO 85.46/86.54/81.17/2.962。Causal Forcing 直接叠 CM-GRPO 只到 85.08/86.12/80.96/2.829。Self Forcing 84.27，Reward Forcing 84.39。
- 历史范式消融（同初始化同缩放）：TF 82.64（动态度最高 3.000）、DF 84.09、SF 84.06（动态度最低 2.347）、DF 换成自 rollout 前缀 83.30、RAVEN 85.15。
- 策略接口消融：EM 核 σ∈{.1,.4,.8}×β∈{0,.004} 六格都在 85.03–85.27，最好一格只比 RAVEN 高 0.12；CM-GRPO 85.46。
- 评测集：VBench 提示集 6,220 条视频；用户研究 100 条长 prompt × 每法 4 样本，对 CausVid / Self Forcing / Reward Forcing / Causal Forcing 全部胜出（比例只画在图里）。

## 关键概念 → 概念页链接

- [[training-time-test]] — 把推理时自己会遇到的上下文搬进训练图（新）
- [[future-participation-loss-scaling]] — 按"后面还有多少元素"给块加权（新）
- [[consistency-kernel-policy]] — 一致性采样步当高斯策略做 GRPO（新）
- [[dmd-distillation]] — 三角色（老师 / fake critic / 学生）与 score 梯度回归的母体
- [[grpo]] — 组内相对优势
- [[chunk-wise-self-forcing]] — Self Forcing 的分块反传近亲；RAVEN 是"历史进图"的另一种切法
- [[teacher-forcing-video-diffusion]] — 被比较的范式之一
- [[kv-cache]] — 历史表示 `H(·)` 就是 cache
- [[stop-gradient]] — Self Forcing 历史里的 `sg` 正是被拿掉的东西
- [[speculative-decoding]] — EAGLE-3 的 training-time test 出处
- [[ode-vs-sde]] — Flow-GRPO 走 ODE→SDE，CM-GRPO 不走
- [[autoregressive-vs-bidirectional-video-diffusion]] — 非对称蒸馏的背景

## 我的批注 / 疑问

- 最值钱的一句：**分布对了不等于有监督**。表 2 里 "DF w/ Self Rollout"（历史换成自生成但仍不反传）83.30，比 DF 的 84.09 还低——只对齐分布、不给梯度，误差只是换个地方堆。RAVEN 的增量恰是"梯度能到历史编码"这一件事。
- 要看清"监督历史"监督的是什么：`x̂_{<t}` 本身是 rollout 采出来的常数张量，梯度到不了它的内容；能到的是**模型怎么把这些块编成 KV**（历史的读法），不是历史的写法。这和 EAGLE-3 一样，是"在自己会遇到的上下文上训"，不是"把上下文也优化了"。
- 交错序列长 2T−1，因果注意力代价大约翻四倍量级，论文没给生成器步的额外开销；70 H200 小时只是总账。
- 摘要说的动机是"长时程质量"，但所有评测都是 VBench 5 秒短视频（Wan 1.3B 81 帧 = 21 latent 帧 ≈ 7 块）；没有一张长视频漂移曲线。"长时程"目前是推断不是证据。
- 表里的 Dyn. Deg. 列**不是** VBench 自带的动态度，是 UnifiedReward-32B 打的分（作者嫌 RAFT 光流会把抖动和漂移也算成运动）；而训练奖励里的 DD 恰恰是 RAFT 光流——评测和奖励刻意错开，是防 reward hacking 的好习惯，但读表要知道两者不是一个尺子。
- CM-GRPO 对 EM 的赢面 +0.19，比 RAVEN 对 Causal Forcing 的 +0.19 同量级，都不算大；真正说服人的是"六格 EM 网格全在一条窄带里、不用调 σ 和 β"。
- shift 家族 α=0 按公式字面是 0·p/(1−p)=0，p=1 处 0/0，"α=0 即均匀"只能当约定读。
- 增益最稳的是动态度：RAVEN 对 Causal Forcing +0.282，而质量和语义只 +0.18/+0.28——历史进图主要治的是"为了稳而不敢动"。

## 跟 wiki 里其他 paper 的关系

- [[causal-rcm]] · 同样在 Self Forcing 之上做因果蒸馏，走的是 CM + DMD 正反散度；RAVEN 不动散度，动的是历史怎么进图。
- [[waveforcing]] / [[avatar-forever]] · 实时自回归视频的同一条线；Avatar-Forever 的 RRT 也是"拿自己的坏历史训"，但仍 stop-gradient。
- [[solarwm]] / [[minwm]] · 都提到 Flow-GRPO 一类少步 RL；CM-GRPO 是给一致性采样器专门做的策略接口。
- [[longcat-video-avatar-1-5]] · Per-Frame GRPO 把优势分到时间分区，RAVEN 则把优势广播到整条轨迹再按块权重缩放。

## 历史定位

- 2024-07 Diffusion Forcing · 每 token 独立噪声级的因果扩散
- 2024-12 CausVid · DF + DMD 做非对称蒸馏
- 2025-06 Self Forcing · 在自己 rollout 的历史上做 DMD，cache 是 sg
- 2025 Causal Forcing / Reward Forcing / LongLive / Rolling Forcing · 初始化、奖励、长视频各补一角
- 2026-05 **RAVEN** · 历史进图 + 一致性核策略
