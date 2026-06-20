---
name: layernorm
type: concept
sources: [attention-is-all-you-need, bert, gpt-1, gpt-2, gpt-3]
updated: 2026-05-22
---

# LayerNorm · 层归一化

## 一句话
对每个 token 自己的 hidden 维度做归一化，不依赖 batch 里其他样本。

## 直觉
[[batchnorm]] 是看一批样本的统计量，适合 CNN 训练；LayerNorm 是每个 token 自己整理自己的特征尺度，适合序列模型。推理时 batch 怎么拼、句子多长，都不影响这个 token 的归一化统计。

这对 LLM 很关键：线上请求 batch 是动态凑的，不能让"旁边坐了谁"改变你这条样本的输出。

## 怎么做的
对 hidden vector `x`：

```text
y = (x - mean(x)) / std(x) * gamma + beta
```

`mean/std` 在 hidden 维度上算，`gamma/beta` 是可学习参数。

## 代码出处
Transformer/BERT/GPT block 里每个 attention / FFN 子层旁边都有 LayerNorm 变体。

## 链接
- [[normalization]] · 归一化家族对照(BN/LN/GN/RMSNorm 只差对哪根轴)+真数字例子
- [[residual-layernorm]] · LayerNorm 跟 residual 怎么配
- [[batchnorm]] · CNN 时代的对照
- [[transformer-architecture]] · Transformer block 的稳定组件
