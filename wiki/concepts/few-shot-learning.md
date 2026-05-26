---
name: few-shot-learning
type: concept
sources: [gpt-3]
updated: 2026-05-22
---

# Few-Shot Learning · 少样本学习

## 一句话
在 prompt 里给几个输入输出例子，让模型不改权重就照着模式完成新样本。

## 直觉
这不是传统机器学习里的"拿几个样本 finetune 一下"，而是 GPT-3 语境下的 [[in-context-learning]]：例子只放在上下文里，模型读完就临时对齐任务格式。

像你给同事看三条工单处理样例，然后第四条让他照格式做，不需要改他的脑子。

## 怎么做的
```text
English: sea otter
French: loutre de mer

English: cheese
French: fromage

English: apple
French:
```

模型从前两个例子推断"这是翻译任务"，然后补最后一行。

## 代码出处
GPT-3 论文的 zero-shot / one-shot / few-shot 评测设置。

## 链接
- [[gpt-3]] · 来源 paper
- [[in-context-learning]] · 更大的机制
- [[emergent-abilities]] · few-shot 能力随 scale 浮现
