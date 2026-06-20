---
name: norm-regularization
type: concept
sources: []
updated: 2026-06-18
---

# 范数 / 正则化 · 衡量"权重多大"并罚它别太大

## 一句话
**范数**把一个向量"整体多大"压成一个数:**L2** = 欧氏长度 `√Σxᵢ²`(直线距离)、**L1** = 绝对值和 `Σ|xᵢ|`(街区距离)。**正则化** = 在 loss 里加一项权重的范数当"罚款",逼权重别长太大 → 防过拟合;**L2(weight decay)** 让权重均匀缩小,**L1** 逼出稀疏(很多权重正好 = 0)。

## 直觉 · 范数 = 一个向量整体多大

向量有好几个分量,"它整体多大"得用一个数概括,这就是范数:
- **L2 范数** `‖x‖₂ = √(x₁²+x₂²+…)`:勾股定理那种**直线距离**(从原点到这个点)。最常用,平滑可导。
- **L1 范数** `‖x‖₁ = |x₁|+|x₂|+…`:**街区/曼哈顿距离**(只能横平竖直走的总路程)。

**为什么要"正则"权重**:权重太大 → 模型能把训练数据**死记硬背**(连噪声都拟合)→ 过拟合,新数据上崩。办法:在 loss 后面加一项 `λ·‖w‖`,训练时**既要降原 loss、又要保持权重小**,`λ` 调罚得多狠。

- **L2 正则 / weight decay**:加 `½λ‖w‖₂²`。它的梯度是 `λw` → 每步更新里多一个"把 w 往 0 拉一点"的力,等价于**每步把权重乘一个略小于 1 的数**(所以叫"权重衰减")。效果:权重**整体均匀变小**,但很少正好为 0。
- **L1 正则**:加 `λ‖w‖₁`。它会逼出**稀疏**——很多权重被直接压成 **0**(相当于自动做特征选择)。

## 为什么 L1 稀疏、L2 不

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- Panel A: L2 圆 -->
  <text class="reveal d1" x="180" y="32" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#3949ab">L2 · 圆(没有角)</text>
  <line class="reveal d1" x1="80" y1="130" x2="280" y2="130" stroke="#bbb" stroke-width="1"/>
  <line class="reveal d1" x1="180" y1="60" x2="180" y2="200" stroke="#bbb" stroke-width="1"/>
  <circle class="draw d2" cx="180" cy="130" r="52" fill="none" stroke="#3949ab" stroke-width="2" pathLength="1000"/>
  <!-- loss 等高线椭圆从右上压来，切在斜方向 -->
  <ellipse class="reveal d3" cx="248" cy="70" rx="60" ry="38" fill="none" stroke="#9b2c2c" stroke-width="1.4" stroke-dasharray="4 3" transform="rotate(35 248 70)"/>
  <circle class="reveal d3" cx="215" cy="96" r="5" fill="#9b2c2c"/>
  <text class="reveal d3" x="180" y="218" text-anchor="middle" font-size="9.5" fill="#7a6f5d">最优落在斜方向 → 两权重都非零(只变小)</text>

  <!-- Panel B: L1 菱形 -->
  <text class="reveal d4" x="540" y="32" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#1f4d3a">L1 · 菱形(角在轴上)</text>
  <line class="reveal d4" x1="440" y1="130" x2="640" y2="130" stroke="#bbb" stroke-width="1"/>
  <line class="reveal d4" x1="540" y1="60" x2="540" y2="200" stroke="#bbb" stroke-width="1"/>
  <polygon class="draw d4" points="540,78 592,130 540,182 488,130" fill="none" stroke="#1f4d3a" stroke-width="2" pathLength="1000"/>
  <ellipse class="reveal d5" cx="600" cy="78" rx="60" ry="38" fill="none" stroke="#9b2c2c" stroke-width="1.4" stroke-dasharray="4 3" transform="rotate(35 600 78)"/>
  <circle class="reveal d5" cx="540" cy="78" r="5" fill="#9b2c2c"/>
  <text class="reveal d5" x="540" y="64" text-anchor="middle" font-size="9" fill="#9b2c2c">切在顶角(x=0)</text>
  <text class="reveal d5" x="540" y="218" text-anchor="middle" font-size="9.5" fill="#7a6f5d">角在坐标轴上 → 最优爱落在角 → 某权重=0(稀疏)</text>
</svg>
</figure>

正则相当于"把解约束在一个球里"(范数 ≤ 某值)。**L2 的球是圆**——光滑、没有偏好的方向,最优解一般落在某个斜方向,两个权重都非零、只是被压小。**L1 的球是菱形**——**尖角正好戳在坐标轴上**,loss 等高线压过来时**特别容易切在角上**,而角意味着某个坐标 = 0。维度越多,角越多越尖,稀疏越明显。

## 数字例子 · 手算
权重 `w = [3, 4]`:
```
L2 范数 ‖w‖₂ = √(3² + 4²) = √25 = 5      （勾股，直线距离）
L1 范数 ‖w‖₁ = |3| + |4| = 7              （街区距离）
```
**L2 正则怎么缩权重**(weight decay 的来历):
```
正则项 R = ½·λ·‖w‖₂²，它对 w 的梯度 = λ·w
一步更新: w ← w − lr·(原梯度 + λw)
        = w·(1 − lr·λ) − lr·原梯度
          └ 每步先把 w 乘 (1−lr·λ) 即略小于 1 → 持续往 0 收 ┘
```
比如 `lr=0.1, λ=0.1` → 每步权重先 ×0.99,再走原梯度。这就是优化器里 `weight_decay` 参数干的事。

## 落点
- **weight_decay**:几乎所有训练默认开 L2 正则(AdamW 把它做对了)。
- **梯度裁剪**:按梯度的 **L2 范数**裁(`‖grad‖ > 阈值就缩回去`),治 [[gradient-backprop]] 的梯度爆炸。
- **RMSNorm**:除以特征的均方根 ≈ 除以 `L2/√n`,见 [[normalization]]。
- **L1 稀疏**:Lasso 回归、模型剪枝、压缩里逼零。

## 代码出处 / 来源
- 标准内容:Lp 范数、L1/L2 正则(Ridge/Lasso)、weight decay
- 落点:`torch.optim.AdamW(weight_decay=...)`、`clip_grad_norm_`

## 链接
- [[gradient-backprop]] · 正则给梯度多加一项;梯度裁剪按 L2 范数
- [[normalization]] · RMSNorm 除以 L2/√n;归一化跟范数同源
- [[matrix-rank]] · 低秩是另一种"约束复杂度";正则约束的是权重大小
- [[cross-entropy]] · 总 loss = 交叉熵 + λ·正则项
