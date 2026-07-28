---
name: hybrid-linear-softmax-attention
type: concept
sources: [sana-video-2]
updated: 2026-07-28
---

# Hybrid Linear–Softmax Attention · 大多数层做摘要，少数层逐一核对

## 一句话

按固定节奏混排线性 attention 与完整 softmax attention：前者承担长序列的大部分计算，后者周期性恢复每个 query 对每个 token 的独立关系。

## SANA-Video 2.0 的节奏

```text
Linear → Linear → Linear → Softmax → 重复
```

softmax 占 25%。32 层模型有 24 层 linear、8 层 softmax；40 层模型有 30 层 linear、10 层 softmax。

这里的 softmax layer 不是事后校准一个数，而是重新计算完整 token-to-token attention。它产出的丰富表示随后进入下一轮线性层。

## 为什么不是越多 softmax 越好

在固定宽深的短程代理实验里，50% softmax 验证损失最低 0.897；25% 是 0.905，却在 1080p 形状上比 50% 少 29% 延迟。作者因此选质量—延迟拐点，而不是最低 loss。

25% 是具体实验选择，不是理论常数。序列长度、head 维度、kernel 和训练配方变化后，合理比例也可能变化。

## 链接

- [[gated-linear-attention]] · 便宜层怎样压缩关系。
- [[block-attention-residuals]] · 怎样把 softmax anchor 的特征带到更深层。
- [[sana-video-2]] · 完整架构、消融和效率口径。
