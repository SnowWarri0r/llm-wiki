---
name: progressive-resolution-training
type: concept
sources: [qwen-image-2, mrt, krea-2]
updated: 2026-06-15
---

# 渐进式分辨率训练 · 256P→512P→…→2K

## 一句话
先在小图上训（便宜、快，学全局构图/语义），再逐步升到大图（学细节/纹理）；不一上来就在 2K 从零训。

## 直觉 · 先画缩略图，再放大抠细节

`P` = 图像分辨率（256P≈256 像素、512P、1024P、2048P）。一上来就在 2K 从零训**又贵又不稳**（高分辨率每步算力随像素数平方涨、梯度也更抖）。

渐进式的做法：**低分辨率先跑海量便宜步**学"什么东西摆哪、语义构图"，再用**少量贵的高分辨率步**抠细节、纹理。

> 类比：画画先画**小缩略图抓构图**，确定布局对了，再**放大抠细节**——不会一上来就在大画布上抠每根头发。

最高那级（如 2048P）= 原生 2K（[[qwen-image-2]] 的卖点）。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="pr-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#6a3a8e"/></marker></defs>
  <!-- 阶梯 -->
  <g class="reveal d1" fill="#e2d6ef" stroke="#6a3a8e">
    <rect x="70" y="150" width="120" height="40"/><rect x="210" y="120" width="120" height="70"/><rect x="350" y="84" width="120" height="106"/><rect x="490" y="40" width="150" height="150"/>
  </g>
  <g class="reveal d2" font-family="JetBrains Mono,monospace" font-size="10" font-weight="700" text-anchor="middle" fill="#4a2668">
    <text x="130" y="174">256P</text><text x="270" y="158">512P</text><text x="410" y="140">1024P</text><text x="565" y="118">2048P</text>
  </g>
  <!-- 小图变清晰 -->
  <g class="reveal d2"><rect x="108" y="156" width="20" height="20" fill="#cce5e1" stroke="#1a6a64"/></g>
  <g class="reveal d3"><rect x="252" y="128" width="26" height="26" fill="#cce5e1" stroke="#1a6a64"/><rect x="258" y="134" width="6" height="6" fill="#4a6b3a"/></g>
  <g class="reveal d4"><rect x="392" y="92" width="34" height="34" fill="#cce5e1" stroke="#1a6a64"/><rect x="398" y="98" width="8" height="8" fill="#4a6b3a"/><rect x="412" y="110" width="6" height="6" fill="#b8841c"/></g>
  <g class="reveal d5"><rect x="540" y="50" width="48" height="48" fill="#cce5e1" stroke="#1a6a64"/><rect x="546" y="56" width="10" height="10" fill="#4a6b3a"/><rect x="566" y="70" width="8" height="8" fill="#b8841c"/><rect x="552" y="78" width="6" height="6" fill="#9b2c2c"/></g>
  <!-- 箭头 -->
  <g class="reveal d5" stroke="#6a3a8e" stroke-width="1.5" fill="none">
    <line x1="190" y1="186" x2="208" y2="186" marker-end="url(#pr-h)"/><line x1="330" y1="186" x2="348" y2="186" marker-end="url(#pr-h)"/><line x1="470" y1="186" x2="488" y2="186" marker-end="url(#pr-h)"/>
  </g>
  <text class="reveal d6" x="130" y="212" text-anchor="middle" font-size="9" fill="#6a3a8e">便宜·海量步</text>
  <text class="reveal d6" x="130" y="224" text-anchor="middle" font-size="9" fill="#6a3a8e">学全局构图</text>
  <text class="reveal d6" x="565" y="212" text-anchor="middle" font-size="9" fill="#6a3a8e">贵·少量步</text>
  <text class="reveal d6" x="565" y="224" text-anchor="middle" font-size="9" fill="#6a3a8e">抠细节纹理</text>
</svg>
</figure>

## 怎么做的
```
阶段1: 在 256P 数据上训很多步      # 便宜，学构图/语义
阶段2: 切到 512P 继续训
阶段3: 切到 1024P
阶段4: 多分辨率 512/1024/2048 混训  # 原生 2K
```
每升一级换更高分辨率的数据继续训（同一套权重），低级学到的全局结构被高级继承、只补细节。也常配 mixed-resolution（一个 batch 里混多种分辨率）增强泛化。

## 代码出处
- [[qwen-image-2]]：256P→512P(+合成)→512P/1024P→多分辨率(512/1024/2048)→SFT 六段
- [[mrt]]：~70K 步 @512×512 → ~20K 步 @1024×1024

## 链接
- [[qwen-image-2]] · 六段训练就是它
- [[mrt]] · 512→1024 两段
- [[kl-vae]] · 高分辨率下 latent 压缩更省
