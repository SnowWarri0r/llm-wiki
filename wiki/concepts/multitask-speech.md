---
name: multitask-speech
type: concept
sources: [whisper]
updated: 2026-05-25
---

# Multitask Speech · 一个模型干多件事

## 一句话
Whisper 一个模型同时做语音转录、语音翻译、语言识别、时间戳对齐 —— 全靠输入序列里的**特殊 token** 区分任务，不改架构。

## 直觉
以前 ASR 系统是一个任务一个模型（识别用一个、翻译用一个、语言检测用一个）。Whisper 把所有任务塞进同一个 encoder-decoder —— 怎么做到的？

核心思路跟 GPT 系列一脉相承：**用输入格式编码任务**。

Whisper 的 decoder 输入序列长这样：

```
<|startoftranscript|> <|zh|> <|transcribe|> <|notimestamps|> 你好世界<|endoftext|>
```

```
<|startoftranscript|> <|zh|> <|translate|> <|notimestamps|> hello world<|endoftext|>
```

第一条：中文语音 → 转录中文文字。
第二条：中文语音 → 翻译成英文。

**唯一差别是 `<|transcribe|>` 换成了 `<|translate|>`** —— 同一个模型，同一份权重，靠这个 token 切换任务。

## 怎么做的

| 特殊 token | 作用 |
|---|---|
| `<\|startoftranscript\|>` | 序列开始 |
| `<\|zh\|>` / `<\|en\|>` / ... | 语言标签（99 种语言） |
| `<\|transcribe\|>` | 任务 = 语音转文字（保持原语言） |
| `<\|translate\|>` | 任务 = 语音翻译成英文 |
| `<\|notimestamps\|>` | 不输出时间戳 |
| `<\|0.00\|>` `<\|0.50\|>` ... | 时间戳 token（每 30ms 一个） |
| `<\|endoftext\|>` | 序列结束 |

训练时所有任务的数据混在一起，模型学会根据开头的 token 组合决定"这次要干嘛"。

## 为什么这种设计好

1. **共享表示**：语音识别和语音翻译共享 encoder —— 学到的语音特征能同时服务两个任务
2. **零额外架构**：不需要给每个任务加 head，所有输出都是 text token
3. **组合灵活**：新语言 / 新任务只需加新的 special token + 训练数据
4. **跟 GPT 输入格式思路一致**：[[input-transformations]]（GPT-1 那篇）就是用文本格式编码任务结构的鼻祖

## 链接
- [[whisper]] · 论文
- [[input-transformations]] · GPT-1 的任务格式编码
- [[transformer-architecture]] · encoder-decoder 架构
