---
name: training-vs-inference
type: topic
updated: 2026-05-25
---

# 训练 vs 推理 · 同一个模型的两种运行方式

## 一句话
训练时看得见答案（并行、快），推理时看不见（自回归、慢）。同一个 Transformer 架构在两种模式下的执行流程完全不同。

## 为什么需要单独讲
绝大多数 paper 只画架构图（"encoder + decoder 长这样"），不讲"训练时数据怎么流 / 推理时数据怎么流"。但很多关键概念（teacher forcing / causal mask / KV cache / 并行 vs 自回归）只有放在"训练 vs 推理"的对比里才能理解。

## 涉及的 paper
- [[attention-is-all-you-need]] · encoder-decoder（原版 Transformer）
- [[gpt-1]] / [[gpt-2]] / [[gpt-3]] · decoder-only
- [[bert]] · encoder-only
- [[whisper]] · encoder-decoder（语音版）
- [[rope]] · 位置编码在两种模式下的行为

## 关键概念
- [[kv-cache]] · 推理加速的核心
- [[prefill-decode]] · LLM 推理两阶段
- [[causal-language-model]] · 训练时的 causal mask
- [[masked-language-model]] · BERT 训练方式
