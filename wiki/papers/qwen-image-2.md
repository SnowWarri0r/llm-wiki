---
name: qwen-image-2
type: paper
source: https://arxiv.org/abs/2605.10730
ingested: 2026-06-15
authors: [Qwen Team, Alibaba]
year: 2026
---

# Qwen-Image-2.0 · 生成与编辑统一成一个模式

## 一句话
把文生图和编辑统一进一个"条件→目标"模式：生成时条件只有文字，编辑时把原图 VAE latent 和文字嵌入拼接 `Concat(ℰ_x, h_y)` 喂同一个 MMDiT，没点名的区域天然照抄。20B MMDiT，主打中文文字渲染 + 1K token 长指令直出文字密集版面。

## 它要解决的痛点
过去文生图和"改图"常是分开的模型/管线（两套权重、两种用法）。本质上它俩是同一件事——给定条件产出目标图，区别只在条件里有没有原图。

## 核心贡献
- **统一生成+编辑**：单 MMDiT backbone，"joint condition-target"。编辑 = 条件里拼一段原图 latent（`Concat(ℰ_x, h_y)`）；天然一致性（latent 当 context，没点名照抄、只改点名处），不用额外 mask。
- **架构**：frozen [[qwen3-vl]] 条件编码器 + MMDiT（[[qk-rmsnorm]] RMSNorm、纯乘性调制 h'=αh 无加性 bias、SwiGLU、[[mrope]] MSRoPE 跨模态位置）。
- **VAE 升级 f16c64**：16× 压缩（1.0 是 8×）、64 latent 通道，残差自编码 + 语义对齐损失，PSNR 33.42 / SSIM 0.9225。
- **六段训练 + Data Flywheel**：256P→512P→多分辨率(到 2K)→SFT；闭环数据飞轮把失败样本路由到 RL/预训练/prompt 工程。
- **DMD 蒸馏**：40 步老师 → 4-NFE 学生保质（辅助 fake-score 用 [[flow-matching]]）。
- 结果：LMArena T2I ELO 1168（全球 #9 / 中文 #1，超 Nano Banana）；原生 2K。

## 关键概念 → 概念页
- [[diffusion-transformer]] · MMDiT backbone（joint condition-target）
- [[qwen3-vl]] · frozen 条件编码器（强 VLM 决定指令遵循上限）
- [[kl-vae]] · latent 空间（升到 16× f16c64）
- [[mrope]] · MSRoPE 跨模态联合位置
- [[qk-rmsnorm]] · MMDiT 里防 attention 炸

## 我的批注 / 疑问
- 一句话记牢：**生成和编辑都是"条件→目标"，编辑只是条件里拼一段原图 latent；同一个 MMDiT，没点名天然照抄**。蒸馏(DMD 4-NFE)跟 [[drifting-models]]/[[diffusion-opd]] 一条少步化线。
- 来源：arxiv 全文 HTML 未出，细节取自 ar5iv 全文镜像 + abstract + GitHub；机制(Concat/f16c64/六段/DMD)已确证。
- 待查：MSRoPE 在文字密集长指令下怎么排版位置；Data Flywheel 的失败判定标准；DMD 与 Drifting 的具体异同。
