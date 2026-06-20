---
name: markov-chain
type: concept
sources: [diffusion-opd, ode-sde]
updated: 2026-06-12
---

# Markov Chain · 马尔可夫链 · 只看现在、不看历史

## 一句话
一串状态，下一步**只取决于你现在在哪、跟怎么走到这儿无关**（无记忆）；每步用一条"转移核"规则跳。扩散去噪就是它的高斯版。

## 直觉 · 跳格子 / 天气

马尔可夫链就一条性质：**无记忆**。

- **跳格子游戏**：你下一步能去哪，只看你<strong>现在</strong>站哪一格；前面掷了几次骰子绕过来的，游戏不在乎。
- **天气模型**：明天的天气只由<strong>今天</strong>推，上周怎样不直接进公式。

```
P(x_next | x_now, x_前, x_更前, …)  =  P(x_next | x_now)
                                          └ 只剩当前这一项 ┘
```

中间那个 `P(x_next | x_now)` 叫**转移核**——"站这儿，下一步会去哪"的规则。整条链 = 反复套用这条规则。

## 高斯转移 · 下一步不是一个点，是一团钟形雾

普通链下一步可能是个确定位置。**高斯**马尔可夫链是说：每步的转移核是个**正态分布（钟形）**——给定 `x_now`，下一步 `x_next` 从一团**钟形雾**里抽：

- 雾的**中心（均值 μ）**= "该往哪挪"（扩散里是模型猜的）
- 雾的**胖瘦（协方差 σ²）**= 这步有多少不确定 / 噪声

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="mc-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#1f3a5f"/></marker>
  <marker id="mc-x" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker></defs>
  <!-- 钟形雾（每步转移） -->
  <g class="draw d2" fill="none" stroke="#4a6b3a" stroke-width="1.6">
    <path pathLength="1000" d="M150,96 C172,96 178,62 200,62 C222,62 228,96 250,96"/>
    <path pathLength="1000" d="M330,96 C352,96 358,62 380,62 C402,62 408,96 430,96"/>
    <path pathLength="1000" d="M510,96 C532,96 538,62 560,62 C582,62 588,96 610,96"/>
  </g>
  <text class="reveal d3" x="380" y="48" text-anchor="middle" font-size="9.5" fill="#4a6b3a">每步 = 一团钟形雾（雾心 μ · 雾胖瘦 σ）</text>
  <!-- 状态节点 -->
  <g class="reveal d1" font-size="11" font-weight="700" text-anchor="middle">
    <circle cx="100" cy="130" r="22" fill="#c8d4e2" stroke="#1f3a5f"/><text x="100" y="134" fill="#1f3a5f">x_T</text>
    <circle cx="280" cy="130" r="22" fill="#faf4e1" stroke="#1f3a5f"/><text x="280" y="134" fill="#1f3a5f">x₂</text>
    <circle cx="460" cy="130" r="22" fill="#faf4e1" stroke="#1f3a5f"/><text x="460" y="134" fill="#1f3a5f">x₁</text>
    <circle cx="640" cy="130" r="22" fill="#d8e6ce" stroke="#4a6b3a" stroke-width="1.6"/><text x="640" y="134" fill="#3a5a2a">x₀</text>
  </g>
  <g class="reveal d1" font-size="8" fill="#7a6f5d" text-anchor="middle">
    <text x="100" y="166">噪声</text><text x="640" y="166">图像</text>
  </g>
  <!-- 转移箭头（只看前一格） -->
  <g class="reveal d2" stroke="#1f3a5f" stroke-width="1.8" fill="none">
    <line x1="124" y1="120" x2="256" y2="120" marker-end="url(#mc-h)"/>
    <line x1="304" y1="120" x2="436" y2="120" marker-end="url(#mc-h)"/>
    <line x1="484" y1="120" x2="616" y2="120" marker-end="url(#mc-h)"/>
  </g>
  <text class="reveal d3" x="190" y="113" text-anchor="middle" font-size="8.5" fill="#1f3a5f">只看前一格</text>
  <!-- 被无视的历史 -->
  <path class="reveal d4" d="M100,156 Q280,220 452,150" fill="none" stroke="#9b2c2c" stroke-width="1.4" stroke-dasharray="5 3" marker-end="url(#mc-x)"/>
  <text class="reveal d4" x="270" y="214" text-anchor="middle" font-size="9" fill="#9b2c2c">✗ 不看更早的历史（无记忆）</text>
  <text class="reveal d5" x="360" y="240" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#3a3128">扩散去噪 = 一串只看当下、每步钟形雾的跳跃</text>
</svg>
</figure>

## 怎么做的 · 扩散就是高斯马尔可夫链

把 [[ode-sde]] 那条**反向 SDE 按时间切成离散步**，每步正好是"按 drift 挪到雾心 μ + 加一团高斯噪声 σ" = **一个高斯转移**。所以：

> **反向 SDE 离散化 = 高斯马尔可夫链** —— 同一个东西两种说法。

关键细节（[[diffusion-opd]] 靠它）：**每步雾的胖瘦 σ_t 是提前定好的 noise schedule 说了算，模型只决定雾心 μ 往哪瞄**。于是学生、老师两个模型，**雾一样胖、只是雾心瞄的地方不同** → 才有 [[closed-form-kl]]（同协方差高斯 KL=均值差²）。

## 代码出处
- 概念性：任何 DDPM 实现的 `p_sample` 循环——每步 `x = μ_θ(x, t) + σ_t · z`（z~N(0,1)），就是一次高斯转移
- [[ode-sde]] 的 Euler–Maruyama 一步 `x += f·dt + √dt·g·z` 是它的连续时间版

## 链接
- [[ode-sde]] · 反向 SDE 离散化就是高斯马尔可夫链
- [[closed-form-kl]] · 同协方差高斯每步 KL 有闭式解
- [[diffusion-opd]] · 用"每步高斯转移"把蒸馏 KL 塌成 MSE
