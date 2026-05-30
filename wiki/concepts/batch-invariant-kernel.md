---
name: batch-invariant-kernel
type: concept
sources: [interaction-models-tml]
updated: 2026-05-22
---

# Batch-Invariant Kernel · 批大小不变算子

## 一句话
同一条样本不管跟谁凑 batch，kernel 都尽量按同一顺序做浮点运算，结果保持 bit-for-bit 一致。

## 直觉
GPU 上很多算子会因为 batch 形状不同而换算法、换归约顺序。数学上差不多，浮点位上不一样。对普通聊天模型这只是微小噪声；对 TML 这种要做 [[bitwise-determinism]] 的系统，它会让训练/推理不一致，debug 也变成猜谜。

Batch-invariant kernel 的目标是：batch 只是调度外壳，不改变单条样本的计算路径。

## 怎么做的
- 固定归约顺序，避免 batch size 改变时自动换 kernel
- attention 切分用稳定策略，比如 [[split-kv]]
- MoE expert 调度避免因为 batch composition 改变专家内部排序
- 必要时牺牲一点峰值吞吐，换可复现性和线上/离线一致性

## 代码出处
当前只有 TML 文章级描述；没有公开 kernel 代码。

## 链接
- [[bitwise-determinism]] · 目标
- [[split-kv]] · attention 场景里的具体手段
- [[grouped-gemm-vs-gemv]] · MoE 推理场景里的调度取舍
