---
name: vits
type: paper
source: https://arxiv.org/abs/2106.06103
upstream: https://github.com/jaywalnut310/vits
ingested: 2026-07-05
authors: Jaehyeon Kim, Jungil Kong, Juhee Son (ICML 2021)
---

# VITS · 把 VAE + 归一化流 + GAN 拧成一个端到端 TTS

## 一句话
2021 的里程碑:第一个真正好用的**端到端**并行 TTS——一个模型直接文本→波形,不再"文本→mel→波形"两段分开训;骨架是条件 VAE,先验用归一化流掰复杂、对齐用 MAS、节奏用随机时长预测器、波形用 GAN 对抗打磨,MOS 4.43 逼近真人 4.46。

## 它要解决的痛点
以前 TTS 是两段式:声学模型(Tacotron2)把文本变 mel 频谱,再一个 vocoder(HiFi-GAN)把 mel 变波形,两段**分开训**。问题:① vocoder 在**真** mel 上训、推理却吃声学模型产的**假** mel → 失配,得 fine-tune 打补丁(论文里 Tacotron2+HiFiGAN 3.77 → fine-tuned 才 4.25);② mel 是人为中间量,有信息损失。想端到端直接文本→波形,难在:文本(短、离散)和波形(长、连续)差异巨大,中间还有"每个音素占多少帧"的对齐不确定。

## 核心贡献
- **条件 VAE 做骨架**:后验编码器从线性谱抽潜变量 z、解码器(HiFi-GAN 生成器)把 z 还原成波形;训练最大化 ELBO(重建 + KL)。先验 p(z|文本) 由文本给。
- **归一化流掰先验**:文本先验是简单高斯、音频后验很复杂,直接拉 KL 会互相将就糊掉。在先验上套一个**可逆流** f 把简单高斯变复杂,够得着后验。
- **MAS 单调对齐**:文本 N 音素、音频 T 帧(T≫N),用动态规划找**使似然最大的单调对齐**,不用外部对齐器(承 Glow-TTS)。
- **随机时长预测器(SDP)**:同一句话可快可慢(一对多),用基于流的随机时长给节奏一个分布、采样出变化,比确定性时长更自然(VITS 4.43 > VITS-DDP 确定性 4.39)。
- **对抗训练**:HiFi-GAN 判别器 + 特征匹配损失,让波形逼真。
- **端到端 + 并行**:非自回归,合成 ×67.12 实时(DDP ×90.93),远快于 Glow-TTS+HiFiGAN 的 ×27.48。

## 关键概念 → 概念页链接
- [[conditional-vae]] — 条件变分自编码器:后验编码、潜变量、ELBO
- [[normalizing-flow]] — 可逆变换把简单分布掰成复杂分布(精确似然)
- [[monotonic-alignment-search]] — 动态规划找文本↔音频的单调对齐
- [[stochastic-duration-predictor]] — 基于流的时长分布,建模一对多节奏
- [[flow-matching]] — 对比:同是"流",但 flow matching 学连续速度场,归一化流是离散可逆层
- [[log-mel-spectrogram]] — 重建损失比的就是 mel

## 我的批注 / 疑问
- VITS 的漂亮在于**把四件难事各用一个对的工具**:分布匹配用 VAE、先验表达力用流、对齐用 DP、节奏多样性用随机流——最后 GAN 收尾。不是堆料,是各司其职。
- "两段失配"这个痛点很典型:任何"A 产中间量喂给 B、但 B 在真中间量上训"的流水线都会踩,端到端联合训是解法。
- 承上启下:MAS 来自 Glow-TTS,HiFi-GAN 判别器来自 HiFi-GAN;VITS 把它们缝进一个 VAE。后来的 TTS(含 [[viitorvoice]]、[[fish-speech-s2-pro]])多转向离散 codec + LM/NAR 路线,但 VITS 这套"连续潜变量 + 流 + 对抗"仍是端到端 TTS 的经典参照。
