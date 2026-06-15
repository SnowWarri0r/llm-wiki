---
name: normalization
type: concept
sources: [video-vae]
updated: 2026-06-15
---

# 归一化家族 · BatchNorm / LayerNorm / GroupNorm / RMSNorm · 只差"对哪根轴"

## 一句话
所有归一化做的事一样——把一组激活拉回均值 0、方差 1，再配可学的缩放 γ 和偏移 β；**唯一区别是：对<u>哪一组数</u>求那个均值/方差**。

## 直觉 · 对哪根轴平均

训练时每层激活会乱飘(太大/太小/分布漂移)，不稳难训。归一化把一组数 `x` 拉回 `(x−μ)/σ` 再 `·γ+β`。把激活看成张量 **[N 批量, C 通道, 空间]**，各变体只是圈不同切片去算 μ/σ：

一张成绩表 `[学生 × 科目]` 的类比：
- **BatchNorm**：每一**科**在全班拉曲线(按列) → 要全班在场。
- **LayerNorm**：每个**学生**在自己各科上拉曲线(按行) → 一个人就能算。
- **GroupNorm**：科目**分组**(理/文)，每个学生在每组内拉曲线。

## 举个数字例子 · 同一个矩阵，三种 norm 三种结果

设 2 个样本 × 4 个通道(空间=1)：

```
        ch1  ch2  ch3  ch4
样本1     1    2    3    4
样本2    10   20   30   40
```

**LayerNorm（按行：每个样本的 4 个特征）**
```
样本1: μ=2.5, σ≈1.118 → [-1.34, -0.45, +0.45, +1.34]
样本2: μ=25,  σ≈11.18 → [-1.34, -0.45, +0.45, +1.34]
```
两行归一化后**一模一样**——样本2 是样本1 的 10 倍，行内归一把整体 scale 抹掉了。每个样本自己算，**不看别的样本**。

**BatchNorm（按列：每个通道跨 2 个样本）**
```
ch1: [1,10]  μ=5.5  σ=4.5  → [-1, +1]
ch2: [2,20]  μ=11   σ=9    → [-1, +1]   ch3/ch4 同理 → [-1,+1]
```
每**列**变 [-1,+1]——**必须两个样本都在场**才能算(batch 小/变长就崩)。

**GroupNorm（G=2：每行内分 [ch1,ch2] [ch3,ch4] 两组）**
```
样本1: 组A[1,2] μ=1.5 σ=0.5 →[-1,+1]; 组B[3,4] μ=3.5 σ=0.5 →[-1,+1]  ⇒ [-1,+1,-1,+1]
样本2: 组A[10,20]μ=15 σ=5  →[-1,+1]; 组B[30,40]μ=35 σ=5 →[-1,+1]   ⇒ [-1,+1,-1,+1]
```
每个样本**自己**算(像 LayerNorm 不看 batch)，但只在**组内**(保留点通道局部性)。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- 三个面板：同一个 2×4 网格，高亮不同的平均组 -->
  <!-- Panel LN -->
  <text class="reveal d1" x="120" y="40" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f3a5f">LayerNorm · 按行</text>
  <g class="reveal d1" font-size="9" text-anchor="middle" fill="#3a3128">
    <g fill="none" stroke="#bfb398"><rect x="40" y="56" width="36" height="26"/><rect x="76" y="56" width="36" height="26"/><rect x="112" y="56" width="36" height="26"/><rect x="148" y="56" width="36" height="26"/><rect x="40" y="82" width="36" height="26"/><rect x="76" y="82" width="36" height="26"/><rect x="112" y="82" width="36" height="26"/><rect x="148" y="82" width="36" height="26"/></g>
    <text x="58" y="73">1</text><text x="94" y="73">2</text><text x="130" y="73">3</text><text x="166" y="73">4</text>
    <text x="58" y="99">10</text><text x="94" y="99">20</text><text x="130" y="99">30</text><text x="166" y="99">40</text>
  </g>
  <g class="draw d2" fill="none" stroke="#1f3a5f" stroke-width="2.4"><rect x="38" y="54" width="148" height="28" rx="3" pathLength="1000"/><rect x="38" y="80" width="148" height="28" rx="3" pathLength="1000"/></g>
  <text class="reveal d3" x="112" y="126" text-anchor="middle" font-size="8.5" fill="#1f3a5f">每行(一个样本)自己归一</text>
  <!-- Panel BN -->
  <text class="reveal d1" x="360" y="40" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">BatchNorm · 按列</text>
  <g class="reveal d1" font-size="9" text-anchor="middle" fill="#3a3128">
    <g fill="none" stroke="#bfb398"><rect x="280" y="56" width="36" height="26"/><rect x="316" y="56" width="36" height="26"/><rect x="352" y="56" width="36" height="26"/><rect x="388" y="56" width="36" height="26"/><rect x="280" y="82" width="36" height="26"/><rect x="316" y="82" width="36" height="26"/><rect x="352" y="82" width="36" height="26"/><rect x="388" y="82" width="36" height="26"/></g>
    <text x="298" y="73">1</text><text x="334" y="73">2</text><text x="370" y="73">3</text><text x="406" y="73">4</text>
    <text x="298" y="99">10</text><text x="334" y="99">20</text><text x="370" y="99">30</text><text x="406" y="99">40</text>
  </g>
  <g class="draw d2" fill="none" stroke="#9b2c2c" stroke-width="2.4"><rect x="278" y="54" width="36" height="56" rx="3" pathLength="1000"/><rect x="314" y="54" width="36" height="56" rx="3" pathLength="1000"/><rect x="350" y="54" width="36" height="56" rx="3" pathLength="1000"/><rect x="386" y="54" width="36" height="56" rx="3" pathLength="1000"/></g>
  <text class="reveal d3" x="352" y="126" text-anchor="middle" font-size="8.5" fill="#9b2c2c">每列(一个通道)跨样本归一</text>
  <!-- Panel GN -->
  <text class="reveal d1" x="600" y="40" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#2f6e4a">GroupNorm · 行内分组</text>
  <g class="reveal d1" font-size="9" text-anchor="middle" fill="#3a3128">
    <g fill="none" stroke="#bfb398"><rect x="520" y="56" width="36" height="26"/><rect x="556" y="56" width="36" height="26"/><rect x="592" y="56" width="36" height="26"/><rect x="628" y="56" width="36" height="26"/><rect x="520" y="82" width="36" height="26"/><rect x="556" y="82" width="36" height="26"/><rect x="592" y="82" width="36" height="26"/><rect x="628" y="82" width="36" height="26"/></g>
    <text x="538" y="73">1</text><text x="574" y="73">2</text><text x="610" y="73">3</text><text x="646" y="73">4</text>
    <text x="538" y="99">10</text><text x="574" y="99">20</text><text x="610" y="99">30</text><text x="646" y="99">40</text>
  </g>
  <g class="draw d2" fill="none" stroke="#2f6e4a" stroke-width="2.4"><rect x="518" y="54" width="74" height="28" rx="3" pathLength="1000"/><rect x="592" y="54" width="74" height="28" rx="3" pathLength="1000"/><rect x="518" y="80" width="74" height="28" rx="3" pathLength="1000"/><rect x="592" y="80" width="74" height="28" rx="3" pathLength="1000"/></g>
  <text class="reveal d3" x="592" y="126" text-anchor="middle" font-size="8.5" fill="#2f6e4a">每行内分 2 组各自归一</text>
  <text class="reveal d4" x="360" y="170" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#3a3128">同一个矩阵，圈哪片求 μ/σ 不同 → 这就是全部区别</text>
  <text class="reveal d4" x="360" y="194" text-anchor="middle" font-size="9" fill="#7a6f5d">BN 要全 batch 在场；LN / GN 一个样本自己就能算</text>
</svg>
</figure>

## RMSNorm + 为什么 video-vae 换掉 GroupNorm
**RMSNorm** = [[layernorm]] 砍掉"减均值"和偏移，只**除以特征的均方根(RMS)×可学缩放** → 更省、效果不输；现代 LLM(LLaMA/Qwen)、[[qk-rmsnorm]]、Wan-VAE 都用。

[[video-vae]] 把 **GroupNorm 换成 RMSNorm**：GroupNorm 要在**空间(+组通道)**上求统计，做因果/流式视频时会**跨时间混信息**、破坏逐帧因果和缓存；RMSNorm 只拿**每个位置自己的特征**归一 → 不跨时间 → 保住因果 + 无限长流式。

## 怎么做的
```
通用：y = γ · (x − μ_S) / sqrt(var_S + ε) + β     # S = 求统计的那组数
BatchNorm   S = 同通道、跨 batch + 空间      （推理用 running 统计 = EMA）
LayerNorm   S = 一个样本/位置的所有通道
InstanceNorm S = 一个样本一个通道、跨空间
GroupNorm   S = 一个样本、一组通道 + 空间    （G=1≈LN，G=C≈IN）
RMSNorm     不减均值，只除 RMS：y = γ · x / sqrt(mean(x²)+ε)
```

## 代码出处
- `torch.nn.BatchNorm2d / LayerNorm / GroupNorm / RMSNorm`
- GroupNorm 原始：Wu & He 2018；那张经典"对哪根轴"立方体图是它画的

## 链接
- [[batchnorm]] · 按通道跨 batch；推理 running 统计是 [[ema]]
- [[layernorm]] · 按 token 自己的特征；Transformer 标配
- [[qk-rmsnorm]] · RMSNorm 用在 attention 的 Q/K
- [[video-vae]] · 把 GroupNorm 换 RMSNorm 保因果
- [[ema]] · BatchNorm 推理统计 = 训练时的 EMA
