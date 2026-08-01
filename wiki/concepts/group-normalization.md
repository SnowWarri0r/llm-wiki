---
name: group-normalization
type: concept
sources: [diffusion-unet]
updated: 2026-07-27
---

# Group Normalization · 分组归一化

## 一句话

不借同 batch 里别人的统计量；每个样本自己把通道分组，每组算均值和方差，再归一化。

## 为什么扩散 U-Net 爱用它

高分辨率生成很吃显存，单卡 batch 往往很小。BatchNorm 用整批样本估计均值与方差，小 batch 下容易抖；GroupNorm 只看当前样本，所以 batch 是 1 也能照常算。

## 原始定义

把某个样本的一组元素记为 \(S\)：

\[
\mu=\frac{1}{|S|}\sum_{i\in S}x_i,\qquad
\sigma^2=\frac{1}{|S|}\sum_{i\in S}(x_i-\mu)^2
\]

\[
\widehat x_i=\frac{x_i-\mu}{\sqrt{\sigma^2+\varepsilon}}
\]

\(|S|\) 是这组元素数；\(\varepsilon\) 是防止除零的小常数。之后还有可学习的缩放 \(\gamma\) 与平移 \(\beta\)：

\[
y_i=\gamma_i\widehat x_i+\beta_i
\]

## 数字例子

取一组两数 \(x=[1,3]\)：

\[
\mu=(1+3)/2=2
\]

\[
\sigma^2=((1-2)^2+(3-2)^2)/2=1
\]

暂时忽略很小的 \(\varepsilon\)：

\[
\widehat x=[(1-2)/1,(3-2)/1]=[-1,1]
\]

若 \(\gamma=2,\beta=0.5\)：

\[
y=2[-1,1]+0.5=[-1.5,2.5]
\]

自检：归一化后的 \([-1,1]\) 均值是 0，方差是 1。

## 跟扩散时间条件的关系

ADM 不把 \(\gamma,\beta\) 固定死，而是让时间 / 类别嵌入生成每个 block 的 scale 与 shift。于是同一份空间特征在高噪声与低噪声时会被不同地调制。详见 [[diffusion-timestep-conditioning]]。

## 链接

- [[diffusion-unet]] · GN 在扩散 ResBlock 里的位置
- [[batchnorm]] · 用 batch 统计量的另一种归一化
- [[adaptive-layernorm]] · DiT 里同类的条件调制思路
