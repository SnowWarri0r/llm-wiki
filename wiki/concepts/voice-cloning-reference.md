---
name: voice-cloning-reference
type: concept
sources: [fish-speech-s2-pro, viitorvoice]
updated: 2026-07-02
---

# Voice Cloning Reference · 声音克隆参考音频

## 一句话
给 TTS 模型一段参考音频，让它抽取说话人音色、韵律和风格条件，再生成同风格的新语音。

## 直觉
文本只告诉模型"说什么"，参考音频告诉模型"用谁的声音怎么说"。它相当于语音版 few-shot：不用重新训练说话人模型，只在输入条件里给一个示范。

## 怎么做的
- 输入 10-30 秒左右参考音频
- 模型/codec 提取说话人和声学条件
- 生成时文本内容走语言侧，音色/风格走参考条件
- 输出经 [[rvq-codec]] 或声学 decoder 还原为波形

## 代码出处
fish-speech README / demo 工作流；具体入口需要继续读本地 `raw/fish-speech` clone。

## 链接
- [[fish-speech-s2-pro]] · 来源
- [[rvq-codec]] · 声学 token 承载音色信息
- [[dual-ar]] · 生成架构
