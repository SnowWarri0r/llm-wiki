---
name: temporal-depth-transformer
type: concept
sources: [moshi, personaplex]
updated: 2026-08-12
---

# Temporal–Depth Transformer · 时间轴走大步，帧内再补多层音频码

## 一句话

时间 Transformer 每 80 毫秒处理一次对话历史；深度 Transformer 只在当前 80 毫秒帧里，依次补齐多层音频 codebook。

## 为什么要拆两层

Mimi 每个时刻不只给一个音频 token，而是给 8 个从语义到声学细节的 token。若把它们全摊平，大模型的时间轴会从 12.5 步/秒膨胀到 100 步/秒。两层结构把“跨时间理解对话”与“同一帧补声音细节”分开。

## 数据怎样走

PersonaPlex 每帧有 17 路输入：用户 8 路音频码、agent 8 路音频码、agent 1 路文字码。17 个嵌入向量先逐元素相加，得到一个时间帧向量。时间 Transformer 处理这条 12.5 Hz 序列；深度 Transformer 再读时间状态与本帧已经生成的 codebook，输出 agent 的 8 路音频码。

## 数字例子

1 秒语音有 `12.5` 帧。每帧双方各 8 个音频码，再加 1 个 agent 文字码，共 `8 + 8 + 1 = 17` 路。

- 直接摊平音频层：单方就是 `12.5 × 8 = 100` 个时间位置/秒；
- Temporal–Depth：大时间轴仍只有 `12.5` 个位置/秒；每个位置内部再做 8 次较小的深度预测。

这不是把总计算白白消掉，而是避免让最贵的跨时间 Transformer 在每个 codebook 上重复前进。

## 链接

- [[moshi]] · 原始系统与完整公式
- [[personaplex]] · 沿用并增加角色 / 音色提示
- [[rvq-codec]] · 为什么一个音频帧有多层 codebook
- [[audio-codebook-delay]] · 为什么声学细节晚一帧
