---
name: score-function
type: concept
sources: [flow-matching, ode-sde, dmd]
updated: 2026-07-22
---

# Score Function · ∇log p(x) · 对数概率梯度

## 一句话
对一个概率密度 p(x)，**score = ∇log p(x)** —— 指向"概率密度更大的方向"的向量。diffusion 模型学这个，flow matching 不学这个。

## 直觉
想象数据分布是一坨地形（高度 = 概率密度）。在地形上某一点 x：
- **概率密度 p(x)** = 这点的地形高度
- **score ∇log p(x)** = 这点的<strong>上坡方向 + 坡度</strong>

如果你想生成 "像数据的样本"，就<strong>沿 score 方向走</strong> —— 一步步爬向高密度区域。这就是 diffusion 反向去噪的本质。

类比 1：迷雾里找村庄。你看不到全局地图（不知道 p(x) 长什么样），但每点能感受到"哪边人多 / 灯光更密"（score 方向）。沿这个感觉走，最终到村庄（高密度区）。

类比 2：物理。如果 p 是势能函数 e^(-E)，那 ∇log p = -∇E = 受力方向。粒子在势场里运动 = 沿 score 走。

## 为什么是 log
两个原因：

**1 · 数值范围合理**。`p(x)` 在高维空间常常是 10⁻¹⁰⁰ 这种夸张小数；`log p(x)` 是 -230 左右，神经网络好处理。

**2 · 让梯度公式简化**。`∇p(x) / p(x) = ∇log p(x)` —— 学 score 等于学 "归一化的梯度方向"，不受 p 数值大小影响，只关注方向。

## 为什么 diffusion 学 score 而不是 p 本身
学 p 直接需要知道 partition function（积分配一才能归一化）—— 高维上 intractable。

学 score 跳过 partition function：
```
∇log p(x) = ∇log [unnormalized_p(x) / Z]
          = ∇log unnormalized_p(x) - ∇log Z
          = ∇log unnormalized_p(x)        # Z 是常数, 梯度为 0
```

→ 只要知道 unnormalized density 的形状就够，partition function 自动消掉。

## diffusion 怎么学 score
直接学 score 没法做（不知道 p_t 是啥）。Trick：用<strong>加噪后样本预测原噪声</strong>，通过 Tweedie's formula 转成 score。

```python
# Diffusion 训练
x_0 ~ data
ε ~ N(0, I)
t ~ U(0, T)
x_t = √(ᾱ_t)·x_0 + √(1 − ᾱ_t)·ε       # 加噪到 t 时刻
ε_pred = model(x_t, t)                # 模型预测噪声
loss = || ε_pred − ε ||²              # MSE on noise

# 推理时通过 Tweedie's formula:
score_at_t = -ε_pred / √(1 − ᾱ_t)     # 等价于学到了 score
```

这就是 [[flow-matching]] 论文吐槽 diffusion "训练目标不直观"的原因 —— 你想生成，结果学了"加噪样本的噪声预测"，绕一圈才转回 score。

## flow matching 怎么避开 score
flow matching 直接学 [[velocity-field]] v(x, t) —— "该往哪走"。完全不需要 score 这个抽象。

数学上两者有关系：在某些 path（如 VP-SDE）下，velocity 跟 score 有线性关系，所以 diffusion 可以视作 flow matching 的特例。但<strong>训练目标的直观度</strong>差异巨大。

## 跟 energy-based model 的关系
EBM 学 unnormalized log p（叫 energy E(x)，其实是 −log p 加常数）。score = −∇E。

EBM / score-matching / diffusion 一脉相承，都是"绕过 partition function"的路线。flow matching 是另一条路：<strong>不解决 partition function，直接绕开整个 p 的建模，只学搬运速度</strong>。

## 链接
- [[flow-matching]] · 提出不学 score 的方案
- [[velocity-field]] · flow matching 学的替代目标
- [[math-symbols]] · ∇ / log / partition function 这些符号的速查
- [[ode-sde]] · score 是 SDE 反向漂移里的关键项（diffusion 那头）
