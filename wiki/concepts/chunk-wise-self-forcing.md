---
name: chunk-wise-self-forcing
type: concept
sources: [wan-animate-2]
updated: 2026-08-12
---

# Chunk-wise Self-Forcing · 整段定方向，分块算梯度

## 一句话

先让 score 网络看完整生成视频，再把生成器按块重放、累加梯度，兼顾长程质量与显存。

## 直觉

批改长作文时，老师先通读全文判断人物是否前后一致，再逐段标修改意见。若每段只看自己，省内存却看不见跨段漂移；若整篇同时反传，又容易撑爆显存。

## 怎么做的

1. **无梯度 rollout**：生成完整视频，记录每块最后一次带噪输入与最终干净输出。
2. **整段算方向**：重新加噪后，由 real-score 与 fake-score 网络看完整序列，得到 DMD 方向；这一步不保留生成器计算图。
3. **逐块重放**：一次只重放一个块，接上预先算好的 score 方向，得到该块对生成器参数的梯度。
4. **累加后更新**：块与块之间 detach，所有块梯度相加，只做一次参数更新。

\[
g=\sum_{i=1}^{M}\nabla_{\theta_s}L_i
\]

\[
\theta_s\leftarrow\theta_s-\eta g
\]

- <code>M</code>：视频被切成的块数；
- <code>L_i</code>：第 <code>i</code> 块的蒸馏损失；
- <code>\theta_s</code>：学生生成器参数；
- <code>g</code>：所有块累积出的总梯度；
- <code>\eta</code>：学习率。

## 数字例子

三块重放得到梯度 <code>g₁=0.4</code>、<code>g₂=−0.1</code>、<code>g₃=0.2</code>：

\[
g=0.4-0.1+0.2=0.5
\]

若当前参数 <code>θₛ=2</code>，学习率 <code>η=0.1</code>：

\[
\theta_s^{\mathrm{new}}=2-0.1\times0.5=1.95
\]

stop-gradient 不是把模型永久冻结；它只是让上一块的计算图在进入下一块前断开。当前块仍正常反向传播，最后三个块的梯度仍共同更新同一套参数。

## 链接

- [[wan-animate-2]] · 用于 8 帧分块的 Lite 模型
- [[dmd-distillation]] · real/fake score 差为什么能提供分布匹配方向
- [[teacher-forcing-video-diffusion]] · Self-Forcing 要修复的训练/推理错位
