---
name: block-causal-attention
type: concept
sources: [wan-streamer-v01, wan-streamer-v03, interactive-avatar, causal-rcm]
updated: 2026-08-14
---

# Block-Causal Attention · 块因果注意力

## 一句话

同一个时间块里的 token 可以互相看，后面的时间块只能看自己和过去，不能偷看未来。

## 为什么不只用普通 causal mask

连续音视频在同一个 160 ms 时间段里会产生一批 token。它们表示同一小段画面和声音，没有必要像文字那样一个 token 接一个 token 串行等待。块因果注意力把时间线切成块：

```text
块 1：块内互相可见
块 2：可看块 1，也可看块 2 内部
块 3：可看块 1、2，也可看块 3 内部
未来块：不可见
```

这同时保留两件事：块之间遵守时间因果，块内利用 GPU 并行计算。

## 四格 mask

若每块只有一个简化 token，注意力可见关系是下三角；若每块有很多 token，下三角的每个小格会扩展成一个全可见方块：

```text
查询块 1  [看 1] [禁止] [禁止]
查询块 2  [看 1] [看 2] [禁止]
查询块 3  [看 1] [看 2] [看 3]
```

## 与全双工的关系

Wan-Streamer 的 25 FPS 视频每帧 40 ms；160 ms 流式单元包含 4 帧。模型每处理完一块，就能吸收新的用户音视频并生成下一块。块越短，反应机会越频繁；块太短又会增加调度、通信和解码开销。

## 链接

- [[wan-streamer-v01]] · 六路信号如何按 160 ms 块排进一条因果时间线
- [[wan-streamer-v03]] · 160 ms 流式单元怎样进入完整系统
- [[causal-language-model]] · token 级因果注意力与自回归预测的基础
- [[kv-cache]] · 历史块为什么不必反复重算
- [[full-duplex-multimodal-interaction]] · 输入输出并行的产品目标
