---
name: flow-matching
type: paper
source: https://arxiv.org/abs/2210.02747
upstream: https://arxiv.org/abs/2210.02747
ingested: 2026-05-21
authors: Lipman, Chen, Ben-Hamu, Nickel, Le (Meta AI) · ICLR 2023
---

# Flow Matching for Generative Modeling

把 diffusion 的"加噪 → 学 score → 反向去噪"那一整套替换成更简单的：**直接学一个速度场 v(x, t)，从噪声 ODE 积分到数据**。训练目标是普通 regression loss（MSE），没有 SDE / score matching 那些黑魔法。

## 一句话
**把噪声→数据的生成问题转成一个"学速度场"的回归问题**。给定起点（噪声）和终点（数据），定义一条路径，让模型学每一时刻应该往哪个方向走。

## 它要解决的痛点
2022 之前 diffusion 是 SOTA 生成模型，但训练和推理都不直观：
- 训练目标是 **score matching**（学 ∇log p(x)），不直观为啥这个能 work
- 推理走 **SDE**（带随机项的逆 diffusion），数学要写一堆补偿项
- **只支持 OU 噪声 schedule**（高斯标准过程），换其他 path 难
- 步数多（50-1000 步）

实际上做生成只需要一件事：**找一条从噪声分布到数据分布的路径，让模型沿着走**。Flow matching 把这事直接说出来。

## 核心贡献
1. **理论**：[[velocity-field]] —— 任何概率路径 p_t(x) 都对应一个唯一的速度场 v_t(x)，能让 ODE `dx/dt = v_t(x)` 把样本从 p_0 推到 p_1
2. **训练目标**：[[conditional-flow-matching]] —— 不需要 marginal 速度场（intractable），用 conditional 替代（每条样本的速度），数学上等价。loss 是 simple MSE
3. **路径自由**：[[probability-path]] —— 不限定 OU 过程，可以选任意 p_t。论文证明<strong>最优传输（OT）路径就是直线</strong> —— 噪声到数据的直接连线
4. **straight-line 路径 = 少步推理**：OT 路径下样本沿直线走，理论上 1 步 ODE 就够；实际 4-20 步达到 diffusion 50-1000 步的质量
5. **跟 diffusion 兼容**：diffusion 是 flow matching 的一种特殊情况（OU 过程对应一种 path）

## 关键概念
- [[velocity-field]] · v(x, t) · 每个 (位置, 时间) 该往哪走
- [[probability-path]] · p_t(x) · 噪声到数据的概率密度演化
- [[conditional-flow-matching]] · 训练时实际用的 loss
- [[ode-vs-sde]] · flow（确定性）vs diffusion（随机性）
- [[optimal-transport]] · OT 路径就是直线，最短传输

## 我的批注
- **最重要的简化是 "学速度而不是 score"**。Score 是 ∇log p，是个未知分布的导数，需要绕一圈才能学；velocity 是直接的"该往哪走"，是个直观量。<strong>把不直观的目标换成直观的目标 = 训练稳、调参少</strong>
- **OT 路径让"采样几步就行"成为可能**。Diffusion 经典 50-1000 步是因为 SDE 路径是曲折的（每步只能走一点点）。OT 直线下理论上一步到位 —— Rectified Flow（Liu et al. 2022）、Stable Diffusion 3 等都用这思路
- **TML 用 flow matching 做音频输出不是偶然**。音频是连续值（mel / waveform），RVQ 离散化损失信息且不可微；flow matching 直接在连续空间生成，可端到端联训。这是为什么 TML 选 flow matching 而不是 fish-speech 的 RVQ codec
- **跟 fish-speech 的 RVQ 路线对照很有意思**：RVQ 把音频<strong>离散化</strong>给 LLM 当 token；flow matching 让 LLM 直接<strong>生成连续</strong>音频特征。两条不同的"LLM + 音频"哲学
- **数学上一个 elegant 的 unification**：flow matching = diffusion + 任意路径 + ODE 而非 SDE。Diffusion 在 flow matching 视角下只是个特例 —— 这种 generalize 论文价值远超只解决某个 benchmark

## 跟 wiki 里其他 paper 的关系
- [[interaction-models-tml]] · 用 flow matching 做端到端音频输出（替代 RVQ codec）
- [[fish-speech-s2-pro]] · 走的另一条路 —— RVQ codec + Dual-AR 离散 token
- [[audio-tokenization-rvq-vs-flow]] · 跨 paper 的对比 thread
- 后续发展：Rectified Flow（Liu 2022）· Stable Diffusion 3 · Flux 等都基于 flow matching

## 历史定位
- 2020 DDPM · Diffusion 起点 · SDE-based · score matching
- 2021 DDIM · 把 SDE 写成 ODE · 但训练仍是 score matching
- 2022-05 Rectified Flow · OT 直线路径 · 跟 flow matching 同期
- 2022-10 **Flow Matching** · 统一框架 · velocity field + MSE 训练
- 2023 Stable Diffusion 3 · flow matching 应用到 latent diffusion
- 2024+ · 音频 / 视频生成大模型多数转向 flow matching 路线
