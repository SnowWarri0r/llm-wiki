---
name: log-mel-spectrogram
type: concept
sources: [dmel, interaction-models-tml, whisper, fft, qwen3-asr]
updated: 2026-06-14
---

# Log-Mel Spectrogram · Fbank · 对数 Mel 频谱图

## 一句话
把 1D 音频波形转成 2D `[频道 × 时间]` 的能量矩阵 —— 跟人耳听到的"哪个时刻、哪个频段、有多响"对应。ASR 圈管它叫 **Fbank**（log mel filterbank energies），同一个东西。

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

## Fbank / MFCC · 正名
- **Fbank**（filter bank energies）= **就是本页这张 log-mel 图**。名字来自下面第 ④ 步那"一排三角滤波器"（filter bank）。Qwen3-ASR 用的是 128 维 Fbank。
- **MFCC** = Fbank 之上再做一步 **DCT**（离散余弦变换，去相关）。老式 ASR（GMM-HMM）需要 DCT 把特征解耦；神经网络不怕特征相关，所以现代 ASR（[[whisper]] / [[qwen3-asr]]）直接吃裸 **Fbank**，不做 DCT。

## 从波形到 Fbank · 五步
从一段 16kHz 波形到 Fbank，五步走（前三步合起来就是 [[fft]] 页的 **STFT**）：

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="fb-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#7a6f5d"/></marker></defs>
  <!-- 连接箭头 + 动词 -->
  <g class="reveal d2" stroke="#7a6f5d" stroke-width="1.3" fill="none">
    <line x1="114" y1="104" x2="138" y2="104" marker-end="url(#fb-h)"/>
    <line x1="234" y1="104" x2="258" y2="104" marker-end="url(#fb-h)"/>
    <line x1="354" y1="104" x2="378" y2="104" marker-end="url(#fb-h)"/>
    <line x1="474" y1="104" x2="498" y2="104" marker-end="url(#fb-h)"/>
    <line x1="594" y1="104" x2="618" y2="104" marker-end="url(#fb-h)"/>
  </g>
  <g class="reveal d3" font-size="8" fill="#7a6f5d" text-anchor="middle">
    <text x="126" y="98">分帧</text><text x="246" y="98">加窗</text><text x="366" y="98">FFT</text><text x="486" y="98">mel</text><text x="606" y="98">log</text>
  </g>
  <!-- ① 波形 -->
  <g class="reveal d1"><rect x="18" y="56" width="96" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <polyline class="draw d2" pathLength="1000" points="26,104 38,84 50,120 62,84 74,116 86,88 98,112 106,104" fill="none" stroke="#1f3a5f" stroke-width="1.6"/></g>
  <!-- ② 分帧 -->
  <g class="reveal d2"><rect x="138" y="56" width="96" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <polyline points="146,104 158,90 170,116 182,90 194,114 206,92 218,110 226,104" fill="none" stroke="#bfb398" stroke-width="1.1"/>
    <rect x="150" y="78" width="34" height="52" fill="none" stroke="#9b2c2c" stroke-width="1.2"/><rect x="172" y="78" width="34" height="52" fill="none" stroke="#9b2c2c" stroke-width="1.2" opacity="0.6"/><rect x="194" y="78" width="34" height="52" fill="none" stroke="#9b2c2c" stroke-width="1.2" opacity="0.35"/>
  </g>
  <!-- ③ 加窗 -->
  <g class="reveal d3"><rect x="258" y="56" width="96" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <path d="M268,132 Q306,72 344,132" fill="none" stroke="#4a6b3a" stroke-width="1.4" stroke-dasharray="3 2"/>
    <polyline points="272,124 288,106 298,98 306,96 314,98 324,106 340,124" fill="none" stroke="#1f3a5f" stroke-width="1.5"/>
  </g>
  <!-- ④ FFT 功率谱 -->
  <g class="reveal d4"><rect x="378" y="56" width="96" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <line x1="386" y1="138" x2="466" y2="138" stroke="#7a6f5d" stroke-width="0.8"/>
    <g fill="#1f3a5f"><rect x="392" y="110" width="7" height="28"/><rect x="404" y="86" width="7" height="52"/><rect x="416" y="118" width="7" height="20"/><rect x="428" y="96" width="7" height="42"/><rect x="440" y="122" width="7" height="16"/><rect x="452" y="106" width="7" height="32"/></g>
  </g>
  <!-- ⑤ Mel 三角滤波器组 -->
  <g class="reveal d5"><rect x="498" y="56" width="96" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <line x1="504" y1="138" x2="590" y2="138" stroke="#7a6f5d" stroke-width="0.8"/>
    <g fill="none" stroke="#b8841c" stroke-width="1.2">
      <polygon points="504,138 512,110 520,138"/><polygon points="518,138 528,104 538,138"/><polygon points="536,138 550,100 564,138"/><polygon points="560,138 578,98 592,138"/>
    </g>
  </g>
  <!-- ⑥ log → Fbank 矩阵 -->
  <g class="reveal d6"><rect x="618" y="56" width="84" height="96" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <g>
      <rect x="628" y="70" width="13" height="13" fill="#1f3a5f" opacity="0.85"/><rect x="643" y="70" width="13" height="13" fill="#1f3a5f" opacity="0.4"/><rect x="658" y="70" width="13" height="13" fill="#1f3a5f" opacity="0.7"/><rect x="673" y="70" width="13" height="13" fill="#1f3a5f" opacity="0.25"/>
      <rect x="628" y="86" width="13" height="13" fill="#1f3a5f" opacity="0.5"/><rect x="643" y="86" width="13" height="13" fill="#1f3a5f" opacity="0.8"/><rect x="658" y="86" width="13" height="13" fill="#1f3a5f" opacity="0.35"/><rect x="673" y="86" width="13" height="13" fill="#1f3a5f" opacity="0.6"/>
      <rect x="628" y="102" width="13" height="13" fill="#1f3a5f" opacity="0.3"/><rect x="643" y="102" width="13" height="13" fill="#1f3a5f" opacity="0.55"/><rect x="658" y="102" width="13" height="13" fill="#1f3a5f" opacity="0.85"/><rect x="673" y="102" width="13" height="13" fill="#1f3a5f" opacity="0.45"/>
    </g>
    <text x="660" y="134" text-anchor="middle" font-size="7.5" fill="#7a6f5d">mel × 帧</text>
  </g>
  <!-- 步骤标签 -->
  <g class="reveal d1" font-size="8.5" fill="#3a3128" text-anchor="middle" font-weight="700">
    <text x="66" y="176">①波形</text><text x="186" y="176">②分帧</text><text x="306" y="176">③加窗</text><text x="426" y="176">④FFT功率谱</text><text x="546" y="176">⑤Mel三角</text><text x="660" y="176">⑥log→Fbank</text>
  </g>
  <text class="reveal d6" x="360" y="208" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#3a3128">②③④ = STFT（你 FFT 页学的）· ⑤ Mel 滤波器组求和 · ⑥ 取 log → 一列 Fbank</text>
</svg>
</figure>

1. **分帧** — 把连续波形切成 ~25ms 一帧、每 10ms 滑一帧（帧间重叠）。语音只在 ~25ms 内近似平稳，短到这尺度频谱才有意义；重叠是怕帧接缝丢信息。<em>（像把连续视频切成一格格短镜头。）</em>
2. **加窗** — 每帧乘一个 Hamming/Hann 窗（两头淡出到 0）。硬生生方形剪一段会在接缝制造假高频（**频谱泄漏**），FFT 出来一堆不存在的频率；加窗把两头淡入淡出，接缝不"咔哒"。
3. **每帧 FFT（STFT）** — 对每个加窗帧做一次 [[fft]] → 取幅度平方 = **功率谱**："这帧里各频率各占多少能量"。就是 FFT 页讲的"切窗、每段做一次 FFT"。
4. **Mel 三角滤波器组**（← Fbank 名字由来）— 在频率轴上摆一排**三角形滤波器**（~80 或 128 个），按 Mel 刻度排：低频处密、高频处疏（贴人耳）。每个三角把它覆盖那段功率谱**加权求和成一个数** → 几百个 FFT bin 塌成 80/128 个 Mel band 能量。<em>（像一排漏斗，各收集自己那段频率的能量。）</em>
5. **取 log** — 每个滤波器能量取对数（响度是对数感知 + 压动态范围）。

每帧 → 一列 80/128 维 log-mel 能量；沿时间堆 → `[n_mels × T]` = **Fbank**。

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
- [[fft]] · 频谱怎么算出来的：把信号切窗、每段做一次 FFT（STFT）
