---
name: next-sentence-prediction
type: concept
sources: [bert]
updated: 2026-05-21
---

# Next Sentence Prediction · NSP

## 一句话
给 BERT 两段文本 A 和 B，让 [CLS] 这个位置的表征做二分类：B 是不是 A 在原文里的下一段？

## 直觉
BERT 想给问答、推理这类**段间关系**任务一个好的 pretrain 信号。MLM 主要是 token 级，NSP 想加段级。

输入构造：
```
[CLS] A1 A2 ... An [SEP] B1 B2 ... Bm [SEP]
                                      ↑ 同 segment embedding 标 0 / 1
```

正样本：B 真的是 A 在语料里的下一段（50%）  
负样本：B 是语料随机抽的另一段（50%）

[CLS] 位置 forward 后的 hidden state → 二分类头 → cross-entropy loss。

## 怎么做的
```python
# 训练时构造样本
if random() < 0.5:
    A, B = read_consecutive_paragraphs()   # 正样本
    label = 1
else:
    A = read_paragraph()
    B = read_random_paragraph()            # 负样本
    label = 0

tokens = ["[CLS]"] + A + ["[SEP]"] + B + ["[SEP]"]
segment_ids = [0]*(len(A)+2) + [1]*(len(B)+1)
hidden = bert(tokens, segment_ids)
cls_logits = classifier(hidden[0])         # [CLS] 位置
nsp_loss = cross_entropy(cls_logits, label)
```

总 loss = MLM loss + NSP loss，两个任务联合训练。

## 它的问题（RoBERTa 2019 证伪）
- **任务太简单**：随机抽的负样本通常话题完全不同，模型靠"主题词共现"就能 99% 判对，根本没学到段落逻辑关系
- **占的训练算力**值不回：与其训 NSP，不如把这部分算力用来 MLM 更长的序列

RoBERTa 实验：去掉 NSP，把输入改成更长的纯 doc 拼接，BERT 各项指标反而更好。

## 后续替代
- **SOP (Sentence Order Prediction)**：ALBERT 提出。正样本是 A→B，负样本是把 A 和 B 顺序<strong>对换</strong>（同一对，反着拼）。话题相同，必须真懂逻辑才能判 —— 比 NSP 难、信号更纯
- **完全去掉**：RoBERTa / DeBERTa 走这条路

## 我的判断
NSP 是 BERT 论文里**唯一被后续证明是错的设计**。但有意思的是，论文作者当年还是凭直觉 + 消融选了它 —— 这提醒我们：**在新范式刚出来时，作者也不知道什么真正重要**。

## 链接
- [[bert]] · 提出
- [[masked-language-model]] · 配套
- [[encoder-only-paradigm]] · 载体
