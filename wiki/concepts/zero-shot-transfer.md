---
name: zero-shot-transfer
type: concept
sources: [gpt-2, gpt-3, sam]
updated: 2026-06-23
---

# Zero-Shot Transfer · 不 finetune 直接用 prompt 触发任务

## 一句话
预训练完的 LM <strong>不改一个参数</strong>，直接在 prompt 里写任务格式，让模型续写出答案。

## 直觉
GPT-1 的范式是"pretrain → 加个 head → finetune"。一个任务一份模型 weights 一组 head 参数。

GPT-2 发现：**LM 足够大、训练数据足够多，它在预训练阶段已经"见过"无数次每种任务的格式**。比如 WebText 里有大量"... TL;DR:" 这种格式的文本，模型见过几百万次后，自然学会"看到 TL;DR: 就要总结前文"。

类比：教小孩做数学题。pretrain+finetune 是"先让他学语文（pretrain）再专门刷数学题（finetune）"；zero-shot 是"给他读够多书后，问他一道数学题 + 写'答：'，他能直接续写出答案"。前提是<strong>书里有足够多带答案的数学题</strong>。

## 怎么做的
**摘要**：
```
[文章正文]
TL;DR:
```
模型继续写 → 摘要

**翻译**：
```
The cat sat on the mat = 
```
模型续写 → "Le chat s'est assis sur le tapis"

**阅读理解**：
```
[文章]
Q: What did the cat do?
A:
```
模型续写 → "The cat sat on the mat"

**情感分类**：
```
Review: "This movie is terrible"
Sentiment:
```
模型续写 → "negative"

每个任务都靠<strong>提示文本</strong>把任务格式喂给模型，输出是 LM 续写的下一段 token。

## 跟 GPT-1 input transformations 的关系
GPT-1 的 input transformations（用 [start] [delim] [extract] 编码任务结构）跟 zero-shot 是<strong>同一个 idea 的不同阶段</strong>：
- GPT-1: 用特殊 token + finetune（仍要改 weights）
- GPT-2: 用自然语言 prompt + 不 finetune（不改 weights）
- GPT-3: prompt 里塞几个例子（few-shot in-context learning）

一条直接的演化线。区别在<strong>触发任务需要的精度</strong>：
- GPT-1 117M 模型，prompt 单靠"TL;DR:"触发不了 —— 需要 finetune 把这个映射强化
- GPT-2 1.5B 模型，prompt"TL;DR:"已经能触发 —— 模型自己学到了这层映射
- GPT-3 175B 模型，连给几个例子的能力都有 —— in-context learning 浮现

**触发不了 → 能触发 → 能学新任务**：scale 把每个台阶都打通。

## 它的局限
- 准确度不高：GPT-2 zero-shot 翻译 BLEU 5-10 分，远低于专门 finetune 的 30-40 分
- prompt sensitive：同一任务用不同提示词差别巨大（"TL;DR:" vs "Summary:" vs "总结："）
- 不可控：模型经常输出格式不对的内容，需要 prompt engineering

这些局限在 GPT-3 / instruction tuning / RLHF 后逐步缓解，但 zero-shot 仍是个<strong>启发式</strong>能力，不像 finetune 那样可工程化。

## 链接
- [[gpt-2]] · 提出
- [[input-transformations]] · 前身
- [[in-context-learning]] · 后续演化（GPT-3）
- [[language-modeling-as-multitask]] · 理论解释
