---
name: grouped-gemm-vs-gemv
type: concept
sources: [interaction-models-tml]
updated: 2026-05-22
---

# Grouped GEMM vs GEMV

## 一句话
MoE 推理里，小 batch 常像很多个 GEMV；把同 expert 的 token 凑起来可变成 grouped GEMM，吞吐更好但会增加调度等待。

## 直觉
GEMV 是"一个向量乘一个矩阵"，适合单请求低延迟，但 GPU 吃不饱。GEMM 是"一批向量乘矩阵"，吞吐高。MoE 每个 token 只去少数 expert，天然把 batch 打散，所以系统要决定：马上算一个 token，还是等一等把同 expert 的 token 凑成小批。

这就是实时交互里的经典 trade-off：低延迟 vs 高吞吐。

## 怎么做的
- **GEMV 路线**：token 到 expert 就立刻算，排队少，GPU 利用率低
- **Grouped GEMM 路线**：按 expert 聚合 token，一次跑多个小矩阵乘，GPU 更满
- **TML 的痛点**：[[micro-turn]] 只有 200ms 级预算，过度凑批会伤手感
- **确定性问题**：凑批顺序改变也可能影响 [[bitwise-determinism]]

## 代码出处
当前是 TML 文章级系统设计点；没有公开实现。

## 链接
- [[moe]] · 为什么会有 expert 分流
- [[batch-invariant-kernel]] · batch composition 不能改变结果
- [[nvls]] · 多 GPU expert 通信的低延迟组件
