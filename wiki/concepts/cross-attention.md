---
name: cross-attention
type: concept
sources: [attention-is-all-you-need]
updated: 2026-05-22
---

# Cross-Attention · 交叉注意力

## 一句话
Decoder 用自己的 Query，去查 Encoder 输出的 Key/Value，让生成过程能看见输入序列。

## 直觉
Self-attention 是"班里同学互相看"；cross-attention 是"写答案的人翻参考资料"。翻译任务里，encoder 先读完整个源语言句子；decoder 每生成一个目标词，就用 cross-attention 回头查源句里相关位置。

## 怎么做的
在 Transformer decoder block 里通常有三段：

1. masked self-attention：decoder 看自己已经生成的前缀
2. cross-attention：decoder 的 hidden state 做 Q，encoder 输出做 K/V
3. FFN：逐 token 处理

Decoder-only GPT 路线把 encoder 和 cross-attention 都砍掉，统一变成前缀条件生成。

## 代码出处
Transformer 原论文架构图里的 "multi-head attention over encoder output" 子层。

## 链接
- [[transformer-architecture]] · cross-attention 的位置
- [[multi-head-attention]] · 具体 attention 机制
- [[decoder-only-paradigm]] · 为什么后来的 GPT 路线不用它
