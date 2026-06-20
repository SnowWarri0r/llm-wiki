---
name: qwen3-asr
type: paper
source: https://arxiv.org/abs/2601.21337
ingested: 2026-06-14
authors: [Qwen Team, Alibaba]
year: 2026
---

# Qwen3-ASR · 给 LLM 接个耳朵

## 一句话
不从头训 ASR：拿预训练 Qwen3 LLM 当解码器，前面接一个音频编码器（AuT，耳朵）+ projector（翻译插头），让音频"说成 LLM 听得懂的输入"。就是 modality-projector 模式，专做语音、规模拉满，post-train 自 Qwen3-Omni。

## 它要解决的痛点
Whisper 从零训 encoder-decoder，连语言能力都得硬学。但语言这件事 LLM 早学透了——别重学，直接拿来当解码器；还顺手解锁了"prompt 塞热词定制转写"（解码器是会读 prompt 的 LLM）。

## 核心贡献
- **架构**：音频 → AuT 编码器 → projector → Qwen3 LLM → 文字。1.7B 版 = Qwen3-1.7B + 300M AuT(hidden 1024)；另有 0.6B 版。= [[modality-projector]] 模式（minimind-o 同骨架），解码器换成现成 LLM。
- **AuT 编码器**：AED 式独立预训练；128 维 Fbank → **8× 下采样 → 12.5Hz token 率**；**动态 flash-attention 窗口 1s~8s** → 同一个模型既流式（1s 短块低延迟）又离线（8s 长上下文高精度）。
- **训练四段**：① AuT 预训练(~4000 万小时伪标注，中英为主) → ② Omni 预训练(Qwen3-Omni，3T token) → ③ ASR SFT(风格迁移到 ASR I/O + context biasing) → ④ RL 用 **[[gspo]]**(~5 万条) 磨噪声鲁棒/稳定。
- **亮点**：context biasing(prompt 塞热词)、52 语言/方言 + 语种识别、带 BGM 整首歌、Qwen3-ForcedAligner 填槽式 NAR 时间戳(RTF≈0.001)。
- **结果**：LibriSpeech WER 1.63/3.38；带口音英语 16.07 完胜 Whisper-large-v3 的 21.30；0.6B TTFT 92ms、2000s 音频/秒。

## 关键概念 → 概念页
- [[modality-projector]] · 音频→LLM 输入空间的"翻译插头"，同骨架
- [[log-mel-spectrogram]] · 输入是它的近亲 Fbank 128 维
- [[gspo]] · 第④段 RL 用的方法（GRPO 序列级版）
- [[whisper]] · 对照：从头 enc-dec vs LLM 接耳朵
- [[forced-alignment]] · 时间戳能力：Qwen3-ForcedAligner 填槽 + NAR

## 我的批注 / 疑问
- 一句话记牢：**语言交给预训练 LLM，只新训"耳朵+插头"；解码器是 LLM 这点顺手解锁 prompt 热词定制**。是 modality-projector 在 ASR 上的生产级落地。
- 待查：AuT 的动态窗口具体怎么训（窗口大小怎么采样）；context biasing 在 SFT 里数据怎么构造；ForcedAligner 填槽 NAR 的槽位数怎么定。
