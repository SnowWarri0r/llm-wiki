---
name: encoder-only-paradigm
type: concept
sources: [bert]
updated: 2026-05-21
---

# Encoder-Only Paradigm · 编码器路线

## 一句话
只用 Transformer 的 encoder 部分（双向 self-attention，没有 causal mask），目标是<strong>产生表征</strong>而不是<strong>生成 token</strong>。

## 直觉
Transformer 原论文是 encoder-decoder（翻译任务）。2018 三条路同时出现：
- **encoder-only**：BERT · 双向 attention · 输出表征 → 理解任务
- **decoder-only**：GPT · 因果 mask · 输出下一 token → 生成任务
- **encoder-decoder**：T5 / BART · 两边都有 · 输入序列 → 输出序列任务（翻译、摘要）

Encoder-only 的核心选择是 **"双向"换"不能生成"** —— 它能看到每个位置左右的全部上下文，所以表征精确；代价是无法做自回归生成。

## 结构差异
**BERT encoder layer**（双向）：
```
y = LayerNorm(x + MultiHeadAttention(x, x, x))   # 没 mask，所有位置互看
y = LayerNorm(y + FFN(y))
```

**GPT decoder layer**（因果）：
```
y = LayerNorm(x + MaskedMultiHeadAttention(x, x, x))  # causal mask
y = LayerNorm(y + FFN(y))
```

差别只在 attention 的 mask。**架构几乎一样，训练目标决定一切**。

## 各代表
- **BERT** (2018) · 12/24 层 encoder
- **RoBERTa** (2019) · 同 BERT 结构，去 NSP，扩数据
- **ALBERT** (2020) · 跨层参数共享，参数省 18×
- **DeBERTa** (2021) · 解耦 attention 的位置和内容
- **DistilBERT / TinyBERT** · 压缩
- **ELECTRA** (2020) · MLM 换成 replaced-token-detection，效率高

## 现在还活着吗
**不在前沿语言模型里。** 2020 GPT-3 之后，decoder-only 用 in-context learning 几乎可以做所有任务，连分类都不用专门 finetune。

但是在两个领域活得很好：
- **嵌入 / 检索 / RAG**：BGE / E5 / Cohere-Embed 几乎都基于 BERT。decoder-only 算嵌入慢、不双向
- **小型分类 / NER / 信息抽取**：finetune 一个 BERT 比 prompt 一个 decoder-only 便宜得多

## 跟 decoder-only 的根本对照
| | encoder-only | decoder-only |
|---|---|---|
| Attention | 双向 | 因果 |
| 主任务 | 还原 / 分类 / 表征 | 生成下一 token |
| 训练信号密度 | 稀疏（仅 mask 处） | 密集（每个位置） |
| 适合 | 理解 / 检索 | 生成 / 通用 |
| 扩展性 | 中等（330M 顶天就够用） | 极强（→ 100B+） |

## 链接
- [[bert]] · encoder-only 代表
- [[gpt-1]] · decoder-only 对照
- [[self-attention]] · attention 的可见性差异是核心
- [[transformer-architecture]] · 都是它的子集
