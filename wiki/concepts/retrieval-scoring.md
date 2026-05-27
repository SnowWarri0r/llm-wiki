---
name: retrieval-scoring
type: concept
sources: [generative-agents]
updated: 2026-05-27
---

# Retrieval Scoring · 记忆检索排序

## 一句话
从 [[memory-stream]] 里捞记忆时，按 **时近度 × 重要性 × 相关性** 三个维度加权排序 —— 不是最新的就最好，也不是最重要的就最好，是三者的乘积最高的。

## 直觉
你现在要决定"今天下班后干嘛"。你大脑里会冒出哪些记忆？

- **时近度**高的："刚才同事说今晚有个聚会"（1 小时前发生的）
- **重要性**高的："上周体检报告说我该开始运动了"（重要但不是今天发生的）
- **相关性**高的："我三天前查了一家新开的健身房"（跟"下班后干嘛"直接相关）

你大脑自动把这三个维度综合排序了 —— 不会只因为"刚发生"就排第一，也不会只因为"很重要"就排第一。

## 怎么做的

```python
score = alpha * recency(memory) 
      + beta  * importance(memory) 
      + gamma * relevance(memory, query)

# recency:    指数衰减, 越近的分越高 (e^(-decay * hours_ago))
# importance: 存入时 LLM 打的 1-10 分, 归一化到 [0,1]
# relevance:  memory embedding 跟 query embedding 的余弦相似度
```

三个系数 α / β / γ 控制偏重 —— 论文里大致均衡，但可以按场景调。

**检索出 top-K 条记忆后，拼成文本塞进 LLM 的 prompt**：

```
[Relevant memories]
- (2 hours ago) 同事说今晚有聚会
- (3 days ago) 查了一家新健身房，离公司 10 分钟
- (1 week ago) 体检报告建议每周运动 3 次

Based on these memories, what would you do after work?
```

LLM 基于这些"回忆"做决策 —— 效果就像一个有记忆的人在思考。

## 为什么三个维度都要

| 只用一个维度 | 会出什么问题 |
|---|---|
| 只用时近度 | agent 只记得最近几分钟的事，完全没有长期记忆 |
| 只用重要性 | agent 永远被最重大的事件主导（"被裁员"这条记忆会压倒一切），没法正常生活 |
| 只用相关性 | agent 会捞出很久以前的相关记忆但忽略刚发生的事，反应迟钝 |

三个维度乘在一起 = **"最近发生的 + 确实重要 + 跟当前情况相关"的记忆排最前面**。

## 跟 RAG 的关系

RAG（检索增强生成）的核心也是"检索 → 塞进 prompt"，但标准 RAG 只用**相关性**排序（向量相似度）。Generative Agents 加了**时近度 + 重要性**两个维度 —— 这是 agent 场景跟知识问答场景的核心区别：agent 需要"像人一样回忆"，不只是"找最相关的文档"。

## 链接
- [[memory-stream]] · 被检索的数据源
- [[agent-reflection]] · 反思结果也参与检索
- [[generative-agents]] · 论文
