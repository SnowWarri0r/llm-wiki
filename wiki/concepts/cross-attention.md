---
name: cross-attention
type: concept
sources: [attention-is-all-you-need]
updated: 2026-05-22
---

# Cross-Attention · 交叉注意力

## 一句话
Decoder 用自己的 Query，去查 Encoder 输出的 Key/Value，让生成过程能看见输入序列。

## 直觉
Self-attention 是"班里同学互相看"；cross-attention 是"写答案的人翻参考资料"。翻译任务里，encoder 先读完整个源语言句子；decoder 每生成一个目标词，就用 cross-attention 回头查源句里相关位置。

## 看一遍 · Decoder 翻 Encoder 的资料（动图）

翻译 "我爱猫" → 已生成 "I love"，decoder 现在要出下一个词。它的当前向量做 **Q**，去跟 encoder 三个词的 **K** 逐个比对，"猫"命中、权重最高，于是把"猫"的 **V** 抄回来 → 解出 cat。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 330" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <text x="130" y="38" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f3a5f">Encoder 输出（源句 我爱猫）</text>
  <text x="600" y="38" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">Decoder（已生成 I love…）</text>

  <!-- Encoder 三个词 K/V（静态底） -->
  <g>
    <rect x="65" y="70" width="130" height="46" rx="3" fill="#dbe6f0" stroke="#1f3a5f"/>
    <text x="130" y="92" text-anchor="middle" font-size="13" fill="#1f3a5f">我</text><text x="130" y="108" text-anchor="middle" font-size="8.5" fill="#5b6b7d">K · V</text>
  </g>
  <g>
    <rect x="65" y="142" width="130" height="46" rx="3" fill="#dbe6f0" stroke="#1f3a5f"/>
    <text x="130" y="164" text-anchor="middle" font-size="13" fill="#1f3a5f">爱</text><text x="130" y="180" text-anchor="middle" font-size="8.5" fill="#5b6b7d">K · V</text>
  </g>
  <g>
    <rect x="65" y="214" width="130" height="46" rx="3" fill="#dbe6f0" stroke="#1f3a5f"/>
    <!-- 命中高亮：pulse -->
    <rect class="pulse" x="65" y="214" width="130" height="46" rx="3" fill="#b8841c" opacity="0"/>
    <text x="130" y="236" text-anchor="middle" font-size="13" fill="#1f3a5f">猫</text><text x="130" y="252" text-anchor="middle" font-size="8.5" fill="#5b6b7d">K · V</text>
  </g>

  <!-- Decoder 当前位置（静态底） -->
  <rect x="535" y="140" width="150" height="64" rx="3" fill="#f3d9d9" stroke="#9b2c2c"/>
  <text x="610" y="164" text-anchor="middle" font-size="10" fill="#9b2c2c">当前位置 → 出 Q</text>
  <text class="reveal d6" x="610" y="190" text-anchor="middle" font-size="14" font-weight="700" fill="#3a3128">= cat</text>

  <!-- ① Q 逐个比对每个 K：三条线描出来（箭头另作元素，等线描完再浮现） -->
  <text class="reveal d1" x="360" y="60" text-anchor="middle" font-size="10" fill="#9b2c2c">① Q 拿去跟每个 K 比对</text>
  <path class="draw d2" pathLength="1000" d="M535,172 L197,93"  fill="none" stroke="#b9a07a" stroke-width="1.3" stroke-dasharray="5 3"/>
  <path class="draw d2" pathLength="1000" d="M535,172 L197,165" fill="none" stroke="#b9a07a" stroke-width="1.3" stroke-dasharray="5 3"/>
  <path class="draw d2" pathLength="1000" d="M535,172 L197,237" fill="none" stroke="#9b2c2c" stroke-width="2.4"/>
  <polygon class="reveal d6" points="197,93 208,88 208,98" fill="#b9a07a"/>
  <polygon class="reveal d6" points="197,165 208,160 208,170" fill="#b9a07a"/>
  <polygon class="reveal d6" points="197,237 210,230 210,244" fill="#9b2c2c"/>

  <!-- ② 命中 -->
  <text class="reveal d4" x="250" y="282" text-anchor="middle" font-size="10" fill="#7a5a12">②「猫」命中·权重最高</text>

  <!-- ③ 把猫的 V 抄回 decoder：弧线描出来 -->
  <text class="reveal d5" x="430" y="300" text-anchor="middle" font-size="10" fill="#4a6b3a">③ 抄回它的 V → 解出 cat</text>
  <path class="draw d5" pathLength="1000" d="M197,250 Q380,315 533,196" fill="none" stroke="#4a6b3a" stroke-width="2.4"/>
  <polygon class="reveal d8" points="533,196 522,190 523,203" fill="#4a6b3a"/>

  <!-- Q / V 标签球 -->
  <g class="reveal d1"><circle cx="520" cy="172" r="12" fill="#9b2c2c"/><text x="520" y="176" text-anchor="middle" font-size="11" fill="#fff" font-weight="700">Q</text></g>
  <g class="reveal d5"><circle cx="205" cy="250" r="12" fill="#4a6b3a"/><text x="205" y="254" text-anchor="middle" font-size="11" fill="#fff" font-weight="700">V</text></g>
</svg>
</figure>

> Self-attention 是"Q/K/V 都来自同一条序列"；cross-attention 把 **Q 留在 decoder、K/V 换成 encoder 的输出**——唯一的差别就是 K/V 从哪来。

## 怎么做的
在 Transformer decoder block 里通常有三段：

1. masked self-attention：decoder 看自己已经生成的前缀
2. cross-attention：decoder 的 hidden state 做 Q，encoder 输出做 K/V
3. FFN：逐 token 处理

Decoder-only GPT 路线把 encoder 和 cross-attention 都砍掉，统一变成前缀条件生成。

## 代码出处
Transformer 原论文架构图里的 "multi-head attention over encoder output" 子层。

## 链接
- [[transformer-architecture]] · cross-attention 的位置
- [[multi-head-attention]] · 具体 attention 机制
- [[decoder-only-paradigm]] · 为什么后来的 GPT 路线不用它
