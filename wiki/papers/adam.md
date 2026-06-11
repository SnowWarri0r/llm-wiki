---
name: adam
type: paper
source: https://arxiv.org/abs/1412.6980
ingested: 2026-06-11
authors: [Diederik P. Kingma, Jimmy Ba]
year: 2014
---

# Adam · 自适应矩估计优化器

## 一句话
给梯度记两个 EMA——一阶动量 m（记方向、抹抖）+ 二阶 v（梯度平方的 EMA，记大小），更新量 = lr·m̂/(√v̂+ε)，每个参数都拿到自己的自适应步长。动量 + RMSprop 合体，几乎不用调参，Transformer/LLM 默认优化器。

## 它要解决的痛点
SGD 一个全局学习率走天下，在"窄沟"loss 地形里：陡方向步子相对太大→来回弹，平方向步子相对太小→爬得慢。一个 lr 没法同时适配陡和平。

## 核心贡献
- **一阶动量 m = 梯度的 [[ema]]**（β1=0.9）：平滑方向，一致累积、抖动相消（=带惯性的重球）。
- **二阶 v = 梯度平方的 EMA**（β2=0.999）：每参数最近梯度多大；更新除 √v → 逐参数自适应步长（来自 RMSprop）。
- **bias correction**：m、v 从 0 起步早期偏小，各除 (1−βᵗ) 修正；t 大了自动消失。
- **更新**：`θ ← θ − lr·m̂/(√v̂+ε)`，默认 ε=1e-8。
- **AdamW**：解耦 weight decay，Transformer/LLM 默认。

## 关键概念 → 概念页
- [[ema]] · Adam 的两个矩都是梯度的 EMA
- [[cross-entropy]] · 它优化的损失之一（分类/LLM）

## 我的批注 / 疑问
- Adam 就是 EMA 的两连击：一个滚梯度(方向)、一个滚梯度平方(大小)，前者除后者。记牢"m 管往哪走、√v 管走多大、bias 修刚起步别太怂"。
- 跟我学的串起来：[[dino]] 的 teacher/center 也是 EMA、BatchNorm running 也是 EMA——同一个滚动平均到处复用。
- 待查：AdamW 的解耦 weight decay 具体跟 L2 正则差在哪（数学上为什么"解耦"更对）。
