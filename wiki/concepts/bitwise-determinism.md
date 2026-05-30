---
name: bitwise-determinism
type: concept
sources: [interaction-models-tml]
updated: 2026-05-20
---

# Bitwise Determinism · 位级确定性

## 一句话
同样的输入，训练 kernel 和推理 kernel 跑出来的浮点数在**二进制位上完全相同**。

## 直觉
你以为浮点运算"一样的输入 = 一样的输出"。其实**不是**：
- GPU kernel 为了效率会改 reduce 顺序（先加哪两个）
- Tensor parallel 切分会让不同卡算的部分汇总顺序变
- 同一份代码跑两次，最后几位浮点可能不同

对推理影响不大（人感知不到末位差异）。但对 **RL 训练 + 长 session 对话**就是大坑：
- RL 训练时用一套训练 kernel 算梯度
- Rollout / sampling 时换一套推理 kernel
- 学到的 policy 行为分布 ≠ sampler 实际产生的分布 → 训练发散 / 不稳定

## TML 怎么做到
用 [[batch-invariant-kernel]] —— "对 batch 划分不敏感"的算子：
- 同一个样本无论跟谁同批，单独算出来的数值都一样
- 强制结果只依赖样本本身，不依赖同批 buddy
- 代价：~5% 性能损失（值得）

具体 kernel 改动包括：
- Attention 走固定的 [[split-kv]] 切法（prefill 和 decode 走同一种切，结果 bit-for-bit 一致）
- Reduce 走固定顺序的实现
- MoE 路由走可重现的 deterministic 实现

## 为什么 fish-speech 不需要这条
fish-speech 也做 [[grpo]] RL 对齐 —— 理论上同样会吃这个亏。猜测原因：
- fish-speech 用 SGLang 推理，推理基建相对固定
- TTS reward 信号相对短 horizon（一句话内），漂移容忍度高
- 而 TML 的对话 RL 是长 horizon + 多模态，bitwise 漂移会被放大

这条值得做成 thread 问一下：[[fish-speech-grpo-determinism-question]]

## 链接
- [[interaction-models-tml]] · 论文
- [[batch-invariant-kernel]] · 实现手段
- [[split-kv]] · Attention 的具体保 bit 手段
- [[grpo]] · RL 训练对它的依赖
- [[prefill-decode]] · 两阶段必须保 bit
