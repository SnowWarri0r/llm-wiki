---
name: next-token-forward-pass
type: concept
sources: [gpt-2, attention-is-all-you-need]
updated: 2026-06-05
---

# 一次前向 · 从 token 到下一个 token（每一步算了什么）

## 一句话
跟着一个 token 走完整条前向链：**查表成向量 → QKV 算注意力 → 堆 N 层 → 末位向量撞词表 → softmax 出概率 → 挑一个 token**。两个 softmax 不是一回事，是这页要拆清的关键。

## 先把最容易混的点钉死 · 两个 softmax

Transformer 里有**两个完全不同的 softmax**，初学者几乎都会混：

| | **注意力 softmax** | **输出 softmax** |
|---|---|---|
| 在**什么集合**上归一化 | 序列里的**位置**（前面 N 个 token） | 整个**词表**（5 万个候选 token） |
| 出来的是 | 注意力**权重**（我该看前面哪几个词） | 下一个 token 的**概率分布** |
| 出现在 | 每一层 attention 内部，N 层就有 N 次 | **只在最后**，整个模型一次 |
| 形状 | N×N | 1×词表大小（如 50257） |

你问的"怎么通过 softmax 得到概率分布"——是**右边那个**。"怎么跟 token 匹配上"——是它前面一步（LM head）。下面端到端走一遍，标清每一步。

## 全流程一张图

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#1f3a5f"/></marker>
  </defs>
  <!-- token -->
  <g class="reveal d1">
    <rect x="20" y="95" width="74" height="40" rx="3" fill="#ffffff" stroke="#1f3a5f"/>
    <text x="57" y="112" text-anchor="middle" font-size="11" fill="#3a3128">"垫"</text>
    <text x="57" y="127" text-anchor="middle" font-size="8.5" fill="#7a6f5d">token id</text>
    <line x1="94" y1="115" x2="118" y2="115" stroke="#1f3a5f" stroke-width="1.4" marker-end="url(#ar)"/>
  </g>
  <!-- embedding -->
  <g class="reveal d2">
    <rect x="120" y="90" width="86" height="50" rx="3" fill="#dbe6f0" stroke="#1f3a5f"/>
    <text x="163" y="109" text-anchor="middle" font-size="10" fill="#3a3128">查表→向量</text>
    <text x="163" y="124" text-anchor="middle" font-size="8.5" fill="#7a6f5d">[768]</text>
    <line x1="206" y1="115" x2="230" y2="115" stroke="#1f3a5f" stroke-width="1.4" marker-end="url(#ar)"/>
  </g>
  <!-- N layers -->
  <g class="reveal d3">
    <rect x="232" y="78" width="150" height="74" rx="3" fill="#c8d4e2" stroke="#1f3a5f"/>
    <text x="307" y="98" text-anchor="middle" font-size="10" font-weight="700" fill="#1f3a5f">× N 层</text>
    <text x="307" y="116" text-anchor="middle" font-size="9" fill="#3a3128">QKV → attn softmax</text>
    <text x="307" y="130" text-anchor="middle" font-size="9" fill="#3a3128">→ 加权和V → FFN</text>
    <text x="307" y="145" text-anchor="middle" font-size="8" fill="#7a6f5d">每个位置仍是 [768]</text>
    <line x1="382" y1="115" x2="406" y2="115" stroke="#1f3a5f" stroke-width="1.4" marker-end="url(#ar)"/>
  </g>
  <!-- final vector -->
  <g class="reveal d4">
    <rect x="408" y="90" width="92" height="50" rx="3" fill="#dbe6f0" stroke="#1f3a5f"/>
    <text x="454" y="106" text-anchor="middle" font-size="9.5" fill="#3a3128">末位向量</text>
    <text x="454" y="120" text-anchor="middle" font-size="8.5" fill="#7a6f5d">[768]</text>
    <text x="454" y="132" text-anchor="middle" font-size="8" fill="#9b2c2c">"接下来"的浓缩</text>
    <line x1="500" y1="115" x2="524" y2="115" stroke="#1f3a5f" stroke-width="1.4" marker-end="url(#ar)"/>
  </g>
  <!-- LM head -->
  <g class="reveal d5">
    <rect x="526" y="82" width="86" height="66" rx="3" fill="#f3d9d9" stroke="#9b2c2c"/>
    <text x="569" y="100" text-anchor="middle" font-size="9.5" font-weight="700" fill="#9b2c2c">LM head</text>
    <text x="569" y="114" text-anchor="middle" font-size="8.5" fill="#3a3128">撞整个词表</text>
    <text x="569" y="127" text-anchor="middle" font-size="8.5" fill="#3a3128">→ logits</text>
    <text x="569" y="140" text-anchor="middle" font-size="8" fill="#7a6f5d">[50257]</text>
    <line x1="612" y1="115" x2="636" y2="115" stroke="#9b2c2c" stroke-width="1.4" marker-end="url(#ar)"/>
  </g>
  <!-- softmax + token -->
  <g class="reveal d6">
    <rect x="638" y="90" width="66" height="50" rx="3" fill="#ffffff" stroke="#9b2c2c"/>
    <text x="671" y="106" text-anchor="middle" font-size="9" fill="#9b2c2c">softmax</text>
    <text x="671" y="119" text-anchor="middle" font-size="8" fill="#7a6f5d">→概率→挑</text>
    <text x="671" y="133" text-anchor="middle" font-size="11" fill="#3a3128">"子"</text>
  </g>
  <!-- two softmax labels -->
  <g class="reveal d4">
    <text x="307" y="185" text-anchor="middle" font-size="9" fill="#1f3a5f">↑ 注意力 softmax（在位置上，N 次）</text>
    <line x1="307" y1="152" x2="307" y2="176" stroke="#1f3a5f" stroke-width="0.8" stroke-dasharray="3 2"/>
  </g>
  <g class="reveal d6">
    <text x="569" y="205" text-anchor="middle" font-size="9" fill="#9b2c2c">↑ 输出 softmax（在词表上，1 次）</text>
    <line x1="569" y1="148" x2="569" y2="196" stroke="#9b2c2c" stroke-width="0.8" stroke-dasharray="3 2"/>
  </g>
</svg>
</figure>

## ① token → 向量 · 查表
token 不是字，是个**整数 id**（"垫" 可能是 id 27431）。模型第一件事是拿这个 id 去**嵌入表**里查出一行向量，比如 768 维。从此这个 token 在模型里就是一个 [768] 的向量，后面所有计算都在向量上做。

## ② QKV · 每个 token 算出三样东西
对每个位置的向量 x，乘三个权重矩阵得到三个新向量（详见 [[self-attention]]）：

```
Q = x · W_Q   # 我想找什么（query，提问）
K = x · W_K   # 我能被什么找到（key，标签）
V = x · W_V   # 被选中后我交出什么（value，内容）
```

直觉：每个 token 既是个**提问者**（Q），又是个**带标签的资料**（K 是标签、V 是正文）。注意力就是"拿我的提问 Q，去跟所有 token 的标签 K 比对，谁对得上就多抄一点谁的正文 V"。

## ③ 注意力 softmax · 在"位置"上得到权重
拿当前 token 的 Q，跟前面每个 token 的 K 做点积 → 一串"匹配分"。**这串分过 softmax，归一化成权重**（加起来=1）：

```
scores  = Q · Kᵀ / √d        # 跟前面每个位置的匹配分
weights = softmax(scores)     # ← 第一个 softmax：在【位置】上
out     = weights · V         # 按权重把各 token 的 V 加权抄过来
```

**这里的 softmax 输出的是"我该看前面哪几个词"，不是 token 概率**。一层里每个位置都干一次，N 层就有 N 轮。点积大→权重大→那个位置的 V 抄得多。

## ④ 堆 N 层 → 拿最后一个位置的向量
attention 出来再过 FFN（前馈），算一层。叠 N 层（GPT-2 small 是 12 层）。每过一层，每个位置的 [768] 向量被不断改写，越来越"懂上下文"。

> "堆 N 层"（深度，竖着叠）和 ③ 里的"多头"（一层内横着拆 h 个头）是**两个垂直的轴**，最容易混——区别和配图见 [[transformer-architecture]] 的"深度 vs 多头"一节。

预测下一个词时，我们只关心**最后一个位置**的那个 [768] 向量——它是模型对"接下来该是什么"的全部浓缩判断。

## ⑤ LM head · 末位向量怎么"撞"上 token（你问的匹配在这）
这一步回答"怎么跟 token 匹配上"。有一个**输出矩阵 W_out**，形状 `[词表大小 × 768]`——**每一行是一个 token 的"代表向量"**（"子"有一行，"垫"有一行，5 万个 token 5 万行）。

把末位向量 h 跟**每一行**做点积：

```
logit_i = h · W_out[i]     # h 跟第 i 个 token 的代表向量有多像
logits  = h · W_outᵀ       # 一次算完 → [50257] 个分数，每个 token 一个
```

**点积 = 相似度**。所以 `logit_i` 就是"末位向量 h 跟第 i 个 token 像不像"。h 越接近哪个 token 的代表向量，那个 token 的 logit 越高。这就是"匹配"的真相——**不是查表对号，是向量相似度打分**。

<figure style="margin:26px 0; padding:22px; background:#f4eee2; border:1px solid #c4bba6; border-radius:4px;">
<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="ar2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#9b2c2c"/></marker></defs>
  <!-- hidden vector h -->
  <g class="reveal d1">
    <text x="70" y="30" text-anchor="middle" font-size="11" font-weight="700" fill="#9b2c2c">末位向量 h</text>
    <text x="70" y="44" text-anchor="middle" font-size="8.5" fill="#7a6f5d">[768]</text>
    <rect x="52" y="55" width="36" height="18" fill="#9b2c2c" opacity="0.7"/>
    <rect x="52" y="73" width="36" height="18" fill="#9b2c2c" opacity="0.35"/>
    <rect x="52" y="91" width="36" height="18" fill="#9b2c2c" opacity="0.85"/>
    <rect x="52" y="109" width="36" height="18" fill="#9b2c2c" opacity="0.5"/>
    <text x="70" y="143" text-anchor="middle" font-size="9" fill="#7a6f5d">⋮</text>
  </g>
  <!-- dot with each row -->
  <g class="reveal d2">
    <text x="200" y="30" text-anchor="middle" font-size="10" fill="#3a3128">跟每个 token 的代表向量点积</text>
    <g font-size="10" fill="#3a3128">
      <text x="150" y="62">"子"  · h →</text>
      <text x="150" y="92">"垫"  · h →</text>
      <text x="150" y="122">"猫"  · h →</text>
      <text x="150" y="152">"香蕉" · h →</text>
      <text x="150" y="178" font-size="9" fill="#7a6f5d">…5 万个…</text>
    </g>
  </g>
  <!-- logits -->
  <g class="reveal d3">
    <text x="330" y="30" text-anchor="middle" font-size="10" font-weight="700" fill="#3a3128">logits（原始分）</text>
    <g font-size="10" fill="#3a3128">
      <text x="330" y="62" text-anchor="middle">8.2</text>
      <text x="330" y="92" text-anchor="middle">2.1</text>
      <text x="330" y="122" text-anchor="middle">1.5</text>
      <text x="330" y="152" text-anchor="middle">-3.0</text>
    </g>
    <line x1="370" y1="100" x2="400" y2="100" stroke="#9b2c2c" stroke-width="1.4" marker-end="url(#ar2)"/>
    <text x="430" y="30" text-anchor="middle" font-size="10" font-weight="700" fill="#9b2c2c">softmax</text>
    <text x="430" y="44" text-anchor="middle" font-size="8" fill="#7a6f5d">→概率</text>
  </g>
  <!-- prob bars：从左生长，错峰 -->
  <rect class="grow-x reveal d4" x="470" y="54" width="180" height="16" fill="#9b2c2c"/>
  <rect class="grow-x reveal d5" x="470" y="84" width="34" height="16" fill="#9b2c2c" opacity="0.6"/>
  <rect class="grow-x reveal d6" x="470" y="114" width="20" height="16" fill="#9b2c2c" opacity="0.45"/>
  <rect class="grow-x reveal d7" x="470" y="144" width="4" height="16" fill="#9b2c2c" opacity="0.3"/>
  <g>
    <text class="reveal d4" x="658" y="66" font-size="9" fill="#3a3128">"子" 0.89</text>
    <text class="reveal d5" x="512" y="96" font-size="9" fill="#3a3128">"垫" 0.06</text>
    <text class="reveal d6" x="498" y="126" font-size="9" fill="#3a3128">"猫" 0.03</text>
    <text class="reveal d7" x="482" y="156" font-size="9" fill="#3a3128">"香蕉" 0.00</text>
  </g>
  <text class="reveal d7" x="470" y="195" font-size="10" fill="#1f3a5f">↑ 在【整个词表】上归一化，加起来=1 → 这才是"下一个 token 的概率分布"</text>
  <text class="reveal d8" x="470" y="225" font-size="10" fill="#9b2c2c">挑最高的 → 输出 "子"（贪心）</text>
  <text class="reveal d8" x="470" y="245" font-size="9" fill="#7a6f5d">或按概率随机抽（temperature / top-k / top-p）</text>
</svg>
</figure>

> weight tying：GPT-2 里这个输出矩阵 W_out **就是输入嵌入表转置**——同一张表，进来时拿它把 token 查成向量，出去时拿它把向量撞回 token。"代表向量"和"嵌入向量"是同一个东西。

## ⑥ 输出 softmax · logits → 概率分布
5 万个 logits 还只是"原始分"，有正有负、加起来不等于 1。**过一次 softmax，归一化成概率**：每个 token 一个 0~1 的概率，全部加起来=1。这就是"下一个 token 的概率分布"。logit 最高的 token 概率最大。

## ⑦ 挑一个 token
- **贪心**：直接取概率最高的（图里的 "子"）。
- **采样**：按概率随机抽——temperature 调随机度，top-k / top-p 砍掉长尾只在高概率候选里抽。这就是为什么同一个 prompt 每次回答略有不同。

挑出的 token id → 查回字符 → 拼到序列末尾 → **整条链再跑一遍**预测再下一个。这就是"自回归"，也是 [[kv-cache]] 要优化的地方（前面 N 个 token 的 K/V 不用重算）。

## 链接
- [[self-attention]] · ②③ 的 QKV 与注意力细节
- [[transformer-architecture]] · ④ 的层怎么堆
- [[kv-cache]] · ⑦ 自回归时缓存前面的 K/V
- [[training-vs-inference]] · 训练时这条链是并行一次算完，推理时一个一个挤
- [[gpt-2]] · weight tying（输入嵌入 = 输出头）出处
- [[causal-language-model]] · 训练时怎么让模型只看左边来学这条链
- [[tokenization]] · ① 入口:文本先切成 token 才进模型
- [[sampling-decoding]] · ⑦ 出口:从 logits 分布里挑下一个 token
