---
name: audiovisual-cross-attention
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Audiovisual Cross-Attention · 音视频双向交叉注意力

## 一句话

视频拿自己的问题去查声音，声音也拿自己的问题去查视频，并用共同时间轴对齐事件。

## 直觉

self-attention 只能在同一模态内部找关系：画面知道杯子碰桌子，却不知道应产生什么声音；音频知道有一声脆响，却不知道画面里是哪件物体。cross-attention 让一边提供 query，另一边提供 key/value。

双向很重要：

- `audio → video`：语音音素、节拍和撞击声可以修正嘴型、动作时机；
- `video → audio`：说话人、碰撞物、房间和镜头可以修正音源、音色、Foley 与混响。

## 怎么做的

\[
A_{V\leftarrow A}=\operatorname{softmax}\left(\frac{Q_VK_A^\top}{\sqrt d}\right)V_A
\]

- `Q_V`：视频 token 提出的查询；
- `K_A`：音频 token 的检索索引；
- `V_A`：匹配后真正取回的音频内容；
- `d`：query/key 的共同宽度；
- `√d`：控制点积分布，避免 softmax 太尖；
- 反方向把 V/A 交换即可。

LTX-2 在跨模态 Q/K 上只使用 1D 时间 RoPE。声音没有画面 `x,y`，所以跨模态先回答“是不是同一时刻”，空间位置由视频内容特征自行决定。

## 数字例子

视频中 `0.40s` 的碰撞 token，对三个音频 token 的缩放后 score 为 `[1,3,1]`：

```text
softmax ≈ [0.107, 0.787, 0.107]
audio values = [0.2, 1.0, 0.1]
output = .107×.2 + .787×1 + .107×.1 ≈ .819
```

中间时刻的声音获得约 78.7% 权重，取回的碰撞特征接近 1。自检：权重和约为 `1.001`，差异来自三位小数舍入。

## 跟普通 cross-attention 的区别

普通文生图 cross-attention 通常只有“图像 query 查文本 K/V”；LTX-2 这里是两个生成模态互查，并额外让各自噪声时间步调制输入、让对方噪声进度控制写回门。

## 链接

- [[ltx-2]] · 逐层 A↔V 交互
- [[cross-attention]] · 通用机制
- [[rotary-position-embedding]] · 共同时间坐标的注入方式
- [[adaptive-layernorm]] · 不同去噪进度下控制信息交换

