---
name: causal-streaming-vae
type: concept
sources: [wan-streamer-v01, uniswap-av]
updated: 2026-08-18
---

# 因果流式 VAE · 压缩当前音视频时不偷看未来

## 一句话

把声音或视频压进 latent、再还原出来时，每个时间点只依赖当前和过去信号。

## 为什么普通 VAE 可能不够

离线视频 VAE 常用跨时间卷积：编码当前帧时同时看前后几帧，解码时也可能整段联合处理。离线生成没问题，实时通话却等不到未来帧。

因果流式 VAE 把时间方向改成单向：

```text
还原第 1 块：只能用第 1 块
还原第 2 块：可用第 1、2 块
还原第 3 块：可用第 1、2、3 块
```

## 四帧例子

25 FPS 下每帧 40 ms，一个 160 ms 单元包含 4 帧。若离线 VAE 还要等后面 4 帧才能编码当前单元，光等数据就多出 160 ms；严格因果后，当前 4 帧一到齐就能开始处理。

这只是时间账的教学例，不代表 Wan-Streamer 披露了 VAE 的卷积核或缓存结构。论文只明确说音频与视频 VAE、编码器和解码器都严格因果，没有公开具体架构与压缩率。

## 链接

- [[wan-streamer-v01]] · 因果 VAE 如何接到统一 Transformer 与解码播出
- [[video-vae]] · 视频怎样压成时空 latent
- [[audio-vae]] · 音频怎样压成适合生成的连续 latent
- [[native-streaming-contract]] · 为什么整条链都必须遵守同一因果约束
- [[autoregressive-vs-bidirectional-video-diffusion]] · 离线双向生成与流式因果生成的区别
- [[uniswap-av]] · 使用 LTX-2.3 的因果视频 VAE，把 3 个 latent 帧变成约 24 个像素帧
