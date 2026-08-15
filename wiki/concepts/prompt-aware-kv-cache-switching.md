---
name: prompt-aware-kv-cache-switching
type: concept
sources: [interactive-avatar]
updated: 2026-08-12
---

# 提示词感知的 KV cache 切换 · 指令变了，邻近视频块的缓存也要换

## 一句话

提示词不变就复用旧 KV；提示词改变时，只把受旧提示影响的相邻视频块重新加噪、重算 KV，参考帧与长期记忆缓存继续保留。

## 直觉

KV cache 像把上一段计算写成备忘录。模型一直在“坐着聊天”时，继续读旧备忘录很省事；突然收到“站起来拿书”，旧邻块的内部特征仍带着“坐着”的条件，直接复用会拖慢新动作出现。

## 怎么做的

同一提示词连续生成时，参考块、相邻块、短期记忆和长期记忆的缓存都复用。提示词从旧值切到新值时：

1. 保留参考块和两类 memory cache；
2. 丢弃受旧提示影响的相邻生成块 KV；
3. 把已经生成的邻块 latent 重新加到当前噪声等级；
4. 与当前待去噪 latent、新文字条件一起前向，重算邻块 KV；
5. 后续块读取新 cache。

论文把结果简写成

\[
\mathcal K\leftarrow\operatorname{Replace}(\mathcal K_{\mathrm{old}},\mathcal K_{\mathrm{new}}).
\]

这只是状态更新记号，不是一条训练损失。

## 数字例子

设当前上下文包含参考块 R、两个邻块 A/B、短期记忆 S、长期记忆 L，共 5 组 cache。提示词未变时 5 组全复用；提示词改变时只重算 A/B：

```text
全量重算：R + A + B + S + L = 5 组
选择重算：    A + B         = 2 组
少重算：5 − 2 = 3 组，占原 60%
```

这不是论文的实际毫秒数，只展示“为什么选择性刷新比全量刷新便宜”。论文没有报告 cache switching 单独节省多少毫秒；消融表里的 FPS 也不能代替动作启动延迟。

## 跟普通 KV cache 的区别

普通 KV cache 只问“前缀算过没有”。提示词感知切换还要问“这份前缀表示是在什么条件下算的”。输入 token 没变，也可能因为文字条件变了而需要刷新隐藏状态与 K/V。

## 链接

- [[interactive-avatar]] · Cache-Switching 的来源
- [[kv-cache]] · 普通 Transformer cache 的基础
- [[block-causal-attention]] · 当前块能读取哪些历史块
