---
name: positional-encoding
type: concept
sources: [attention-is-all-you-need, rope]
updated: 2026-05-20
---

# Positional Encoding · 位置编码

## 一句话
Attention 本身**对位置不敏感**（"dog bites man" 和 "man bites dog" 算出来一样），所以要显式给每个位置加一个独特的"位置向量"。

## 直觉
RNN 天然有顺序：t=1 → t=2 → t=3。Attention 是**置换不变的** —— 对 Q · K^T 来说，把 K 矩阵的行打乱不影响结果（只影响输出的对应位置）。

为了让 transformer 能区分"第一个 the" vs "第二个 the"，要给每个 token 加一个**只依赖位置的向量**：

```
input = embedding(token) + PE(position)
```

PE(pos) 必须对每个 pos 唯一，且让模型能学到"相对位置"信息。

## Sinusoidal PE（论文用的）
```
PE(pos, 2i)   = sin(pos / 10000^(2i / d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i / d_model))
```

第 i 维用频率 1 / 10000^(2i / d_model) 的正弦/余弦。低维高频，高维低频。

**为什么这么设计**：
- 每个位置 pos 在 d_model 维度上有唯一的频率指纹
- 任何相对位置 k 都能表达成 PE(pos+k) 是 PE(pos) 的**线性变换**（用 sin/cos 加法定理）→ 模型能学相对位置
- 不需要训练（无参数）
- 可外推到训练时没见过的长序列（理论上）

## 后续改进
论文这种 sinusoidal PE 是 OG 方案，但有问题（外推效果一般、跟现代长上下文不太搭）。现代 LLM 大多换了：

- **Learned PE**（GPT-2）：把 PE 当 embedding 训。简单但不能外推。
- **Rotary PE / RoPE**（GPT-J / LLaMA / Mistral / Qwen）：不在 embedding 层加位置，而是每层 attention 算之前**旋转 Q/K** —— 点积天然包含相对位置，零额外参数。2024-2025 几乎所有新 LLM 都用。详见 [[rotary-position-embedding]]。
- **ALiBi**（BLOOM）：在 attention scores 上加位置距离偏置。可外推。
- **NoPE**：完全不要 PE，让模型自己学（小模型不行，大模型 OK）。

## 链接
- [[self-attention]] · attention 为什么不带位置
- [[attention-is-all-you-need]] · 论文（sinusoidal PE）
- [[rope]] · RoPE 论文
- [[rotary-position-embedding]] · RoPE 详解
- [[relative-position-encoding]] · 为什么相对位置好
- [[transformer-architecture]] · 在哪嵌入 PE
