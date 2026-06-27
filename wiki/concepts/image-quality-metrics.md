---
name: image-quality-metrics
type: concept
sources: [qwen-image-2, qwen-image-bench]
updated: 2026-06-15
---

# 图像质量指标 · PSNR / SSIM · 重建得像不像

## 一句话
两把尺子量"重建图 vs 原图"差多少：PSNR 死磕逐像素误差（取对数变 dB，越高越好），SSIM 看局部亮度/对比度/结构（0~1，越接近 1 越像）。

## 直觉 · 给 VAE 的"还原度"打分

最常见用途：[[kl-vae]] 把图**编码成 latent 再解码回来**，丢了多少？PSNR/SSIM 高 = "压了再解几乎不丢"，latent 是忠实压缩。

- **PSNR（峰值信噪比）**：先算原图和重建图的**逐像素平方差均值（MSE）**，再取对数变分贝。误差越小 → dB 越高。30+ 不错、40+ 很好。
  - **软肋**：死磕单像素。图整体平移一两像素、人眼看一模一样，PSNR 却暴跌——跟人感知不一致。这正是 [[lpips]] / [[perceptual-loss]] 存在的理由。
- **SSIM（结构相似性）**：不死磕单像素，在一小块窗口里比**亮度 + 对比度 + 结构（纹理图案）**。0~1，1=完全一样。
  - 跟 [[lpips]] 同一个动机（像素差 ≠ 人眼觉得像），但 SSIM 是**手写公式**（便宜），LPIPS 是**学出来的深度特征距离**。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- PSNR 标尺 -->
  <text class="reveal d1" x="60" y="56" font-size="11" font-weight="700" fill="#1f3a5f">PSNR（dB，越高越好）</text>
  <rect class="reveal d1" x="80" y="66" width="187" height="18" fill="#efd6c8"/>
  <rect class="reveal d1" x="267" y="66" width="224" height="18" fill="#f0e0a8"/>
  <rect class="reveal d1" x="491" y="66" width="149" height="18" fill="#d8e6ce"/>
  <g class="reveal d1" font-size="8" fill="#7a6f5d" text-anchor="middle">
    <text x="173" y="98">差 &lt;30</text><text x="379" y="98">不错 30–40</text><text x="565" y="98">很好 40+</text>
    <text x="80" y="62">20</text><text x="267" y="62">30</text><text x="491" y="62">40</text><text x="640" y="62">45</text>
  </g>
  <g class="draw d2"><line x1="381" y1="60" x2="381" y2="90" pathLength="1000" stroke="#9b2c2c" stroke-width="2.4"/></g>
  <text class="reveal d3" x="381" y="112" text-anchor="middle" font-size="9.5" font-weight="700" fill="#9b2c2c">VAE = 33.42</text>
  <!-- SSIM 标尺 -->
  <text class="reveal d3" x="60" y="146" font-size="11" font-weight="700" fill="#1a6a64">SSIM（0–1，越接近 1 越像）</text>
  <rect class="reveal d3" x="80" y="156" width="560" height="18" fill="#cce5e1"/>
  <g class="reveal d3" font-size="8" fill="#7a6f5d" text-anchor="middle"><text x="80" y="152">0</text><text x="360" y="152">0.5</text><text x="640" y="152">1.0</text></g>
  <g class="draw d3"><line x1="597" y1="150" x2="597" y2="180" pathLength="1000" stroke="#9b2c2c" stroke-width="2.4"/></g>
  <text class="reveal d4" x="597" y="200" text-anchor="middle" font-size="9.5" font-weight="700" fill="#9b2c2c">VAE = 0.9225</text>
  <text class="reveal d4" x="300" y="200" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11" font-weight="700" fill="#3a3128">PSNR 死磕像素(平移即崩) · SSIM 看结构(更贴人眼)</text>
</svg>
</figure>

## 怎么做的
```
MSE   = mean( (原图 − 重建)² )            # 逐像素平方差均值
PSNR  = 10 · log10( MAX² / MSE )          # MAX=像素最大值(255 或 1.0)，单位 dB
SSIM  = 在滑窗里综合 [亮度l · 对比度c · 结构s]，对全图取平均  # ∈ [0,1]
```
报告时常 PSNR + SSIM 一起给：前者管"整体像素准不准"，后者管"结构/纹理像不像"，互补。

## 代码出处
- `torchmetrics.PeakSignalNoiseRatio` / `StructuralSimilarityIndexMeasure`；或 `skimage.metrics.peak_signal_noise_ratio` / `structural_similarity`
- [[qwen-image-2]] 报 VAE f16c64 的 PSNR 33.42 / SSIM 0.9225

## 链接
- [[kl-vae]] · 主要拿它给 VAE 重建打分
- [[lpips]] · 学出来的感知距离；补 PSNR/SSIM 不贴人眼的短板
- [[perceptual-loss]] · 同动机：像素差 ≠ 感知
- [[qwen-image-2]] · 用到这俩数
