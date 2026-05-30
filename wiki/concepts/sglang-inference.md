---
name: sglang-inference
type: concept
sources: [fish-speech-s2-pro]
updated: 2026-05-22
---

# SGLang Inference

## 一句话
SGLang 是 LLM 推理服务栈；fish-speech 复用它来拿到高效 batching、KV cache 管理和 serving 基建。

## 直觉
TTS 看起来是音频任务，但 Dual-AR 的慢模型本质上像一个 decoder-only LLM：吃文本/语音条件，吐离散 token。既然问题长得像 LLM 推理，就可以直接借 LLM serving 的轮子，而不是从零写 scheduler、cache manager、batcher。

## 怎么做的
- 用 [[prefill-decode]] 两阶段组织请求
- 用 [[kv-cache]] 管理长上下文
- 用 continuous batching / paged cache 提高 GPU 利用率
- 把 [[dual-ar]] 的慢 AR 模型接到通用推理框架里

## 代码出处
`raw/fish-speech/` 是本地软链，默认不进仓；具体入口需要在本地 clone 中继续查。

## 链接
- [[fish-speech-s2-pro]] · 来源
- [[dual-ar]] · 为什么能复用 LLM serving
- [[kv-cache]] · 推理内存账本
- [[prefill-decode]] · 推理阶段拆分
