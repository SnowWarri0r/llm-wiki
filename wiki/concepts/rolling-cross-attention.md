---
name: rolling-cross-attention
type: concept
sources: [faceplex]
updated: 2026-08-11
---

# Rolling Cross-Attention · 滚动交叉注意力

## 一句话

一个待生成动作随队列前移，每一轮都读取新的语音隐藏状态，临近输出时信息最完整。

## 直觉

表情不能只看开口前的声音：一个音节末尾、停顿或笑声会改变前后几帧的嘴形。FacePlex 先生成语音，再把音频和表情一起暂存。某个表情片段在队列里待三轮，每轮都能读到后来已由系统生成的语音状态。

这不是预测用户的未来，也不是偷看测试答案。它替代严格只看过去的单次 cross-attention，用约 240 毫秒固定等待换取局部双向语音上下文。

## 怎么做的

设队列长 (L=4)，第 (i) 个动作槽对第 (j) 个语音隐藏槽是否可见由二值 mask (A_{ij}) 决定：

- full：全部为 1；
- block diagonal：仅 (i=j)；
- causal：仅 (j\le i)；
- anti-causal：仅 (j\ge i)。

队列每 80 毫秒前移一次。同一个动作片段不是永远固定在某个格子，因此它一生中读取到的语音范围大于一次 attention 的四个槽位。

## 数字例子

动作片段 (X_t) 刚进入队尾时读取 `[h_{t-3},h_{t-2},h_{t-1},h_t]`；下一轮读取 `[h_{t-2},h_{t-1},h_t,h_{t+1}]`；到输出前读取 `[h_t,h_{t+1},h_{t+2},h_{t+3}]`。

把所有轮次取并集，它见过 (h_{t-3}) 到 (h_{t+3})。后面三项之所以可用，是因为系统已先生成并缓存相应语音；代价是等待 (3×80=240) 毫秒。

## 跟严格因果 attention 的对照

- 严格因果：零额外未来缓冲，但嘴形可能缺少音节尾部线索。
- Rolling full mask：局部语音上下文更完整，但增加固定等待与队列状态。

## 链接

- [[faceplex]] · Rolling Cross-Attention 的提出论文
- [[cross-attention]] · Query 怎样读取另一条序列的 Key/Value
- [[rolling-flow-matching]] · 同一滚动队列中的生成进度
