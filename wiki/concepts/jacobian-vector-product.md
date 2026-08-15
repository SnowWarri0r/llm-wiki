---
name: jacobian-vector-product
type: concept
sources: [rcm]
updated: 2026-08-12
---

# JVP · 只问模型沿这一条方向会怎样变

## 一句话

JVP 不展开完整 Jacobian，只计算输入沿指定方向移动时，输出的瞬时变化。

## 直觉

一张地形图在每个方向都有坡度。完整 Jacobian 像把东西南北所有坡度都测一遍；JVP 只问“我现在沿东北走，海拔每秒变多少”。连续时间一致性只需要老师轨迹这一条方向，因此不用构造巨大 Jacobian。

## 怎么做的

模型 \(F:\mathbb R^n\to\mathbb R^m\)，输入为 \(x\)，指定方向为 \(v\)：

\[
\operatorname{JVP}(F,x,v)=J_F(x)v
=\left.\frac{d}{d\epsilon}F(x+\epsilon v)\right|_{\epsilon=0}.
\]

- \(J_F(x)\)：输出每一维对输入每一维偏导组成的 \(m\times n\) Jacobian。
- \(v\)：输入移动方向，与 \(x\) 同形。
- \(J_F(x)v\)：输出沿 \(v\) 的方向导数，与模型输出同形。
- \(\epsilon\)：只用于定义“移动一丁点”的标量。

## 数字例子

令 \(F(x_1,x_2)=[x_1^2+x_2,\;3x_1-x_2]\)，在 \(x=[2,1]\) 沿 \(v=[1,-2]\) 移动。

\[
J_F(2,1)=\begin{bmatrix}4&1\\3&-1\end{bmatrix},\qquad
J_Fv=\begin{bmatrix}4&1\\3&-1\end{bmatrix}
\begin{bmatrix}1\\-2\end{bmatrix}
=\begin{bmatrix}2\\5\end{bmatrix}.
\]

用小步长 \(\epsilon=0.001\) 自检：

```text
F([2,1]) = [5,5]
F([2.001,.998]) ≈ [5.002001, 5.005]
(新−旧)/.001 ≈ [2.001,5] ≈ [2,5]  ✓
```

## 跟反向传播的对照

- JVP / forward mode：给定输入方向，求所有输出怎样变；适合“输入和输出同样大”的生成网络切线。
- VJP / reverse mode：给定输出方向，求所有输入或参数怎样受影响；普通反向传播主要用这一类。
- JVP 不是没有梯度。训练 rCM 时，JVP 先构造目标，参数更新仍会做反向传播。

## 链接

- [[rcm]] · 用 FlashAttention-2 JVP 把切线计算扩到 14B。
- [[continuous-time-consistency]] · 为什么连续一致性需要方向导数。
- [[flash-attention]] · rCM 把原值和切线一起分块流式计算。
- [[gradient-backprop]] · 与反向模式自动微分的关系。
