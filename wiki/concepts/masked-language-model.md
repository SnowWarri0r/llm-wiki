---
name: masked-language-model
type: concept
sources: [bert]
updated: 2026-05-21
---

# Masked Language Model · MLM

## 一句话
随机把句子里 15% 的 token 换成 `[MASK]`，让模型用<strong>剩下所有位置</strong>（左右都行）的信息预测被遮住的词。

## 直觉
传统语言模型只能学单向（"下一个词是什么"或"上一个词是什么"），是为了避开"目标词不能看自己"。

MLM 用一个简单粗暴的诡计绕开：**先把要预测的位置遮成 `[MASK]`，模型看不到答案了，所以双向可见也安全**。代价是预训练阶段输入分布跟下游不太一样（有 `[MASK]`），所以工程上有 80/10/10 策略平衡。

类比：完形填空。给你一段话挖掉一些词，让你猜。比起从左到右一个一个补，完形填空让模型必须同时利用左右两边线索 —— 学到的表征更"理解性"。

## 怎么做的
```python
# 训练时每条样本
tokens = tokenize("the cat sat on the [mat] yesterday")
#                                       ↑ 这里被选中（15% 概率）

# 80/10/10 策略
roll = random()
if roll < 0.8:
    tokens[i] = "[MASK]"          # 标准做法
elif roll < 0.9:
    tokens[i] = random_token()    # 替换成随机词，强迫模型不靠 [MASK] 标记
else:
    tokens[i] = tokens[i]         # 不改，但仍要预测——强迫模型对每个位置都"上心"

# forward
hidden = bert(tokens)              # 双向 transformer encoder
logits = decoder_head(hidden[i])   # 只在被选中位置算 loss
loss = cross_entropy(logits, original_token)
```

每条样本平均挖 15% 的 token，所以训练信号比 LM 的"每个 token 都预测"稀疏了 6 倍多 —— **BERT 训练的数据量必须更大，wall-clock 更长**。

## 为什么是 15%
论文没给详细消融。后来研究：
- 太低（5%）信号太弱
- 太高（40%）上下文残缺，难还原
- 15% 是个经验最优区间

## 为什么 80/10/10
关键问题：训练时 token 序列里有 `[MASK]`，但 finetune 和 inference 时<strong>不会出现 `[MASK]`</strong>。如果 100% 都换成 [MASK]，模型会过度依赖 [MASK] 这个特殊 token —— 一旦没了它，行为就变差。

80/10/10 让模型：
- 80% 时学习"用上下文还原"
- 10% 时学习"识别错词" —— 当真实数据有噪声时仍稳健
- 10% 时学习"对所有位置都保持表征质量" —— 因为不知道哪个会被算 loss

## 跟 GPT 的对比
- **GPT (causal LM)**：每个位置都预测下一个 token。训练信号密集（每个位置都贡献 loss），但只能看左边
- **BERT (MLM)**：只在 mask 位置预测。训练信号稀疏，但能看双向
- 工程取舍：相同数据量下 GPT 训练信号更多，BERT 表征质量更精

后来研究发现 decoder-only 在足够数据 + 足够大模型下表征也能很好 → GPT 路线赢了。但短数据 + 小模型场景 BERT 系仍优。

## 链接
- [[bert]] · 提出论文
- [[next-sentence-prediction]] · 配套的另一个预训练任务
- [[encoder-only-paradigm]] · MLM 的载体
- [[self-attention]] · 双向自注意力是关键，没 causal mask
