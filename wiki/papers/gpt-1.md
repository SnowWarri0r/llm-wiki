---
name: gpt-1
type: paper
source: https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf
upstream: https://openai.com/research/language-unsupervised
ingested: 2026-05-21
authors: Radford, Narasimhan, Salimans, Sutskever (OpenAI) · 2018-06
---

# GPT-1 · Improving Language Understanding by Generative Pre-Training

OpenAI 在 BERT 之前 4 个月发的 paper。**第一个把"Transformer + 大规模 LM 预训练 + 任务 finetune"做成一套方法**，赢了 9 项 benchmark。当时被 BERT 盖过去，但 decoder-only + causal LM 的路线最终通往了 GPT-3 / ChatGPT。

## 一句话
**用 Transformer decoder 在 BookCorpus 上预训练"预测下一个词"，再 finetune 到各种下游任务** —— 用输入文本格式编码任务结构，避免给每个任务设计新架构。

## 它要解决的痛点
2017 Transformer 出来，2018 大家在试它怎么用。当时 NLP 主流：每个任务都从随机初始化或浅 embedding（word2vec / GloVe）训一个专门模型。

问题：
1. 标注数据少。情感分析 SST-2 才 6.7K 训练样本，从头训一个 transformer 必过拟合
2. 任务多种多样。分类 / 蕴含 / 相似度 / 多选 —— 都需要不同的 head 结构
3. 当时 ELMo（双向 LSTM 拼接特征）已经证明"在无标注语料上预训练"有用，但 LSTM 没法 scale

OpenAI 的赌局：**用 Transformer + 大规模 LM 预训练 + 简单 finetune 流程，能不能压过所有任务专门方法？**

## 核心贡献
1. **预训练任务**：[[causal-language-model]] —— 标准自回归 LM，每个位置预测下一个 token。训练信号密度极高（每个位置都算 loss）
2. **架构**：Transformer decoder × 12 层，带因果 mask 的 self-attention。117M 参数，BookCorpus 7000 本书做预训练
3. **任务接入**：[[input-transformations]] —— 不为每个任务设计新结构，而是<strong>把任务结构编码进输入文本</strong>（分隔符 + 拼接）。共用一个模型骨架
4. **Auxiliary LM loss**：finetune 时 LM loss 跟下游任务 loss 加权混合，让模型不忘记预训练的语言能力
5. **结果**：9 / 12 项 benchmark SOTA，证明思路对头

## 关键概念
- [[causal-language-model]] · CLM · 自回归预测下一个 token
- [[input-transformations]] · 用输入格式喂任务，不改架构
- [[decoder-only-paradigm]] · 跟 BERT 的 encoder-only 对照
- [[pretrain-finetune-paradigm]] · 跟 BERT 共享，但 GPT-1 更早实现
- [[self-attention]] · 这里带 causal mask
- [[transformer-architecture]] · 它的 decoder 部分

## 我的批注
- **被 BERT 盖过去是历史的偶然**。GPT-1（June 2018）早 BERT（Oct 2018）4 个月。但 BERT 双向 + MLM 在当年 NLP benchmark（GLUE 这种 understanding-heavy）上分数更高，吸走了所有注意力
- **Auxiliary LM loss 是个被低估的 trick**：在 finetune 时联合优化 LM loss 和任务 loss。后来 ChatGPT 的 SFT 阶段也是类似的"别忘了基础能力"思路
- **真正改变历史的不是 GPT-1 本身，是它的 thesis**：causal LM 预训练 + scale → 通用语言能力。这条路一直延伸到 GPT-3 / Claude / Llama，BERT 在前沿模型里已经退场了
- **Input transformations 是 prompting 的雏形**：把"the premise is X. the hypothesis is Y. is it entailed?"这种结构当作输入 —— GPT-3 in-context learning 只是把这件事推到极致（连 finetune 都不需要）
- 论文里没出现 "scaling laws" 这种词，但 thesis 已经隐含 —— "wonder if more data + more layers would keep improving"。后续 GPT-2 / GPT-3 就是逐步把这个假设推到极致

## 跟 wiki 里其他 paper 的关系
- [[attention-is-all-you-need]] · GPT-1 拿走了它的 decoder 部分
- [[bert]] · 同期同范式但 encoder-only + MLM，benchmark 当年赢了
- [[resnet]] · 每个 transformer block 仍带残差，深层训得动靠它
- 它跟 GPT-2 / GPT-3 是一条线：scaling 推到极致后从 finetune 走到 in-context learning

## 历史定位
- 2017 Transformer · 原始 paper · encoder-decoder · 翻译用
- 2018-06 **GPT-1** · 117M · decoder-only · CLM · pretrain+finetune · 9 项 SOTA
- 2018-10 BERT · 340M · encoder-only · MLM · pretrain+finetune · 11 项 SOTA（成为当年明星）
- 2019-02 GPT-2 · 1.5B · scale up · zero-shot 浮现
- 2020-06 GPT-3 · 175B · in-context learning 替代 finetune
- 2022-11 ChatGPT · GPT-3.5 + RLHF · 真正改变世界
