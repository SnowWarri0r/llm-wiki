---
name: velocity-field
type: concept
sources: [flow-matching, interaction-models-tml]
updated: 2026-05-21
---

# Velocity Field · 速度场 · v(x, t)

## 一句话
对每个 (位置 x, 时间 t)，告诉你这个粒子应该往哪个方向、以多快的速度走。flow matching 就是让神经网络学这个函数。

## 直觉
想象一群粒子从噪声分布（如标准高斯）"流"到数据分布（如 MNIST 数字 / 真实图片）。每个粒子在每个时刻该往哪走？

如果你知道一个速度场 `v(x, t)`，每个粒子沿它积分：
```
x_{t+Δt} = x_t + v(x_t, t) · Δt
```
就能从噪声 t=0 走到数据 t=1。

这就是 ODE（Ordinary Differential Equation）的样子。flow matching 训练的核心是<strong>学这个 v</strong>。

类比：风在地图上的分布。如果你知道每个位置每个时间的风向 + 风速，给你一颗气球的起点，你能模拟它的飞行轨迹。flow matching 让神经网络学气象台的风预报功能。

## 数学上的本质
任何概率路径 p_t(x)（一族随时间变化的概率密度）都对应<strong>唯一</strong>一个速度场 v_t(x)，满足 [[continuity-equation]]：
```
∂p_t/∂t + ∇·(p_t · v_t) = 0
```
（粒子守恒：粒子流入流出和密度变化平衡）

flow matching 的洞察是：**不需要直接知道 p_t**（很难算），<strong>只要学 v_t</strong>，对样本 ODE 积分就能采样。

## 训练时怎么学
直观做法：用 marginal velocity field v_t(x)，但它是 intractable 的（要对所有 conditioning 求积分）。

Flow matching 用 **conditional velocity field** 替代：给定一个 target sample x_1（数据点），定义一条从 noise 到 x_1 的<strong>条件路径</strong>，对应的 conditional velocity 是 tractable 的。

线性插值路径（最简单）：
```
x_t = (1 - t) · x_0 + t · x_1     # x_0 是噪声, x_1 是数据
v_t(x | x_1) = x_1 - x_0           # 常数速度，沿直线
```

训练 loss：
```
loss = E_{t, x_0, x_1} || u_θ(x_t, t) - (x_1 - x_0) ||²
```
就是个 MSE —— 让神经网络 u_θ 在每个 (x_t, t) 上预测对应的 velocity。

理论上 conditional FM loss 跟 marginal FM loss 等价（梯度方向相同），所以学出来的 u_θ 就是 marginal velocity field 的近似。

## 推理时怎么用
学完 u_θ 后，从 x_0 ~ N(0, I) 开始，沿 ODE 走 N 步到 x_1：

```python
x = sample_noise()
for t in linspace(0, 1, N):
    v = model(x, t)
    x = x + v * (1/N)
return x  # 生成的数据
```

N 取多少？OT 直线路径下理论 1 步够，实际 4-20 步达到 diffusion 50-1000 步质量。

## 跟 score 的对比
Diffusion 学 score: `s_t(x) = ∇log p_t(x)` —— 概率密度的对数梯度。
Flow matching 学 velocity: `v_t(x)` —— 直接的"该往哪走"。

两者关系：在某些 path 下（如 VP-SDE），velocity 跟 score 有简单线性关系。所以 diffusion 可以视作 flow matching 的特例 —— 但训练目标的<strong>直观度</strong>差异巨大。

## 链接
- [[flow-matching]] · 提出论文
- [[probability-path]] · 路径设计
- [[conditional-flow-matching]] · 实际训练 loss
- [[ode-vs-sde]] · flow vs diffusion
