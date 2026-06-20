---
name: memory-stream
type: concept
sources: [generative-agents]
updated: 2026-05-27
---

# Memory Stream · 记忆流

## 一句话
Agent 看到的、听到的、做的所有事，按时间顺序存成一条流 —— 每条记忆带时间戳和重要性评分，需要的时候检索出来塞进 prompt。

## 直觉
人脑的记忆不是一个文件夹，是一条时间线 —— 你不会按"工作 / 生活 / 学习"分类存，你会按"什么时候发生的"来回忆。而且不是所有记忆都一样重要 —— "今天中午吃了拌面"和"今天被裁员了"存的权重完全不同。

Memory stream 就是给 LLM 搭一个类似的东西：

```
[2024-01-15 09:00] 到公司，跟同事打招呼        (重要性: 1)
[2024-01-15 09:15] 听到隔壁组在讨论裁员消息     (重要性: 7)
[2024-01-15 10:00] 开会，项目正常推进           (重要性: 3)
[2024-01-15 14:00] HR 找我谈话                 (重要性: 9)
[2024-01-15 14:30] 被告知部门整体优化           (重要性: 10)
```

重要性由 LLM 自己打分（"这件事对这个人有多重要，1-10 分"）。

## 怎么做的

1. Agent 每做一件事 / 观察到一件事，存一条记录：`{时间, 描述, 重要性评分}`
2. 重要性评分让 LLM 打（prompt: "On a scale of 1-10, how important is this to the agent?"）
3. 所有记录按时间顺序排成一条流，不删除、不分类
4. 需要做决策时，从流里**检索**最相关的几条，塞进 LLM 的 prompt 当"回忆"
5. **反思**产生的高层总结也存回流里，跟原始观察混在一起

## 跟数据库的类比
Memory stream 就是一张只追加的表：

```sql
CREATE TABLE memory_stream (
    id         SERIAL,
    created_at TIMESTAMP,
    description TEXT,
    importance  INT,        -- 1-10
    embedding   VECTOR(1536) -- 用来做语义检索
);
```

检索时不用 SQL 精确查询，用 [[retrieval-scoring]]（时近度 × 重要性 × 相关性）做加权排序。

## 链接
- [[retrieval-scoring]] · 从流里捞记忆的排序公式
- [[agent-reflection]] · 定期把碎片记忆总结成高层认知
- [[react-loop]] · 多轮 Observation 的来源
- [[deep-research]] · 多轮调研攒下的观察存进流里
- [[generative-agents]] · 论文
