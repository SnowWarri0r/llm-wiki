---
name: ode-vs-sde
type: concept
sources: [flow-matching]
updated: 2026-05-21
---

# ODE vs SDE · 确定性 vs 随机性流

## 一句话
flow matching 用 ODE（确定性流），diffusion 用 SDE（随机性流）。差别是<strong>路径上有没有噪声项</strong>。

## ODE · 确定性
```
dx/dt = v(x, t)
```
给定起点 x_0 和速度场 v，<strong>解唯一确定</strong>。同样的 x_0 跑两次，得到同样的 x_1。

类比：物理粒子在风场中飞，给定起点和风，轨迹完全确定。

## SDE · 随机性
```
dx = f(x, t)·dt + g(t)·dW
```
多了 `dW`（布朗运动 / Wiener process）—— 每一步带随机扰动。同样 x_0 跑两次，得到不同 x_1。

类比：粒子在风场中飞 + 持续被空气分子撞击，每次轨迹略不同。

## 训练目标
**ODE / flow matching**：学 velocity field v(x, t)。loss 是 MSE。

**SDE / diffusion**：学 score function ∇log p_t(x)。loss 是 score matching（带 Tweedie's formula）。

ODE 的训练目标更直观（直接的"该往哪走"），SDE 的目标绕一圈（先学 score 再用它构造速度）。

## 推理步数
**ODE / flow matching**（OT 路径下）：4-20 步就够。粒子沿直线走，每步精确。

**SDE / diffusion**（DDPM 原版）：50-1000 步。粒子被随机扰动，每步只能走一点点。

差距来源：SDE 的随机项让单步预测不准，必须用小步长补偿。

## 但 SDE 有它的优势
不是 ODE 全面赢。SDE 在某些场景有优势：
- **diversity** · 随机扰动让 sample 之间天然不同
- **mode coverage** · 随机性能避开"卡在某个 mode 出不来"
- **理论性质** · SDE 跟物理过程（diffusion equation）对应，数学工具丰富

实践上：SD3 / Flux / 现代音频生成都转向 flow matching (ODE)，因为<strong>少步推理</strong>对部署成本是巨大优势。Diversity 问题通过 inference 时加一点随机扰动（stochastic flow matching）解决。

## ODE 推理为什么不简单等于"积分速度场"
理论上：
```python
for t in 0, 1/N, 2/N, ..., 1:
    x = x + v(x, t) / N
```

实际：用更高阶 ODE 求解器（RK4 / DPM-Solver）能用更少步数达到同质量。所以"flow matching 4 步 ≈ diffusion 50 步"里的 4 步实际是用 4 次 RK4 evaluation = 16 次 model forward，仍快于 diffusion 的 50 次。

## 跟 TML 的关系
TML 的 200ms micro-turn 需要 <strong>极少步数推理</strong>（200ms 预算 = ~5 次 GPU forward）。flow matching 的 OT 路径让"4-8 步生成一段音频"成为可能，而 diffusion 在这预算下质量崩。这是 TML 选 flow matching 而不是 diffusion 的工程动机。

## 链接
- [[flow-matching]] · 用 ODE
- [[velocity-field]] · ODE 的核心
- [[probability-path]] · 路径设计
- [[interaction-models-tml]] · 用 flow matching 做实时音频
