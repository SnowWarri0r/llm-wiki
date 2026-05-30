---
name: probability-path
type: concept
sources: [flow-matching]
updated: 2026-05-21
---

# Probability Path · 概率路径

## 一句话
一族随时间 t ∈ [0, 1] 变化的概率密度 p_t(x)，从 p_0（噪声分布，如标准高斯）连续演化到 p_1（数据分布）。

## 直觉
想象数据分布是一坨复杂形状（如手写数字 MNIST 集合）。噪声分布是一坨简单形状（标准高斯）。

概率路径是 "**怎么把简单形状变形成复杂形状**" 的逐帧动画：t=0 是高斯，t=0.5 是中间形态，t=1 是数据分布。

flow matching 训练就是<strong>学怎么沿这条路径走</strong>。

## 路径的设计自由
diffusion 限定了 path —— 必须是 OU 过程（高斯过程），形式是：
```
p_t(x | x_1) = N(α(t) · x_1, σ(t)²)
```

flow matching 解放了这个约束 —— <strong>你可以选任意 path</strong>。常见选择：

**1 · 线性插值（最简单）**：
```
x_t = (1 - t) · x_0 + t · x_1
```
样本沿直线从 x_0 走到 x_1。

**2 · OT 路径（理论最优）**：
等价于线性插值（在合适的参数化下）。直线意味着<strong>最短路径</strong>，对应 OT（最优传输）解。

**3 · VP-SDE 路径（diffusion 兼容）**：
跟 diffusion 一样的 OU 过程，flow matching 用 ODE 求解。

**4 · 自定义路径**：
比如想让 t=0.5 时刻经过某个中间状态，可以设计 p_t 反映这个。

## OT 路径为什么特别
OT (Optimal Transport) 视角下，从 p_0 到 p_1 的"成本最小"路径是<strong>直线</strong> —— 每个 x_0 沿直线到对应的 x_1。

这有两个好处：
- **少步推理**：理论上 1 步 ODE 就够（沿直线一步到位）
- **训练目标清晰**：conditional velocity = x_1 - x_0，简单常数

实际选 OT 路径的 flow matching 通常 4-20 步达到 diffusion 50-1000 步的质量。

## 反例 · 弯路 path
如果 path 设计不好（如 OU 过程），样本要走<strong>弯路</strong>：
- 先朝某个方向走
- 再回头
- 最后到 target

这意味着 velocity 频繁变化，ODE 解不准（需要更多步数补偿）。Diffusion 之所以要 50-1000 步，部分原因就是 OU 路径不是直线。

## 数学约束
任何 path 都必须满足：
- t=0 时 p_0 是先验分布（如 N(0, I)）
- t=1 时 p_1 是数据分布
- 中间 p_t 处处可微（保证 velocity field 存在）

满足这些约束的 path 有无穷多个。<strong>flow matching 让你自由挑</strong>。

## 链接
- [[flow-matching]] · 提出
- [[velocity-field]] · 跟 path 对应
- [[optimal-transport]] · OT path 的来源
