---
name: rvq-codec
type: concept
sources: [fish-speech-s2-pro, viitorvoice]
updated: 2026-07-02
---

# RVQ Codec · 残差向量量化

## 一句话
把音频压成 **N 层堆叠的 codebook**，第 k 层负责前 k-1 层量化剩下的"误差"。

## 直觉
单个大 VQ codebook 要么太小（音质烂）要么太大（内存爆）。RVQ 把任务分到多层：
- 第 1 层：粗略量化，"大致这是什么音"
- 第 2 层：量化第 1 层的残差 = 一阶修正
- 第 N 层：再修正前 N-1 层留下的高频细节

类比：**JPEG 渐进式编码** —— 先一个低分辨率版本，再叠加细节层。或 **bitplane coding** 把灰度图按位平面切。

## 怎么做的
- fish-speech S2 用 **10 个 codebook**，**~21 Hz** 帧率
- 编码器（卷积栈）把 waveform 编成连续向量
- 第 1 个 codebook 找最近邻 → token₁
- 用 codebook 解码后的向量算残差 → 第 2 个 codebook 找最近邻 → token₂
- 以此类推到 10 层
- 解码器吃 10 路 token 重建波形
- 训练时联合优化编码器 + 解码器 + codebook（VQ-VAE 风格，带 commitment loss + codebook loss）

## 跟 TML dMel 的区别
- **RVQ** = 学出来的 codebook，跨数据集会自动适配，表达力强
- **[[dmel]]** = 规则离散化 Mel 频谱（每个频带按预设格点切）—— 简单、无需训 codebook，但只适合输入侧

为什么 TML 不在输出侧用 RVQ？我的猜测：RVQ 需要 N 层串行解码 → 延迟高；TML 想要 200ms 内吐完音频，选了 [[flow-matching]] 一步到位（但 flow matching 也要 ODE 多步，是另一种 trade-off）。详见 [[audio-tokenization-rvq-vs-flow]]。

## 链接
- [[dual-ar]] · 10 路 token 由 Dual-AR 生成
- [[dmel]] · 对照：TML 的离散化方案
- [[flow-matching]] · TML 选用的非量化路线
- [[audio-tokenization-rvq-vs-flow]] · 横向比较
- [[fish-speech-s2-pro]] · 论文
