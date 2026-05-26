---
name: decoder-only-paradigm
type: concept
sources: [gpt-1, attention-is-all-you-need]
updated: 2026-05-21
---

# Decoder-Only Paradigm · 解码器路线

## 一句话
只用 Transformer 的 decoder 部分（带 causal mask 的 self-attention），目标是<strong>预测序列里每个位置的下一个 token</strong> —— 训练完后天然能做生成。

## 直觉
Transformer 原论文是 encoder-decoder（翻译任务）。2018 三条路同时出现：
- **encoder-only**：BERT · 双向 attention · 输出表征 → 理解任务
- **decoder-only**：GPT · 因果 mask · 输出下一 token → 生成任务
- **encoder-decoder**：T5 / BART · 两边都有 · seq2seq

Decoder-only 的核心选择是<strong>"因果 mask"换"训练 = 推理"</strong>：训练时每个位置就是在做"预测下一个 token"，推理时只是把生成的 token 接回输入再 forward 一次 —— 训练目标和推理使用方式完全一致。这种一致性极大简化了 scaling。

## 结构差异
**GPT decoder layer**（因果）：
```python
y = LayerNorm(x + MaskedMultiHeadAttention(x, x, x))  # 带 causal mask
y = LayerNorm(y + FFN(y))
```

**BERT encoder layer**（双向）：
```python
y = LayerNorm(x + MultiHeadAttention(x, x, x))   # 没 mask，所有位置互看
y = LayerNorm(y + FFN(y))
```

差别只在 attention 的 mask。**架构几乎一模一样，训练目标决定一切**。

## 为什么这条路最后赢了
2018 时大家觉得 encoder-only（BERT）更强 —— 双向上下文嘛，理解任务通吃。但 2020 之后 decoder-only 反超的原因：

1. **训练信号密集**：CLM 每个位置都算 loss，MLM 只在 15% mask 处。同等数据下 decoder-only 看到的预测任务多
2. **生成天然支持**：BERT 需要外挂 decoder 才能生成，decoder-only 直接拿来就用
3. **Scale 行为更顺**：GPT-2 (2019) → GPT-3 (2020) → GPT-4 (2023) 一路 scale 都涨，BERT 线 scale 上去边际收益递减
4. **In-context learning 浮现**：GPT-3 发现"在 prompt 里给几个例子就行"，根本不用 finetune。BERT 系做不到这种 prompt-only 任务

→ decoder-only 从 2020 开始统治大模型，BERT 系退到嵌入 / 检索领域

## 各代表
- **GPT-1** (2018) · 117M · 12 层 · 第一个证明可行
- **GPT-2** (2019) · 1.5B · 48 层 · 发现 zero-shot 浮现
- **GPT-3** (2020) · 175B · 96 层 · in-context learning
- **GPT-4 / Claude / Llama / Qwen** · 一路 decoder-only 到底

## 跟 encoder-only 的根本对照
| | decoder-only | encoder-only |
|---|---|---|
| Attention | 因果 | 双向 |
| 主任务 | 生成下一 token | 还原 / 分类 / 表征 |
| 训练信号密度 | 每位置 | 稀疏（仅 mask 处） |
| 推理与训练 | 完全一致 | 不一致（finetune 时换 head） |
| 适合 | 生成 / 通用 / 大模型 | 理解 / 嵌入 / 小模型 |
| 扩展性 | 极强（→ 100B+） | 中等（330M 顶天） |

## 链接
- [[gpt-1]] · decoder-only 路线起点
- [[bert]] · encoder-only 对照
- [[causal-language-model]] · decoder-only 配套的训练目标
- [[transformer-architecture]] · 它的子集
- [[encoder-only-paradigm]] · 另一条路
