---
name: micro-turn
type: concept
sources: [interaction-models-tml]
updated: 2026-05-20
---

# Micro-Turn · 200ms 微回合

## 一句话
把时间切成 200ms 一片，每片里**输入和输出同时发生**，模型看到的是一条单一交错 token 流。

## 直觉
传统 chat：你说一段完整的 → 模型生成一段完整的 → 你再说一段。时间被切成"两个回合"。

TML：把回合切到 200ms 这个尺度，每个 200ms chunk 里**输入 token 和输出 token 同时入流**：

```
input₀  output₀  input₁  output₁  input₂  output₂  ...
```

对模型：一条单一交错序列（标准 transformer 吃这种没难度）。
对人：感受到的是真正的"同时在线"。

## 为什么是 200ms
工程妥协点：
- 太小（如 50ms）→ [[prefill-decode]] 调用太频繁，GPU 元数据开销吃掉算力
- 太大（如 1s）→ 用户感知到延迟，听觉感知阈值大约就是 200-300ms
- 200ms ≈ 听觉阈值 + GPU prefill 摊薄成本的最低可接受值

## 它替代了什么
传统语音助手 pipeline：
- **[[vad]]**（Voice Activity Detection）判断"用户说完了没"
- **end-of-turn** 启发式决定"该模型说话了"
- 这些都是比主模型笨得多的外挂规则

Micro-turn 把"什么时候该说话 / 什么时候听 / 什么时候插嘴"全交给主模型自己学。符合 bitter lesson —— 见 [[replace-heuristics-with-weights]]。

## 工程支撑
- 客户端按 200ms 一个 chunk 发请求
- 推理服务器维持持久 [[kv-cache]]，每个 chunk 追加进去，不重分配
- 自定义 kernel（[[grouped-gemm-vs-gemv]] / [[nvls]] / [[split-kv]]）针对极低延迟小 batch 优化

## 跟 fish-speech 流式的对照
fish-speech 也吐流式音频 token（TTFA ~100ms），但形态不同：
- fish-speech：单向流，模型在"说"，用户在"等"
- TML micro-turn：双向交错流，两边都在动

fish-speech 解决的是"低延迟生成"；TML 解决的是"低延迟双向并发"。

## 链接
- [[interaction-models-tml]] · 论文
- [[dual-model-architecture]] · 前台模型跑的就是这条 micro-turn 流
- [[early-fusion]] · 各模态进同一 token 流的前提
- [[kv-cache]] · 流式会话的内存账本
- [[vad]] · 被替代的启发式
- [[replace-heuristics-with-weights]] · 这条范式
