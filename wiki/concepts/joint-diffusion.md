---
name: joint-diffusion
type: concept
sources: [asyncpatch-diffusion]
updated: 2026-08-14
---

# Joint Diffusion · 每个位置单独加噪，网络仍联合看全图

## 一句话

普通扩散给整张图一个噪声时刻；联合扩散给第 \(i\) 个空间单元自己的 \(t_i\)，却仍用一个网络同时读全部单元，所以它学到的是联合分布，不是一堆互不相干的局部去噪器。

## 前向加噪

把图像或 latent 展开成 \(N\) 个空间 token：

\[
\begin{aligned}
\mu_i&=\alpha_{t_i}x_i,\\
v_i&=\sigma_{t_i}^{2},\\
q_i&=\mathcal N(z_{i,t_i};\mu_i,v_iI),\\
q(\mathbf z_{\mathbf t}\mid\mathbf x)&=\prod_{i=1}^{N}q_i
\end{aligned}
\]

- \(\mathbf x=(x_1,\dots,x_N)\)：干净图像的 \(N\) 个 token。
- \(\mathbf t=(t_1,\dots,t_N)\)：时刻场；第 \(i\) 个 token 使用 \(t_i\)。
- \(z_{i,t_i}\)：第 \(i\) 个 token 加噪后的状态。
- \(\alpha_{t_i}\)：该位置保留的干净信号系数。
- \(\sigma_{t_i}\)：该位置的噪声系数。
- \(\mu_i,v_i\)：只是把该位置的高斯均值与方差暂时缩写，分别等于 \(\alpha_{t_i}x_i\) 和 \(\sigma_{t_i}^{2}\)。
- \(q_i=q(z_{i,t_i}\mid x_i,t_i)\)：第 \(i\) 个位置的局部加噪分布简称。
- \(I\)：单位协方差，表示加入标准独立高斯噪声。
- \(\prod_i\)：给定干净图后，前向噪声按 token 独立采样。

“前向独立”不等于“反向也独立”。网络在预测第 \(i\) 个位置的 score 时，输入是整个 \(\mathbf z_{\mathbf t}\)；它可以用已经干净的左半边帮助去噪右半边。

## 四格数字例

设四个 token 的时刻为 \([0,0,.8,.8]\)。前两格保持干净，后两格高度加噪。若干净值是 \([2,1,4,3]\)，且玩具日程在 \(t=.8\) 取 \(\alpha=.6,\sigma=.8\)，后两格噪声取 \([-1,.5]\)：

~~~text
前两格：t=0 → [2, 1]
第三格：.6×4 + .8×(-1) = 1.6
第四格：.6×3 + .8× .5   = 2.2
联合输入：[2, 1, 1.6, 2.2]
~~~

网络不是只看 1.6 猜第三格；它看完整的四格布局再给第三格修改方向。补图能成立，靠的就是这个“噪声独立、预测联合”。

## 链接

- [[asyncpatch-diffusion]] · 把这个定义做成可训练的采样器和 U-Net
- [[score-function]] · 为什么 score 是与输入同形的修改方向
- [[diffusion-timestep-conditioning]] · 从单一时刻条件到空间时刻场
