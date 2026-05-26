---
name: inline-emotion-tags
type: concept
sources: [fish-speech-s2-pro]
updated: 2026-05-22
---

# Inline Emotion Tags · 内联情绪标签

## 一句话
在输入文本里直接插入 `[whisper]`、`[laugh]` 这类标签，让 TTS 模型控制语气、情绪或副语言声音。

## 直觉
传统 TTS 常把风格控制做成独立参数面板。Inline tags 把控制信号写进文本流里，像 prompt 里夹一条导演指令：这句小声说、这里笑一下、下一段激动一点。

好处是接口简单；坏处是标签体系要跟训练数据对齐，否则模型会把标签当普通文本读出来或忽略。

## 怎么做的
- 训练数据里保留/标注情绪和副语言 token
- tokenizer 把标签当特殊 token
- 生成时文本内容和控制 token 一起进 [[dual-ar]] 模型
- 声学侧通过 [[rvq-codec]] 输出对应语音细节

## 代码出处
fish-speech S2 Pro 功能描述；具体 tag 列表需要读本地 `raw/fish-speech`。

## 链接
- [[fish-speech-s2-pro]] · 来源
- [[dual-ar]] · 控制 token 被谁消费
- [[voice-cloning-reference]] · 另一种风格条件
