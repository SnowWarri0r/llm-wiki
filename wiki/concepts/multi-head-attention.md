---
name: multi-head-attention
type: concept
sources: [attention-is-all-you-need]
updated: 2026-05-20
---

# Multi-Head Attention · 多头注意力

## 一句话
把 attention 跑 **h 次**（论文 h=8），每次用不同的 Q/K/V 投影 → 每个 head 学不同的关系模式 → concat 后再线性。

## 直觉
单个 attention 头只能学**一种**关系模式。比如它可能学到"形容词 → 它修饰的名词"。但句子里同时有句法关系、语义关系、共指关系、词性关系 —— 单头表达力不够。

多头 = **并行多个 attention 看不同维度**。一个 head 关注句法，另一个关注语义，第三个关注共指 ... 加起来表达力翻 8 倍但计算量基本不变（每个 head 的 d_k 维度从 d 降到 d/h）。

类比：一个人看小说只能注意情节；多头是"一个看情节 + 一个看人物 + 一个看修辞 + 一个看时代背景"同时读。

## 怎么做的
```
for head h in [0, ..., 7]:
  Q_h = x · W_Q_h    # 各自的投影矩阵
  K_h = x · W_K_h
  V_h = x · W_V_h
  head_h = softmax(Q_h · K_h^T / √d_k) · V_h

output = concat(head_0, ..., head_7) · W_O
```

**dimension 安排**：
- 输入 d_model = 512
- 每个 head 的 d_k = d_v = 64
- 8 heads × 64 = 512 = d_model
- 总参数量 ≈ 单头 attention with d_model=512 的量

所以多头**不是免费的扩张能力**，是**同样参数预算下重新分配**。

## 各 head 真的学到了不同模式吗
论文附录可视化了不同 head 的 attention 模式。后来 BERT / GPT 论文也都做过：
- 有的 head 学 "主语 → 谓语"
- 有的学 "代词 → 指代对象"
- 有的学 "标点 → 它分隔的两个子句"

不是所有 head 都有清晰含义，有些是冗余的。Pruning 研究表明可以剪掉一半 head 而性能基本不掉。

## 链接
- [[self-attention]] · 单头基础
- [[attention-is-all-you-need]] · 论文
- [[transformer-architecture]] · 在哪用到
