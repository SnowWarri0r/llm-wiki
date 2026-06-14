---
name: gspo
type: concept
sources: [qwen3-asr]
updated: 2026-06-14
---

# GSPO · Group Sequence Policy Optimization · 把重要性比率提到序列级

## 一句话
GRPO 在 **token 级**算重要性比率（每个 token 一个 `r`）；GSPO 把比率提到**整条序列**——因为每个 token 只采一次、token 级比率是高方差噪声、容易把训练带崩，而奖励本来就是给整条序列的。

## 直觉 · 别逐字纠，看整篇

先接上 [[grpo]]：它的 loss 还是 PPO 那套 `clip(r, 1±ε)·A + KL`，其中 `r = π_new / π_old` 是**重要性比率**（新旧策略给同一段输出的概率之比，用来做 off-policy 校正）。GRPO 给**每个 token 各算一个 `r_t`**。

问题在这儿：**每个 token 在那条采样里只出现一次**。拿"只采了一个样本"去估一个 token 的概率比，根本做不了有效的分布校正，只会**灌进高方差噪声** → 梯度估计不稳 → 长序列、尤其 MoE（路由让每步概率更抖）下**训练直接崩**。

GSPO 的修法：**奖励既然是给<u>整条</u>回答的，off-policy 校正和优化就也该在<u>整条序列</u>级别做**。用整句的似然比当一个 `r_seq`，clip、加权、优化全在序列级。

> 类比：给一篇作文打分，你不会**逐字**去纠"这个字该不该写"（噪声大、还自相矛盾），而是看**整篇**好坏来调。逐字微调是抖动，整篇判断才稳。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <line x1="360" y1="34" x2="360" y2="226" class="reveal d1" stroke="#bfb398" stroke-width="1" stroke-dasharray="5 4"/>
  <!-- 左 GRPO token 级 -->
  <text class="reveal d1" x="175" y="44" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#9b2c2c">GRPO · token 级</text>
  <g class="reveal d2" font-size="9" text-anchor="middle">
    <rect x="40" y="100" width="42" height="30" rx="3" fill="#faf4e1" stroke="#bfb398"/><text x="61" y="119" fill="#3a3128">y₁</text>
    <rect x="92" y="100" width="42" height="30" rx="3" fill="#faf4e1" stroke="#bfb398"/><text x="113" y="119" fill="#3a3128">y₂</text>
    <rect x="144" y="100" width="42" height="30" rx="3" fill="#faf4e1" stroke="#bfb398"/><text x="165" y="119" fill="#3a3128">y₃</text>
    <rect x="196" y="100" width="42" height="30" rx="3" fill="#faf4e1" stroke="#bfb398"/><text x="217" y="119" fill="#3a3128">y₄</text>
    <rect x="248" y="100" width="42" height="30" rx="3" fill="#faf4e1" stroke="#bfb398"/><text x="269" y="119" fill="#3a3128">y₅</text>
  </g>
  <!-- 每 token 一个抖动比率 -->
  <g class="reveal d3" font-size="8.5" font-weight="700" fill="#9b2c2c" text-anchor="middle">
    <text x="61" y="84">r₁=1.4</text><text x="113" y="84">r₂=0.6</text><text x="165" y="84">r₃=1.7</text><text x="217" y="84">r₄=0.5</text><text x="269" y="84">r₅=1.3</text>
  </g>
  <text class="reveal d3" x="175" y="162" text-anchor="middle" font-size="9.5" fill="#9b2c2c">每 token 一个比率，只采一次</text>
  <text class="reveal d4" x="175" y="180" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#9b2c2c">高方差噪声 → 易崩（MoE 更甚）</text>
  <!-- 右 GSPO 序列级 -->
  <text class="reveal d4" x="545" y="44" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#1a6a64">GSPO · 序列级</text>
  <g class="reveal d5" font-size="9" text-anchor="middle">
    <rect x="420" y="100" width="42" height="30" rx="3" fill="#cce5e1" stroke="#1a6a64"/><text x="441" y="119" fill="#0f4a45">y₁</text>
    <rect x="472" y="100" width="42" height="30" rx="3" fill="#cce5e1" stroke="#1a6a64"/><text x="493" y="119" fill="#0f4a45">y₂</text>
    <rect x="524" y="100" width="42" height="30" rx="3" fill="#cce5e1" stroke="#1a6a64"/><text x="545" y="119" fill="#0f4a45">y₃</text>
    <rect x="576" y="100" width="42" height="30" rx="3" fill="#cce5e1" stroke="#1a6a64"/><text x="597" y="119" fill="#0f4a45">y₄</text>
    <rect x="628" y="100" width="42" height="30" rx="3" fill="#cce5e1" stroke="#1a6a64"/><text x="649" y="119" fill="#0f4a45">y₅</text>
  </g>
  <!-- 一个序列级比率罩住 -->
  <path class="reveal d6" d="M420,86 L670,86" stroke="#1a6a64" stroke-width="2"/>
  <path class="reveal d6" d="M420,86 L420,94 M670,86 L670,94" stroke="#1a6a64" stroke-width="2"/>
  <text class="reveal d6" x="545" y="80" text-anchor="middle" font-size="9.5" font-weight="700" fill="#1a6a64">整条一个比率 r_seq（似然比，长度归一）</text>
  <text class="reveal d6" x="545" y="162" text-anchor="middle" font-size="9.5" fill="#1a6a64">跟奖励同粒度（奖励本就给整条）</text>
  <text class="reveal d6" x="545" y="180" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#1a6a64">低方差 → 稳，尤其救活 MoE RL</text>
</svg>
</figure>

## 怎么做的

```
GRPO（token 级）:  r_t = π_new(y_t | x, y_<t) / π_old(y_t | x, y_<t)   # 每个 token 各 clip
GSPO（序列级）:    r_seq = ( π_new(y | x) / π_old(y | x) )^(1/|y|)      # 整条一个比率，长度归一
                  loss = clip(r_seq, 1±ε) · A      # clip / 优化都在序列级
```

- **A 还是 [[grpo]] 那个组相对 advantage**（同 prompt 采 G 条、组内标准化）——GSPO 只改"重要性比率在哪一级"，不动 advantage 的算法。
- **长度归一**（开 `1/|y|` 次方）让不同长度的序列比率可比，避免长序列比率指数爆/塌。
- 好处：**低方差、稳**；显著**稳住 MoE 的 RL 训练**（token 级在 MoE 上尤其抖）；简化 RL 基建。Qwen3 / [[qwen3-asr]] 的 RL 阶段用的就是它。

## 举个数字例子 · 4 个 token 的回答

设一条回答 `y` 只有 4 个 token，列出新旧策略给每个 token 的概率，顺手算 token 级比率 `r_t = π_new/π_old`：

| token | π_old | π_new | r_t（token 级） |
|---|---|---|---|
| y₁ | 0.5 | 0.6 | 1.20 |
| y₂ | 0.4 | 0.2 | **0.50** ← 抖得最凶 |
| y₃ | 0.6 | 0.7 | 1.17 |
| y₄ | 0.5 | 0.55 | 1.10 |

**GRPO（token 级）**：每个 token 各拿自己的 `r_t` 去 clip + 更新。`y₂` 的 0.50 是个大摆动，还**超出 clip 区间 [0.8, 1.2] → 被砍到 0.8**，单这一个 token 就被狠推一下。一条回答里几个这种"只采一次、估不准"的 token，梯度就被搅得很抖。

**GSPO（序列级）**：先把整条似然乘起来，再开 `|y|` 次方：

```
P_old(y|x) = 0.5·0.4·0.6·0.5    = 0.0600
P_new(y|x) = 0.6·0.2·0.7·0.55   = 0.0462
raw 比      = 0.0462 / 0.0600    = 0.77
r_seq = 0.77 ^ (1/4)            ≈ 0.94      # 开 4 次方 = 长度归一
```

`r_seq` 正好是 4 个 token 比率的**几何平均**：`(1.20·0.50·1.17·1.10)^(1/4) ≈ 0.94`。**那个抖得最凶的 0.50，被另外三个正常 token 一揉，稀释成温和的 0.94**——一个稳的比率罩住整条，跟"奖励本来就是给整条回答的"对上了。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- clip 区间带 -->
  <rect class="reveal d1" x="60" y="110" width="560" height="40" fill="#d8e6ce" opacity="0.5"/>
  <text class="reveal d1" x="614" y="118" text-anchor="end" font-size="8.5" fill="#4a6b3a">clip 区间 [0.8, 1.2]</text>
  <!-- baseline r=1 -->
  <line class="reveal d1" x1="60" y1="130" x2="620" y2="130" stroke="#7a6f5d" stroke-width="1" stroke-dasharray="5 4"/>
  <text class="reveal d1" x="64" y="126" font-size="8.5" fill="#7a6f5d">r = 1.0（新旧一样）</text>
  <!-- token 级柱 -->
  <g class="reveal d2">
    <rect x="118" y="110" width="44" height="20" fill="#9b2c2c" opacity="0.5"/>
    <text x="140" y="104" text-anchor="middle" font-size="9" font-weight="700" fill="#9b2c2c">1.20</text>
  </g>
  <g class="reveal d3">
    <rect x="268" y="130" width="44" height="50" fill="#9b2c2c"/>
    <text x="290" y="194" text-anchor="middle" font-size="9" font-weight="700" fill="#9b2c2c">0.50</text>
    <line x1="262" y1="150" x2="318" y2="150" stroke="#9b2c2c" stroke-width="1.4" stroke-dasharray="3 2"/>
    <text x="324" y="153" font-size="8" fill="#9b2c2c">← 被 clip 到 0.8，狠推一下</text>
  </g>
  <g class="reveal d4">
    <rect x="418" y="113" width="44" height="17" fill="#9b2c2c" opacity="0.5"/>
    <text x="440" y="107" text-anchor="middle" font-size="9" font-weight="700" fill="#9b2c2c">1.17</text>
  </g>
  <g class="reveal d4">
    <rect x="538" y="120" width="44" height="10" fill="#9b2c2c" opacity="0.5"/>
    <text x="560" y="114" text-anchor="middle" font-size="9" font-weight="700" fill="#9b2c2c">1.10</text>
  </g>
  <!-- token 标签 -->
  <g class="reveal d2" font-size="9" fill="#3a3128" text-anchor="middle">
    <text x="140" y="214">y₁</text><text x="290" y="214">y₂</text><text x="440" y="214">y₃</text><text x="560" y="214">y₄</text>
  </g>
  <text class="reveal d2" x="140" y="228" text-anchor="middle" font-size="8" fill="#9b2c2c">token 级：各推各的</text>
  <!-- 序列级 r_seq 线 -->
  <line class="draw d3" pathLength="1000" x1="110" y1="136" x2="590" y2="136" stroke="#1a6a64" stroke-width="2.6"/>
  <text class="reveal d5" x="350" y="246" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#1a6a64">r_seq = 0.94（几何平均）→ 一个稳值罩整条，0.50 被揉化</text>
</svg>
</figure>

**为什么要开 `1/|y|` 次方（长度归一）**：不归一的话，raw 比是所有 token 概率比的**连乘**，会随长度**指数爆/塌**——100 个 token 的连乘比可能小到 `1e-10`。开 `|y|` 次方把它拉回"平均每 token 的比率"尺度，不同长度的回答**可比**，长回答也不会因为长就被放大。

## 代码出处
- 概念性：把 GRPO 实现里逐 token 的 `ratio = exp(logp_new - logp_old)` 换成**整条序列求和再除以长度**：`ratio = exp((logp_new.sum() - logp_old.sum()) / len)`，clip 与加权改在序列维度
- 来源：Qwen 团队 GSPO 论文（arXiv 2507.18071，2025）

## 链接
- [[grpo]] · GSPO 的直接前身；只把 token 级比率换成序列级
- [[ppo]] · 重要性比率 + clip 的老家
- [[rl-for-llm-people]] · 重要性采样 / off-policy 这些术语先在这打底
- [[qwen3-asr]] · RL 阶段用 GSPO 磨噪声鲁棒 + 转写稳定
