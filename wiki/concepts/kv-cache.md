---
name: kv-cache
type: concept
sources: [interaction-models-tml, fish-speech-s2-pro]
updated: 2026-05-20
---

# KV Cache

## 一句话
Transformer 每层 attention 算过的 Key / Value 矩阵存下来，下一个 token 直接复用，不重算前面所有 token。

## 直觉
Attention 公式里 Query 是"当前 token 在问什么"，Key/Value 是"序列里每个位置存了什么"。一次推理一个 token 时，Key/Value 是前缀全部 token 的，重新算一遍 O(N²) 浪费。KV cache 把它存下来，每步只新增当前 token 的 K/V 拼上去 → O(N) per step。

## 关键场景
- **长序列推理**：核心瓶颈 = KV cache 内存（每层 × N token × hidden_dim × 2）
- **流式会话**（fish-speech / TML 都用）：cache 在 GPU 内存里持久存在，每个新 chunk 追加；不重分配 = 省 latency
- **batched 推理**：paged KV cache（vLLM/SGLang）让多个 session 共享 GPU 内存池
- **prefix sharing**：相同 prompt prefix 复用 cache（RadixAttention）

## 链接
- [[prefill-decode]] · prefill 阶段填 cache、decode 阶段读 cache
- [[split-kv]] · 切 cache 沿序列维并行算
- [[micro-turn]] · 200ms chunk 模式下持久 cache 的关键
- [[sglang-inference]] · fish-speech 复用的推理栈
- [[ai-memory-hierarchy]] · KV cache 正是最吃 HBM 那层带宽/容量的数据
