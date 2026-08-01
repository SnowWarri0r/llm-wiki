---
name: gated-linear-attention
type: concept
sources: [sana-video-2]
updated: 2026-07-28
---

# Gated Linear Attention · 把所有 token 先写进固定大小的公共状态

## 一句话

不为每个 query 保存一整行 softmax 权重，而把 key/value 先汇总进固定大小状态，再让每个 query 读取；序列成本接近线性，但细粒度 token-to-token 关系会被压缩。

## 从普通 attention 看差别

普通 attention：

\[
O=\operatorname{softmax}(QK^\top)V.
\]

先形成 \(N\times N\) 关系表。线性注意力选择可分解的非负特征映射 \(\phi\)，交换乘法顺序：

\[
O=\phi(Q)\left(\phi(K)^\top V\right).
\]

括号里先算出固定大小的状态。SANA-Video 2.0 还给写入和输出各加一扇门：

\[
S=\sum_n v_n(\beta_n k_n)^\top.
\]

- \(\beta_n\)：第 \(n\) 个 token 写多少。
- \(S\)：所有 token 共用的一份摘要。
- 输出 gate：第 \(j\) 个 token 从摘要读出的内容保留多少。

## 为什么会有秩瓶颈

若 head 维度 \(d=128\)，无论有 1,000 还是 100,000 个 token，状态都只有 \(128\times128\)，秩最高 128。完整 softmax 关系表则可以表达更多彼此独立的 token 关系。

所以它像“先把整场会议写成纪要再回答问题”：读得快、存得少，但不保证保住每一个人与每一个时刻的精确对应。

## 链接

- [[sana-video-2]] · 三层 gated linear + 一层 softmax 的视频生成落地。
- [[hybrid-linear-softmax-attention]] · 用周期性 softmax 补精细关系。
- [[self-attention]] · 完整两两注意力。
- [[flash-attention]] · 不改 softmax attention 结果的 IO 优化。
