---
name: react-loop
type: concept
sources: [generative-agents]
updated: 2026-06-15
---

# ReAct · Reason + Act · 想一步动一步

## 一句话
让 LLM **交替地"想一句(Reason) → 动一下(Act) → 看结果(Observe)"**，而不是憋一大段答案——下一步做什么取决于上一步看到了什么，这就是 agent 会用工具、能多轮调研的最小循环。

## 直觉 · 闭卷答 vs 开卷边查边写

普通 LLM 回答像**闭卷考试**：脑子里有什么就写什么，写错也没法回头核对。

ReAct 像**开卷 + 能动手**：想到"这我不确定"就停下来去**查一下/算一下/调个 API**，把查到的结果(Observation)接着喂回去，再想下一步。一个问题被拆成一串小步，每步都能看到真实世界的反馈再决定怎么走。

```
Thought: 要算训练成本，得先知道参数量
Act:     search("模型A 参数量")
Obs:     7B
Thought: 还需要 GPU 小时数
Act:     search("模型A GPU hours")
Obs:     130 万 H100·时
Thought: 信息够了，可以估算成本了
Answer:  ...
```

**Thought / Act / Observation** 三件一轮，循环到模型觉得"够了"就收尾。

## 为什么有用
- **接上真实世界**：Act 可以是搜索、抓网页、跑代码、调函数——LLM 从"凭记忆"变成"凭证据"。
- **自带纠错**：Observation 是真实反馈，搜错了下一轮能换关键词，不像闭卷一条道走到黑。
- **可解释**：Thought 链留下了"它为什么这么做"的痕迹，方便排查跑偏。

## 它的坑 vs Planner-Executor
ReAct 是**边走边想**，灵活但**容易绕远、没全局观**——可能在一个子问题上反复横跳。

对照的另一套是 **Planner-Executor（先规划后执行）**：先让模型一次性列完整计划(子任务 1/2/3…)，再逐条执行。有全局观、子任务能并行，但计划定死后**不好临场调整**。

实践里常**混用**：planner 出大纲 → 每个子任务内部跑 ReAct 小循环。[[deep-research]] 系统的 ②③ 轴(工具使用 + 规划控制)基本就建在这两套范式上。

## 代码出处 / 来源
- ReAct 原始论文 arXiv 2210.03629（Yao et al. 2022）
- LangChain / 各类 agent 框架的默认循环大多是 ReAct 变体

## 链接
- [[deep-research]] · 把 ReAct 循环跑几十轮做调研报告
- [[memory-stream]] · 多轮 Observation 攒下来怎么存
- [[memgpt]] · LLM 自己 function call 调度记忆，ReAct 的"动手"升级版
- [[agent-reflection]] · 跑久了把碎片 Observation 提炼成高层认知
