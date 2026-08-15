---
name: continuous-time-consistency
type: concept
sources: [rcm, causal-rcm]
updated: 2026-08-14
---

# 连续时间一致性 · 不逐步走完，也要认出同一个终点

## 一句话

同一条去噪轨迹上的任意带噪点，都应该被映射到同一个干净样本。

## 直觉

老师像导航软件，要用许多小步沿道路开到终点；一致性模型像记住“这条路最终通向哪里”，站在路上任一点都直接报出同一个终点。

离散 Consistency Model 比较相邻两个时间点的输出。连续时间版本把间隔缩到趋近于 0，不再真的造一个邻点，而是要求模型沿老师轨迹移动一丁点时，最终答案不变。

## 怎么做的

设带噪状态为 \(x_t\)，模型的终点预测为 \(f_\theta(x_t,t)\)。理想条件是：

\[
\frac{d}{dt}f_\theta(x_t,t)=0.
\]

总导数同时包含“输入沿轨迹变化”和“时间本身变化”：

\[
\frac{df}{dt}=\frac{\partial f}{\partial x}\frac{dx_t}{dt}+\frac{\partial f}{\partial t}.
\]

- \(t\)：噪声时间；越大通常越接近纯噪声。
- \(x_t\)：时间 \(t\) 的带噪 latent。
- \(dx_t/dt\)：老师速度场给出的轨迹方向。
- \(\partial f/\partial x\)：输入改一点，终点预测怎样变。
- \(\partial f/\partial t\)：输入不动，只改时间标签时，预测怎样变。

这条链式法则怎么来的：时间前进 dt 的瞬间两件事同时发生——位置沿轨迹滑了 \(dx=(dx_t/dt)\,dt\)，时间标签自己 +dt。对 f 做一阶泰勒展开：

\[
f(x+dx,\ t+dt)\approx f(x,t)+\frac{\partial f}{\partial x}dx+\frac{\partial f}{\partial t}dt.
\]

两边减去 \(f(x,t)\)、除以 dt，就是上面的总导数——变化从两扇门进来（输入动一扇、时间标签动一扇），一阶近似下贡献相加。

而「=0」不是恒等式，是把一致性强加成微分语言：离散 CM 要求 \(f(x_{t-\Delta t},t-\Delta t)=f(x_t,t)\)，两边相减、除以 \(\Delta t\)、令 \(\Delta t\to0\)，正是 \(df/dt=0\)。「沿轨迹答案恒定」等价于「沿轨迹总变化率为零」；训练就是逼 \(f_\theta\) 满足它，不是它天然成立。

## 数字例子

用一个教学函数 \(f(x,t)=x-2t\)，老师轨迹为 \(x_t=1+2t\)：

```text
沿轨迹代入：f(x_t,t)=(1+2t)-2t=1
所以无论 t=.2 还是 t=.8，终点预测都是 1。

∂f/∂x=1，dx/dt=2，∂f/∂t=-2
df/dt=1×2+(-2)=0  ✓
```

这就是“一致”：位置门 +2（位置沿轨迹往上漂，推着答案变大）和时间门 −2（时间标签变大，扣掉更多掺入的噪声）恰好抵消，终点答案钉在 1。完美的一致性函数，两扇门永远这样对消。

## 链接

- [[rcm]] · 扩到 14B 视频模型，并用 score regularization 修误差。
- [[jacobian-vector-product]] · 高效计算上式里的方向导数。
- [[velocity-field]] · 提供轨迹方向 \(dx_t/dt\)。
- [[causal-consistency-distillation]] · 因果流式视频里的对应版本。
