---
name: transformer-architecture
type: concept
sources: [attention-is-all-you-need]
updated: 2026-05-20
---

# Transformer Architecture · 整体架构

## 一句话
Encoder 6 层 + Decoder 6 层，每层都是"multi-head attention + FFN + residual + layernorm"的标准块。Decoder 多一个 cross-attention 子层看 encoder 输出。

## Encoder 单层
```
x → MultiHeadAttention(x, x, x)  → Add & LayerNorm → 
  → FFN(·) → Add & LayerNorm → output
```

- **Self-attention**：每个位置看序列所有位置（包括自己）
- **FFN**：两层 MLP（线性 → ReLU → 线性），dim 中间是 2048（输入 512）
- **Residual + LayerNorm**：让梯度好流，深层训得动

## Decoder 单层
```
y → MaskedMultiHeadAttention(y, y, y) → Add & LayerNorm →
  → MultiHeadAttention(y, x_enc, x_enc) → Add & LayerNorm →
  → FFN(·) → Add & LayerNorm → output
```

- **第一个 self-attention 加 causal mask**：每个位置只能看到自己和之前（不偷看未来）
- **[[cross-attention]]** 子层：Q 来自 decoder，K/V 来自 encoder → "decoder 看 encoder 在编码什么"
- 其他跟 encoder 一样

## 输入处理
```
input_tokens → embedding → + positional_encoding → 进 encoder
target_tokens → embedding → + positional_encoding → 进 decoder
```

参见 [[positional-encoding]]。

## 输出
Decoder 最后一层 → linear → softmax → 词表上的概率分布

训练时跟 ground truth 算 cross-entropy loss，teacher forcing（喂真实前缀给 decoder）。

## 配置（论文 base 版）
- d_model = 512
- 6 层 encoder + 6 层 decoder
- h = 8 head, d_k = d_v = 64
- FFN d_ff = 2048
- dropout 0.1
- 总参数 65M

## 现代变种
- **GPT 系列**：去掉 encoder，纯 decoder + causal mask（用 decoder 做完整任务）
- **BERT**：去掉 decoder，纯 encoder + masked LM 训练
- **T5 / BART**：保留 encoder-decoder（适合 seq2seq 任务如翻译、摘要）

GPT 路线最后赢了：decoder-only + 自回归生成成为通用范式。

## 链接
- [[self-attention]] · 核心操作
- [[multi-head-attention]] · 每个 attention 子层用的
- [[positional-encoding]] · 怎么加位置信息
- [[cross-attention]] · Decoder 独有的子层
- [[residual-layernorm]] · 训练稳定的关键
- [[attention-is-all-you-need]] · 论文
