---
name: generalized-causal-attention
type: concept
sources: [sensenova-vision]
updated: 2026-07-17
---

# Generalized Causal Attention · 一条多模态序列里，精确规定谁能看谁

## 一句话

普通语言模型只允许后面的 token 看前面的 token；Bagel 把这条规则扩展到文字、输入图和待生成图：文字仍按顺序读，同一张图内部可以双向互看，后续内容可以读取已经完成的条件，但不能偷看尚未生成的答案。

## 为什么不能全都互相看

设训练序列是：

```text
[用户文字] [输入图] [回答文字] [要生成的图]
```

训练时“要生成的图”对应的干净答案已经在数据里。如果后面的文字或下一张图能够直接读取这份答案，模型就会在训练时作弊；推理时没有答案可偷看，结果会崩。反过来，同一张图的 patch 又不是一句从左到右的话，限制成严格因果注意力没有必要，图内 patch 可以双向交换信息。

所以 Bagel 使用分块规则：

| query 来自 | 可以读取 |
|---|---|
| 文字 token | 当前位置之前的文字与已经给定的条件 |
| 输入图的语义 token | 先前内容 + 同一张输入图的全部语义 token |
| 待生成图的带噪 VAE token | 先前条件 + 同一张图的全部带噪 VAE token |
| 后续内容 | 已完成图像的干净 VAE / 语义 token，但不能读取训练时的带噪答案块 |

## 为什么同一张图会出现三份表示

Bagel 对一张图可能同时保留三类 token，它们分工不同：

- **SigLIP2 / ViT token**：强调“图里是什么”，供理解和条件对齐；
- **干净 VAE token**：表示已经完成的图像，供后续内容继续引用；
- **带噪 VAE token**：当前正在被流匹配还原的变量，只服务于这次图像生成。

训练时带噪 VAE token 有回归目标，但不能成为后续 token 的捷径。推理完成一张图后，模型把它解码并换成干净表示，再继续生成后面的文字或图像。

## 和 MoT 的关系

两者回答的是不同问题：

- [[mixture-of-transformers]] 决定“这个 token 使用哪套 Transformer 权重”；
- generalized causal attention 决定“这个 token 在注意力里允许读取哪些位置”。

一个 token 可以走生成专家，同时读取理解专家产生的文字 key/value。**专家不同，不妨碍共享上下文；共享上下文，也不代表共享权重。**

## 链接

- [[sensenova-vision]] · 直接复用 Bagel 的注意力与双专家底座
- [[mixture-of-transformers]] · 理解专家与生成专家如何分工
- [[unified-multimodal-generation]] · 为什么这种底座能承载文本、图像和混合输出

## 来源

- Bagel: *Emerging Properties in Unified Multimodal Pretraining*, arXiv:2505.14683v3，§2.2 Generalized Causal Attention。
