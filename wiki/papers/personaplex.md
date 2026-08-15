---
name: personaplex
type: paper
source: https://arxiv.org/abs/2602.06053
upstream: https://research.nvidia.com/labs/adlr/personaplex/
ingested: 2026-08-12
authors: Rajarshi Roy, Jonathan Raiman, Sang-gil Lee, Teodor-Dumitru Ene, Robert Kirby, Sungwon Kim, Jaehyeon Kim, Bryan Catanzaro · NVIDIA · ICASSP 2026
year: 2026
---

# PersonaPlex · 同一套实时语音模型，既能换声音，也能换身份

Moshi 已经能边听边说、被打断后及时停下，但它没有一套直接可控的“你是谁、该怎么说、用谁的声音说”。PersonaPlex 不重做语音骨干，而是在对话开始前放进一段声音示范和一段角色说明，再用 2,250 小时合成对话把模型教会：后面既要模仿音色，也要守住角色。

## 一句话

**先给模型听一小段参考声音，再告诉它“你是航空客服”；之后它仍按 80 毫秒节拍边听边说，但声音和行为都受这两段提示控制。**

## 最容易误读的三点

1. 它不是 ASR → LLM → TTS 级联，而是继承 Moshi 的端到端 speech-to-speech 骨干。
2. “17 路 token”不是每 80 毫秒串行跑 17 次大 Transformer；16 路音频嵌入与 1 路文字嵌入先相加，时间 Transformer 每秒只前进 12.5 次，深度 Transformer 再在当前帧内补 8 路 agent 音频码。
3. 论文主实验模型与公开 `personaplex-7b-v1` 的数据和评测池不同，两个表里的 DMOS 不能直接比较。

## 覆盖地图

正文页面按认知顺序重排了论文 §1–5、Tables 1–5 与 Appendix A / Tables 6–7，并用官方仓库 commit `3428dfd` 补充 prompt 编排、缓存和 codebook delay 的可验证实现。
