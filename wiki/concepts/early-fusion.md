---
name: early-fusion
type: concept
sources: [interaction-models-tml]
updated: 2026-05-20
---

# Early Fusion · 无独立编码器的早融合

## 一句话
各模态用**轻量预处理**直接进同一个 transformer，不用 Whisper / ViT 那种独立大编码器再拼。

## 直觉
传统多模态架构（late fusion）：
- 音频 → Whisper encoder → 特征
- 视频 → ViT encoder → 特征
- 各路特征拼一起 → LLM

问题：
1. 编码器**冻结** → 没法跟着主模型一起 scale
2. 编码器**单独训** → 跟主任务目标脱节
3. **延迟链路长** → 音频要等 Whisper 跑完才能进 transformer

Early fusion = 把编码器砍到最小，让主 transformer 自己吃近似原始的 token。

## TML 怎么做的
| 模态 | 预处理 | 进 transformer 时 |
|---|---|---|
| 音频输入 | [[dmel]] 离散 Mel → 轻 embedding | embed token |
| 视频输入 | 切 40×40 patch → [[hmlp]] 分层 MLP | patch token |
| 文本 | 常规 tokenize | text token |
| 音频输出 | —— | [[flow-matching]] head 解 |

这些预处理组件**跟主 transformer 一起端到端训练**，不是冻结。

## 为什么"轻量预处理"还要保留
你可能问：为什么不让 transformer 直接吃 raw 16kHz waveform？因为：
- 序列太长（1 秒 = 16000 个采样点）
- 没有局部相关性的归纳偏置 = 学习效率低
- 计算资源浪费在"再发明 Mel 频谱"上

dMel / hMLP 这种轻预处理 = **保留必要的归纳偏置**（频域 / 空间局部性），同时让后续表征跟着主模型学。

## 重要 trade-off
Early fusion 听起来全好处，但：
- 训练数据要求**齐全的多模态对齐数据**（音视频文本同步），获取贵
- 模型规模必须够大才能吃下原始模态，小模型反而 late fusion 更好

TML 是 276B MoE 量级才合算。

## 链接
- [[interaction-models-tml]] · 论文
- [[dmel]] · 音频预处理
- [[hmlp]] · 视频预处理
- [[flow-matching]] · 音频输出
- [[replace-heuristics-with-weights]] · "把 pipeline 吃进权重"模式
