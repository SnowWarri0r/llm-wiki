---
name: gpt-2
type: paper
source: https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf
upstream: https://openai.com/research/better-language-models
ingested: 2026-05-21
authors: Radford, Wu, Child, Luan, Amodei, Sutskever (OpenAI) · 2019-02
---

# GPT-2 · Language Models are Unsupervised Multitask Learners

GPT-1 之后 8 个月，OpenAI 把同一架构<strong>放大 13 倍</strong>（117M → 1.5B），换上更干净的数据（WebText），把"prompt 调用就能做任务"这事第一次拿出来 demo。从 GPT-1 的"pretrain + finetune"演化到 GPT-2 的"<strong>pretrain + 直接 prompt 触发</strong>"。

## 一句话
**同一个 Transformer decoder 架构放大到 1.5B + 用 WebText 训，发现 zero-shot 可以触发摘要 / 翻译 / 阅读理解 —— 不用 finetune 也能跨任务工作**。

## 它要解决的痛点
GPT-1 验证了"pretrain + finetune"思路。但每个新任务还得 finetune 一遍，工程上仍麻烦：
- 各任务标注集大小不一，finetune 超参敏感
- 每加一个任务就多一份模型 weights
- 模型大了之后 finetune 阶段成本占比上升

OpenAI 的新假设：**如果 LM 大到一定程度，它在预训练阶段已经"看过"足够多的任务格式 —— 用 prompt 触发就行，根本不用 finetune**。这是从 GPT-1 的 input transformations 顺延的下一步。

## 核心贡献
1. **架构 scale-up** —— 同样 decoder-only Transformer，把 117M 放大到 1.5B（4 个 size：124M / 355M / 774M / 1.5B），证明 LM benchmark loss 在 4 个 size 上单调下降，scaling 行为可预测
2. **WebText 数据集** —— [[webtext]] · 不再用 BookCorpus，改爬 Reddit 至少 3 karma 的外链页面（"人筛过的网页"），~40GB 高质量数据
3. **Zero-shot transfer** —— [[zero-shot-transfer]] · 用提示文本 prompt 触发任务，不改 weights。摘要用 `"TL;DR:"`，翻译用 `"french:"`，QA 用上下文 + 问题
4. **Thesis 升级** —— [[language-modeling-as-multitask]] · 论文标题 "Language Models are Unsupervised Multitask Learners" 直接抛出：LM 训练本身已经在做无数任务（每次预测下一词都是一次小任务），多任务能力是自然涌现的
5. **Staged release** —— 不一次性放 1.5B 权重，先放 124M、再 355M、再 774M、最后 1.5B。开 AI 模型"分阶段释放"先例

## 关键概念
- [[zero-shot-transfer]] · 不 finetune 用 prompt 触发任务，从 input transformations 演化而来
- [[webtext]] · 用 Reddit karma 筛过的网页数据，~40GB
- [[language-modeling-as-multitask]] · LM 训练本身就是多任务学习的视角
- [[causal-language-model]] · 仍是 CLM 预训练，没变
- [[decoder-only-paradigm]] · 仍是 decoder-only，没变

## 我的批注
- **GPT-2 最重要的不是 1.5B 这个数字，是它<strong>把 thesis 表达清楚了</strong>** —— 标题"Language Models are Unsupervised Multitask Learners"一句话把整个 OpenAI 路线钉死。每个后续模型（GPT-3 / GPT-4 / Claude）都在续这本账
- **WebText 是被低估的 contribution**。用 Reddit karma 当数据筛选信号是个聪明 trick —— 让用户当 reviewer，不用付钱标数据。后来所有大数据集（C4 / Pile / RedPajama）多少都借鉴了"用社区信号过滤"的思路
- **"Too dangerous to release"是个 PR 事件**，但开了 AI 安全讨论的头。staged release 现在是 frontier model 的标准做法（Claude / GPT-4 / Llama 都分版本释放）。当年被骂作秀，回头看是必要操作
- **Zero-shot 不是完美的**：论文里很多任务 zero-shot 离 SOTA 还差一大截（如翻译 BLEU 只有 5-10 分，远不如专门 finetune 的模型）。但<strong>趋势在那里</strong>：scale 上去后差距会缩小。这是 GPT-3 175B 真正赢的伏笔
- **跟 BERT 路线的胜负在这里转向**。GPT-1 时候 BERT 在 benchmark 上赢；GPT-2 给出了 prompt 这条路。BERT 的 finetune 模式没法用 prompt 触发 —— scale 越大这个差距越显
- 1.5B 现在听起来小，但 2019 当年是真正的大模型。同期 BERT-large 才 340M。GPT-2 单卡训不动，要 v3 TPU pod。这开启了"模型大到普通研究者训不动"的时代

## 跟 wiki 里其他 paper 的关系
- [[gpt-1]] · 直接前作，同样 decoder-only + CLM，主要变化是 scale + 数据
- [[bert]] · 同 pretrain+finetune 范式的对照路线，GPT-2 这一步开始拉开差距
- [[attention-is-all-you-need]] · 底层架构没变，仍是 Transformer decoder + causal mask
- [[input-transformations]] · GPT-1 的"用输入格式编码任务"是 zero-shot transfer 的直接前身
- 接 GPT-3：scale 推到 175B + in-context learning（在 prompt 里给几个例子）

## 历史定位
- 2018-06 GPT-1 · 117M · 验证 pretrain+finetune 思路 · 仍需 finetune
- 2018-10 BERT · 340M · encoder-only · benchmark 当年明星
- 2019-02 **GPT-2** · 1.5B · zero-shot · prompting 第一次明确 demo
- 2020-01 Scaling Laws · Kaplan et al. · OpenAI 自己后续把 GPT-2 的 scaling 行为形式化
- 2020-06 GPT-3 · 175B · in-context learning · 把 GPT-2 的 thesis 推到爆发
- 2022-11 ChatGPT · GPT-3.5 + RLHF · prompting 范式产品化
