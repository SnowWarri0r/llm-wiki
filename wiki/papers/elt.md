---
name: elt
type: paper
source: https://arxiv.org/abs/2604.09168
upstream: https://arxiv.org/pdf/2604.09168
ingested: 2026-06-10
authors: [Sahil Goyal, Swayam Agrawal, Gautham Govind Anil, Prateek Jain, Sujoy Paul, Aditya Kusupati]
year: 2026
---

# ELT · Elastic Looped Transformers for Visual Generation

## 一句话
把 looped transformer 带进视觉生成：不堆很多不同层，而是把一个 N 层 block 循环套 L 圈（有效深度 N×L、参数只看 N），一次训练出一族深度，推理时按算力挑 L —— 同等算力下 4× 参数缩减。

## 它要解决的痛点
生成模型（DiT / MaskGIT）靠堆很多 unique 层换深度，参数也跟着堆。但深度的价值常常是"重复同一种计算"，用很多不同层去拟合是浪费。ELT 用循环（深度上权重共享）把"算多深"和"用多少参数"解耦，并顺手得到弹性部署。

## 核心贡献
- **循环 = 深度共享权重**：N 个 unique 层组成 block，循环 L 圈，有效深度 N×L、参数只看 N、算力随 L。跟 [[convolution]] 的空间权重共享同源，轴换成深度。详见 [[looped-transformer]]。
- **Elastic / Any-Time 推理**：一次训练出一族深度，推理时按预算挑 L，沿质量-算力前沿滑，不为每个预算单独训。详见 [[elastic-inference]]。
- **ILSD（Intra-Loop Self Distillation）**：teacher 跑满 L_max、student 随机中途退 L_int，loss = 满配真值 + 中途真值×λ + 蒸馏(student 对齐 teacher，stop-grad)，两路更新同一套 Θ → 逼每一档都好用。
- **两类生成都做**：扩散（[[diffusion-transformer]]，SD v1.4 [[kl-vae]] latent）+ 掩码生成（MaskGIT 图像 / MAGVIT 视频）。
- **结果**：ImageNet256 FID 2.0 @111M（vs MaskGIT-XL 446M，4×）；diffusion FID 2.83 @1.1B（vs DiT-32 3.43 @2.1B）；UCF-101 FVD 72.8 @76M；TPU v6e 3.5× 吞吐。

## 关键概念 → 概念页
- [[looped-transformer]] · 同 block 循环套用，深度共享权重
- [[elastic-inference]] · 一族深度，推理挑算力
- [[diffusion-transformer]] · 被循环的底座
- [[kl-vae]] · 在 SD VAE latent 上生成
- [[convolution]] · 空间权重共享，对照深度共享

## 我的批注 / 疑问
- "权重共享"主题的又一面：卷积空间共享、looped 深度共享，都是把重复结构从参数里抽出来做成可复用算子。
- 跟 [[ideogram-4]] 是视觉生成的两条省法：ideogram 省在监督形态、ELT 省在参数复用+弹性深度。共同味道：别把规律摊在参数里，做成结构。
- 待查：循环每圈怎么吃扩散 timestep（论文没细讲每圈的 time 注入），以及 L 在不同 timestep 是否自适应。
