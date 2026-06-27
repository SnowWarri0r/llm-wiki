---
name: diffusion-transformer
type: concept
sources: [ideogram-4, qwen-image-2, mrt, stable-diffusion-3-5, flux-1, cosmos-3, dit]
updated: 2026-06-24
---

# Diffusion Transformer · DiT

> 这页是跨 paper 的概念速览；DiT 原始论文(Peebles & Xie)的精装详解(adaLN-Zero 内部、架构 vs 训练目标、scaling)见 [[dit]]。

## 一句话
把扩散模型里那个老 U-Net 换成 Transformer —— 图像切成 latent token，像处理一串 token 一样去噪。

## 直觉
早期扩散模型（Stable Diffusion）的去噪网络是卷积 U-Net。DiT（Peebles & Xie 2023）发现：**Transformer 在图像生成上一样能 scale，而且更顺**。做法跟 ViT 一个味道 —— 把图像的 latent 切成一堆 patch token，喂进标准 Transformer block，让 self-attention 在 token 之间传信息。时间步 t（扩散到第几步）通过 **AdaLN**（自适应 LayerNorm）调制每个 block 的残差路径。

为什么换 Transformer？因为它能吃下"图像 token + 文本 token 一条序列"，天然适合多模态联合建模 —— 这正是现代 T2I（SD3、FLUX、Ideogram 4）的共同底座。

## 单流 vs 双流（关键分歧）
现代 T2I DiT 有两种把文本和图像 token 放一起的方式：

- **双流 / MMDiT**（SD3、FLUX）：文本和图像各有**一套独立的投影**（Q/K/V、MLP），只在 attention 那一步让两边互相看。两条流并行。
- **单流**（Ideogram 4、Z-Image、Hunyuan 3）：文本和图像 token **共享同一套投影**，每层就是一条 self-attention 序列。结构更简、参数更省。

Ideogram 4 选单流：34 层，文本图像 token 一条序列，靠 3D Multimodal RoPE 把两者放进同一个位置系。**FLUX 则两个都用、分前后**：前段双流 MMDiT 块对齐模态、后段切单流共享权重收尾（见 [[flux-1]]）——先用贵的对齐、再用省的干完。

## 怎么做的
```
# 一个 DiT block (单流, Ideogram 4 风格)
x = [text_tokens; image_latent_tokens]   # 拼成一条序列
for block in layers:                       # 34 层
    x = x + AdaLN(t) * SelfAttn(QKNorm(x), MRoPE)   # 共享投影
    x = x + AdaLN(t) * SwiGLU(x)
# 最终预测 flow matching 的速度场 v(z_t, t)
```

## 链接
- [[dit]] · 原始论文精装页：adaLN-Zero、架构 vs 目标、scaling law
- [[adaptive-layernorm]] · 时间步 t 怎么注进每层(adaLN-Zero)
- [[swiglu]] · 现代 DiT 家族的 FFN(原版 DiT 用 GELU)
- [[mmdit]] · 双流多模态 DiT(文字图像同序列、各自权重)，本页"双流"那支的专页
- [[stable-diffusion-3-5]] · MMDiT 的招牌落地
- [[flux-1]] · 先双流后单流的混合 DiT
- [[ideogram-4]] · 9.3B 单流 DiT
- [[flow-matching]] · DiT 的训练目标（预测速度场）
- [[transformer-architecture]] · DiT 的骨架就是它
- [[mrope]] · 多模态 RoPE 把文本图像放一个位置系
- [[kl-vae]] · DiT 去噪的 latent 空间由它压缩出来
- [[classifier-free-guidance]] · 采样时怎么用 DiT 的条件/无条件两支
