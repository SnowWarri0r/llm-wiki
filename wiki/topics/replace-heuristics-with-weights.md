---
name: replace-heuristics-with-weights
type: topic
sources: [fish-speech-s2-pro, interaction-models-tml]
updated: 2026-05-20
---

# 把外挂规则吃进模型权重

这是这次 ingest 的两个源都在做的**反复出现的范式**，工程系统里也有同形状的事。

## 主张
任何 pipeline 里"用规则 / 启发式 / 小专用模型做的事"，迟早会被"做进主模型权重"。理由：
- 规则被 scaling law 跨过（[[bitter-lesson]]）
- 端到端联训能力 > 段段对接
- 维护规则比训权重还累

## 例子

### TML 干掉的：[[vad]]（Voice Activity Detection）
传统语音助手用小专用模型判断"用户说完没"。TML 把这个判断让主模型自己学 —— [[micro-turn]] 是工程支撑。

### fish-speech 干掉的：phonemizer / G2P
传统 TTS 要把文本转音素（grapheme-to-phoneme），每种语言一套规则或一个小模型。fish-speech 80+ 语言**无需 phonemizer**，主模型直接吃 raw 文本 token。

### TML 干掉的：Whisper-style 独立编码器
[[early-fusion]] 用轻量预处理（[[dmel]] / [[hmlp]]）替代独立大编码器，让多模态表征跟着主模型一起 scale。

### 工程系统里同形状的事
- **把外挂的预检 / 计费门收进调用方自身责任** → 把"外挂检查"收到"自治单元自己负责"
- **轮询调度替换为 callback 事件驱动** → "外挂状态机"被吃进事件流
- **把跨服务的解析 / 校验下沉到统一上下文服务** → 同一个收敛方向

不完全等价于"做进模型权重"，但是**同一种"边界收紧"张力** —— 把分散在各处的小规则收回核心。

## 例外 / 反例
不是所有规则都该吃。该吃的特征：
- 信号噪声比可学（数据量够）
- 输入分布跟主模型 input 一致或可对齐
- 端到端 loss 能反向传到这个判断上

不该吃的：硬约束（safety hard rules）、外部世界状态（实时股价、用户身份）、需要可解释审计的判断（合规检查）。

## 链接
- [[interaction-models-tml]] · VAD 例子
- [[fish-speech-s2-pro]] · phonemizer 例子
- [[early-fusion]] · 独立编码器例子
- [[micro-turn]] · VAD 的替代工程
- [[bitter-lesson]] · 理论根基
