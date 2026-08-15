---
name: hybrid-text-audio-system-prompt
type: concept
sources: [personaplex]
updated: 2026-08-12
---

# Hybrid Text–Audio System Prompt · 文字与声音合成一条系统提示

## 一句话

在实时对话开始前，先让语音模型听一小段“以后用这个声音说”的参考音频，再读一段“你是谁、该怎样回应”的角色说明。

## 直觉

像给演员两张说明卡：第一张是配音样带，管音色；第二张是角色小传，管身份和行为。两张卡都在正式开拍前交给同一个演员，后面的每一句话同时受二者影响。

## 怎么做

PersonaPlex 把 prompt 沿时间拼成两段：

1. voice prompt 段：agent 音频流放参考声音，agent 文字流放 PAD；
2. text prompt 段：agent 文字流放角色说明，agent 音频流放静音；
3. user 音频流在两段 prompt 中都放固定 440 Hz 占位信号；
4. 分隔 token 标记 prompt 结束，随后才进入真实对话；训练时 prompt 本身不计 loss。

## 数字例子

假设参考音频 2 秒、角色说明编码后需要 25 个 80 ms 帧：

- 声音段占 `2 / 0.08 = 25` 帧；
- 文字段再占 25 帧；
- 正式对话从第 51 帧开始。

固定角色可把前 50 帧的 prompt 状态预先算好并缓存；真正来电话时直接从对话边界继续。

## 边界

论文只说 440 Hz 占位让条件更稳定，没有给“为什么一定是 440 Hz”的消融；不能把它讲成已被证明的最优频率。

## 链接

- [[personaplex]] · 来源
- [[voice-cloning-reference]] · 参考声音怎样提供音色条件
- [[full-duplex-multimodal-interaction]] · prompt 之后怎样持续边听边说
