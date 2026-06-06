---
name: kl-vae
type: concept
sources: [ideogram-4]
updated: 2026-06-05
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
