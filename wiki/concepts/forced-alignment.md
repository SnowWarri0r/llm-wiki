---
name: forced-alignment
type: concept
sources: [qwen3-asr]
updated: 2026-06-14
---

# Forced Alignment · 强制对齐 · 把已知文字钉到时间轴上

## 一句话
文字已经给你了（所以叫"强制"），只求每个字/词在音频里**什么时刻**出现（起止时间戳）——就是卡拉OK逐字高亮要算的那个"何时点亮"。

## 直觉 · 卡拉OK / 字幕逐字高亮

普通 ASR（如 [[qwen3-asr]]）是**不知道文字、从音频认出文字**。强制对齐反过来：**转写是定死的**，你只把它**钉到时间轴上**。

最好的类比是**卡拉OK**：歌词（文字）和歌（音频）都有了，卡拉OK 要决定的是"唱到哪个字、什么时候点亮它"——每个字的起止时间。**你不认词，词现成的，只解决时间。** 字幕对齐、配音对口型、语音数据标注都靠它。

经典做法（WhisperX、NFA=NeMo Forced Aligner、Montreal Aligner）：基本是**帧级动态规划 / 自回归**逐个对齐，慢，而且**误差累积**——前一个字的时间戳偏了，后面全跟着漂。

## 怎么做的 · Qwen3-ForcedAligner：填槽 + 非自回归

Qwen3-ASR 配的 **Qwen3-ForcedAligner-0.6B** 把强制对齐重构成**"填空题（slot-filling）"**：

- 拿到转写（一串字），在**每个字后插一个 `[time]` 特殊 token** 当**空槽**——"这个字的时间戳待填"。
- 模型的活：**把每个 `[time]` 槽填上一个时间戳索引**（对应音频第几帧 / 哪个时间 bin）。
- 关键：**非自回归（NAR）**——**所有空槽一次并行全填好**，不是从左到右一个个填。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="fa-r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker>
    <marker id="fa-g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#4a6b3a"/></marker>
  </defs>
  <line x1="362" y1="34" x2="362" y2="228" class="reveal d1" stroke="#bfb398" stroke-width="1" stroke-dasharray="5 4"/>
  <!-- 左 AR -->
  <text class="reveal d1" x="180" y="44" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">自回归：逐个定时间</text>
  <!-- 真实位置 ticks -->
  <line class="reveal d1" x1="44" y1="150" x2="338" y2="150" stroke="#7a6f5d" stroke-width="1"/>
  <g class="reveal d1" stroke="#bfb398" stroke-width="1.4">
    <line x1="70" y1="145" x2="70" y2="155"/><line x1="140" y1="145" x2="140" y2="155"/><line x1="210" y1="145" x2="210" y2="155"/><line x1="280" y1="145" x2="280" y2="155"/>
  </g>
  <text class="reveal d1" x="190" y="168" text-anchor="middle" font-size="8" fill="#7a6f5d">灰 tick = 真实时间</text>
  <!-- AR 预测点（带累积漂移） + 依赖箭头 -->
  <g class="reveal d2">
    <circle cx="70" cy="108" r="5" fill="#4a6b3a"/><text x="70" y="98" text-anchor="middle" font-size="8" fill="#4a6b3a">✓</text>
    <circle cx="158" cy="108" r="5" fill="#9b2c2c"/><circle cx="232" cy="108" r="5" fill="#9b2c2c"/><circle cx="304" cy="108" r="5" fill="#9b2c2c"/>
  </g>
  <g class="reveal d3" fill="none" stroke="#9b2c2c" stroke-width="1.3">
    <path d="M75,104 Q116,86 153,104" marker-end="url(#fa-r)"/><path d="M163,104 Q197,86 227,104" marker-end="url(#fa-r)"/><path d="M237,104 Q270,86 299,104" marker-end="url(#fa-r)"/>
  </g>
  <g class="reveal d3" stroke="#9b2c2c" stroke-width="1" stroke-dasharray="3 2">
    <line x1="158" y1="113" x2="148" y2="148"/><line x1="232" y1="113" x2="214" y2="148"/><line x1="304" y1="113" x2="282" y2="148"/>
  </g>
  <text class="reveal d4" x="190" y="196" text-anchor="middle" font-size="9.5" fill="#9b2c2c">每个依赖前一个 → 一个偏，后面跟着漂</text>
  <text class="reveal d4" x="190" y="212" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11" font-weight="700" fill="#9b2c2c">误差累积 · 还慢（串行）</text>
  <!-- 右 NAR -->
  <text class="reveal d4" x="545" y="44" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1a6a64">NAR 填槽：一次并行</text>
  <!-- 并行预测条 -->
  <rect class="reveal d5" x="408" y="66" width="274" height="20" rx="3" fill="#cce5e1" stroke="#1a6a64"/>
  <text class="reveal d5" x="545" y="80" text-anchor="middle" font-size="8.5" font-weight="700" fill="#0f4a45">一次并行预测全部 [time] 槽</text>
  <g class="reveal d5" stroke="#1a6a64" stroke-width="1.3" fill="none">
    <line x1="425" y1="86" x2="425" y2="102" marker-end="url(#fa-g)"/><line x1="500" y1="86" x2="500" y2="102" marker-end="url(#fa-g)"/><line x1="575" y1="86" x2="575" y2="102" marker-end="url(#fa-g)"/><line x1="650" y1="86" x2="650" y2="102" marker-end="url(#fa-g)"/>
  </g>
  <!-- 真实 tick + 命中点 -->
  <line class="reveal d4" x1="392" y1="150" x2="686" y2="150" stroke="#7a6f5d" stroke-width="1"/>
  <g class="reveal d4" stroke="#bfb398" stroke-width="1.4">
    <line x1="425" y1="145" x2="425" y2="155"/><line x1="500" y1="145" x2="500" y2="155"/><line x1="575" y1="145" x2="575" y2="155"/><line x1="650" y1="145" x2="650" y2="155"/>
  </g>
  <g class="reveal d6" fill="#4a6b3a">
    <circle cx="425" cy="112" r="5"/><circle cx="500" cy="112" r="5"/><circle cx="575" cy="112" r="5"/><circle cx="650" cy="112" r="5"/>
  </g>
  <g class="reveal d6" stroke="#4a6b3a" stroke-width="1" stroke-dasharray="3 2">
    <line x1="425" y1="117" x2="425" y2="148"/><line x1="500" y1="117" x2="500" y2="148"/><line x1="575" y1="117" x2="575" y2="148"/><line x1="650" y1="117" x2="650" y2="148"/>
  </g>
  <text class="reveal d6" x="545" y="196" text-anchor="middle" font-size="9.5" fill="#1a6a64">各槽独立、并行 → 不累积、各管各</text>
  <text class="reveal d6" x="545" y="212" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11" font-weight="700" fill="#1a6a64">误差不漂 · 极快 RTF≈0.001</text>
</svg>
</figure>

> 类比：自回归像**逐行填表**，每行位置依赖上一行 → 一行错、后面全错位级联；NAR 填槽像**一眼看到整张表、每个格子的时间一次盖章盖完** → 不级联、还瞬时。

效果：比 WhisperX / NFA 的**累计平均偏移降 67~77%**，RTF≈0.001（基本瞬时）。这跟你在 [[multi-token-prediction]] 学的"把逐个串行变成一次并行"是同一招——既省时间，又**断开误差累积**。

## 代码出处
- 概念性：在转写序列里每字后插 `[time]` token，一个 NAR 头对所有 `[time]` 位置并行回归 / 分类出时间 bin 索引
- 来源：Qwen3-ASR 技术报告（arXiv 2601.21337）的 Qwen3-ForcedAligner-0.6B

## 链接
- [[qwen3-asr]] · 它的时间戳能力就是 ForcedAligner 给的
- [[multi-token-prediction]] · 同思路：串行 → 一次并行
- [[log-mel-spectrogram]] · 对齐对到的是它的帧（时间 bin）
- [[next-token-forward-pass]] · 对照：自回归逐个 vs NAR 一次出全部
