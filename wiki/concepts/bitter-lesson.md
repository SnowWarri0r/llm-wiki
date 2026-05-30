---
name: bitter-lesson
type: concept
sources: [replace-heuristics-with-weights, vit]
updated: 2026-05-28
---

# Bitter Lesson · 苦涩教训

## 一句话
长期看，能利用算力和数据持续 scale 的学习方法，会吃掉大量人手写规则。

## 直觉
工程师很容易给系统塞聪明规则：语音先 VAD、图像先手工特征、语言先语法树。短期有效，长期常被更大模型+更多数据超过。苦涩之处在于：很多漂亮的人类洞察，最后输给了通用学习系统的规模化。

这不是说规则没用，而是规则最好变成轻量归纳偏置，而不是锁死系统能力的主干。

## 怎么做的
- 保留便宜、稳定、明显有用的预处理，比如 [[dmel]] / [[hmlp]]
- 把语义判断、交互策略、跨模态对齐交给主模型学习
- 评估一个手写模块时问：模型 scale 后它会不会变成瓶颈？

## 代码出处
源自 Rich Sutton 的 "The Bitter Lesson" 思想；当前 wiki 用它解释 [[replace-heuristics-with-weights]]。

## 链接
- [[replace-heuristics-with-weights]] · 本 wiki 的工程化表达
- [[early-fusion]] · 轻预处理 + 主模型学习
- [[vad]] · 被模型化交互替代的规则模块
