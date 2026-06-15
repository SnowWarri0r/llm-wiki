---
name: qwen3-vl-report
type: paper
source: https://arxiv.org/abs/2511.21631
ingested: 2026-06-15
authors: [Qwen Team, Alibaba]
year: 2025
---

# Qwen3-VL · 视觉语言模型怎么看图

## 一句话
一个 VLM = 眼睛(SigLIP-2 ViT) + 翻译插头(MLP merger) + 大脑(Qwen3 LLM)：图按原生分辨率变成变长 token、和文字 token 进同一条序列。Qwen3-VL 三处升级（Interleaved-MRoPE / DeepStack / 文字时间戳）把长视频、细粒度感知、视频定位顶上去。

## 它要解决的痛点
让 LLM 能看图/视频且不丢语言能力；尤其长视频的时空位置建模、细粒度视觉信息保留、精确时间定位，是上一代 VLM 的短板。

## 核心贡献
- **三件套架构**：SigLIP-2 ViT → MLP merger(2×2 视觉特征压成 1 token) → Qwen3 LLM。dense 2/4/8/32B + MoE 30B-A3B/235B-A22B(激活 22B)，各出 non-thinking/thinking。
- **Interleaved-MRoPE**：把 [[mrope]] 的 t/h/w 从"分块各占一段频率"(频谱不均、长视频差)改成"交错铺满高低频" → 长程视频位置强。
- **DeepStack**：抽 3 个中间 ViT 层、各过专用 merger、残差注入 LLM 前 3 层 → 多层视觉特征(浅细节→深语义)都进，不增上下文。同 [[ideogram-4]] "取 13 中间层"思想。
- **文字时间戳**：视频每组帧前缀 `<3.0 seconds>` 文字 token 代替 T-RoPE 绝对时间位置 → 简单精确、利于视频定位/dense caption。外加 per-sample → 平方根归一 per-token loss 平衡文本/多模态。
- **训练**：预训练四阶段(S0 只训 merger 67B@8K → S1 全参 1T@8K → S2 1T@32K → S3 100B@256K) + 后训练三步(长 CoT SFT → 强师蒸馏 → RL)。
- **能力**：原生 256K(→1M)、OCR 32 语种、2D+3D grounding + 点定位、GUI agent、视觉数学(MMMU/MathVista)，纯文本反超同级文本模型。

## 关键概念 → 概念页
- [[qwen3-vl]] · 同名概念页：把它**当文生图文本编码器**用的角度（互补）
- [[modality-projector]] · merger = 视觉版 projector
- [[mrope]] · Interleaved-MRoPE 位置编码
- [[clip]] · SigLIP-2 属 CLIP 家族对比视觉编码器
- [[next-token-forward-pass]] · LLM 解码器主干

## 我的批注 / 疑问
- 一句话记牢：**VLM = 给 LLM 接 ViT 眼睛 + merger 插头；Qwen3-VL 靠 Interleaved-MRoPE + DeepStack + 文字时间戳顶长视频/细粒度**。
- 来源：arxiv HTML/ar5iv 转换失败，直接读原始 PDF(pypdf 抽全文 42 页)，架构/训练/能力均一手核实。
- 待查：DeepStack 选哪 3 层 ViT 的依据；Interleaved 交错的具体频率分配；MoE 30B-A3B vs 235B-A22B 的取舍。
