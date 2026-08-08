---
name: tor-alignment
type: concept
sources: [videofdb]
updated: 2026-08-06
---

# TOR-Alignment · 不只看“抢没抢话”，还看这次应不应该抢

## 一句话

先按对话动态规定本次应该保持安静、继续说、让出、接棒还是短附和，再统计系统行为与规则相符的样本比例。

## 为什么普通 takeover rate 不够

低 takeover rate 对“用户还在思考”是好事，对“用户已经交棒”却是坏事。把所有场景的抢话率直接平均，会把相反目标混在一起。

## 公式

第 \(i\) 条样本实际是否完整拿走话轮记为 \(TO_i\in\{0,1\}\)，所属规则的期望记为 \(TO^*_{c_i}\)。

\[
A_i=\mathbf 1[TO_i=TO^*_{c_i}],\qquad
\mathrm{TOR\!\text{-}Alignment}=\frac1N\sum_{i=1}^{N}A_i.
\]

\(c_i\) 是第 \(i\) 条所属的 timing class；\(A_i\) 是是否匹配的指示量；\(N\) 是总样本数。五条里四条符合，得分就是 80%。

## 它仍然没覆盖什么

二值规则无法完整描述语气、内容质量和动作自然度；同为“及时让出”，200 ms 和 1400 ms 的体验也不同。因此应同时报告 alignment、延迟和 rubric 分数。

## 链接

- [[videofdb]] · 五种 timing class、阈值与模型结果
- [[conversational-nonverbal-dynamics]] · 为什么不同视觉信号要求不同话轮策略
- [[rubric-based-evaluation]] · 时序通过率之外的质量拆分
