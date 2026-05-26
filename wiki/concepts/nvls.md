---
name: nvls
type: concept
sources: [interaction-models-tml]
updated: 2026-05-22
---

# NVLS · NVIDIA Low-Latency SHARP

## 一句话
NVIDIA/NCCL 生态里的低延迟集合通信路径，用来减少多 GPU 之间 all-reduce / reduce-scatter 这类同步成本。

## 直觉
大模型不是一张 GPU 跑完的。每层算完后，GPU 之间常要交换中间结果。普通通信像大家都把纸条传给主持人再广播；NVLS 这类低延迟路径试图把"汇总"推进网络/硬件里，减少来回搬运。

对 [[micro-turn]] 这种 200ms 级交互模型，通信尾延迟会直接变成用户体感延迟。

## 怎么做的
- 在支持的 GPU/NVSwitch/NCCL 环境里启用低延迟 collective
- 把 all-reduce / reduce-scatter 这类操作放到更接近硬件的路径上做
- 与 [[grouped-gemm-vs-gemv]]、[[split-kv]] 一起减少小 batch 推理的系统开销

## 代码出处
当前 wiki 只记录 TML 提到的系统点；具体实现取决于 NCCL / CUDA 环境。

## 链接
- [[micro-turn]] · 为什么低延迟通信重要
- [[moe]] · expert 并行会放大通信需求
- [[grouped-gemm-vs-gemv]] · 小 batch MoE 的计算侧取舍
