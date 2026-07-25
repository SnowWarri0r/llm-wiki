---
name: conditional-flow-matching
type: concept
sources: [flow-matching, hierarchical-denoising-visual-reasoning]
updated: 2026-07-20
---

# Conditional Flow Matching · 条件流匹配

## 一句话
把难算的全局 velocity field 训练目标，换成"给定一对噪声和数据样本时该往哪走"的可监督回归。

## 直觉
真正想学的是：任意位置 `x_t`、任意时间 `t`，整个数据分布应该往哪流。这个目标要对所有可能的数据配对取平均，很难直接算。

Conditional Flow Matching 退一步：训练时先抽一对 `(noise, data)`，在这对之间造一条路径，然后让模型预测这条路径上的速度。论文证明这样训练出来的梯度方向等价于原目标，但工程上简单很多。

## 怎么做的
1. 采样噪声 `x0` 和数据 `x1`
2. 随机采样时间 `t`
3. 用路径公式得到中间点 `x_t`
4. 目标速度通常近似为从 `x0` 指向 `x1` 的方向
5. 模型输入 `(x_t, t, condition)`，回归速度

## 代码出处
Flow Matching 论文的核心训练目标；TML 用它解释音频输出 head 的选择。

## 链接
- [[flow-matching]] · 总概念
- [[velocity-field]] · 模型学的对象
- [[probability-path]] · 路径怎么选
- [[optimal-transport]] · 常见路径选择
