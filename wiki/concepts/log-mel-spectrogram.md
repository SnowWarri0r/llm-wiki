---
name: log-mel-spectrogram
type: concept
sources: [dmel, interaction-models-tml, whisper]
updated: 2026-05-21
---

# Log-Mel Spectrogram · 对数 Mel 频谱图

## 一句话
把 1D 音频波形转成 2D `[频道 × 时间]` 的能量矩阵 —— 跟人耳听到的"哪个时刻、哪个频段、有多响"对应。

## 直觉
波形是 1D 信号（每个采样点一个浮点数，16kHz 采样率 = 每秒 16000 个值）。直接喂 transformer 太长（10 秒音频 = 160000 token）。

Mel spectrogram 做<strong>降维 + 人耳化</strong>：
- 切短时窗（如 25ms）
- 每窗做 FFT → 频率分布
- 把频率轴换成 Mel scale（对数轴 · 人耳感知）
- 取每个 Mel band 的能量
- 取对数（log）让动态范围合理

结果：<strong>`[80 mel bands × N frames]`</strong>，10 秒音频 → 80 × 1000 ≈ 80000 个浮点数，<strong>压缩 2 倍</strong>，更结构化。

每个 cell 是 "这一帧（10ms 左右）这个频段（如 1.2kHz 附近）的 log 能量"。

## 为什么用 Mel 而不是 Hz
人耳对频率是<strong>对数感知</strong>：100Hz → 200Hz 跟 1000Hz → 2000Hz 听起来都是"高了一个八度"。Mel scale 把 Hz 转成感知一致的轴。

公式（简化）：
```
mel(f) = 2595 · log10(1 + f / 700)
```

低频段密、高频段疏 —— 跟人耳分辨率匹配。

## 为什么取 log
原始能量值范围巨大（10⁻⁸ 到 10⁰ 都常见）。取 log 后压缩到 [-8, 0] 范围 —— 神经网络喜欢这种动态范围。

## 跟 raw waveform 的对比
| | raw waveform | log-mel spectrogram |
|---|---|---|
| 维度 | 1D 长序列 | 2D 短矩阵 |
| 长度 | 16000/秒 | 100/秒（10ms 帧）|
| 跟人耳对齐 | 不（线性频率） | 是（Mel scale） |
| 信息完整度 | 100% | ~95%（高频细节略损） |
| 主流应用 | end-to-end 模型（如 WaveNet 输入） | TTS / ASR / speech LLM |

现代 speech LLM 几乎都用 log-mel 输入。raw waveform 太长且不结构化。

## dMel 在这之上做什么
log-mel 仍是连续值（浮点）。dMel 把每个 cell 按 16 bin 量化 → 整张 spectrogram 变成 `[80 × N]` 的 bin index 矩阵 → 每个 index 是 token。送 LLM。

## 链接
- [[dmel]] · 用它的论文
- [[bin-quantization]] · dMel 在它上面做的事
- [[rvq-codec]] · 对照的另一种"音频 → token"路线
- [[interaction-models-tml]] · 应用
