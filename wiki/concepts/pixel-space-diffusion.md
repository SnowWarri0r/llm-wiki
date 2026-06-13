---
name: pixel-space-diffusion
type: concept
sources: [hidream-o1]
updated: 2026-06-10
---

# Pixel-Space Diffusion · 直接在原始像素上扩散

## 一句话
扩散不经 VAE 压成 latent，**直接在原始 RGB 像素上做**——用一个可学的 patch embedding 替掉 VAE 的压缩活，去掉 latent 的信息瓶颈，端到端一个模型。

## 直觉 · 把 VAE 这个外挂收进模型自己

主流是 **latent diffusion**：先用 [[kl-vae]] 把图压 48× 成小 latent，再在 latent 上跑 [[diffusion-transformer]]。VAE 省了算力，但有两个代价：
1. **它是个独立的冻结模型**——单独训、单独存，跟生成器两套参数、两个语义空间。
2. **有信息瓶颈**——压进 latent 时丢掉的高频细节（尤其**文字、小结构**）再也回不来，decoder 只能瞎猜。

pixel-space 的赌注：**别用外挂 VAE，让模型自己的 patch embedding 干压缩这活**，端到端学，没有瓶颈、没有第二个模型。

## 怎么做的 · 大 patch 控住 token 数

"在像素上扩散很贵"是个误解——关键看 **token 数**，而 token 数由 **patch 大小**决定，不是分辨率：

```
latent DiT:  512²×3 图 ─[VAE 编码]→ 64²×4 latent ─[切 patch=2]→ ~1024 token
pixel UiT:   512²×3 图 ───────[直接切 patch≈16]──────────────→ ~1024 token
```

两条路 token 数**差不多**！区别只在"压缩谁来干":
- latent：一个**单独训练的 VAE** 把图压成 latent（带瓶颈）。
- pixel：**patch embedding 这一层线性投影**把 16×16×3=768 个像素直接吃成一个 token，端到端跟整个模型一起训。

解码也更简单：不用 VAE decoder，**反 patch（unpatchify）**把 token 摊回像素就行。

一个必要配套：论文说像素空间扩散**细节本来就够好**，但**长程语义连贯性**弱（局部对、全局不搭）。所以在 flow matching 之外加 **perceptual loss**（[[perceptual-loss]]：LPIPS + DINO 感知损失）——它们比的是深层语义特征，把全局语义/结构连贯补回来。（注：教科书里"perceptual 防 L2 模糊"是另一套常见动机，但**这篇论文给的理由是语义连贯，不是防糊**。）

## 取舍
- **省**：没有独立 VAE（少一个模型、少一套语义空间）、无 latent 瓶颈 → 文字/细节更准。
- **付**：patch embedding 的压缩没有专门 VAE 那么狠，超高分辨率更吃训练（HiDream 用 512→1024→2048 三段渐进顶上去）。

## 代码出处
- HiDream-O1-Image：arXiv 2605.11061（Pixel-level Unified Transformer，无 VAE）
- 对照：Stable Diffusion / FLUX / [[ideogram-4]] 都是 latent + VAE 路线

## 链接
- [[kl-vae]] · 被替掉的那个压缩器（latent 路线的地基）
- [[patch-embedding]] · 替 VAE 干压缩的那层线性投影
- [[diffusion-transformer]] · 在像素 token 上跑的就是它（UiT）
- [[flow-matching]] · 训练目标，外加 perceptual loss 补长程语义连贯
- [[perceptual-loss]] · LPIPS / DINO 到底是啥
- [[unified-transformer]] · 像素+文本+条件一条流的架构
- [[hidream-o1]] · 用 pixel-space 的统一生成模型
