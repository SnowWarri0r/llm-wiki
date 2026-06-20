---
name: matrix-rank
type: concept
sources: []
updated: 2026-06-17
---

# 矩阵的秩 · rank · 一个变换"真正有几个独立旋钮"

## 一句话
秩 = 一个矩阵里**真正独立的方向有几个**。一个 d×k 的大矩阵,秩可能只有几——说明它表面上参数很多,**实际能表达的东西只活在一个很小的子空间里**。"低秩"= 冗余多、可压缩;这正是 [[lora]]、SVD、PCA、注意力瓶颈背后那同一件事。

## 直觉 · 表面很大，实际就几味料

你已经知道秩的定义(线性无关的行/列数)。关键是它**在模型里意味着什么**。

一层网络做的事是 `y = W x`——把输入向量 `x` 经 `W` 变成输出 `y`。这里 `W` 的秩,就是**这个变换真正能产出几个独立方向的输出**:
- `W` 是 d×k,秩最多 `min(d,k)`(满秩)。
- 如果秩只有 `r`(< d,k),那**不管你喂什么 `x`,输出 `y` 永远落在一个 r 维子空间里**——这层的"表达力"其实只有 r 维,剩下的维度是摆设。

所以**秩 = 这个变换真实的"信息带宽 / 独立旋钮数"**。一个 1000×1000 的矩阵若秩=1,意味着它一千列其实全是**同一列的倍数**——一千个数字背后只有"一味料"。

一个具体小例子:
```
[1 2]        行2 = 2×行1  → 只有 1 个独立方向 → 秩 1（其实是 1 维）
[2 4]

[1 0]        两行互相独立     → 秩 2（满秩，真 2 维）
[0 1]
```

## 低秩 = 可压缩(秩怎么省参数)

一个**秩为 r** 的 d×k 矩阵,一定能写成两个瘦长矩阵相乘:
```
W(d×k, 秩 r) = B(d×r) · A(r×k)
参数:  d·k        →    r·(d+k)
```
当 `r ≪ d,k`,右边参数少得多。这就是**低秩分解**——也正是:
- **[[lora]]**:微调的增量 `ΔW` 被假设低秩,直接训 `B·A`(秩 r=16 之类),省上百倍参数。
- **SVD / PCA**:任何矩阵都能拆成 `r` 个"秩 1 块"按强度(奇异值 σ)排序相加;**只保留最强的前几个 σ、丢掉长尾**,就是有损压缩(图像压缩、降维、embedding 都这套)。

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="mr-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#3949ab"/></marker></defs>
  <!-- 大矩阵 W -->
  <rect class="reveal d1" x="56" y="50" width="96" height="96" rx="3" fill="#d6d9f0" stroke="#3949ab"/>
  <text class="reveal d1" x="104" y="102" text-anchor="middle" font-size="11" font-weight="700" fill="#28306e">W</text>
  <text class="reveal d1" x="104" y="162" text-anchor="middle" font-size="8.5" fill="#7a6f5d">d×k = d·k 个数</text>
  <text class="reveal d1" x="104" y="40" text-anchor="middle" font-size="8" fill="#9b2c2c">但秩只有 r</text>
  <!-- = -->
  <text class="reveal d2" x="186" y="104" text-anchor="middle" font-size="18" fill="#3a3128">=</text>
  <!-- B (d×r) 瘦高 -->
  <rect class="reveal d2" x="216" y="50" width="34" height="96" rx="3" fill="#cde0d4" stroke="#1f4d3a"/>
  <text class="reveal d2" x="233" y="102" text-anchor="middle" font-size="10" font-weight="700" fill="#1f4d3a">B</text>
  <text class="reveal d2" x="233" y="162" text-anchor="middle" font-size="8" fill="#7a6f5d">d×r</text>
  <!-- · -->
  <text class="reveal d3" x="268" y="104" text-anchor="middle" font-size="16" fill="#3a3128">·</text>
  <!-- A (r×k) 扁宽 -->
  <rect class="reveal d3" x="286" y="84" width="96" height="34" rx="3" fill="#f4d7e7" stroke="#b0327a"/>
  <text class="reveal d3" x="334" y="105" text-anchor="middle" font-size="10" font-weight="700" fill="#7a1f55">A</text>
  <text class="reveal d3" x="334" y="138" text-anchor="middle" font-size="8" fill="#7a6f5d">r×k</text>
  <!-- 省参数注 -->
  <text class="reveal d4" x="334" y="60" text-anchor="middle" font-size="8.5" fill="#1f4d3a">只需 r·(d+k) 个数 ≪ d·k</text>

  <!-- 右侧：SVD 谱 -->
  <line x1="430" y1="40" x2="430" y2="160" class="reveal d3" stroke="#aab4c4" stroke-width="1" stroke-dasharray="4 4"/>
  <text class="reveal d4" x="585" y="40" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11.5" font-weight="700" fill="#28306e">SVD 谱：留强的、丢长尾</text>
  <g class="reveal d4">
    <rect x="470" y="70" width="14" height="78" fill="#3949ab"/>
    <rect x="492" y="92" width="14" height="56" fill="#3949ab"/>
    <rect x="514" y="110" width="14" height="38" fill="#3949ab"/>
    <rect x="536" y="130" width="14" height="18" fill="#9aa4bf"/>
    <rect x="558" y="138" width="14" height="10" fill="#9aa4bf"/>
    <rect x="580" y="142" width="14" height="6" fill="#9aa4bf"/>
    <rect x="602" y="144" width="14" height="4" fill="#9aa4bf"/>
    <rect x="624" y="145" width="14" height="3" fill="#9aa4bf"/>
  </g>
  <line class="reveal d5" x1="530" y1="62" x2="530" y2="156" stroke="#b0327a" stroke-width="1.4" stroke-dasharray="3 2"/>
  <text class="reveal d5" x="500" y="178" text-anchor="middle" font-size="8" fill="#3949ab">前 r 个 σ 强</text>
  <text class="reveal d5" x="600" y="178" text-anchor="middle" font-size="8" fill="#7a6f5d">长尾 σ 小→丢</text>
</svg>
</figure>

## 为什么模型里"秩"常很关键
- **微调改动是低秩的**:让一个大模型适应某个任务/画风,往往只在**少数几个方向**上微调——改动量 `ΔW` 天然接近低秩,所以 [[lora]] 用秩 16 的小增量就够。
- **注意力的低秩瓶颈**:多头注意力把 Q/K 投到**更小的 head 维**再算分数,等于人为给注意力矩阵**加了个秩上限**——既省算又当正则。
- **embedding / 表示**:把高维 one-hot 压成低维稠密向量,本质是"真实信息是低秩的,没必要用满维"。
- **秩亏 = 信息丢失**:如果某层权重秩塌到很低(rank collapse),它就把多样的输入挤进很窄的子空间,表达力垮掉——训练里要警惕。

一句话记牢:**秩 = 这个矩阵/变换"真正有几个独立旋钮"。参数多 ≠ 旋钮多;低秩就是"旋钮其实没几个,可以拆成两个小矩阵省着存"。**

## 代码出处 / 来源
- 线性代数标准内容(SVD、低秩近似 Eckart–Young)
- 模型里的落点:[[lora]](Hu et al. 2021)、注意力 head 维瓶颈、PCA/embedding

## 链接
- [[lora]] · "low-rank" 就是这页的秩;微调增量低秩 → 拆成 B·A
- [[multi-head-attention]] · Q/K 投到小 head 维 = 给注意力加秩上限
- [[kl-vae]] · 把图压成低维 latent,也是"真实信息低秩"的体现
- [[pooling]] · 另一种降维/压信息的手段对照
