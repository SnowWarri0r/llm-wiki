---
name: viitorvoice
type: paper
source: https://github.com/viitor-ai/viitor-voice-nar
upstream: https://huggingface.co/ZzWater/ViiTorVoice-NAR
ingested: 2026-07-02
authors: viitor-ai (开源工程项目，无独立论文)
---

# ViiTorVoice · 低帧率语义码 + 并行填声 = 60ms 流式克隆

## 一句话
一个开源的流式零样本 TTS 引擎：把音频压成 12.5 帧/秒的"语义码 + 声学码"，再用非自回归(NAR)掩码并行把码填出来，首帧延迟约 60ms，给一段参考音就能克隆音色。

## 它要解决的痛点
传统 LLM-based TTS 逐帧自回归吐 token：① 帧率高(Encodec ~75Hz)→ 序列长；② 逐帧生成 → 长音频慢、首帧延迟高。要做"实时、可克隆、可控情绪"的语音，得同时砍掉"序列太长"和"逐帧太慢"两条瓶颈。

## 核心贡献（工程整合，非新论文）
- **DualCodec 低帧率码**：24kHz 音频压 1920 倍到 **12.5 帧/秒**(对比 Encodec ~75Hz，约 6× 更短)。第 1 码本是**语义**(从自监督模型 w2v-BERT-2.0 第 16 层蒸馏，码本 16384)，第 2–8 码本量化**波形残差**=声学细节。
- **NAR 掩码并行生成**：不逐帧自回归，而是像"完形填空"一次性并行预测所有码、再迭代精修几步(OmniVoice / SoundStorm / MaskGCT 家族)，从预训练 LLM 初始化。
- **流式首块**：支持首块(first-block)推理，端到端首帧延迟 ~60ms。
- **零样本克隆 + CFG 控制**：给参考音频(或预算好的 prompt 码本)即可克隆；两路 CFG guidance(情绪 `emotion_guidance_scale`、非语言发声 `nvv_guidance_scale`)调情绪/副语言；局部编辑靠对齐后掩码(`expand_mask_ratio`、词级 `align_granularity`)。
- **服务化**：拆成 gRPC v2 服务(encoder / llm / decoder / orchestrator)+ HTTP 网关(:7861)。

## 关键概念 → 概念页链接
- [[dualcodec]] — 低帧率、语义增强的双流神经音频码
- [[semantic-vs-acoustic-tokens]] — 语义码(说什么) vs 声学码(音色/细节)分工
- [[nar-masked-speech-generation]] — 非自回归掩码并行生成(填空式)
- [[rvq-codec]] — DualCodec 底层用的残差向量量化
- [[voice-cloning-reference]] — 参考音频零样本克隆
- [[classifier-free-guidance]] — 两路 CFG 调情绪/副语言

## 我的批注 / 疑问
- **没有独立论文**，是工程项目；硬数字都来自它搭积木用的两篇组件论文(DualCodec arXiv 2505.13000 · Interspeech 2025；OmniVoice arXiv 2604.00688 · k2-fsa)。LLM backbone 规模仓库未公开，页面不臆测。
- 亮点不在"发明新东西"，在**把低帧率语义码(短序列)+ NAR 并行解码(不逐帧)+ 首块流式拼成一条 60ms 的实时克隆链**——这三样各自砍一刀延迟。
- 值得关注：语义码本(RVQ-1)从 w2v-BERT 蒸馏这招，让 LLM 只需预测很短的语义序列，声学细节交给 NAR decoder 并行补——这是"AR 管内容、NAR 管细节"的典型分工。
