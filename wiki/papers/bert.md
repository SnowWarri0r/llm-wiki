---
name: bert
type: paper
source: https://arxiv.org/abs/1810.04805
upstream: https://arxiv.org/abs/1810.04805
ingested: 2026-05-21
authors: Devlin, Chang, Lee, Toutanova (Google AI) · NAACL 2019 best paper
---

# BERT · Bidirectional Encoder Representations from Transformers

Transformer 之后的第一个分叉：**只要 encoder**。把双向上下文压进一个预训练模型，然后给下游 finetune。当时 NLP 的 11 项 benchmark 一夜被刷新。

## 一句话
**把 Transformer 的 encoder stack 单独拿出来，用 masked language model 让它一次性看到双向上下文做预训练**——理解类任务从此进入"先 pretrain 一个，到处 finetune"时代。

## 它要解决的痛点
2017 Transformer 出来，2018 OpenAI 用它的 decoder 部分搞出 GPT-1：从左到右预测下一个词，做 finetune 也能用。但 GPT-1 只能看左边上下文 —— 理解类任务（情感分析、问答、自然语言推理）天生需要双向。

更早的 ELMo 用双向 LSTM 拼接左右两个方向，但本质上还是两个单向模型 stack 在一起，互不通气。**没人真正做出过"一个 transformer，一次 forward 看到双向"的预训练**。

直接的难点：你不能直接训"双向语言模型预测下一个词"——因为它能看到右边，包括它自己。

## 核心贡献
1. **架构**：[[encoder-only-paradigm]] —— 只用 Transformer encoder（双向自注意力），抛弃 decoder
2. **训练任务**：[[masked-language-model]] —— 随机 mask 15% 的 token，让模型从上下文还原。绕开了"双向预测下一词会看到自己"的问题
3. **辅助任务**：[[next-sentence-prediction]] —— 两段输入 [CLS] A [SEP] B [SEP]，预测 B 是不是 A 的下一句（后被 RoBERTa 证伪）
4. **特殊 token**：[CLS] 用于句级分类，[SEP] 分隔段，segment embedding 区分 A/B
5. **结果**：11 项 NLP benchmark SOTA，GLUE 平均分从 GPT-1 的 72.8 提到 80.5

## 关键概念
- [[masked-language-model]] · MLM · BERT 的核心预训练任务
- [[next-sentence-prediction]] · NSP · 段间关系，后被证不重要
- [[encoder-only-paradigm]] · 编码器路线 · 跟 GPT 的 decoder-only 形成两极
- [[pretrain-finetune-paradigm]] · 先 pretrain 再 finetune · NLP 训练范式革命
- [[self-attention]] · 这次没 causal mask 全部可见
- [[transformer-architecture]] · BERT 用的就是 encoder 那一半

## 我的批注
- **真正的洞察不是"双向比单向好"**（这是直觉）。是**找到了一个能让 Transformer 学双向表征的损失函数** —— MLM。Trick is the trick.
- mask 15% 不是数字玄学：太低没有足够信号训练，太高上下文不够还原。15% 这个数后来 RoBERTa / MacBERT 都试过调整，差异不大
- 80%/10%/10% 的 mask 策略（80% 替换成 [MASK]，10% 替换成随机词，10% 保留原词）是为了让 fine-tune 时 token 分布不漂移 —— 这是个工程细节但很关键
- NSP 是 BERT 的"假洞察"：RoBERTa 2019 证明去掉 NSP 改成更长序列 + 更多数据反而更好。理由也合理：NSP 太简单，给的信号几乎都是话题级而不是真正的逻辑关系
- 最有意思的影响不在 BERT 本身，是它<strong>立住了 pretrain+finetune 范式</strong>。在它之前，每个任务都从随机初始化或浅 embedding 训起；之后所有任务都是"载入 BERT，加个小头 finetune"
- 跟 GPT 的对照：GPT 选了 decoder-only + 自回归，赌的是"生成能力是最通用的能力"；BERT 选了 encoder-only + 双向，赌的是"理解能力的表示更精确"。<strong>历史最终选了 GPT 路线</strong>，但 BERT 一族在 search / 嵌入 / RAG 里活得很好

## 跟 wiki 里其他 paper 的关系
- [[attention-is-all-you-need]] · BERT 用的就是它的 encoder 部分，layer 数加深
- [[gpt-1]] · 同期对照，decoder-only 路线
- [[resnet]] · BERT 每层里仍是 `LayerNorm(x + Sublayer(x))` 的残差结构
- 现代 RAG 系统的 embedding model（BGE / E5）几乎都是 BERT 后裔
- ColBERT / SBERT / Sentence-T5 都是把 BERT 的句向量用法专业化

## 历史定位
- 2017 Transformer · 提出但没有专门预训练范式
- 2018 GPT-1 · decoder-only · 用 Transformer 做 LM pretrain + finetune（这条线后来赢了 generation）
- 2018 BERT · encoder-only · 用 MLM 做双向 pretrain + finetune（这条线赢了 understanding）
- 2019 RoBERTa · 把 BERT 调到极致（去 NSP、更长训练、更大数据）
- 2019 ALBERT / DistilBERT · 压缩
- 2020 Sentence-BERT · 把 BERT 变成嵌入模型（RAG 的起点）
- 2023+ · 大多 LLM 是 decoder-only，但 RAG 的检索侧仍是 BERT 后代
