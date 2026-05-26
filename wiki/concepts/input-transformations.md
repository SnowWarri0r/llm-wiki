---
name: input-transformations
type: concept
sources: [gpt-1]
updated: 2026-05-21
---

# Input Transformations · 用输入格式喂任务

## 一句话
不为每个下游任务设计新的网络结构，而是<strong>把任务结构编码进输入文本</strong> —— 用分隔符、拼接顺序告诉模型"这是哪种任务"。

## 直觉
2018 之前 NLP 任务接入一般做法：
- 分类：模型最后接一个二/多分类 head
- 蕴含（NLI）：双输入，需要两路 encoder + 比较层
- 相似度：双输入，cosine 或交叉特征
- 多选 QA：每个候选答案一份 forward，再选最高

每种任务一种架构。GPT-1 觉得这事太麻烦了 —— **能不能让 transformer 一直是同一个 transformer，靠输入格式区分任务？**

类比：你跟同一个人说话，靠语气和句式让他知道"我是在问问题"还是"我在陈述"。模型也是同一个，区别只在输入格式。

## GPT-1 论文里的 4 种格式
**分类（情感、可接受性）：**
```
[start] this movie is terrible [extract]
                                    ↑ 这个位置的 hidden state 接分类头
```

**文本蕴含（NLI · premise → hypothesis）：**
```
[start] the bird is flying [delim] the bird has wings [extract]
                                                          ↑ 分类头预测 entail/contradict/neutral
```

**相似度（两个句子是否同义）：**
```
跑两次：
[start] sentence A [delim] sentence B [extract]
[start] sentence B [delim] sentence A [extract]
两次 hidden 相加 → 分类头
```

**多选 QA：**
```
对每个候选答案 c_i 跑一次：
[start] context + question [delim] c_i [extract]
得到 N 个 hidden，softmax 选最高的
```

`[start]` `[delim]` `[extract]` 是新加的特殊 token，只在 finetune 时学。

## 为什么这套设计影响深远
**它把"任务结构"从架构层挪到了数据层**。以前任务结构是模型架构的一部分（要写代码定义 head）；现在任务结构是输入文本的一部分（只需要文本编码就行）。

这是 prompting 的雏形：
- GPT-1 · "用特殊 token 编码任务结构"（仍需 finetune）
- GPT-2 · 发现可以用 zero-shot prompt 触发任务（"TL;DR:" 让模型做摘要）
- GPT-3 · 用 few-shot in-context learning：在 prompt 里给几个例子就行（连 finetune 都不要）
- ChatGPT · 用"system + user + assistant" 三角色格式

→ 一条直接的演化线。GPT-1 的 input transformations 是这条线的起点。

## 跟 BERT 的对比
BERT 也用了 `[CLS]` / `[SEP]` 这类特殊 token，但它的 head 设计仍是任务专属（每种任务一个 head）。GPT-1 把这思路推得更远：head 也固定（就是 LM head），只靠输入格式区分。

## 链接
- [[gpt-1]] · 提出
- [[causal-language-model]] · 预训练任务（finetune 时跟这个共用 head）
- [[in-context-learning]] · 这思路推到极致的产物
- [[pretrain-finetune-paradigm]] · 它服务的范式
