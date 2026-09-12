---
name: cerebellum-brain-collaboration
type: concept
sources: [gander]
updated: 2026-09-11
---

# Cerebellum–Brain Collaboration · 小脑管接话，大脑管干活

## 一句话

把实时交互和长程推理拆给两个模型：小脑毫秒级听说看，大脑分钟级跑任务，工具调用当神经。

## 直觉

人接电话时"嗯、好、您说"是脊髓反射级的快，真正想问题是另一套慢系统——把这两件事塞进同一个模型，就得在"反应快"和"想得深"之间二选一。拆开以后各自量级合适：小脑是个小而快的全双工流式模型，永远在线；大脑是现成的通用 agent（Codex / Claude Code），**免训练即插即用**——上游 agent 变强，整个系统白嫖升级，不用重训小脑。

## 怎么做的

- 小脑自己能扛日常闲聊和简单检索；判断"这活儿要几分钟"时发结构化工具调用委派给大脑：`task_start`（开任务）、`task_send`（追加输入：main=转向主任务，fork=只读旁问不动主线程）、`task_resolve`（cancel / allow_once / allow_session / deny）。
- 中间的编排 runtime 是执行底座：管流式数据传输、推理调度，还把工具参数**绑定到传输层确认的真实用户轮次**——防止小脑幻觉出任务参数。两种控制面：lean（直通，低延迟）和 coordinator（多一个只出声明式控制计划的模型，管推理强度/权限/交付策略）。
- 大脑执行期间用户随时能跟小脑继续聊或改任务；大脑经 `share` 把关键进展推回小脑，小脑口语化转述。

## 代码出处

- Gander 开源 runtime：gateway 五实体（Project/Task/Run/WorkerEvent/Delivery）+ worker provider 接口；默认 provider 是 Codex app server，一条任务谱系挂一个持久 Codex 线程。

## 链接

- [[gander]] — 提出并开源这套双层架构
- [[streaming-chunk-flattening]] — 小脑内部的流式建模
- [[thinker-talker]] — 小脑再往下拆：想和说分两条路
