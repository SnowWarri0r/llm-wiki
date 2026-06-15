---
name: video-vae
type: concept
sources: [mrt]
updated: 2026-06-15
---

# Video VAE · Wan-VAE · VAE 的视频版

## 一句话
图像 VAE 把一张图压成小 latent；视频 VAE 多压一个**时间**维——3D 因果卷积把空间和时间一起压、只看过去帧，靠特征缓存能编解码无限长视频。

## 直觉 · 给 VAE 加一根时间轴

先接 [[kl-vae]]：图像 VAE 把一张 2D 图压进小 latent（空间 8×），让扩散在压缩空间里画，省算力。视频多一个维度——**时间（很多帧）**。直接拿图像 VAE 一帧帧压？太亏：**相邻帧高度冗余**（几乎一样），白白生成一堆几乎相同的 latent。

视频 VAE（以 **Wan2.1 的 Wan-VAE** 为例）就是 VAE 的视频版，比图像 VAE 多三件事：**时间也压、因果只看过去、缓存做无限长**。

## 怎么做的 · 3D 因果卷积 + 时间压缩 + 缓存

**① 3D 卷积，时间也一起压**：不在单图上做 2D 卷积，而在 **(时间, 高, 宽)** 上做 **3D 卷积**：

```
输入视频 (1+T)×H×W×3  →  latent [1+T/4, H/8, W/8] × 16 通道
                          空间 8×8 = 64×  +  时间 4×（4 帧并成 1 片 latent）
```

相邻帧冗余 → 4 帧打包成 1 片几乎不丢 → 视频 latent token 砍掉 3/4，扩散才跑得动。

**② 因果（causal）**：时间方向的卷积是因果的——每个 latent 帧**只依赖过去帧、不看未来**。好处：(a) 能**逐帧流式**处理任意长视频，不必一次塞进显存；(b) 那个 `1+T` 结构——第一帧是**特殊关键帧**单独处理，于是 **T=0 退化成一张图** → 图像/视频**一套 VAE 通吃**。

**③ 特征缓存 + RMSNorm → 无限长**：因为因果，过去特征定死、可**缓存（feature cache）**、分块往后滚，不回看整段；把 **GroupNorm 换成 RMSNorm**（GroupNorm 跨时间/批混统计、破坏因果与流式；见 [[normalization]] 家族对照）→ 能编解码**无限长 1080P** 不丢历史。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="vv-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#2f6db0"/></marker></defs>
  <!-- 图像 VAE -->
  <text x="40" y="40" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#7a6f5d">图像 VAE（kl-vae）：只压空间</text>
  <rect class="reveal d1" x="60" y="50" width="64" height="64" fill="#faf4e1" stroke="#7a6f5d"/><text x="92" y="86" text-anchor="middle" font-size="9" fill="#3a3128">图 H×W</text>
  <line class="reveal d2" x1="128" y1="82" x2="180" y2="82" stroke="#2f6db0" stroke-width="1.5" marker-end="url(#vv-h)"/><text x="154" y="74" text-anchor="middle" font-size="8" fill="#2f6db0">encode 8×</text>
  <rect class="reveal d2" x="184" y="66" width="32" height="32" fill="#cce5e1" stroke="#1a6a64"/><text x="200" y="86" text-anchor="middle" font-size="7.5" fill="#0f4a45">latent</text>
  <text class="reveal d2" x="260" y="86" font-size="9" fill="#7a6f5d">H/8 × W/8（空间 64×）</text>
  <!-- 分隔 -->
  <line x1="40" y1="132" x2="680" y2="132" class="reveal d3" stroke="#bfb398" stroke-width="1" stroke-dasharray="4 4"/>
  <!-- 视频 VAE -->
  <text x="40" y="156" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#2f6db0">视频 VAE（Wan-VAE）：空间 + 时间 + 因果</text>
  <!-- 多帧堆叠 -->
  <g class="reveal d4">
    <rect x="66" y="180" width="44" height="44" fill="#faf4e1" stroke="#7a6f5d"/>
    <rect x="78" y="172" width="44" height="44" fill="#faf4e1" stroke="#7a6f5d"/>
    <rect x="90" y="164" width="44" height="44" fill="#faf4e1" stroke="#7a6f5d"/>
    <rect x="102" y="156" width="44" height="44" fill="#f3d9d9" stroke="#9b2c2c"/><text x="124" y="182" text-anchor="middle" font-size="7" fill="#7a2020">关键帧</text>
  </g>
  <text x="106" y="238" text-anchor="middle" font-size="8" fill="#7a6f5d">(1+T) 帧</text>
  <line class="reveal d5" x1="150" y1="186" x2="214" y2="186" stroke="#2f6db0" stroke-width="1.5" marker-end="url(#vv-h)"/>
  <text x="182" y="178" text-anchor="middle" font-size="8" fill="#2f6db0">3D 因果卷积</text>
  <!-- 输出 latent -->
  <g class="reveal d5">
    <rect x="222" y="170" width="30" height="30" fill="#cce5e1" stroke="#1a6a64"/>
    <rect x="230" y="164" width="30" height="30" fill="#cce5e1" stroke="#1a6a64"/>
  </g>
  <text x="300" y="180" font-size="9" fill="#0f4a45" font-weight="700">[1+T/4, H/8, W/8] ×16ch</text>
  <text x="300" y="196" font-size="8.5" fill="#7a6f5d">空间 64× + 时间 4×（4 帧→1 片）</text>
  <text x="300" y="218" font-size="8.5" fill="#2f6db0">因果：每帧只看过去 · feature cache → 无限长</text>
  <text x="400" y="244" text-anchor="middle" font-size="8.5" font-weight="700" fill="#9b2c2c">第一帧特殊 → T=0 退化成一张图，图视频通吃</text>
</svg>
</figure>

> 类比：图像 VAE = 压一张照片。Wan-VAE = 压一本**翻页动画书**——不光缩小每页，还把**每 4 页相似的并成 1 页**（压时间），而且**严格从前往后翻**（因果），只记一点缓存就能一直翻下去。

## 代码出处
- Wan2.1 技术报告 arXiv 2503.20314（Wan-VAE：3D 因果 VAE，(1+T)×H×W → [1+T/4, H/8, W/8]×16）
- 仓库 github.com/Wan-Video/Wan2.1

## 链接
- [[kl-vae]] · 图像版地基；视频 VAE 多压一根时间轴
- [[mrt]] · 借 Wan-2.1-VAE 把每个图层裁剪区域编成 region latent
- [[diffusion-transformer]] · latent 扩散在 VAE 压出来的空间里跑
