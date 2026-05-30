---
name: open-questions
type: thread
sources: [fish-speech-s2-pro, interaction-models-tml]
updated: 2026-05-20
---

# 待回答的问题（attached: 每个都该新开一页）

按"看了什么源、还不懂什么"的清单。每条之后展开成自己的 thread 页。

## 来自 TML interaction models

- **200ms 是怎么选出来的**？有没有 ablation 测过 100ms / 400ms 的手感差异？
- **Flow matching ODE 推理步数**？200ms 预算内能跑几步？质量曲线？
- **Background model 怎么训**？双模型共享 context 意味着两个权重模块要怎么联训？还是 background 单独 finetune？
- **MoE 在小 batch 下 gather+gemv vs grouped GEMM 的盈亏点**？什么 batch size 是分界？
- **新基准的 reproducibility**：他们的 TimeSpeak / CueSpeak 题怎么构造？开源吗？

## 来自 fish-speech

- **慢/快 AR 的连接点是 hidden state 还是 logits**？读代码确认。
- **GRPO 的多维 reward 怎么组合**？加权求和 / 多目标 Pareto / 分阶段？
- **[[bitwise-determinism]] fish-speech 不要求？**RL 训练时怎么处理 train/inference kernel 不一致？
- **支持 80+ 语言不用 phonemizer**：是因为 RVQ codec 自动学了发音映射，还是有别的对齐机制？
- 我自己跑：`fish_speech/models/` 目录怎么布局，主入口是哪个

## 跨源问题

- 如果做 **end-to-end 实时语音 AGI**，应该把 fish-speech 风格的 RVQ Dual-AR 怎么改造接入 TML 风格的 micro-turn？
- 双模型 vs 双 AR：哪种"两层"思路更通用？做 agent 工具时该参考哪种？

## 链接
- [[interaction-models-tml]]
- [[fish-speech-s2-pro]]
- [[audio-tokenization-rvq-vs-flow]]
- [[replace-heuristics-with-weights]]
