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

## 代码出处
- 概念性：把 GRPO 实现里逐 token 的 `ratio = exp(logp_new - logp_old)` 换成**整条序列求和再除以长度**：`ratio = exp((logp_new.sum() - logp_old.sum()) / len)`，clip 与加权改在序列维度
- 来源：Qwen 团队 GSPO 论文（arXiv 2507.18071，2025）

## 链接
- [[grpo]] · GSPO 的直接前身；只把 token 级比率换成序列级
- [[ppo]] · 重要性比率 + clip 的老家
- [[rl-for-llm-people]] · 重要性采样 / off-policy 这些术语先在这打底
- [[qwen3-asr]] · RL 阶段用 GSPO 磨噪声鲁棒 + 转写稳定
