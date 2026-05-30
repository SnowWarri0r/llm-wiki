---
name: rope
type: paper
source: https://arxiv.org/abs/2104.09864
upstream: https://arxiv.org/abs/2104.09864
ingested: 2026-05-25
authors: [Jianlin Su, Yu Lu, Shengfeng Pan, Ahmed Murtadha, Bo Wen, Yunfeng Liu]
year: 2021
---

# RoFormer · Rotary Position Embedding (RoPE)

## 一句话
把位置信息编码成 Q/K 向量的**旋转角度**，让 attention 的点积天然就能感知相对位置 —— 不用额外参数，不用改架构，现在几乎所有主流 LLM 都用这个。

## 它要解决的痛点

Transformer 的 attention 本身**对顺序无感**（把 token 打乱，Q·K^T 算出来的分数一模一样）。Attention Is All You Need 用 sinusoidal PE 解决了这件事 —— 在输入层给每个 token 的 embedding 加一个位置向量。

但 sinusoidal PE 有几个问题：

1. **加在输入层就完事** —— 位置信息随着层数加深会被稀释，到后面几层所剩无几
2. **编码的是绝对位置** —— 模型要想知道"token 5 跟 token 8 差几个位置"，得自己从两个绝对编码里做减法；不够直接
3. **长上下文外推差** —— 训练时见过 512 长度，推理时给 2048 就崩（虽然理论上 sin/cos 能外推，实际效果不好）

后来出了 Learned PE（GPT-2 / BERT），直接把位置当 embedding 训。更灵活，但**完全不能外推** —— 没见过的 position id 没有对应 embedding。

RoPE 的做法完全不同：**不在输入层加位置向量，而是在每次算 attention 时把 Q 和 K 按位置旋转**。

## 核心贡献

1. **旋转编码位置**：position m 的 Q 向量被旋转 m×θ 度；position n 的 K 向量被旋转 n×θ 度。Q·K 点积的结果里天然包含 (m−n)×θ —— 这就是相对位置，不用任何额外操作
2. **零额外参数**：旋转角度是按位置计算的（跟 sinusoidal 用同一套频率 10000^(−2i/d)），不需要训练
3. **每层都有位置信息**：因为旋转发生在 attention 计算时（不是输入时），所以位置信号不会随层数稀释
4. **距离越远衰减越快**：RoPE 自带一个性质 —— 两个 token 越远，位置对 attention score 的贡献越弱。这跟直觉一致（离你越远的词对你影响越小）
5. **长上下文可扩展**：后续 NTK-aware scaling / YaRN / Dynamic NTK 等方法可以在 RoPE 基础上把上下文窗口从 4K 扩到 128K+

## 关键概念 → 概念页链接

- [[rotary-position-embedding]] · RoPE 核心机制 —— 旋转 Q/K
- [[relative-position-encoding]] · 为什么"相对位置"比"绝对位置"好
- [[positional-encoding]] · PE 家族全景（sinusoidal / learned / RoPE / ALiBi）
- [[self-attention]] · attention 为什么不带位置
- [[multi-head-attention]] · RoPE 在多头里怎么用
- [[kv-cache]] · RoPE 跟 KV cache 的兼容性

## 我的批注 / 疑问

- RoPE 的数学核心是"旋转保角性" —— 2D 旋转保持向量长度和夹角不变，所以旋转后的点积只多一个 position-dependent 偏移量，不会破坏原始语义相似度
- 实际实现里不会真的做矩阵乘法旋转，而是用 sin/cos 直接重排元素（很快），跟 Flash Attention 完美兼容
- 2024-2025 几乎所有新 LLM 都用 RoPE 或 RoPE 的变体 —— 这篇论文是"静悄悄改变了整个行业"的那种
- Jianlin Su（苏剑林）是中国开发者，这篇论文是中文 NLP 社区对全球 LLM 基础设施贡献最大的成果之一
- 疑问：NTK-aware scaling 到底改了什么？为什么直接拉伸频率不如按信息论调整？→ 后续如果做 context extension 专题可以展开
