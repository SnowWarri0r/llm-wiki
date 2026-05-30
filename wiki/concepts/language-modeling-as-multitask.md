---
name: language-modeling-as-multitask
type: concept
sources: [gpt-2]
updated: 2026-05-21
---

# Language Modeling as Multitask Learning · LM 即多任务学习

## 一句话
GPT-2 论文标题点破的核心 thesis：训练 LM 预测下一词的过程<strong>已经在学无数个具体任务</strong>，多任务能力是预训练的天然副产品。

## 直觉
传统 NLP 把任务理解为离散的：分类是分类、翻译是翻译、问答是问答。每个任务一份数据集一份标注一份模型。

GPT-2 论文标题：**"Language Models are Unsupervised Multitask Learners"** —— 这是对范式的彻底重新框定。

**核心论点**：互联网文本本身就<strong>充满任务示例</strong>。比如：
- 一篇博客文章末尾的 "TL;DR: ..." → 训练 LM 时模型学到 "看到 TL;DR: 就要总结上文"。这是一个隐式的<strong>摘要任务样本</strong>
- "English: Hello. French: Bonjour." → 翻译任务样本
- "Q: ... A: ..." → 问答任务样本
- "Review: ... Sentiment: positive" → 分类任务样本

互联网这种<strong>无标注</strong>文本里，每种任务有几百万到几十亿个隐式样本。LM 训练时每个 token 位置预测下一词，本质上是在<strong>同时</strong>学语法 + 常识 + 翻译 + 摘要 + QA + 分类 + ... 上万种任务。

类比：传统 NLP 是"专科医生"训练 —— 每个科室单独培养。GPT-2 视角是"全科医生"训练 —— 让一个人读完海量医学文献，他自然学会各科室的常识。

## 怎么"读懂"训练数据
模型在<strong>预测下一词</strong>这个单一目标下：

```
... 文章 ... TL;DR: [predict next token]
                    ↑ 这里预测的就是"摘要的第一个词"
                    模型必须先在内部"理解"文章
                    才能预测出合理的总结开头
```

每个这种格式的 sample 都让模型学到一点点"看到 TL;DR: 就该总结"的映射。WebText 里有数百万这种例子，模型学到了。

同理：
- 看到 `english: X french:` 后续 → 学翻译
- 看到 `Q: X A:` 后续 → 学问答
- ...

所以<strong>预训练 = 万任务隐式监督学习</strong>。任务的种类不是训练时显式指定的，是<strong>从数据分布里浮现的</strong>。

## 为什么这个 thesis 重要
1. **解释了为什么大 LM 能 zero-shot**：模型预训练时已经隐式学过这个任务，prompt 只是触发已有能力，不是教新东西
2. **预言了 scaling laws**：更多数据 + 更大模型 → 模型能"覆盖"更多任务类型 + 每种学得更细
3. **奠定 prompt engineering 的合理性**：好的 prompt = 找到预训练时模型见过的"任务格式"信号
4. **暗示了 instruction tuning**：如果普通 LM 预训练已经在学多任务，那么用<strong>更整齐的"指令-回答"对</strong>训一遍（InstructGPT/ChatGPT 做的事）应该效果更好 —— 后来证实了

## 它的局限
"LM 即多任务学习"是个有用的 frame，但<strong>不是所有任务都能从纯 LM 里浮现</strong>：
- 需要复杂多步推理的任务 → CoT prompting / 显式 RL 训练能加强
- 需要工具使用的任务 → 要专门 finetune（如 Toolformer / function calling）
- 需要遵循指令的任务 → 要 instruction tuning + RLHF（GPT-3.5 → ChatGPT 那一步）

所以现代 LLM 的训练 = LM 预训练（多任务学习的隐式版） + 指令微调（多任务学习的显式版） + RLHF（用人类反馈对齐）。GPT-2 立的 thesis 是<strong>第一步</strong>，后续两步是工程上的强化。

## 链接
- [[gpt-2]] · 提出
- [[causal-language-model]] · 多任务学习的载体
- [[zero-shot-transfer]] · 这个 thesis 的直接应用
- [[in-context-learning]] · GPT-3 把这个 thesis 推到极致
