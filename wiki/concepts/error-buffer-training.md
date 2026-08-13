---
name: error-buffer-training
type: concept
sources: [wan-animate-2]
updated: 2026-08-12
---

# Error Buffer Training · 把模型会犯的小错加回训练历史

## 一句话

缓存模型预测与真值的残差，再用残差污染干净历史，让训练输入更像推理时自己的输出。

## 直觉

Teacher Forcing 像练车时永远给你一条完美直路，推理却要沿自己刚刚压歪的车辙继续开。Error Buffer 把以前压歪的幅度记下来，训练下一段时故意把历史稍微挪歪。

## 怎么做的

用一种常见且与论文描述一致的符号写法：

\[
e=\hat x_0-x_0
\]

\[
\tilde x_0=x_0+e
\]

- \(x_0\)：真实干净历史；
- \(\hat{x}_0\)：模型的一步预测；
- <code>e</code>：预测残差，存入缓冲区；
- \(\tilde{x}_0\)：加入旧残差后、用于后续训练的历史。

论文只说明缓冲区维护运行中的误差分布，没有公开容量、更新频率、采样方法或残差缩放系数；上式用于解释机制，不冒充缺失的实现配方。

## 数字例子

真实历史特征为 \(x_0=100\)，模型的一步预测是 <code>97</code>：

\[
e=97-100=-3
\]

\[
\tilde x_0=100+(-3)=97
\]

下一块训练看到的是 97，而不是过于理想的 100；这更接近推理时“模型只能读取自己上一块输出”的情况。

## 跟 Self-Forcing 的区别

Error Buffer 仍以真实历史为底，只叠加旧误差，便宜而稳定；Self-Forcing 会真正让模型连续读取自己的完整生成结果，更贴近推理但计算更贵、训练也更难。

## 链接

- [[wan-animate-2]] · Lite 模型 Teacher Forcing 阶段的修补
- [[teacher-forcing-video-diffusion]] · 为什么训练/推理历史不一致
- [[chunk-wise-self-forcing]] · 后续更彻底的自生成历史训练
