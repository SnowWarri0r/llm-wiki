---
name: pretrain-finetune-paradigm
type: concept
sources: [bert, gpt-1]
updated: 2026-05-21
---

# Pretrain-Finetune Paradigm · 先预训练再微调

## 一句话
先在<strong>无标注</strong>大语料上用自监督任务（MLM / LM）预训练一个 transformer，再在每个下游任务的<strong>小标注集</strong>上 finetune —— 一个 backbone 万能。

## 直觉
2018 之前 NLP 几乎每个任务都是从头训：取 word2vec 或 GloVe embedding，搭一个 LSTM/CNN 上去，标注几千到几万条数据训一个专门模型。每个任务一个模型，互不复用，标注成本高。

Pretrain-finetune 的核心洞察：**语言知识的 99% 来自语法/常识/事实，跟具体下游任务无关**。这部分可以从无标注的 wiki/书/网页里学（自监督），只要 1% 的标注数据就够"指明"特定任务的输出格式。

类比：先让人学语言（pretrain），再训练他做客服 / 法律 / 翻译岗位（finetune）。每个岗位不用从婴儿学起。

## 怎么做的
**Pretrain 阶段**（数百 GB 文本 + 几千卡天 + 一次）：
```python
for batch in unlabeled_corpus:
    # BERT: 随机 mask，预测被遮住的 token
    masked_input, target = mask_15_percent(batch)
    loss = bert(masked_input).predict(target)
    
    # GPT: 因果预测下一个 token
    # loss = gpt(batch[:-1]).predict(batch[1:])
    
    loss.backward()
```

**Finetune 阶段**（几千条标注 + 几个 GPU 时 + 每个任务一次）：
```python
model = load_pretrained_bert()
model.add_head(classifier_for_this_task)   # 一个小线性层
for batch in labeled_data:
    pred = model(batch.text)
    loss = task_loss(pred, batch.label)
    loss.backward()                         # 同时更新 BERT 和 head
```

各任务通常加什么 head：
- 分类（情感、NLI）：[CLS] 的 hidden → 线性层
- 序列标注（NER、POS）：每个 token 的 hidden → 线性层
- 问答（SQuAD）：两个线性层预测 answer 的 start/end 位置

## 为什么这条路赢了
1. **算力规模化**：一次昂贵 pretrain，无数次便宜 finetune
2. **标注数据稀缺友好**：很多任务只有几千条标注，从头训会过拟合
3. **跨任务迁移**：pretrain 学到的语法/常识对所有 NLP 任务都有用
4. **工程简化**：所有任务用同一个 backbone，infra 复用

## 后续演化
- **GPT-2 (2019)**：发现 pretrain 模型大到一定程度，**不 finetune 也能 zero-shot 做下游任务**（prompt-based）
- **GPT-3 (2020)**：in-context learning · 不改 weight，只在 prompt 里给几个例子就行
- **InstructGPT / ChatGPT (2022)**：finetune 阶段换成 RLHF，不再针对单一任务，而是针对"听人指令"
- **Pretrain + RLHF** 现在是大多 LLM 的标配

**Finetune 在 LLM 时代退潮**：因为 prompt + ICL 已经够好；但在小模型（< 1B）和企业内部任务里仍是主力。

## 在 BERT 论文里的具体演示
BERT 论文 Fig 3 给了 4 种典型下游任务的 head 添加方式：
- (a) Sentence pair classification (MNLI, QQP) — [CLS] 的 hidden 接二/三分类
- (b) Single sentence classification (SST-2) — 同上
- (c) Question answering (SQuAD) — 每个 token 的 hidden 预测 start/end logit
- (d) Single sentence tagging (NER) — 每个 token 的 hidden 接序列标注分类头

## 链接
- [[bert]] · 立住这个范式的论文
- [[gpt-1]] · 同期且更早的 paper（也是 pretrain+finetune，只是用 causal LM）
- [[masked-language-model]] · BERT 的 pretrain 任务
- [[in-context-learning]] · 替代它的下一代范式
