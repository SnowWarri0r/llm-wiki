---
name: block-attention-residuals
type: concept
sources: [sana-video-2]
updated: 2026-07-28
---

# Block Attention Residuals · 让深层 token 按需翻早先的块摘要

## 一句话

每若干层冻结一份残差块摘要；后续层不是只接上一层，而是让每个 token 用 softmax 在输入、旧块和当前 partial sum 之间挑一份加权组合。

## 为什么要分块

每层都保存历史，内存约 \(O(NLd)\)。每 \(S\) 层只保存一次，约变成：

\[
O\!\left(N\left\lceil\frac{L}{S}\right\rceil d\right).
\]

SANA-Video 2.0 取 \(S=8\)。32 层最多只有输入和四个完成块来源，而不是 32 份逐层激活。

## 路由不是全视频一把尺

对某个 token \(x\)：

\[
h_l(x)=\sum_i\alpha_{i\to l}(x)v_i(x).
\]

\(\alpha\) 来自共享 query 与每个来源特征的点积再做 softmax。query 跨深度共享，但来源 \(v_i(x)\) 随 token、层与时间步变化，所以不同 token 仍能选不同旧块。

论文的机制干预显示：在新块刚开始、当前 partial sum 尚未重建时，删除旧块来源会让有效秩下降 82%–91%；进入块内部后影响很小。这说明旧块主要在“刚清空工作台”的边界补信息。

## 链接

- [[residual-layernorm]] · 普通逐层残差骨架。
- [[sana-video-2]] · 路由公式、数字例与消融。
- [[hybrid-linear-softmax-attention]] · 被跨深度复用的混合注意力表示。

