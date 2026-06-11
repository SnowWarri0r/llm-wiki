---
name: cross-entropy
type: concept
sources: [gpt-2, dino]
updated: 2026-06-11
---

# Cross-Entropy · 交叉熵 · −log(你押对的概率)

## 一句话
模型对一堆候选输出一个概率分布，交叉熵只看一件事：**你给"正确答案"分了多少概率，取 −log**。押对的概率越高 loss 越低，越低 loss 暴涨。分类 / 预测下一个 token 的标准损失。

## 直觉 · −log 的脾气

`loss = −log(p_正确)`，这个形状是全部关键：

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- 轴 -->
  <g class="reveal d1" stroke="#3a3128" stroke-width="1">
    <line x1="80" y1="40" x2="80" y2="270"/>
    <line x1="80" y1="270" x2="668" y2="270"/>
  </g>
  <g class="reveal d1" font-size="9" fill="#7a6f5d">
    <text x="74" y="48" text-anchor="end">loss</text>
    <text x="668" y="288" text-anchor="end">你给正确答案的概率 p →</text>
    <text x="74" y="273" text-anchor="end">0</text>
    <text x="84" y="52" text-anchor="start">高</text>
    <text x="80" y="284" text-anchor="middle">0</text>
    <text x="370" y="284" text-anchor="middle">0.5</text>
    <text x="660" y="284" text-anchor="middle">1.0</text>
  </g>
  <!-- −log 曲线 -->
  <polyline class="draw d2" pathLength="1000" points="91,90 109,132 138,164 196,196 254,215 370,238 486,254 602,265 660,270" fill="none" stroke="#9b2c2c" stroke-width="2.4"/>
  <!-- 点 + 标注 -->
  <g class="reveal d3" font-size="9" fill="#3a3128">
    <circle cx="138" cy="164" r="4" fill="#9b2c2c"/><text x="148" y="160">p=0.1 → 2.30</text>
    <circle cx="370" cy="238" r="4" fill="#9b2c2c"/><text x="380" y="234">p=0.5 → 0.69</text>
    <circle cx="602" cy="265" r="4" fill="#9b2c2c"/><text x="540" y="258" text-anchor="end">p=0.9 → 0.10</text>
  </g>
  <text class="reveal d4" x="150" y="70" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#9b2c2c">p→0：自信答错 → loss 爆炸(→∞)</text>
  <text class="reveal d4" x="600" y="248" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#4a6b3a">p→1：押对 → loss→0</text>
</svg>
</figure>

```
你给对的概率 → loss
   1.0       → 0       （完全确定且对，无损失）
   0.5       → 0.693
   0.1       → 2.30
   0.01      → 4.61
   →0        → →∞      （自信地答错，惩罚趋于无穷）
```

交叉熵的脾气：**不光要你答对，还要你"敢对"**；但**自信地错会被往死里罚**。这逼模型诚实地分配概率，不敢乱赌——蒙混（什么都给 0.5）loss 不低，赌错（给错的答案高分）loss 爆炸。

## 怎么做的 · 为什么叫"交叉"

它本质是比**两个分布**：你预测的 `p` vs 真实的 `q`。完整式子 `−Σ q·log p`（对所有候选，真实概率 × 你给的 log 概率，求和取负）。

- **分类 / 预测 token**：真实分布 `q` 是 **one-hot**——概率全压在正确那一项（是猫 → [猫=1, 其它=0]）。代进去，求和只剩正确项，塌成 `−log(p_正确)`。最常见。
- **软标签（如 [[dino]]）**：`q` **不是 one-hot**，是另一个分布（teacher 的软输出）。这时用完整的 `−Σ q·log p`——让整条预测分布去贴整条目标分布，不是只对一个答案。

## 更妙的直觉 · 用错码本多花的比特

信息论视角：**熵** = 用最优编码给一个分布编码、平均花多少比特。**交叉熵** = 你拿**预测分布 p 当码本**去编码**真实分布 q** 实际花的比特。猜得越不准、编码越浪费 → 交叉熵越大。它永远 ≥ 真实分布自己的熵，**多出来的正好是 KL 散度**：

```
交叉熵(q, p) = 熵(q) + KL(q ‖ p)
```

熵(q) 是真值自带、固定的。所以 **最小化交叉熵 = 最小化 KL(q‖p) = 让预测分布 p 逼近真实分布 q**。训练在干的就是这个。

## 代码出处
- `torch.nn.CrossEntropyLoss`（内部 = log_softmax + NLLLoss）/ `F.cross_entropy`
- 几乎所有分类、LLM 预训练（[[next-token-forward-pass]] 的输出 softmax）都用它

## 链接
- [[next-token-forward-pass]] · LLM 预训练损失 = 对真实下一个 token 的交叉熵
- [[dino]] · student 软分布 vs teacher 软分布的交叉熵
- [[grpo]] · 在交叉熵基础上加 reward 加权 + KL 约束
- [[rl-for-llm-people]] · KL 散度跟交叉熵的关系在这条线里
