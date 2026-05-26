---
name: dual-model-architecture
type: concept
sources: [interaction-models-tml]
updated: 2026-05-20
---

# Dual-Model Architecture · 双模型架构

## 一句话
**前台 always-on 低延迟模型** + **后台异步深推理模型**，共享 context，前台委托后台干慢活。

## 直觉
人的大脑也是双系统（Kahneman System 1 / System 2）。"快直觉 + 慢深思" 这个分工在工程上一直有，TML 的新意是 **把这种分工做进单一系统的两个权重模块**，且**共享 context**。

类比常见的异步服务架构：
- 前台 BFF 跑 socket，持续推状态
- 后台 worker 被消息队列触发，长任务做完回调
- 前台/后台分在两个服务上

TML 是把这同一种形状收到**模型权重内**：前台 interaction model 跑 [[micro-turn]]，遇到要深推理的事情委托后台 background model，结果 streaming 回流织进对话。

## 怎么做的
- **Interaction Model**：276B MoE / 12B 激活（每个 token 只过 12B 计算路径）。always-on，跑在 200ms tick 上。
- **Background Model**：异步运行，做长 reasoning、tool calls、规划。
- **共享 context**：不是独立 API 调用 —— 两边读同一个对话状态，前台可以引用后台正在做的事。
- 前台知道**什么时候**该委托（自己学的判断），不靠外挂调度器。

## 为什么不全用一个大模型
- 一个 276B 模型跑 200ms tick → GPU 烧不起，延迟也守不住
- 一个 12B 小模型做长 reasoning → 能力不够
- 分两层 = 拿热路径的 latency 换冷路径的 capacity

## 跟 fish-speech Dual-AR 的对照
都叫"双模型"，但维度完全不同：
- [[dual-ar]] 是**生成路径上**的主从：慢/快沿 codec 层级分工
- 这里是**控制流上**的分工：前台/后台沿时间尺度分工

## 跟工程系统的对照
现代 web/AI 服务架构里也有同形状的事：前台 BFF + 后台 worker 的服务版。**重要差别**：服务版要写消息队列 topic、写并发槽位、写 callback 协议；权重版理论上让模型自己学这些 —— 但前提是数据集里有大量"前台 → 委托后台 → 回收结果"的标注样本。

## 链接
- [[interaction-models-tml]] · 论文
- [[micro-turn]] · 前台跑的是 micro-turn
- [[moe]] · 前台用 MoE 稀疏激活省算力
- [[dual-ar]] · 不同维度的"双模型"
