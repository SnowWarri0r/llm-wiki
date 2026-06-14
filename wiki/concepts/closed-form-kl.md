---
name: closed-form-kl
type: concept
sources: [diffusion-opd]
updated: 2026-06-12
---

# 闭式 KL · 同协方差高斯 KL = 均值差²

## 一句话
"闭式"= 有个干净公式能直接代数算（对立面是撒随机点模拟着估）；两个**同协方差高斯**的 KL 散度就有闭式解，直接塌成两个均值差的平方（MSE）。

## 直觉 · 公式直算 vs 撒豆子估

先回顾 **KL 散度**（[[cross-entropy]] 里见过）：衡量**两个分布差多少**——用 Q 描述真相 P 时"多浪费/多惊讶"。一样就是 0，越不像越大。

**"闭式（closed-form）"** = 有个**公式直接代进去就出结果**：

- 圆面积 `πr²` → **闭式**，代进去就出
- 不知道公式、往正方形里**撒豆子**数落进圆内的比例去估面积（蒙特卡洛）→ **不是闭式**，慢、还带随机噪声

一般两个分布的 KL 是个积分，通常只能撒点估（贵、有方差）。但**两个高斯之间的 KL 有现成精确公式**——不用撒点。

## 怎么做的 · 同协方差时塌成 MSE

两个高斯的 KL 本来还带协方差的比值、行列式、迹这些项。但当两个高斯**胖瘦一样（同协方差 σ²I）**时，那些项**全约掉**，只剩均值之差：

```
KL( N(μ_s, σ²I) ‖ N(μ_t, σ²I) ) = ‖μ_s − μ_t‖² / (2σ²)
                                    └ 两个"雾心"的距离平方 ┘
```

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="ck-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#3a3128"/></marker></defs>
  <line class="reveal d1" x1="70" y1="175" x2="660" y2="175" stroke="#3a3128" stroke-width="1"/>
  <!-- teacher bell -->
  <path class="draw d2" pathLength="1000" d="M150,175 C210,175 230,60 290,60 C350,60 370,175 430,175" fill="none" stroke="#1a6a64" stroke-width="2.4"/>
  <line class="reveal d3" x1="290" y1="175" x2="290" y2="64" stroke="#1a6a64" stroke-width="1" stroke-dasharray="4 3"/>
  <text class="reveal d3" x="290" y="192" text-anchor="middle" font-size="10" fill="#1a6a64">μ_t</text>
  <!-- student bell -->
  <path class="draw d3" pathLength="1000" d="M270,175 C330,175 350,60 410,60 C470,60 490,175 550,175" fill="none" stroke="#9b2c2c" stroke-width="2.4"/>
  <line class="reveal d4" x1="410" y1="175" x2="410" y2="64" stroke="#9b2c2c" stroke-width="1" stroke-dasharray="4 3"/>
  <text class="reveal d4" x="410" y="192" text-anchor="middle" font-size="10" fill="#9b2c2c">μ_s</text>
  <!-- delta -->
  <line class="reveal d5" x1="290" y1="108" x2="410" y2="108" stroke="#3a3128" stroke-width="1.4" marker-start="url(#ck-h)" marker-end="url(#ck-h)"/>
  <text class="reveal d5" x="350" y="100" text-anchor="middle" font-size="10" font-weight="700" fill="#3a3128">‖μ_s − μ_t‖</text>
  <text class="reveal d6" x="600" y="88" text-anchor="middle" font-size="9" fill="#7a6f5d">两条一样宽</text>
  <text class="reveal d6" x="600" y="100" text-anchor="middle" font-size="9" fill="#7a6f5d">（同 σ）</text>
  <text class="reveal d6" x="360" y="220" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#3a3128">同宽钟形 → 差距只看峰心错开多远 → 一个 MSE</text>
</svg>
</figure>

这就是为什么 [[diffusion-opd]] 能把"每步让学生贴老师"的 KL 蒸馏，变成一个稳的 MSE：去噪每步是 [[markov-chain]] 的高斯转移，雾胖瘦 σ 由 schedule 定死、师生相同，于是 **KL 只剩比两个雾心隔多远**，没有 RL 那种采样方差。

## 代码出处
- `torch.distributions.kl_divergence(Normal(μ_s,σ), Normal(μ_t,σ))` 对高斯返回的就是这个闭式
- 实践里直接写成 `((mu_s - mu_t)**2).sum() / (2*sigma**2)`，省掉构造分布

## 链接
- [[cross-entropy]] · KL = 交叉熵 − 熵；这页是它在高斯上的闭式特例
- [[markov-chain]] · 同协方差的来历：每步雾胖瘦由 schedule 定、与策略无关
- [[diffusion-opd]] · 把每步 KL 蒸馏塌成均值 MSE 的那篇
