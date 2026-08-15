---
name: asyncpatch-timestep-sampling
type: concept
sources: [asyncpatch-diffusion]
updated: 2026-08-14
---

# AsyncPatch Timestep Sampling · 先选全局噪声，再分配局部时钟

## 一句话

不让每个 patch 在 \([0,1]\) 各抽各的，而是先均匀抽一个全图平均时刻 \(\bar t\)，再在以 \(\bar t\) 为中心的对称区间内给各 patch 抽时刻。

## 为什么独立均匀抽反而不够自由

若 \(M\) 个 patch 的 \(t_i\) 都独立服从 \(U(0,1)\)，单个时刻的方差是 \(1/12\)，样本均值的方差则是：

\[
\begin{aligned}
\operatorname{Var}(\bar t)&=\frac{1}{12M},\\
\operatorname{Std}(\bar t)&=\frac{1}{\sqrt{12M}}
\end{aligned}
\]

- \(M\)：patch 数量。
- \(t_i\)：第 \(i\) 块的噪声时刻。
- \(\bar t=M^{-1}\sum_i t_i\)：这张图的 patch 平均时刻。
- \(\operatorname{Var}\)：方差，衡量平均值的波动平方。
- \(\operatorname{Std}\)：标准差，回到与时刻相同的量纲。

当 \(M=64\) 时，标准差只有 \(\sqrt{1/768}\approx.036\)。因此平均时刻经常在 \(0.5\pm0.07\) 附近，很少跑到接近 0 或 1 的区域。

## 采样公式

\[
\begin{aligned}
\bar t&\sim U(t_{\min},t_{\max}),\\
\delta&=\min(\bar t-t_{\min},\ t_{\max}-\bar t,\ .5),\\
t^-&=\bar t-\delta,\qquad t^+=\bar t+\delta,\\
t_i&\sim U(t^-,t^+).
\end{aligned}
\]

- \(t_{\min},t_{\max}\)：允许的时刻范围，常可看成 0 到 1。
- \(\bar t\)：先均匀抽到的全图中心时刻。
- \(\delta\)：从中心向左右能对称张开的半宽；不越界，也不超过 0.5。
- \(t^-,t^+\)：本张图各 patch 可使用的最小、最大时刻。
- \(U(a,b)\)：区间 \([a,b]\) 上的均匀分布。

## 两组数字

~~~text
全局偏干净：bar_t=.25
delta=min(.25,.75,.5)=.25
各 patch 从 [0,.5] 抽，区间中心是 .25

全局偏噪：bar_t=.80
delta=min(.80,.20,.5)=.20
各 patch 从 [.60,1] 抽，区间中心是 .80
~~~

这样既能看到整体很干净 / 很噪的图，又保留同一张图内的局部时刻差。严格说，独立抽出的有限个 \(t_i\) 的样本均值会在 \(\bar t\) 周围波动；对称区间保证的是期望中心。

## 链接

- [[asyncpatch-diffusion]] · 给出这个采样器的论文
- [[joint-diffusion]] · 这些时刻怎样变成联合加噪状态
- [[diffusion-timestep-conditioning]] · 时刻条件如何进入去噪网络
