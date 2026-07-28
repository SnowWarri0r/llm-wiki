---
name: causal-consistency-distillation
type: concept
sources: [minwm]
updated: 2026-07-24
---

# Causal Consistency Distillation · 不存整条 ODE 轨迹也能学少步

## 一句话

让学生在相邻两个噪声时刻给出同一个干净视频段：左边由当前学生预测，右边由 EMA 学生接住老师走过的一小步；这样在线产生监督，不必预先保存大量 ODE 中间 latent。

## 它要替代什么

少步学生原本可以用离线 ODE 数据训练：先让慢速因果老师跑完整去噪轨迹，把每个中间状态存盘；之后学生学习从指定中间状态直接跳到干净结果。问题是生成和保存轨迹都很贵。

一致性蒸馏只现场做老师的一小步：

\[
\mathcal L_{\mathrm{CD}}=
\mathbb E\left[
w(t)\,
d\!\left(
G_\theta(x_t^i,x_{\mathrm{gt}}^{<i},t),
G_{\theta^-}(\hat x_{t-\Delta t}^i,x_{\mathrm{gt}}^{<i},t-\Delta t)
\right)
\right].
\]

- `i`：当前自回归视频段；
- \(x_t^i\)：当前段在噪声时刻 `t` 的状态；
- \(x_{\mathrm{gt}}^{<i}\)：当前段之前的真实干净历史；
- \(\hat x_{t-\Delta t}^{i}\)：因果老师从 \(t\) 沿 ODE 走一小步得到的状态；
- \(G_\theta\)：正在训练的学生；
- \(G_{\theta^-}\)：学生参数的 EMA 副本，作为停止梯度的稳定目标；
- `w(t)`：不同噪声时刻的权重；
- `d`：距离函数，例如平方误差。

## 一个标量例子

若当前学生预测 `.60`，EMA 目标预测 `.55`，距离取平方差，且 `w(t)=2`：

```text
L = 2 × (.60 − .55)²
  = 2 × .0025
  = .005
```

学生被要求在两个相邻时刻都指向同一个干净结果。EMA 目标只提供靶子，不随这一项损失一起反向传播，否则靶子也会跟着学生同时移动。

## 代价没有消失，只是换了位置

离线 ODE 把老师计算提前做完并占用磁盘；causal CD 在训练时在线调用老师和 EMA 学生，省存储、少数据准备，但每个训练 step 的模型调用更多。

## 链接

- [[minwm]] · Stage 2a 与 2b 的完整取舍
- [[ema]] · \(\theta^{-}\) 为什么比当前参数更适合当目标
- [[ode-vs-sde]] · 一小步 ODE 到底是什么意思
- [[teacher-forcing-video-diffusion]] · 公式里的真实历史从哪里来
