---
name: thinker-performer-streaming
type: concept
sources: [wan-streamer-v01, wan-streamer-v02, wan-streamer-v03]
updated: 2026-08-06
---

# Thinker–Performer Streaming · 状态更新与连续 latent 生成分工

## 一句话

Thinker 维护因果上下文和 KV cache，Performer 在同一时间预算里生成更耗算力的视频、音频 latent；两边用流水线重叠，而不是等整段做完再交棒。

## 先别和 Thinker–Talker 混淆

- **Thinker–Performer**：Wan-Streamer 的服务分工。Thinker 管流式状态与编解码，Performer 管条件流匹配的连续 latent 生成。
- **Thinker–Talker**：DuplexOmni 等语音模型里“先出语义文字、再渲染语音 codec”的模型结构。

名字相似，解决的问题不同。

## 一次 160 ms 单元里发生什么

把当前单元记作 \(k\)：

1. Thinker 编码当前用户音视频，更新因果序列和 KV cache；
2. Performer 根据已经准备好的条件生成下一个单元的音视频 latent；
3. Thinker 同时可以解码上一个单元的 latent；
4. 三段工作尽量重叠，整个流水线才跟得上 160 ms 的交付节奏。

这里要分清 **吞吐约束** 和 **响应延迟**：每个单元的稳态工作量必须在 160 ms 节拍内消化，论文报告的模型侧端到端信号延迟则约为 200 ms。前者像流水线每分钟能做多少件，后者像一件产品从入口到出口走多久。

## v0.2 为什么给 Performer 多卡

高分辨率视频 latent 序列较长，v0.2 用 Ulysses 上下文并行把它切给多张 GPU；音频 latent 短，不必同样切分。Thinker 仍放在单卡，避免因果状态和频繁的小块调度被额外通信拖慢。

每个 Performer rank 还把新来的 K/V 直接写入自己负责的预分片 cache。这样历史增长时不用先复制一份完整 K/V，再在每个 160 ms 单元里重新切分。

## 链接

- [[wan-streamer-v01]] · 初版两卡时间线与第 k 段何时生成、何时播出
- [[wan-streamer-v03]] · v0.3 沿用了哪一段服务路径
- [[wan-streamer-v02]] · v0.2 为什么改服务拓扑，以及三种延迟口径
- [[distributed-training-parallelism]] · Ulysses 怎样沿 token 维切长序列
- [[conditional-flow-matching]] · Performer 实际回归什么连续目标
- [[kv-cache]] · Thinker 保存的历史状态
