---
name: generative-agents
type: paper
source: https://arxiv.org/abs/2304.03442
upstream: https://arxiv.org/abs/2304.03442
ingested: 2026-05-27
authors: [Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein]
year: 2023
---

# Generative Agents · Interactive Simulacra of Human Behavior

## 一句话
给 LLM 加上**记忆流 + 反思 + 规划**三件套，让 25 个 AI agent 在一个虚拟小镇里自主生活 —— 会交朋友、传八卦、组织派对、甚至谈恋爱。这套架构是现在几乎所有"有记忆的 AI agent"的祖宗。

## 它要解决的痛点

LLM 本身**没有记忆**。你跟 ChatGPT 聊完关掉窗口，它什么都不记得。就算在一次对话里，context window 也有上限 —— 塞不进更多信息，之前说的就丢了。

这意味着 LLM 没法做"持续存在的角色" —— 它不记得昨天跟你聊了什么、不记得上周发生的事、不会因为积累了足够多的观察而"顿悟"某件事。

Generative Agents 的核心问题：**怎么让 LLM 表现得像一个"活着的人"** —— 有长期记忆、会总结经验、能根据过去的经历做决策、行为随时间演化？

## 核心贡献

1. **Memory Stream（记忆流）**：所有观察（看到的、听到的、做的）按时间顺序存成一条流，每条记忆带时间戳 + 重要性评分
2. **Retrieval（检索）**：需要做决策时，从记忆流里捞出最相关的记忆。排序公式 = 时近度 × 重要性 × 相关性
3. **Reflection（反思）**：定期把大量低层记忆总结成高层认知（"我观察到 A/B/C → 我觉得 X"）。反思本身也存进记忆流，形成层级结构
4. **Planning（规划）**：每天早上生成当天计划，遇到新情况会修改计划。计划也存进记忆流
5. **Smallville 实验**：25 个 agent 在一个像素风小镇里生活，涌现出了论文作者都没预料到的社会行为 —— 自发组织情人节派对、信息在社交网络里扩散、关系随时间深化或疏远

## 关键概念 → 概念页链接

- [[memory-stream]] · 记忆的存储和组织方式
- [[agent-reflection]] · 从碎片观察里提炼高层认知
- [[retrieval-scoring]] · 时近度 × 重要性 × 相关性
- [[in-context-learning]] · LLM 通过 prompt 里的记忆片段"回忆"
- [[transformer-architecture]] · 底层还是 Transformer（GPT-3.5）

## 我的批注 / 疑问

- 这篇论文的核心洞察：**LLM 已经有了"思考"能力，缺的是"记得"和"回忆"的机制**。这套架构本质上就是在给 LLM 补一个外挂记忆系统
- 工程上这套方案每个 agent 每步都要调 LLM（评分重要性、检索排序、反思、规划、行动），token 消耗极大。25 个 agent 跑两天模拟消耗了几千美元的 API 费用
- 但概念框架极其清晰且可工程化：memory stream 就是数据库、retrieval 就是向量检索 + 加权排序、reflection 就是定时任务做摘要。每一块都能用现成工具替代 LLM 调用来降成本
- 2023 年之后几乎所有 AI companion / AI NPC / AI agent 框架（AutoGPT、BabyAGI、LangChain agent、Character.AI）都在不同程度上复用了这套 memory + reflection + planning 的骨架
- 疑问：reflection 的触发时机怎么选？论文说"重要性分数累积超过阈值"就触发 —— 但这个阈值怎么调？调大了 agent 反应迟钝，调小了 token 费用爆炸
