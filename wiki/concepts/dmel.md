---
name: dmel
type: concept
sources: [dmel, interaction-models-tml]
updated: 2026-05-21
---

# dMel · 离散 Mel 频谱

## 一句话
把 log-mel 频谱图按预设 bin 量化成离散 token，让音频能像文本一样直接喂进 transformer —— 不用训 codec。

## 直觉
log-mel 频谱图 = 把波形按短时窗做 FFT → 转到 Mel 尺度（人耳感知的对数频率）→ 取对数 → 得到 `[频带 × 时间]` 的连续矩阵。

传统 Whisper / TTS pipeline 把这个矩阵喂给独立编码器（CNN + transformer），或者训个 neural codec 离散化。

**dMel = 跳过编码器/codec**，直接把每个频道按 K 个 bin 等距切片（如 16 bin），token 就是 bin index。主 transformer 自己学怎么用这些 token。

## 跟 RVQ codec 的对比
- **dMel**：**规则**离散化，无需训 codebook · 简单可控 · 跨语言稳定 · 可解释
- [[rvq-codec]]：**学**出来的 codebook · 表达力强 · 训练复杂 · 跟训练域绑定 · 黑盒

实证上两者在 speech-LLM 训练里<strong>性能相当</strong>。dMel 用简单度换 RVQ 那点表达力优势。

## TML 怎么用
TML 用 dMel 做<strong>输入</strong>（音频 → bin token 喂 transformer），用 [[flow-matching]] 做<strong>输出</strong>（生成连续 mel → vocoder）。两端都不用 RVQ codec，整条链路端到端可微。

## 链接
- [[dmel]]（这一篇 paper）
- [[interaction-models-tml]] · 应用方
- [[bin-quantization]] · 核心机制
- [[log-mel-spectrogram]] · 输入基础
- [[rvq-codec]] · 对照路线
- [[audio-tokenization-rvq-vs-flow]] · 横向比较
