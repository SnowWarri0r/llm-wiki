---
name: causal-language-model
type: concept
sources: [gpt-1, attention-is-all-you-need]
updated: 2026-05-21
---

# Causal Language Model · CLM · 自回归语言模型

## 一句话
给定前 N 个 token，预测第 N+1 个 token。训练时每个位置都做这个预测 —— 每个 token 都贡献一份 loss。

## 直觉
从小你学语文是这样：读完一句话的开头能猜接下来的词。"今天天气真..." → "好 / 热 / 冷 / 不错"。猜对说明你懂语法 + 常识 + 词频分布。

CLM 把这个变成训练目标：模型读完前缀，预测下一个 token 的概率分布；跟真实下一个 token 算交叉熵。

**关键洞察**：要把"猜下一个词"做对，模型要学：
- 语法（前面是主语，后面该是动词或形容词）
- 语义（"今天天气"后面接什么合理）
- 常识（"水沸腾后是" → "气体" 不是 "固体"）
- 推理（"如果 A > B 且 B > C，那么 A" → "> C"）

→ 一个"预测下一词"任务，逼着模型把整个世界知识压进权重。这是 LLM 的核心训练范式。

## 怎么做的
```python
# 单条样本: "the cat sat on the mat"
tokens = tokenize("the cat sat on the mat")  # [the, cat, sat, on, the, mat]

# 输入 vs target 错位一格
input  = [the, cat, sat, on, the]
target = [cat, sat, on, the, mat]

# 一次 forward，所有位置同时预测下一个
hidden = transformer(input)  # shape: [seq_len, hidden_dim]
logits = lm_head(hidden)      # shape: [seq_len, vocab_size]

# 每个位置算 loss
loss = cross_entropy(logits, target).mean()
```

**关键技巧**：训练时一次 forward 同时算所有位置的 loss。但 attention 必须加 **causal mask** —— 位置 i 只能看到 ≤ i 的 token，否则模型作弊（直接看到下一个 token）。

## 为什么训练效率高
对比 BERT 的 [[masked-language-model]]：
- MLM：每条样本 15% 位置做预测 → 训练信号稀疏
- CLM：每条样本所有位置都做预测 → 训练信号密集 6 倍多

同等 wall-clock 下，CLM 让 transformer 看到的"预测任务"次数远多于 MLM。这部分解释了为什么 decoder-only 模型 scale 上去更顺。

## 推理时怎么生成
训练完后，用 CLM 生成文本：
```python
prompt = "今天天气真"
tokens = tokenize(prompt)

for _ in range(max_new):
    logits = model(tokens)
    next_token = sample(logits[-1])    # 最后一个位置的预测
    tokens.append(next_token)
    if next_token == EOS: break

print(detokenize(tokens))
```

每生成一个 token 就把它接到输入后面，再 forward 一次。这就是<strong>自回归生成</strong>（autoregressive generation）—— "auto" = 自己，"regress" = 回归到之前的输出。

## 跟其他训练目标的对比
| 目标 | 信号密度 | 双向 | 生成？ | 谁用 |
|---|---|---|---|---|
| **Causal LM (CLM)** | 每位置都算 | 否 | 可以 | GPT 系 / Llama / Claude |
| **Masked LM (MLM)** | 15% 位置 | 是 | 不行（需 decoder） | BERT 系 |
| **Replaced Token Detection** | 每位置 | 是 | 不行 | ELECTRA |
| **Prefix LM** | 部分位置 | 部分 | 可以 | T5 / UL2 |

decoder-only + CLM 现在是大模型主流。原因：训练简单、生成天然、scaling 行为好。

## 链接
- [[gpt-1]] · 最早用 CLM + Transformer 做大规模预训练
- [[masked-language-model]] · 对照的另一条预训练路线
- [[self-attention]] · CLM 必须加 causal mask 的就是它
- [[decoder-only-paradigm]] · CLM 的载体
