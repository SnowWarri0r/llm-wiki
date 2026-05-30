---
name: math-symbols
type: concept
sources: [flow-matching, attention-is-all-you-need, resnet, gpt-3]
updated: 2026-05-22
---

# 数学符号速查

ML paper 里反复出现的数学符号 + 它们对应的"工程意思"。看到不认识的就翻这页。

## 微积分相关

### `∂` · 偏导数（partial derivative）
"对某个变量求导，把其他变量当常数"。

例子：`∂y/∂x` = "y 怎么随 x 变"。当 y 还依赖别的变量（比如 z），∂ 表示<strong>只关心 x 这个轴</strong>，其他变量当固定。

工程类比：`gradient[x]` —— 多维空间里只看一个坐标方向的斜率。

### `∇` · nabla / 梯度（gradient）
对一个标量函数，<strong>对所有变量都求偏导，打包成一个向量</strong>。

例子：`∇f(x, y, z) = (∂f/∂x, ∂f/∂y, ∂f/∂z)` —— 一个 3 维向量，指向 f 增长最快的方向。

工程类比：`torch.autograd.grad(f, [x, y, z])` 返回的那个向量。

### `∇·` · 散度（divergence）
对一个<strong>向量场</strong> v(x)，∇·v 是<strong>每个点"流出 vs 流入"的差</strong>。

例子：风场里某点的散度大于 0 → 气流从这点向外发散；小于 0 → 气流向这点汇聚。

为什么 flow matching 关心散度：[[continuity-equation]] `∂p/∂t + ∇·(p·v) = 0` 就是说"粒子既不凭空冒出来也不凭空消失"（守恒）。

### `Δ` / `δ` · delta · 小变化
`Δt` = "时间的一小步"，`δx` = "x 的微小扰动"。在 ODE 里 `x_{t+Δt} = x_t + v·Δt` 就是"沿速度走一小步"。

## 概率相关

### `p(x)` · 概率密度
"x 这个值出现的相对密集程度"。不是概率，是密度（在连续情况下）。

数据分布 `p_data(x)` = 训练数据的密度，标准高斯 `N(0, I)` = `p_0(x) = (2π)^{-d/2}·exp(-||x||²/2)`。

### `E[·]` 或 `𝔼[·]` · 期望（expectation）
"概率加权平均"。

```python
E_{x ~ p}[f(x)]  # 等价于
# (1/N) * sum(f(x_i) for x_i in samples_from_p)  当 N → ∞
```

flow matching loss 公式里的 `E_{t, x_0, x_1}[...]` = "对所有 (t, x_0, x_1) 的组合求平均"。

### `log p(x)` · 对数概率
直接用 p 数值范围太广（10⁻¹⁰ 到 1.0），取 log 后变成 -23 到 0 这种神经网络友好的范围。

### `∇log p(x)` · score
就是上面"梯度"应用到"对数概率"。直觉上：<strong>这个向量指向概率密度更大的方向</strong>。详见 [[score-function]]。

### `ε` · epsilon · 噪声
通常表示 `ε ~ N(0, I)` —— 一个标准高斯噪声向量。diffusion 加噪 / flow matching 起点都用它。

## 线性代数相关

### `||x||` · 向量的 norm（长度）
默认是 L2 norm：`||x|| = sqrt(x₁² + x₂² + ... + x_d²)` —— 欧几里得距离。

`||x||²` 就是去掉根号：`x₁² + ... + x_d²`。loss 函数里常见的 `||a - b||²` 是 MSE 的向量版。

### `Q · Kᵀ` · 矩阵乘 + 转置
- `·` 矩阵乘法（在 numpy/torch 里写成 `@`）
- `Kᵀ` = K 的转置（行列互换）

attention 里的 `Q · Kᵀ` 是 [seq, d] @ [d, seq] = [seq, seq] —— 每对 (i, j) 算一个 attention score。

### `I` · 单位矩阵 / identity matrix
对角线 1，其他位置 0。`N(0, I)` = 各维独立的标准高斯。

### `√` · 平方根
注意 `√d_k` 在 attention 里是 d_k 的<strong>标量</strong>平方根，不是矩阵开根。`sqrt(64) = 8`，用来除 attention score 防 softmax 饱和。

## 函数相关

### `f_θ(x)` · 参数化函数
下标 θ 表示"这个函数由参数 θ 决定"。神经网络通常写成 `u_θ`、`f_θ` —— θ 就是 weights。训练 = 找最优 θ。

### `~` · 采样自
`x ~ N(0, I)` = "x 从标准高斯里采样"。
`t ~ U(0, 1)` = "t 从 [0, 1] 均匀分布采样"。

### `→` / `↦` · 映射 / 函数
`f: ℝᵈ → ℝᵏ` = "f 把 d 维向量映射到 k 维"。

### `argmin` / `argmax`
`argmin_x f(x)` = "让 f 最小的那个 x"。训练 loss 是 `argmin_θ L(θ)`。

## 微分方程相关

### ODE · 普通微分方程
`dx/dt = v(x, t)` —— 给定 v，给定 x_0，<strong>解唯一</strong>。flow matching 用这个。

求解：欧拉法 `x_{t+Δt} = x_t + v(x_t, t)·Δt`，或更高阶的 RK4。

### SDE · 随机微分方程
`dx = f(x, t)·dt + g(t)·dW` —— 比 ODE 多了 `dW`（Wiener process，布朗运动），<strong>带随机扰动</strong>。同样 x_0 跑两次结果不同。diffusion 用这个。

详见 [[ode-vs-sde]]。

### `dW` · Wiener process 增量
布朗运动的微小变化。可理解为 `dW ~ N(0, dt)` 的小随机扰动。

## 希腊字母速查（常用）

| 字母 | 读音 | 通常含义 |
|---|---|---|
| α (alpha) | alpha | noise schedule 系数（如 ᾱ_t） |
| β (beta) | beta | regularization / noise variance |
| γ (gamma) | gamma | learning rate / discount |
| δ (delta) | delta | 微小变化 |
| ε (epsilon) | epsilon | 噪声 / 容差 |
| θ (theta) | theta | 模型参数 |
| λ (lambda) | lambda | 权重系数 / 特征值 |
| μ (mu) | mu | 均值 |
| σ (sigma) | sigma | 标准差 |
| τ (tau) | tau | 温度 / 时间常数 |
| φ (phi) | phi | 函数（如 phi 网络） |
| ψ (psi) | psi | 另一个函数 |
| ω (omega) | omega | 频率 / 权重 |

带 bar 的（如 ᾱ）通常表示"累积的"或"平均的"。带 hat 的（如 x̂）表示"估计的 / 预测的"。

## 链接
- [[ode-vs-sde]] · ODE vs SDE 详细
- [[score-function]] · score 详细
- [[velocity-field]] · flow matching 学的东西
- [[probability-path]] · 概率密度演化路径
- [[continuity-equation]] · 粒子守恒方程详解
