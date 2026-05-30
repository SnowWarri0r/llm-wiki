---
name: memgpt
type: paper
source: https://arxiv.org/abs/2310.08560
upstream: https://arxiv.org/abs/2310.08560
ingested: 2026-05-28
authors: [Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, Joseph E. Gonzalez]
year: 2023
---

# MemGPT · Towards LLMs as Operating Systems

## 一句话
把 LLM 的 context window 当成 RAM，外部存储当硬盘 —— 让 LLM **通过 function call 自己管自己的记忆**：哪些塞进 context、哪些挪到外部、什么时候要回看老对话。**操作系统级别的记忆管理思路套在 agent 身上**。

## 它要解决的痛点

[[generative-agents]] 那套（记忆流 + 反思 + 检索）很优雅，但有个落地问题 —— **整个记忆调度系统是"外部编排"的**。也就是说，外面有一段代码在告诉 LLM "现在该检索了 / 现在该反思了"。LLM 自己不知道什么时候 context 快满了、什么时候该把哪段记忆调回来。

MemGPT 反过来 —— **LLM 自己管自己的记忆**。

借用 OS 的思路：传统计算机的 RAM 装不下所有数据，但操作系统通过虚拟内存机制让程序"以为"自己有无限内存 —— 实际上 OS 在后台做 page in / page out。MemGPT 把这套搬到 LLM 上：

- **LLM 的 context window = RAM**（有限，快）
- **外部存储 = 硬盘**（无限，慢）
- **LLM 自己 = CPU + OS**（既执行任务，又调度记忆）

## 核心贡献

1. **OS 抽象**：第一次把 LLM 当操作系统来设计 —— 多层记忆 + page 机制 + 中断响应
2. **LLM 自主调度记忆**：通过 function calling，LLM 可以主动调用 `append_to_memory()` / `search_archival_memory()` / `edit_core_memory()` 等函数，自己决定记什么、忘什么、查什么
3. **两层记忆 + 一个"持久状态"**：
   - **Core memory**（核心区）：永远在 context 里，存 agent 人设和当前用户描述
   - **Recall memory**（对话记忆）：完整对话历史，按需检索
   - **Archival memory**（归档记忆）：任意外部信息（文档 / 知识库），LLM 主动查
4. **Context 满了的自动处理**：当 context 接近上限时，LLM 自己触发"系统中断"，把 old messages 写入 recall memory，腾出空间继续

## 关键概念 → 概念页链接

- [[virtual-context-management]] · 把 context window 当虚拟内存管的核心思路
- [[memory-stream]] · Generative Agents 的对应物（被动检索 vs MemGPT 主动调度）
- [[agent-reflection]] · 跟 MemGPT 的 core memory 更新有重叠
- [[retrieval-scoring]] · MemGPT 的 archival memory 也是检索, 但触发是 LLM 主动决定
- [[in-context-learning]] · MemGPT 完全建立在 LLM 的 function calling 能力之上

## 我的批注 / 疑问

- MemGPT 跟 [[generative-agents]] 最大的区别是**谁在调度** —— Generative Agents 是外面有"大脑"在编排（什么时候反思、什么时候检索），MemGPT 是 LLM 自己当大脑
- 工程上的 trade-off：自主调度更优雅但**对 LLM 的能力要求很高** —— GPT-3.5 用 MemGPT 经常做出蠢决策（不该 archive 的 archive 了 / 检索关键词错了）；GPT-4 才稳定。GPT-3.5 时代 Generative Agents 那套外部编排反而更可靠
- MemGPT 现在已经演化成了 **Letta** 框架（letta.com）—— 同一个团队，把论文里的概念产品化了
- 真实工程落地里**两套常被混用** —— 用 MemGPT 的 LLM-自主调度处理对话历史；用 Generative Agents 的外部编排处理"反思"（因为反思的触发条件不该完全交给 LLM 自己判断）
- 疑问：core memory 的内容怎么避免被 LLM "随手改坏"？论文说有人工 review 机制但实际工程里这一步往往被跳过 —— 后果是 agent 人设可能在几轮对话里悄悄漂移
