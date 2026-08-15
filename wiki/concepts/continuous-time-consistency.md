---
name: continuous-time-consistency
type: concept
sources: [rcm]
updated: 2026-08-12
---

# 连续时间一致性 · 不逐步走完，也要认出同一个终点

## 一句话

同一条去噪轨迹上的任意带噪点，都应该被映射到同一个干净样本。

## 直觉

老师像导航软件，要用许多小步沿道路开到终点；一致性模型像记住“这条路最终通向哪里”，站在路上任一点都直接报出同一个终点。

离散 Consistency Model 比较相邻两个时间点的输出。连续时间版本把间隔缩到趋近于 0，不再真的造一个邻点，而是要求模型沿老师轨迹移动一丁点时，最终答案不变。

## 怎么做的

设带噪状态为 (x_t)，模型的终点预测为 (f_\theta(x_t,t))。理想条件是：

\[
\frac{d}{dt}f_\theta(x_t,t)=0.
\]

总导数同时包含“输入沿轨迹变化”和“时间本身变化”：

\[
\frac{df}{dt}=\frac{\partial f}{\partial x}\frac{dx_t}{dt}+\frac{\partial f}{\partial t}.
\]

- (t)：噪声时间；越大通常越接近纯噪声。
- (x_t)：时间 `t` 的带噪 latent。
- (dx_t/dt)：老师速度场给出的轨迹方向。
- (\partial f/\partial x)：输入改一点，终点预测怎样变。
- (\partial f/\partial t)：输入不动，只改时间标签时，预测怎样变。

## 数字例子

用一个教学函数 (f(x,t)=x-2t)，老师轨迹为 (x_t=1+2t)：

```text
沿轨迹代入：f(x_t,t)=(1+2t)-2t=1
所以无论 t=.2 还是 t=.8，终点预测都是 1。

∂f/∂x=1，dx/dt=2，∂f/∂t=-2
df/dt=1×2+(-2)=0  ✓
```

这就是“一致”：状态在变，时间也在变，但两种变化恰好抵消，终点答案不变。

## 链接

- [[rcm]] · 扩到 14B 视频模型，并用 score regularization 修误差。
- [[jacobian-vector-product]] · 高效计算上式里的方向导数。
- [[velocity-field]] · 提供轨迹方向 (dx_t/dt)。
- [[causal-consistency-distillation]] · 因果流式视频里的对应版本。
