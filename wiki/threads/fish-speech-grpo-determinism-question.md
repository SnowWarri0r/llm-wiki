---
name: fish-speech-grpo-determinism-question
type: thread
sources: [fish-speech-s2-pro, bitwise-determinism]
updated: 2026-05-22
---

# Fish Speech GRPO Determinism Question

## 一句话
fish-speech 做 GRPO/RL 对齐时，训练采样和推理 serving 的 kernel 不一致会不会影响 reward 归因？

## 问题背景
TML 强调 [[bitwise-determinism]]：训练和推理 kernel 要尽量 bit-for-bit 一致。fish-speech 则更像常规 LLM/TTS 工程：训练、采样、serving 可能走不同栈。

如果 [[grpo]] 的 reward 对细微音频差异敏感，那么 kernel 差异、采样温度、codec decode 差异都可能让"同一策略"的表现看起来不一样。

## 需要查什么
- fish-speech RL 阶段是不是直接用 serving kernel 采样
- reward 是文本级、语音级，还是多维组合
- [[sglang-inference]] 是否只用于推理，还是训练采样也复用
- 多次采样的随机性如何固定 seed / cache / tokenizer

## 暂时判断
它大概率不追求 TML 那种 bitwise determinism，而是接受常规 RL 的采样噪声，通过组内相对 reward 抵消一部分不稳定。但这需要读代码确认。

## 链接
- [[fish-speech-s2-pro]]
- [[grpo]]
- [[bitwise-determinism]]
- [[sglang-inference]]
