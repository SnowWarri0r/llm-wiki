---
name: deep-research
type: concept
sources: [generative-agents, memgpt]
updated: 2026-06-15
---

# Deep Research · 深度研究系统 · 派一个会上网的研究员

## 一句话
你给一个问题，它**自己拆子问题、规划路线、多轮上网搜读、交叉核对、最后综合成一篇带引用的报告**——本质是一个**会用搜索工具的 [[memory-stream]] agent 循环**，跑几分钟、几十次工具调用，而不是普通 RAG 那种一问一答。

## 直觉 · 从"查字典"到"派实习生"

普通 **RAG 聊天**：你问一句 → 检索 top-k 几段 → 塞进 prompt → 答一段。**一来一回，一次检索**，答得快但浅，遇到需要"先查 A 才知道该查 B"的问题就抓瞎。

**Deep Research**：你给一个开放问题（"对比 2024 年三大开源推理模型的训练成本"）→ 它先**拆成子问题**、**定调研计划**，然后开始一轮轮地搜、读、判断"这页有用吗 / 下一步该搜啥"，碰到矛盾信息会**交叉核对**，最后把几十个来源**综合成一篇长报告并逐条标注出处**。

一句类比：
- **RAG** = 让你**查一下字典**——翻一页，念给你听。
- **Deep Research** = 派一个**实习研究员**，给他一天时间和一台联网电脑，回来交一份调研报告。

这篇综述（Xu & Peng 2025，arXiv 2506.12594）盘点了 2023 年以来 **80+ 个** 这类系统（OpenAI / Gemini / Perplexity 的 Deep Research，及一堆开源实现），它不发明新模型，而是提了个**统一的分类框架**——任何一个深度研究系统都能用 4 根轴拆开来对比。

## 四根技术轴 · 拆解任何一个深度研究系统

<figure style="margin:26px 0; padding:22px; background:#f3f0ea; border:1px solid #c9bfae; border-radius:4px;">
<svg viewBox="0 0 720 360" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="dr-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#8a5a2b"/></marker>
    <marker id="dr-loop" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#b8841c"/></marker>
  </defs>

  <!-- 上半：普通 RAG 单轮 -->
  <text class="reveal" x="40" y="34" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#7a6f5d">普通 RAG · 一问一答一次检索</text>
  <g class="reveal" font-size="9.5" text-anchor="middle" fill="#3a3128">
    <rect x="48" y="48" width="78" height="34" rx="4" fill="#faf4e1" stroke="#7a6f5d"/><text x="87" y="69">问题</text>
    <rect x="178" y="48" width="92" height="34" rx="4" fill="#faf4e1" stroke="#7a6f5d"/><text x="224" y="69">检索 top-k</text>
    <rect x="322" y="48" width="78" height="34" rx="4" fill="#faf4e1" stroke="#7a6f5d"/><text x="361" y="69">塞 prompt</text>
    <rect x="452" y="48" width="78" height="34" rx="4" fill="#e8efe4" stroke="#4a6b3a"/><text x="491" y="69">答一段</text>
  </g>
  <g class="reveal" stroke="#7a6f5d" stroke-width="1.4" marker-end="url(#dr-h)">
    <line x1="126" y1="65" x2="174" y2="65"/><line x1="270" y1="65" x2="318" y2="65"/><line x1="400" y1="65" x2="448" y2="65"/>
  </g>
  <text class="reveal" x="560" y="69" font-size="9" fill="#9b2c2c">浅 · 不会"先查A才知查B"</text>

  <line x1="40" y1="100" x2="680" y2="100" class="reveal" stroke="#c9bfae" stroke-width="1" stroke-dasharray="4 4"/>

  <!-- 下半：Deep Research 多轮 agent 循环 -->
  <text class="reveal" x="40" y="126" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#8a5a2b">Deep Research · 多轮 agent 循环</text>

  <!-- 拆解 / 规划 -->
  <g class="reveal d1" font-size="9.5" text-anchor="middle" fill="#3a3128">
    <rect x="40" y="142" width="84" height="34" rx="4" fill="#faf4e1" stroke="#7a6f5d"/><text x="82" y="159">开放问题</text>
    <rect x="150" y="142" width="96" height="34" rx="4" fill="#fbeed6" stroke="#b8841c"/><text x="198" y="159">拆子问题</text><text x="198" y="170" font-size="7.5" fill="#7a6f5d">③ 规划</text>
  </g>
  <g class="reveal d1" stroke="#8a5a2b" stroke-width="1.4" marker-end="url(#dr-h)"><line x1="124" y1="159" x2="146" y2="159"/></g>

  <!-- 中央循环框 -->
  <rect class="draw d2" x="278" y="132" width="220" height="120" rx="8" fill="none" stroke="#b8841c" stroke-width="1.6" stroke-dasharray="5 4" pathLength="1000"/>
  <text class="reveal d2" x="388" y="148" text-anchor="middle" font-size="8.5" font-style="italic" font-family="Fraunces,serif" fill="#b8841c">调研循环（跑 N 轮）</text>
  <g class="reveal d3" font-size="9.5" text-anchor="middle" fill="#3a3128">
    <rect x="298" y="160" width="68" height="30" rx="4" fill="#e3edf5" stroke="#3d5a6c"/><text x="332" y="179">② 搜索</text>
    <rect x="410" y="160" width="68" height="30" rx="4" fill="#e3edf5" stroke="#3d5a6c"/><text x="444" y="179">读网页</text>
    <rect x="354" y="210" width="84" height="30" rx="4" fill="#f1e3ef" stroke="#9a2f5e"/><text x="396" y="229">判断下一步</text>
  </g>
  <g class="reveal d4" stroke="#b8841c" stroke-width="1.4" marker-end="url(#dr-loop)">
    <line x1="366" y1="175" x2="406" y2="175"/>
    <path d="M444 190 Q444 212 438 222" fill="none"/>
    <path d="M354 222 Q320 212 332 192" fill="none"/>
  </g>
  <text class="reveal d4" x="388" y="252" text-anchor="middle" font-size="7.5" fill="#9a2f5e">够了吗？不够→再搜</text>

  <!-- 综合输出 -->
  <g class="reveal d5" font-size="9.5" text-anchor="middle" fill="#3a3128">
    <rect x="524" y="160" width="84" height="34" rx="4" fill="#fbe9e3" stroke="#bf5a1e"/><text x="566" y="177">④ 综合</text><text x="566" y="188" font-size="7.5" fill="#7a6f5d">去重·核对矛盾</text>
    <rect x="524" y="210" width="84" height="34" rx="4" fill="#e8efe4" stroke="#4a6b3a"/><text x="566" y="227">报告</text><text x="566" y="238" font-size="7.5" fill="#7a6f5d">逐条带引用</text>
  </g>
  <g class="reveal d5" stroke="#8a5a2b" stroke-width="1.4" marker-end="url(#dr-h)"><line x1="498" y1="180" x2="520" y2="180"/><line x1="566" y1="194" x2="566" y2="208"/></g>

  <!-- ① 模型底座 -->
  <text class="reveal d3" x="388" y="288" text-anchor="middle" font-size="9" fill="#7a6f5d">① 基础模型 + 推理引擎 —— 整个循环的"脑子"，是否带长思维链(reasoning)决定它会不会规划</text>

  <text class="reveal d5" x="40" y="324" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#3a3128">四根轴：① 脑子是谁 · ② 手伸多远 · ③ 会不会规划 · ④ 产出可不可信</text>
  <text class="reveal d5" x="40" y="344" font-size="9" fill="#7a6f5d">看任何"深度研究"产品，套这四轴就能秒拆它强在哪、弱在哪</text>
</svg>
</figure>

综述的骨架是这张**分类表**——理解它，你看任何一个深度研究系统都能秒拆：

| 轴 | 管什么 | 关键设计选择 |
|---|---|---|
| ① **基础模型 + 推理引擎** | 谁在思考 | 用哪个 LLM；是否带 **reasoning**（o1 那种长思维链，直接决定它会不会规划）；有没有专门为 agent 调过 |
| ② **工具使用 + 环境交互** | 怎么够到外部世界 | 搜索引擎 / 网页抓取 / 代码执行 / 调 API；用 **[[react-loop]]**(想一步→动一步) 还是直接函数调用 |
| ③ **任务规划 + 执行控制** | 怎么不跑偏、何时停 | 先规划后执行(planner-executor) / 边走边想 / 多 agent 分工；**停止准则**(信息够了没) |
| ④ **知识综合 + 输出生成** | 怎么攒成报告 | 多源**去重**、**矛盾消解**、**引用对齐**(每句话能追到出处)、长文组织 |

## ② ③ 轴的核心：两种 agent 循环范式

深度研究系统怎么"边查边想"，主要是两套套路：

**ReAct（Reason + Act，边走边想）**：交替**想一句 → 动一下 → 看结果 → 再想**。
```
Thought: 我得先知道模型A的参数量    Act: search("模型A 参数量")
Obs: 7B                            Thought: 那训练成本得查它的GPU时
Act: search("模型A GPU hours") ...
```
好处是**灵活**——下一步搜啥取决于上一步看到啥；坏处是**容易绕远**、没全局观。

**Planner-Executor（先规划后执行）**：先让模型**一次性列出完整调研计划**（子任务 1/2/3…），再逐条执行、最后汇总。
好处是**有全局观、可并行**（子任务互不依赖时可同时搜）；坏处是计划定死后**不好临场调整**。

实际系统常**混用**：先 planner 出大纲，每个子任务内部跑 ReAct 小循环；难的还会上**多 agent**——一个主管 agent 拆活、派给多个子 agent 各查一块、再收回综合（[[memgpt]]/[[generative-agents]] 那条"LLM 当 OS / 自主体"的思路在这里复用）。

## ④ 轴最难：可信度

报告写得漂亮没用，关键是**每句话能不能追到来源、来源之间矛盾了怎么办**。综述把 ④ 轴的难点单列：
- **去重**：80 个网页里一半是互相抄的，得识别"同一事实的不同复述"。
- **矛盾消解**：来源 A 说成本 50 万、来源 B 说 200 万——是口径不同还是有错？得标注而非硬选一个。
- **引用对齐**：生成的每个论断挂到具体出处，这是 Deep Research 区别于"一本正经胡说"的命根子，也接 [[retrieval-scoring]] 那套"哪条证据更该信"的排序。

## 综述还点了什么
- **覆盖面**：商用(OpenAI/Gemini/Perplexity) + 开源，跨学术/科研/商业/教育多个场景。
- **公认挑战**：准确性(幻觉+错误引用)、隐私、知识产权(大量抓别人内容)、可及性(贵、慢)。
- **本质判断**：Deep Research 是 **agent 能力 + 信息检索 + 长文综合**的交叉点，是"LLM 从答题者变成调研员"的产品化落点。

## 代码出处 / 来源
- 综述 arXiv 2506.12594《A Comprehensive Survey of Deep Research》(Xu & Peng 2025)，4 维分类法 + 80+ 系统盘点
- 代表系统：OpenAI Deep Research、Gemini Deep Research、Perplexity；ReAct 原始 arXiv 2210.03629

## 链接
- [[react-loop]] · ②③轴核心循环：想一步→动一步→看结果
- [[memgpt]] · "LLM 当 OS、自己调度记忆"——多 agent / 长任务的地基
- [[generative-agents]] · LLM 自主体(记忆流+反思+规划)，深度研究的 agent 侧近亲
- [[memory-stream]] · 多轮调研攒下的观察怎么存
- [[retrieval-scoring]] · ④轴可信度：哪条证据更该信
- [[virtual-context-management]] · 几十轮搜读塞不下 context 时怎么调度
