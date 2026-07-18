---
name: activation-checkpointing
type: concept
sources: [krea-2, cosmos-3]
updated: 2026-07-16
---

# Activation Checkpointing · 少存中间结果，反向时重新算

## 一句话
前向时少记几份“草稿纸”，反向传播需要时再重算；省的是显存，花的是计算。

## 它为什么存在

训练不只存模型权重。反向传播还要用每层的中间激活；视频 token 很多时，激活往往比参数更占显存。Activation checkpointing 会挑少数边界激活保存，边界之间的结果先丢掉，反向经过这一段时再跑一次前向。

## 数字例子

假设 A、B、C、D 四个 block，每个 block 的中间激活占 2 GB：

```text
全部保存：A + B + C + D = 8 GB，反向时直接读取

只保存 A 和 D：2 + 2 = 4 GB
反向要用 B、C 时：从 A 再跑一遍 B、C

省下激活显存：8 - 4 = 4 GB
代价：B、C 的前向计算多做一次
```

自检：重算得到的 B、C 必须与原前向一致，否则梯度会变。因此随机数、dropout 和算子确定性也要正确处理。

## selective 和 full 有什么区别

- **Selective Activation Checkpointing** 只重算最占显存、重算又相对便宜的部分。
- **Full checkpointing** 把整段都重算，显存省得更多，额外 FLOPs 也更多。

Cosmos 3 报告中，选择性方案约增加 13% 开销；整层重算约增加 33% FLOPs。Krea 2 则按分辨率调整：低分辨率只挑昂贵 block，高分辨率才更激进地重算。

## 别跟模型 checkpoint 混淆

Activation checkpoint 在 GPU 内存里做“丢掉再重算”，只活在当前训练步；模型 checkpoint 是把权重、优化器状态和训练进度写到持久存储，用来崩溃恢复。

## 链接

- [[krea-2]] · 随分辨率调整重算范围
- [[cosmos-3]] · 选择性重算与完整重算的开销对比
- [[training-checkpointing-and-recovery]] · 写盘存档是另一件事
