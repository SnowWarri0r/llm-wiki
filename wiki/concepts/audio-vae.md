---
name: audio-vae
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Audio VAE · 把波形压成适合生成模型处理的声音 latent

## 一句话

先把密集波形变成时频图，再压成低帧率 latent；生成完成后由 decoder 和 vocoder 还原声音。

## 直觉

16kHz 双声道音频每秒有 32,000 个采样值，直接让 Transformer 对每个采样点做 attention 太贵。音频 VAE 先用 mel-spectrogram 把“每个瞬间有哪些频率”整理出来，再把它压成每秒几十个高维 token。

它替代的是 raw waveform 级生成。代价是 VAE/vocoder 可能丢掉细微相位与高频细节，latent 设计也会给最终音质设上限。

## 怎么做的

```text
训练/编码：stereo waveform 16kHz
          → 左右声道各自 mel-spectrogram
          → 沿 channel 拼接
          → causal VAE encoder
          → temporal latent tokens

解码：latent → VAE decoder → stereo mel → vocoder → stereo waveform 24kHz
```

“causal”表示每个时间 latent 只依赖当前与过去输入，便于流式和按时间处理。vocoder 负责把频谱变成可播放波形，不预测场景语义。

## 数字例子

LTX-2 报告给出约 25 token/s、每 token 128 维：

```text
4 秒  → 4×25 = 100 token → 100×128 = 12,800 latent 标量
20 秒 → 20×25 = 500 token → 500×128 = 64,000 latent 标量
```

当前实现把每个时间位置写成 `[8 channels,16 frequency slots]`，`8×16=128`。这说明 latent 形状，不等于 128 个互相独立的声学量。

## 跟 codec token 的对比

VQ/RVQ codec 通常把声音变成离散码本索引；LTX-2 的 audio VAE 输出连续向量，适合 flow/diffusion 直接预测速度。连续 latent 不需要选离散类别，但解码质量仍取决于 autoencoder。

## 链接

- [[ltx-2]] · 立体声音频 latent 与 HiFi-GAN vocoder
- [[log-mel-spectrogram]] · 波形到时频图
- [[flow-matching]] · 在连续 audio latent 上学习速度场
- [[rvq-codec]] · 离散声音 token 的对照路线

