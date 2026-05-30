---
name: optimal-transport
type: concept
sources: [flow-matching]
updated: 2026-05-22
---

# Optimal Transport · 最优传输

## 一句话
在生成模型里，OT path 可以理解成让噪声分布搬到数据分布时尽量少绕路。

## 直觉
想象把一堆沙从左边搬成右边的形状。随便搬也能成功，但会绕路、浪费力气；optimal transport 问的是：怎么搬总体代价最小。

Flow Matching 用 OT 风格路径时，噪声到数据更接近直线，所以推理 ODE 往往可以少走几步。

## 怎么做的
- 给每个噪声点和数据点建立配对或近似配对
- 让中间状态沿配对方向插值
- 模型学习这条路径上的 [[velocity-field]]
- 推理时从噪声沿学到的场积分到数据

## 代码出处
Flow Matching 论文把 OT path 作为重要概率路径之一讨论。

## 链接
- [[probability-path]] · OT 是路径选择之一
- [[flow-matching]] · 用路径训练生成模型
- [[ode-vs-sde]] · OT flow 属于确定性 ODE 思路
