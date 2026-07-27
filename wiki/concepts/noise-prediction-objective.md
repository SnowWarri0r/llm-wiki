---
name: noise-prediction-objective
type: concept
sources: [diffusion-unet, dit]
updated: 2026-07-27
---

# Noise Prediction Objective · 让网络猜“刚才加进去的噪声”

## 一句话

训练时自己往干净样本里加一份已知高斯噪声，再让网络把这份噪声猜回来；因为标签是自己造的，不需要人工标注。

## 加噪公式

\[
x_t=\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon
\]

- \(x_0\)：干净样本；
- \(t\)：随机抽到的噪声时刻；
- \(\bar\alpha_t\)：到时刻 \(t\) 还保留多少信号的累计系数；
- \(\epsilon\sim\mathcal N(0,I)\)：本次实际加入的标准高斯噪声；
- \(x_t\)：带噪样本。

网络 \(\epsilon_\theta(x_t,t,c)\) 接收带噪样本、时刻和可选条件 \(c\)，预测噪声：

\[
\mathcal L=\mathbb E\left[\left\|\epsilon_\theta(x_t,t,c)-\epsilon\right\|_2^2\right]
\]

\(\theta\) 是网络参数；期望表示对图片、时刻和噪声反复抽样求平均；平方范数就是各位置误差平方后相加或取平均。

## 数字例子

令 \(x_0=2\)、\(\bar\alpha_t=0.64\)、\(\epsilon=-0.5\)：

\[
x_t=0.8\times2+0.6\times(-0.5)=1.3
\]

若网络预测 \(\widehat\epsilon=-0.3\)：

\[
\mathcal L=(-0.3-(-0.5))^2=0.2^2=0.04
\]

预测噪声还能反推出干净值：

\[
\widehat x_0=
\frac{x_t-\sqrt{1-\bar\alpha_t}\widehat\epsilon}{\sqrt{\bar\alpha_t}}
=\frac{1.3-0.6\times(-0.3)}{0.8}
=1.85
\]

若 \(\widehat\epsilon=-0.5\) 完全猜对：

\[
\widehat x_0=(1.3+0.3)/0.8=2
\]

正好回到原值，算术闭环。

## 它和网络骨架是两回事

U-Net、DiT 都能训练这个目标。网络回答“拿什么结构预测”，目标回答“让它预测什么”。后来的模型也会改成预测 \(x_0\) 或速度 \(v\)，骨架不必跟着换。

## 链接

- [[diffusion-unet]] · 用 U 形卷积网络预测噪声
- [[dit]] · 换成 Transformer 仍能预测同一个目标
- [[flow-matching]] · 改成预测速度场的另一套训练目标
- [[ode-vs-sde]] · 不同采样器怎样使用网络输出

