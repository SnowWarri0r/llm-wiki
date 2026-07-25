---
name: kl-vae
type: concept
sources: [ideogram-4, qwen-image-2, mrt, stable-diffusion-3-5, pid-pixel-diffusion, rae-dit, meshflow, drifting-models]
updated: 2026-07-22
---

# KL-VAE · 把图压进 latent 的那层地基

## 一句话
一个轻度正则的自编码器，把 512×512×3 的像素图压成 64×64×4 的小 latent —— **扩散模型不在像素上画画，在这个压缩空间里画，省 48 倍计算**。

## 直觉 · 别在 4K 画布上猜噪声

直接在像素上做扩散（512×512×3 ≈ 78 万个数）太贵：每一步去噪都要在这么大的张量上跑一遍网络，2K 图更是天文数字。

观察是：**自然图像有巨大冗余**。隔壁像素几乎一样，整片天空就一个颜色。真正的"信息"远少于像素数。

所以 latent diffusion 的套路（Stable Diffusion / FLUX / [[ideogram-4]] 全是这路子）：
1. 先训一个 **VAE**，把图压成一张小得多的 latent（64×64×4，约 1.6 万个数，缩了 48 倍）。
2. **扩散模型（DiT）只在这张小 latent 上工作** —— 加噪、去噪、flow matching 全在 latent 空间。
3. 画完的 latent 再用 VAE 的 decoder 还原成像素图。

[[diffusion-transformer]] 那条"ODE 从噪声到干净 latent"里的 latent，就是这个 VAE 定义出来的。VAE 是地基，DiT 在上面盖楼。

## 怎么做的 · encoder / decoder + 一点 KL

```
像素图 ──encoder──▶ latent (64×64×4) ──decoder──▶ 重建图
   512×512×3          压缩 48×            还原回像素
```

- **Encoder**：一串卷积下采样，把图压成低分辨率多通道的 latent。
- **Decoder**：反过来上采样，把 latent 还原成像素。
- 训练目标：重建图要像原图（L1/L2 + 感知损失 + 常配一个 GAN 判别器让细节更锐）。

那 **KL** 是什么？VAE 的 encoder 输出的不是一个固定 latent，而是一个高斯分布（均值+方差），再采样。**KL 项把这个分布往标准正态 N(0,1) 拉**，作用是让 latent 空间**平滑、规整、没有空洞** —— 这样扩散模型在里面"游走加噪去噪"时，每个点都对应一张合理的图，不会采样到一片无意义的死区。

<figure style="margin:26px 0; padding:22px; background:#f4f1ea; border:1px solid #c4bba6; border-radius:4px;">
<svg viewBox="0 0 720 410" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;">
  <!-- 顶部说明：encoder 吐的是云不是点 -->
  <g font-family="JetBrains Mono,monospace">
    <text x="20" y="26" font-size="11" fill="#3a3128">encoder 输出 = 一朵高斯云（均值±方差），采样取其中一点：</text>
    <circle cx="470" cy="22" r="14" fill="#9b2c2c" opacity="0.12"/>
    <circle cx="470" cy="22" r="9"  fill="#9b2c2c" opacity="0.18"/>
    <circle cx="470" cy="22" r="4"  fill="#9b2c2c" opacity="0.30"/>
    <circle cx="468" cy="24" r="2.2" fill="#9b2c2c"/>
    <text x="492" y="26" font-size="10" fill="#7a6f5d">← 模糊一团，不是一个硬点</text>
  </g>

  <!-- ===== 左panel：没有 KL ===== -->
  <text x="190" y="62" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#9b2c2c">没有 KL · 每张图各占一座孤岛</text>
  <rect x="40" y="75" width="300" height="280" fill="#ffffff" stroke="#c4bba6" stroke-width="1"/>
  <!-- 孤岛（彼此分开，中间大片空白） -->
  <g class="reveal d1">
    <circle cx="100" cy="135" r="26" fill="#9b2c2c" opacity="0.10"/><circle cx="100" cy="135" r="13" fill="#9b2c2c" opacity="0.20"/><circle cx="100" cy="135" r="4" fill="#9b2c2c"/>
    <circle cx="285" cy="120" r="24" fill="#4a6b3a" opacity="0.10"/><circle cx="285" cy="120" r="12" fill="#4a6b3a" opacity="0.20"/><circle cx="285" cy="120" r="4" fill="#4a6b3a"/>
    <circle cx="115" cy="300" r="25" fill="#1f3a5f" opacity="0.10"/><circle cx="115" cy="300" r="12" fill="#1f3a5f" opacity="0.20"/><circle cx="115" cy="300" r="4" fill="#1f3a5f"/>
    <circle cx="290" cy="295" r="24" fill="#b8841c" opacity="0.12"/><circle cx="290" cy="295" r="12" fill="#b8841c" opacity="0.22"/><circle cx="290" cy="295" r="4" fill="#b8841c"/>
  </g>
  <!-- 游走箭头：从孤岛掉进死区（先描线，再落死区标记） -->
  <path class="draw d2" pathLength="1000" d="M100,135 Q150,170 190,205" fill="none" stroke="#3a3128" stroke-width="1.6"/>
  <polygon class="reveal d6" points="190,205 182,198 188,210" fill="#3a3128"/>
  <!-- 死区标记 -->
  <g class="reveal d6">
    <text x="195" y="212" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="22" fill="#b03030">✗</text>
    <text x="195" y="232" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" fill="#b03030">死区</text>
    <text x="195" y="246" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#7a6f5d">采样到这=噪声</text>
  </g>
  <text x="60" y="345" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#7a6f5d">岛与岛之间是空的 → 游不过去</text>

  <!-- ===== 右panel：有 KL ===== -->
  <text x="530" y="62" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#1f3a5f">有 KL · 被拉向 N(0,1) 挤成连续一团</text>
  <rect x="380" y="75" width="300" height="280" fill="#ffffff" stroke="#c4bba6" stroke-width="1"/>
  <!-- N(0,1) 单位圈 -->
  <g class="reveal d1">
    <circle cx="530" cy="215" r="105" fill="#1f3a5f" opacity="0.06"/>
    <circle cx="530" cy="215" r="105" fill="none" stroke="#1f3a5f" stroke-width="1" stroke-dasharray="5 4"/>
    <text x="530" y="120" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="#1f3a5f">N(0,1)</text>
  </g>
  <!-- 密集点云：处处有图，没有空洞 -->
  <g fill="#1f3a5f" class="reveal d3">
    <circle cx="530" cy="215" r="3.4"/>
    <circle cx="500" cy="200" r="3"/><circle cx="560" cy="205" r="3"/><circle cx="515" cy="240" r="3"/><circle cx="552" cy="238" r="3"/>
    <circle cx="485" cy="225" r="3"/><circle cx="575" cy="228" r="3"/><circle cx="525" cy="180" r="3"/><circle cx="500" cy="170" r="2.7"/>
    <circle cx="555" cy="175" r="2.7"/><circle cx="470" cy="205" r="2.7"/><circle cx="590" cy="200" r="2.7"/><circle cx="540" cy="265" r="2.7"/>
    <circle cx="505" cy="268" r="2.7"/><circle cx="478" cy="250" r="2.7"/><circle cx="582" cy="252" r="2.7"/><circle cx="525" cy="150" r="2.5"/>
    <circle cx="490" cy="245" r="2.5"/><circle cx="565" cy="195" r="2.5"/><circle cx="510" cy="215" r="2.7"/><circle cx="548" cy="218" r="2.7"/>
    <circle cx="460" cy="225" r="2.4"/><circle cx="600" cy="222" r="2.4"/><circle cx="530" cy="285" r="2.4"/><circle cx="520" cy="195" r="2.7"/>
  </g>
  <!-- 游走箭头：处处落点都有效 -->
  <path class="draw d4" pathLength="1000" d="M485,200 Q530,235 575,210" fill="none" stroke="#9b2c2c" stroke-width="1.8"/>
  <polygon class="reveal d8" points="575,210 566,206 569,217" fill="#9b2c2c"/>
  <text x="412" y="345" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#1f3a5f">挨在一起 → 中间每个点也是合理的图</text>
</svg>
</figure>

> 一句话看图：**没 KL，latent 散成孤岛，岛之间是死区**——扩散模型一旦游走到空白处，解出来就是噪声。**有 KL，所有图被拉向原点挤成连续一团**，中间任何一个点都对应一张合理的图，可以平滑地加噪去噪、插值过渡。

## 关键 · 这里的 KL 权重很小

这是常被误解的点：latent diffusion 用的 VAE，**KL 权重压得极低**。

为什么？KL 太强 → latent 被硬塞进 N(0,1)，会丢细节、重建糊。这里要的不是一个"会生成图的强 VAE"，而是一个**高保真的压缩器**，只加一丁点 KL 把 latent 空间约束得别太野。

所以它更像"**一个带轻微正则的自编码器**"，而不是教科书里那种靠自己采样生成的 VAE。生成能力全交给上面的扩散模型，VAE 只负责忠实地压缩和还原。

## 一个数字直觉
- 像素：512×512×3 = 786,432 个数
- latent：64×64×4 = 16,384 个数
- DiT 每一步去噪的计算量直接缩到 ~1/48 —— 这就是 latent diffusion 能跑 2K 原生图的底气。

## 代码出处
- 提出：Latent Diffusion Models (LDM), Rombach et al. 2021, arXiv 2112.10752
- 参考实现：diffusers 库 `AutoencoderKL`
- Ideogram / FLUX / SD3 都在自家训练的 KL-VAE latent 上做 DiT

## 链接
- [[diffusion-transformer]] · DiT 工作的 latent 空间就是 VAE 给的
- [[flow-matching]] · 速度场学的是 latent 空间里噪声→干净的路径
- [[patch-embedding]] · DiT 把 latent 再切 patch 喂进 transformer
- [[ideogram-4]] · 单流 DiT 在 KL-VAE 的 latent 上做生成
- [[video-vae]] · 视频版：多压一根时间轴 + 因果（Wan-VAE）
- [[stable-diffusion-3-5]] · 在 16 通道 VAE latent 上跑 MMDiT 扩散
- [[pixel-diffusion-decoder]] · 把这个确定性解码器换成条件像素扩散([[pid-pixel-diffusion]])
- [[representation-autoencoder]] · 干脆换成冻结语义编码器当 latent([[rae-dit]])
