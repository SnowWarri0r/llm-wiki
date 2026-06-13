---
name: minimind-o
type: paper
source: https://github.com/jingyaogong/minimind-o
upstream: https://arxiv.org/abs/2605.03937
ingested: 2026-06-08
authors: [jingyaogong]
year: 2026
---

# MiniMind-O · 0.1B 端到端 Omni

## 一句话
从 0 实现的 ~0.1B 端到端 Omni 模型：单一权重同时听文/音/图、说出流式语音。当前公开最小的完整 Omni 之一，代码/权重/数据/技术报告全开源，单卡 3090 约 2 小时跑通 mini 全链路。

## 它要解决的痛点
把语音纳入 Omni，最直接的是 ASR→LLM→TTS **级联**：语音先转文字、LLM 处理、再合成语音。但中间多一次转文字，**延迟、语气、情绪信息都受损**。MiniMind-O 让语音和文本在 **hidden state 层直连**，在 0.1B 规模下保留端到端 Omni 链路，目标是让人能从第一行代码读起、自己训一个能听看说的模型。

## 核心贡献
- **Thinker–Talker 双路径**：Thinker（8 层 MiniMind）读多模态出语义文本；Talker（4 层）在 Thinker 语义条件上渲染音频 codes。理解和发声解耦，让 Talker 能很小。详见 [[thinker-talker]]。
- **条件取中间层（bridge）**：Thinker 喂 Talker 的不是 embedding（语义薄）也不是末层（被 LM head 过度塑形），而是中间层（默认 层数//2−1），上下文+跨模态已融、又没被输出目标污染。
- **Talker 用 MTP 一次出 8 层 Mimi codes**：Mimi 是 8 层 RVQ 神经码（12.5Hz/24kHz），MTP 同帧并行预测 8 层避免序列 8 倍膨胀；共享主体 + 轻量 codebook adapter 控参数。详见 [[multi-token-prediction]]、[[rvq-codec]]。
- **冻结编码器 + projector 注入**：语音 SenseVoice-Small、图像 SigLIP2 都冻结抽特征，两层 MLP projector 投影进 MiniMind 隐空间的占位符（early fusion）。只训 Thinker+Talker+projector。详见 [[modality-projector]]、[[early-fusion]]。
- **流式 + 实时打断**：边吐文本边用 MTP 补 8 层 codes，Mimi 增量解码 24kHz；配 [[vad]] 实现 barge-in 打断、近似双工。音色走 in-context 克隆（[[voice-cloning-reference]]）+ CAM++ embedding。
- **训练按数据流接入**：不拆复杂预训练，T2A（对齐语音输出）→ A2A（接语音输入）→ I2T（对齐视觉，只训 vision_proj）。

## 关键概念 → 概念页
- [[thinker-talker]] · 想的说的分两路 + bridge 中间层
- [[multi-token-prediction]] · 同帧并行预测 8 层 codebook
- [[modality-projector]] · 冻结编码器 + MLP 注占位符
- [[rvq-codec]] · Mimi 是 RVQ 神经码（fish-speech 同款）
- [[voice-cloning-reference]] · in-context 音色克隆
- [[vad]] · 实时打断 barge-in
- [[early-fusion]] · 三模态落同一序列
- [[moe]] · minimind-3o-moe 变体

## 我的批注 / 疑问
- 这是 fish-speech 那条线的"麻雀版"：Mimi=RVQ、Talker 处理多码本、音色靠参考条件全是熟面孔，缩到 0.1B 还凑齐"听看说"。读它的代码能把 fish-speech 学的东西落地一遍。
- 两个可迁移判断：① 语音生成瓶颈在**多码本输出端**不在语言端（Thinker 能小、Talker 不能太小）；② **条件取中间层**是个干净的小技巧（embedding 薄 / 末层被输出目标污染）。
- Talker hidden 消融印证"小≠划算"：768 因为和主干同维、能用 Thinker 后 4 层初始化，一致性最稳。
- 音色克隆还是 Beta：能分男女声/语调，但到不了"一段参考稳定复刻"的产品级。
