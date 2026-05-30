---
name: vad
type: concept
sources: [interaction-models-tml, replace-heuristics-with-weights]
updated: 2026-05-22
---

# VAD · Voice Activity Detection

## 一句话
判断音频里什么时候有人声、什么时候静音/噪声的传统语音模块。

## 直觉
传统语音助手要先决定"用户是不是说完了"，才轮到模型回答。VAD 就像门口的传感器：检测到声音开门，检测到沉默关门。

问题是人类对话不是这么规整：会打断、犹豫、拖长音、边想边说。硬 VAD 门槛会把交互切成笨拙的轮次。

## 怎么做的
- 传统方案看短时能量、频谱特征、人声概率
- 工程上常设置 silence threshold 和 hangover time
- TML 的 [[micro-turn]] 思路是把这种外部规则弱化，让模型在连续流里自己学何时听、何时说

## 代码出处
这是通用语音系统组件；当前 wiki 主要作为 TML 被替代启发式的对照。

## 链接
- [[micro-turn]] · 替代 VAD 式轮次切分
- [[replace-heuristics-with-weights]] · 把外挂规则吃进权重
- [[early-fusion]] · 连续流式输入的架构基础
