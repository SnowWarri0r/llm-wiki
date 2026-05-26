---
name: residual-layernorm
type: concept
sources: [attention-is-all-you-need, bert, gpt-1, gpt-2, gpt-3]
updated: 2026-05-22
---

# Residual + LayerNorm

## 一句话
Transformer block 里每个子层都配 `x + sublayer(x)` 和 [[layernorm]]，让深层网络既能传梯度又能稳住激活尺度。

## 直觉
[[residual-connection]] 给信息一条直达高速路，LayerNorm 给每个 token 做尺度整理。一个负责"别学坏了还能走原路"，一个负责"每层输出别越跑越飘"。

没有这对组合，Transformer 堆到几十层、上百层会非常难训。

## 怎么做的
常见有两种摆法：

- **Post-LN**：`LayerNorm(x + Sublayer(x))`，原始 Transformer 用法
- **Pre-LN**：`x + Sublayer(LayerNorm(x))`，后来的大模型更常见，深层训练更稳

直觉上 Pre-LN 让 residual 主干更干净，梯度更容易沿着 identity path 往回走。

## 代码出处
Transformer 原论文 block；现代 GPT/BERT 系列实现都有对应变体。

## 链接
- [[layernorm]] · 归一化组件
- [[residual-connection]] · 残差组件
- [[transformer-architecture]] · block 结构
