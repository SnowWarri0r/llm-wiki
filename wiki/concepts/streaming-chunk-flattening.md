---
name: streaming-chunk-flattening
type: concept
sources: [gander]
updated: 2026-09-11
---

# Streaming Chunk Flattening · 听到的、看到的、说出的，拍平进一条 token 流

## 一句话

按 1 秒切窗，每窗 = [感知 token + 控制 token + 文本 token]，串成单条因果序列，让模型每秒决定一次听还是说。

## 直觉

turn-based 对话里"用户说完"是一个特权信号，靠 VAD 判端点触发生成。拍平之后没有特权角色：外界输入只是持续被观测的世界状态，模型活在一个永远在线的环境里，**每个 chunk 都要回答"要不要出声"**——接话时机从外挂模块变成模型自己的自回归预测，能随模型智能一起变强。

## 怎么做的

- 每 1 秒组一个 chunk：该窗内到达的音频 token（≈10/s）+ 视觉 token，接一个**控制 token**，再接模型选择输出的 N 个文本 token（N 可以是 0）。chunk 依次拼接喂标准因果 LLM；窗内先看新感知再生成，保证每个输出 token 都以最新观测为条件。
- 控制 token 三选一：**listen**（本窗沉默继续观察）、**speak**（本窗要说话，后面的文本送去合成语音）、**interrupt**（掐掉自己没说完的话——用户开口了或场景变了）。控制先于内容：把"要不要说"和"说什么"解耦，比混在一步预测里更稳。
- 上下文固定 128 chunk ≈ 2 分钟滑窗，滚动淘汰最老的 chunk，长会话推理成本恒定。

## 数字例子

一场 96 秒的对话：96 个 chunk；模型若在其中 30 个 chunk 说话、语速被数据改写约到 8 token/s，文本输出 ≈ 30×8=240 token；其余 66 个 chunk 只出 1 个 listen token。同样 96 秒若让 LLM 直接自回归 50 帧/s 的语音 token，仅输出侧就是 96×50=4800 步——拍平+控制 token 把解码步数压了一个数量级。

## 链接

- [[gander]] — 本页机制的出处（其小脑）
- [[cerebellum-brain-collaboration]] — chunk 流之上的双层架构
- [[full-duplex-multimodal-interaction]] — 它服务的交互形态
- [[vad]] — 被它内化掉的外挂端点检测
