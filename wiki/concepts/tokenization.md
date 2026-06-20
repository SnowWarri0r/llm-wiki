---
name: tokenization
type: concept
sources: []
updated: 2026-06-18
---

# Tokenization / BPE · 文本怎么切成 token 喂给模型

## 一句话
模型不直接吃字符也不吃整词,而是吃**子词 token**。**BPE**(Byte-Pair Encoding)从单个字符起步,**反复把"出现最多的相邻一对"合并成一个新 token**,直到词表到设定大小。结果:常见词合成一个 token、罕见词拆成几个、没见过的也能用碎片拼出来。

## 直觉 · 字符太长、整词爆表,BPE 折中

喂模型前要把文本切成一串离散单元。两个极端都不好:
- **按字符**:词表小(几十个)、永不 OOV,但**序列超长**——"internationalization" 20 个字符 = 20 步,注意力 O(N²) 吃不消。
- **按整词**:序列短,但**词表爆炸**(几十万词)、且遇到没见过的词(新词、拼写、代码变量)直接 **OOV**(out-of-vocabulary)抓瞎。

**BPE 折中**:让**高频片段合成一个 token、低频的拆开**。常用词("the""ing")一个 token;罕见词("antidisestablish…")拆成几个常见子词;再没见过的,最差也能拆到字符/字节级拼出来——**永不 OOV,序列又不至于太长**。

<figure style="margin:26px 0; padding:22px; background:#f1eee8; border:1px solid #c7bca8; border-radius:4px;">
<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- 三种切法对照（panel，互不交叠） -->
  <!-- 按字符 -->
  <text class="reveal d1" x="120" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#9b2c2c">按字符</text>
  <g class="reveal d1" font-size="11" text-anchor="middle" fill="#3a3128">
    <rect x="34" y="50" width="26" height="26" rx="3" fill="#efd6c8" stroke="#9b2c2c"/><text x="47" y="68">l</text>
    <rect x="62" y="50" width="26" height="26" rx="3" fill="#efd6c8" stroke="#9b2c2c"/><text x="75" y="68">o</text>
    <rect x="90" y="50" width="26" height="26" rx="3" fill="#efd6c8" stroke="#9b2c2c"/><text x="103" y="68">w</text>
    <rect x="118" y="50" width="26" height="26" rx="3" fill="#efd6c8" stroke="#9b2c2c"/><text x="131" y="68">e</text>
    <rect x="146" y="50" width="26" height="26" rx="3" fill="#efd6c8" stroke="#9b2c2c"/><text x="159" y="68">r</text>
  </g>
  <text class="reveal d1" x="120" y="98" text-anchor="middle" font-size="9" fill="#7a6f5d">序列太长(5 个)</text>
  <!-- 按整词 -->
  <text class="reveal d2" x="360" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#b8841c">按整词</text>
  <rect class="reveal d2" x="312" y="50" width="96" height="26" rx="3" fill="#f0e0a8" stroke="#b8841c"/>
  <text class="reveal d2" x="360" y="68" text-anchor="middle" font-size="11" fill="#3a3128">lower</text>
  <text class="reveal d2" x="360" y="98" text-anchor="middle" font-size="9" fill="#7a6f5d">词表爆 + 新词 OOV</text>
  <!-- BPE -->
  <text class="reveal d3" x="600" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#1f4d3a">BPE(折中)</text>
  <g class="reveal d3" font-size="11" text-anchor="middle" fill="#3a3128">
    <rect x="540" y="50" width="50" height="26" rx="3" fill="#cde0d4" stroke="#1f4d3a"/><text x="565" y="68">low</text>
    <rect x="592" y="50" width="40" height="26" rx="3" fill="#cde0d4" stroke="#1f4d3a"/><text x="612" y="68">er</text>
  </g>
  <text class="reveal d3" x="600" y="98" text-anchor="middle" font-size="9" fill="#7a6f5d">常见块成 token、低频拆开</text>

  <line x1="40" y1="120" x2="680" y2="120" class="reveal d3" stroke="#c7bca8" stroke-width="1" stroke-dasharray="4 4"/>
  <text class="reveal d4" x="360" y="150" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#3a3128">高频片段合成一个 token，低频拆成常见子词 —— 永不 OOV，序列又不爆</text>
  <text class="reveal d5" x="360" y="180" text-anchor="middle" font-size="9.5" fill="#7a6f5d">模型看到的是 token 不是字母 → 这就是它"拼不对单词 / 数不清某字母几个"的根</text>
</svg>
</figure>

## 怎么做的 · BPE 训练(手算几步)
语料里几个词(带出现次数),先全拆成字符:
```
hug  ×3  →  h u g
hugs ×2  →  h u g s
hum  ×1  →  h u m
```
**反复合并出现最多的相邻对**:
```
第1轮 数相邻对:  "h u"=3+2+1=6  "u g"=3+2=5  "g s"=2  "u m"=1
        最高 "h u"=6 → 合并成 hu
        现在:  hu g ×3 |  hu g s ×2 |  hu m ×1

第2轮:  "hu g"=3+2=5  "g s"=2  "hu m"=1
        最高 "hu g"=5 → 合并成 hug
        现在:  hug ×3 |  hug s ×2 |  hu m ×1

第3轮:  "hug s"=2  "hu m"=1  → 合并 "hug s" → hugs
```
学到的合并规则(按顺序):`h+u→hu`、`hu+g→hug`、`hug+s→hugs`。**结果**:
- `hug` → **1 个 token**(高频,合成了)
- `hugs` → **1 个 token**
- `hum` → `hu` + `m` **2 个 token**(低频,没合全,拆着)

**推理时**就拿这套合并规则去切新文本:能合的按规则合,合不动的留子词/字符。词表大小 = 初始字符数 + 合并次数(GPT 级别常 5 万~10 万)。

## 落点 · 这解释了一堆 LLM 怪现象
- **"strawberry 里几个 r"数不清**:模型看到的是 token(可能 `straw`+`berry`),不是一个个字母,自然数不准。
- **数字/代码切得碎**:数字常被拆成奇怪的块,影响算术;代码 tokenizer 专门优化过。
- **中文**:多按字/字节切,一个汉字可能 1~3 个 token。
- **按 token 计费 / 算上下文长度**:你付的钱、能塞多长,都按 token 数,不是字数。每步预测下一个 token 也是在整个 [[softmax]] 词表上选。

## 代码出处 / 来源
- BPE:Sennrich et al. 2016(原用于机器翻译);GPT 系用 byte-level BPE(tiktoken)
- 变体:WordPiece(BERT)、Unigram/SentencePiece(多语言/语音)

## 链接
- [[next-token-forward-pass]] · 模型预测的"下一个"就是下一个 token
- [[softmax]] · 输出是整个 token 词表上的概率分布
- [[sampling-decoding]] · 从那个分布里挑 token 就是解码
- [[kv-cache]] · 序列长度按 token 算,BPE 让它不至于爆
- [[rvq-codec]] · 语音侧的"离散化"对照(那是把音频压成离散码)
