---
name: sparse-attention
type: concept
sources: [gpt-3]
updated: 2026-05-21
---

# Sparse Attention · 稀疏注意力

## 一句话
不让每个 token 看序列里所有其他 token（O(N²) 太贵），而是<strong>限制只看部分位置</strong>（如局部窗口 / 跨步采样），把复杂度降到 O(N·√N) 或 O(N·log N)。

## 直觉
标准 self-attention 的 O(N²) 在长序列下吃不消：
- N=1024 · 100 万次 attention 计算 / 层
- N=8192 · 6700 万次
- N=32768 · 10.7 亿次

要训长上下文模型必须省 attention 计算。Sparse attention 的思路：<strong>大多数 token 对其实不重要</strong>，只关注少数关键位置就够。

类比：你看一本书理解某段时，主要参考前文几页 + 章节摘要，不需要每读一行都回头扫整本书。Sparse attention 就是给 transformer 装这种"有重点的扫读"。

## GPT-3 用的方案
GPT-3 论文里没给详细架构，但提了 "use alternating dense and locally banded sparse attention layers, similar to the Sparse Transformer"。

具体来说，GPT-3 的 96 层 attention 里：
- **奇数层**：标准 full attention（O(N²)）
- **偶数层**：strided sparse attention（只看 stride 步长上的 token）

这相当于"局部精看 + 跨层全局联系"的折中。

## 主流 sparse 方案
1. **Strided / Sparse Transformer** (Child et al. 2019) —— GPT-3 用的。token i 看 i-1, i-stride, i-2*stride, ...
2. **Local window** (Longformer) —— token i 只看 [i-w, i+w] 窗口
3. **Sliding window + dilated** (Longformer / BigBird) —— 局部 + 跨步 + 几个 global token
4. **Random** (BigBird) —— 随机选 k 个位置当 attention key
5. **Linear attention** (Performer / Linformer) —— 用核技巧把 softmax 近似成线性

不同方案 trade-off 不同 expressivity / efficiency。GPT-3 用最简单的 strided 方案，因为 Sparse Transformer 已经验证它够用。

## 为什么不能全用 sparse
sparse attention 损失一些表达力。GPT-3 用 alternating 而不是全 sparse —— 至少一半层保留 full attention，让模型在<strong>关键层</strong>能看到任意位置。这是个常见折中。

## 后来的发展
- **2022 FlashAttention** —— 不改架构，直接优化标准 attention 的 GPU 实现（memory-aware tiling）。让 dense attention 在长序列上也快起来 → sparse 的实用价值下降
- **2023 sliding window + ROPE 长上下文** —— Claude / GPT-4 转向"标准 attention + 工程优化 + 位置编码改良"
- **2024 状态空间模型（Mamba）** —— 用 RNN-style state space 替代 attention，本质上线性复杂度

GPT-3 当年用 sparse 的工程动机被 FlashAttention 部分消解了 —— 现代 LLM 多数回到 standard attention + GPU optimization。

## 链接
- [[gpt-3]] · 用 alternating dense/sparse
- [[self-attention]] · 标准版的复杂度问题
- [[flash-attention]] · 对照:它精确不跳对、只优化 IO;sparse 是近似改算法
- [[transformer-architecture]] · 框架
