---
name: fish-speech-s2-pro
type: paper
source: raw/fish-speech/README.md
upstream: https://arxiv.org/abs/2603.08823
ingested: 2026-05-20
---

# Fish Audio S2 Pro

4B 参数多语言 TTS 系统，本地有 clone（软链到 `raw/fish-speech`）。

## 一句话
用 **Dual-AR**（慢 AR 4B + 快 AR 400M）+ **RVQ codec**（10 codebook ~21Hz）+ **GRPO** 对齐做出来的开源 TTS，质量超过 Seed-TTS / MiniMax Speech-02 / Qwen3-TTS。

## 它要解决的痛点
- 经典 TTS pipeline（phonemizer → 声学模型 → vocoder）多段串联，每段独立训练，对齐和情感控制困难
- 单一大 AR 在高采样率 token 流上跑不动（每秒 1000+ token × 大模型 = 推爆）
- 后训练阶段（pre-train → instruction-tune）数据分布不一致，传统 RLHF reward model 跟 pre-train 数据脱节

## 核心贡献
1. **架构**：[[dual-ar]] —— 慢 AR 出主语义 codebook，快 AR 出 9 个残差 codebook，整体结构与标准 LLM 同构 → 直接吃 SGLang 推理优化
2. **codec**：[[rvq-codec]] —— 10 codebook 残差量化，~21Hz 帧率
3. **对齐**：[[grpo]] —— Group Relative Policy Optimization，多维 reward（语义准确、指令遵循、音色相似、声学偏好），且 reward model = 数据清洗 / 标注用的同一套模型，避免分布漂移
4. **细粒度控制**：sub-word 级别的自然语言 tag（`[whisper]` `[excited]` `[angry]`），15000+ tag 支持自由文本描述
5. **流式性能**：H200 单卡 RTF 0.195 / TTFA ~100ms / 3000+ acoustic tokens/s
6. **多语言**：80+ 语言，不需要 phonemizer 或语言专属预处理

## 关键概念
- [[dual-ar]] · 慢 AR 主从 + 快 AR 残差
- [[rvq-codec]] · 残差向量量化 codec
- [[grpo]] · Group Relative Policy Optimization
- [[sglang-inference]] · 推理加速栈
- [[kv-cache]] · 流式 TTS 的内存账本
- [[voice-cloning-reference]] · 10-30 秒参考音频做克隆
- [[inline-emotion-tags]] · `[whisper]` 风格的内联控制

## 我的批注
- "Dual-AR 跟标准 LLM 同构" 是最值得记的工程取舍 —— 直接复用所有 LLM 推理基建，不用自己写一套 codec-aware infra
- GRPO 用同一套模型做 reward 这条非常优雅 —— 解决了 reward hacking 和 distribution mismatch 两个老问题
- 跟 TML 的对照：fish-speech 走 [[rvq-codec]] 离散 token 路线，TML 走 [[flow-matching]] 连续值路线。详见 [[audio-tokenization-rvq-vs-flow]]
- 这次复习的目标：把训练 loss 怎么写、慢/快 AR 怎么连接的具体 PyTorch 代码搞清楚

## 待补
- 跑通本地推理（之前跑过但忘了）
- 读 `fish_speech/models/` 实际代码画一张 dual-AR 数据流图
- 看技术报告 PDF 把 GRPO reward 多维信号搞清楚
