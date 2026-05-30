---
name: split-kv
type: concept
sources: [interaction-models-tml]
updated: 2026-05-22
---

# Split-KV · 沿 KV 序列切分 attention

## 一句话
把 attention 里的 Key/Value 缓存按序列维切成几段并行算，再用稳定归约合回来。

## 直觉
decode 时当前 Query 只有一个或少数几个 token，但它要看很长的 [[kv-cache]]。如果一个 kernel 串着扫完整 KV，长上下文会慢；把 KV 切段并行扫，就像多人分头查同一本账本，最后汇总最相关的结果。

难点在"最后汇总"：softmax attention 不是简单相加，切段后要保证数值稳定，还要让切分策略在 prefill/decode 中尽量一致。

## 怎么做的
1. 将 KV cache 沿 context length 切成固定 chunk
2. 每个 chunk 独立算局部 attention score、局部 max、局部加权和
3. 用 log-sum-exp 风格的稳定合并得到全局 softmax 结果
4. 固定 chunk 和归约顺序，服务 [[bitwise-determinism]]

## 代码出处
当前是 TML kernel 设计描述；没有公开实现可指行号。

## 链接
- [[kv-cache]] · 被切分的数据结构
- [[prefill-decode]] · 两阶段都要考虑切分一致
- [[batch-invariant-kernel]] · 保 bit 的更大目标
- [[micro-turn]] · 长上下文流式交互的低延迟需求
