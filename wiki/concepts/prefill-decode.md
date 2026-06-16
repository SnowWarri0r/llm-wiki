---
name: prefill-decode
type: concept
sources: [interaction-models-tml]
updated: 2026-05-20
---

# Prefill / Decode

## 一句话
LLM 推理两阶段：**prefill** 一次性吃整段输入并行算所有 token，**decode** 一个一个往外吐。

## 直觉
- **Prefill**：拿到 prompt → 并行算所有 token 的 K/V → 填 [[kv-cache]]。GPU 利用率高（大矩阵乘）。
- **Decode**：每步依赖上一步 token，串行 → GPU 利用率低（小矩阵乘）。

正常 LLM 服务 prefill 占总时间 10-30%，decode 70-90%。

## 微回合场景下变了
[[micro-turn]] 模式 200ms chunk → prefill 极小（只有几个新 token），decode 极频繁。原来 prefill 的优化经验不再适用，反而**元数据开销**（kernel launch、内存分配、调度）成了瓶颈。

## 链接
- [[kv-cache]] · prefill 填 cache，decode 读 cache
- [[split-kv]] · 让两阶段走同一种切法保 bitwise
- [[micro-turn]] · 微回合放大了 decode 频次
- [[ai-memory-hierarchy]] · decode 被 HBM 带宽卡脖子,正是内存层级痛点
