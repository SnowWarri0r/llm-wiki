---
name: representation-autoencoder
type: concept
sources: [rae-dit]
updated: 2026-06-18
---

# Representation Autoencoder · RAE · 拿"看懂图的编码器"当扩散 latent

## 一句话
不再为扩散单训一个 [[kl-vae]] 压缩器,而是**拿一个冻结的预训练表征编码器(SigLIP-2 / DINOv2)当 encoder、只训一个轻量 decoder 还原像素**;扩散直接在这个**高维语义 latent** 里跑。比 VAE 收敛快、抗过拟合、越 scale 越赢。

## 直觉 · 压缩坐标 vs 概念坐标

主流 latent 扩散先训个 VAE 把图压成低维 latent(常 <100 维)。但 VAE 是**为"忠实还原"训的**——latent 轴**没语义**(纯压缩编码),压缩还丢细节。扩散在这种"压缩坐标系"里学得慢、还易过拟合。

RAE 的观察:**已经有一堆"看懂图"的模型**([[dino]]v2、SigLIP,自监督/对比学出来的强表征)。直接拿它们的输出空间当 latent——
- 编码器**冻结不训**(它已经把图组织成了语义结构);
- **只训一个轻量解码器**把语义 embedding 还原成像素(L1 + LPIPS + Gram + 对抗损失)。

类比:VAE = 自己存一个 **zip 压缩包**(紧凑但坐标没意义、有损);RAE = 直接在一个**"已经理解图像"的概念坐标系**里作画——"附近 = 语义相似",扩散学起来顺,解码器只管把概念渲染回像素。

## 怎么做的
```
图 ──[冻结 SigLIP-2/DINOv2]──> 高维语义 latent (256 token × 1152 维)
                                      │  扩散(DiT + flow matching)在这里跑
                                      ▼
                              [只训这个轻量解码器] ──> 像素
```
对照 VAE:VAE 的 encoder+decoder 都要训、latent 低维无语义;RAE 的 encoder 白嫖现成表征、只训 decoder、latent 高维有语义。

## 为什么更好(rae-dit 实测)
- **收敛快**:比 FLUX 的 VAE 基线 GenEval 快 **4.0×**、DPG 快 4.6×。
- **抗过拟合**:VAE 微调 **64 epoch 后崩**(loss 塌向 0),RAE **稳到 256 epoch** 还在涨——高维+语义结构是**隐式正则**。
- **越大越赢**:0.5B→9.8B 全程 RAE>VAE,差距随规模变大。

## 一个必须的代价:维度相关噪声调度
语义 latent 维度 `m=N×d` 远大于 VAE。高维里加同样噪声相对腐蚀更小,所以**时间步要按 `α=√(m/n)` 往"更多噪声"挪**,补回信噪比。去掉它性能腰斩(GenEval 49.6→23.6)。这是 RAE 唯一不能省的技术;反倒是宽 diffusion head、噪声增强解码这些小模型补丁,放大后都没必要。

## 代码出处 / 来源
- [[rae-dit]] · Scaling T2I Diffusion Transformers with Representation Autoencoders(arXiv 2601.16208)
- 编码器:SigLIP-2 So400M / DINOv2 / WebSSL

## 链接
- [[rae-dit]] · 这页的来源论文(把 RAE scale 到大规模 T2I)
- [[kl-vae]] · 被替掉的低维压缩 latent
- [[dino]] · DINOv2 这类自监督表征编码器(RAE 的 encoder 之一)
- [[pid-pixel-diffusion]] · 对照:PiD 换解码端、RAE 换编码端,都挑战"VAE 是不是最佳地基"
- [[diffusion-transformer]] · 在语义 latent 上跑的仍是 DiT
- [[flow-matching]] · 训练目标
