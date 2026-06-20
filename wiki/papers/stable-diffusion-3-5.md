---
name: stable-diffusion-3-5
type: paper
source: https://arxiv.org/abs/2403.03206
ingested: 2026-06-16
authors: [Stability AI, Esser et al.]
year: 2024
---

# Stable Diffusion 3.5 · 整流流 + MMDiT 文生图

## 一句话
SD3 那套架构(arXiv 2403.03206《Scaling Rectified Flow Transformers》)的产品化开源版:整流流少步采样 + [[mmdit]](文字图像同序列、双权重) + 三文本编码器(CLIP-L/CLIP-G/T5-XXL) + QK-Norm 稳训,在 16 通道 VAE latent 空间画。Large 8B / Medium 2.5B 开源权重(2024-10)。

## 它要解决的痛点
老文生图(U-Net + cross-attention)里图像是主角、文字只是从旁边喷进来的"调料",信息流不对等 → 长 prompt 顾此失彼、拼写/排版差。SD3 让文字和图像平起平坐。

## 核心贡献
- **整流流(Rectified Flow)**:不走 DDPM 加噪去噪,学一条噪声↔图近乎直线的速度场([[flow-matching]] 家族),路径直 → 步数少。训练用 **logit-normal 时间步采样**偏向轨迹中段(论文:偏向"感知上重要的尺度")。
- **MMDiT 主干**:文字 + 图像 token 拼一条序列共享自注意力(双向对齐),但**每模态各用各的 QKV/MLP 权重**。长 prompt 服从、文字渲染大涨的根。
- **三文本编码器**:CLIP-L + CLIP-G + T5-XXL;T5 吃显存可丢掉省内存。
- **QK-Norm**(3.5 相比 3 的关键稳定性补丁):算 attention 前归一化 Q、K,防 logit 随规模爆炸 → softmax 饱和 → 训练崩。SD3.5 还把 MMDiT 块单注意力换**双注意力层**。
- **家族**:Large 8B / Large Turbo(蒸馏 ~4 步,见 [[dmd-distillation]]) / Medium 2.5B(**MMDiT-X**:前 13 层加自注意力,消费级能跑)。

## 关键概念 → 概念页
- [[mmdit]] · 文字图像同序列、双权重的多模态扩散 Transformer
- [[flow-matching]] · 整流流的训练目标(速度场)
- [[qk-rmsnorm]] · QK-Norm 稳住大规模训练
- [[kl-vae]] · 16 通道 latent 空间
- [[clip]] · 三编码器里的两个 CLIP
- [[dmd-distillation]] · Turbo 的少步化蒸馏

## 我的批注 / 疑问
- 一句话记牢:**把"文字当调料"换成"文字和图像坐同一张桌子"(MMDiT),再用直线少步的整流流跑完**。同样吃 MMDiT 的有 [[qwen-image-2]] / [[mrt]]。
- 来源:SD3 abstract(整流流偏感知尺度 + MMDiT 双权重双向流已确证)+ SD3.5 模型卡/diffusers 博客(QK-Norm、双注意力、8B/2.5B 已确证);三编码器 CLIP-L/G+T5-XXL 为 SD3 通识。
- 待查:logit-normal 的精确参数;双注意力层与 MMDiT-X 在不同尺寸上的具体差异。
