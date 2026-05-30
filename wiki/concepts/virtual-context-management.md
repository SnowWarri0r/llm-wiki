---
name: virtual-context-management
type: concept
sources: [memgpt]
updated: 2026-05-28
---

# Virtual Context Management · 虚拟上下文管理

## 一句话
把 LLM 的 context window 当 RAM、外部存储当硬盘 —— LLM 自己通过 function call 决定哪些信息留在 context 里、哪些挪出去。**OS 的虚拟内存思路套在 agent 身上**。

## 直觉 · OS 怎么管内存的

操作系统面对一个问题：程序需要的数据可能远超 RAM 容量。怎么办？

**虚拟内存机制**：

1. 把数据分成"页" (page)
2. 当前用到的页留在 RAM 里
3. 暂时不用的页换到硬盘 (page out)
4. 程序要访问硬盘上的页时，触发"缺页中断"(page fault)，OS 把那一页换回 RAM (page in)
5. 程序感觉自己有无限内存 —— 实际上 RAM 在后台不停换页

**LLM 面对的是一模一样的问题** —— context window 装不下所有对话历史 / 所有文档 / 所有记忆。MemGPT 把 OS 这套搬过来：

| OS 概念 | MemGPT 对应 |
|---|---|
| RAM | LLM 的 context window |
| 硬盘 | 外部数据库 / 向量库 |
| Page in | LLM 调 `search_memory()` 把外部信息拉回 context |
| Page out | LLM 调 `archive_message()` 把老消息归档到外部 |
| 缺页中断 | "context 快满了" → 触发系统消息 → LLM 决定怎么处理 |
| CPU | LLM 推理本身 |
| OS | LLM **加上**它的 function-calling 能力 |

## 三层记忆架构

MemGPT 把记忆分三层，每层定位完全不同：

### Core Memory · 核心区
**永远在 context 里**。存最关键的"agent 状态" —— 人设、对当前用户的描述、长期目标。容量很小（几百 token），但**LLM 每次推理都能看到**。

类比：CPU 寄存器。最快、最贵、最少。

可以被 LLM 自己更新（通过 `core_memory_replace()` 之类的函数）。

### Recall Memory · 对话记忆
**完整的对话历史**，包括所有被换出 context 的消息。容量很大，但 LLM 看不到 —— 想看得主动检索。

类比：本地 SSD。容量大，访问需要明确请求。

LLM 用 `conversation_search(query)` 来翻找。

### Archival Memory · 归档记忆
**任意外部信息** —— 文档、知识库、用户上传的资料、agent 自己沉淀下来的"重要 insight"。

类比：外接硬盘 / 云存储。容量无限，访问最慢。

LLM 用 `archival_memory_search(query)` 来查；也可以主动 `archival_memory_insert(content)` 把当前对话里值得长期保留的东西存进去。

## 关键：page fault 的处理

当 context 用得差不多满时，MemGPT 不是简单截断，而是**给 LLM 发一个系统消息**：

```
[system] Warning: Your context is 90% full. 
You should review your recent messages and decide which 
to archive to recall_memory.
```

LLM 看到这个消息后，主动决定：

```python
archive_messages(message_ids=[m1, m2, m3])
```

这就是 **page out**。被归档的消息从 context 里消失，进入 recall memory 数据库。**Context 里腾出空间继续对话**。

如果后面对话中提到了那段被归档的内容（比如用户问 "你还记得上周我跟你说的那个事吗"），LLM 主动调 `conversation_search("上周用户提到的事")` —— 这就是 **page in**。

## 跟 Generative Agents 的关键区别

| 维度 | [[generative-agents]] | MemGPT |
|---|---|---|
| 调度者 | **外部编排代码** ("现在该检索了 / 现在该反思了") | **LLM 自己** (通过 function calling) |
| 记忆触发 | 每步都自动跑检索 + 评分 | LLM 自己决定何时检索 |
| 反思 | 定时按重要性累积触发 | core memory 由 LLM 主动更新 |
| 对 LLM 要求 | 中等 (GPT-3.5 就够) | 高 (GPT-4 才稳, 3.5 经常乱调度) |
| 优雅度 | 一个清晰的流水线 | 一个 OS-like 系统 |
| 工程难度 | 中 | 高 (function-calling 健壮性 + 系统消息时机) |

简单说：**Generative Agents 是给 LLM 配了个"秘书"在外面管事，MemGPT 是让 LLM 自己长出"管事的能力"**。后者更高阶但对 LLM 自身能力要求也更高。

## 工程落地的取舍

实际系统里**两套常被混用**：

- **对话历史** 用 MemGPT 思路 —— LLM 自己判断什么时候 archive 老消息
- **反思 / 总结** 用 Generative Agents 思路 —— 用外部 cron job 定期做摘要，不交给 LLM 自己决定（因为 LLM 自己很难准确判断"现在攒到足够多记忆该总结一下了"）
- **检索** 两边一样 —— 都是 RAG 的变体，区别只是触发方是 LLM 还是外部代码

## 链接
- [[memgpt]] · 论文
- [[memory-stream]] · Generative Agents 的对应记忆机制
- [[retrieval-scoring]] · 都用到的检索基础
- [[in-context-learning]] · function calling 的基础能力
