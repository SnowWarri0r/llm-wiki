---
name: dmd-distillation
type: concept
sources: [dmd, dmd2, senseflow, qwen-image-2, mrt, pid-pixel-diffusion, flux-1, krea-2, drifting-models]
updated: 2026-07-24
---

# DMD 蒸馏 · 匹配整批图像，不逐步临摹老师

## 一句话

DMD 用“老师目标分布的 score − 学生当前分布的 score”训练少步生成器；原始 DMD 是 **1 NFE**，4 步和 8 步来自后续 DMD 家族应用。

## 先拆掉一个混淆：DMD 不等于 4 步

**NFE（Number of Function Evaluations）**就是生成一张图调用神经网络多少次。原始论文 [[dmd]] 把 EDM 的 512 次前向或 Stable Diffusion 的 50 步蒸成一次前向。Qwen-Image、MRT、PiD 等后来把 DMD 或 DMD2 用成 4/8 步，那是同一家族的后续配置，不是原始论文的定义。

## 直觉

逐轨迹蒸馏要求同一份噪声 `z` 经过学生后，必须得到老师几十步采样的那张指定图片。一步学生很难完整拟合这张复杂映射。

DMD 放松成分布要求：不检查每张作品是不是逐笔临摹，只检查学生交来的一批图，在逼真度和多样性上是否像老师那批。它仍保留少量 `(z, 老师图 y)` 回归作为稳定器；“不逐样本强制对齐”不等于“完全没有配对数据”。

## 怎么做的

学生生成 `x=G_θ(z)`。DMD 在 `x` 上随机加噪，再让两套扩散去噪器估计 score：

- `s_real`：冻结老师给出的目标分布方向；
- `s_fake`：额外 fake-score 模型给出的学生当前分布方向；它每轮都用最新学生图继续训练。

生成器梯度的核心是：

\[
\nabla_\theta D_{\mathrm{KL}}\approx
\mathbb E\left[w_t\alpha_t
\left(s_{\mathrm{fake}}-s_{\mathrm{real}}\right)
\frac{\partial G_\theta}{\partial\theta}\right].
\]

梯度下降会减去它，所以最终效果是“吸向 real、离开 fake 已经堆得过密的区域”。只用 real score，很多样本可能全挤向最近的同一个模式；fake score 提供分散作用。

## 数字例子

设某次训练只有一个标量：`α=.8`，权重 `w=1.5`，real score `1.5`，fake score `.1667`，并令 `∂G/∂θ=1`：

```text
g = 1.5×.8×(.1667−1.5) = −1.6
θ_new = θ − .1×g = θ + .16
```

参数沿 real score 指向的方向增加。附录用伪损失把这个梯度塞进自动求导：

\[
L_{\mathrm{pseudo}}=\tfrac12
\left\|x-\operatorname{stopgrad}(x-g)\right\|_2^2.
\]

若 `x=1.2, g=-1.6`，冻结目标为 `2.8`，所以 `dL/dx=1.2-2.8=-1.6`，与预先算好的 `g` 完全一致。去掉 stopgrad 后左右两个 `x` 一起动，梯度会抵消。

## 原始 DMD、DMD2、SenseFlow、TDM 的边界

| 方法 | 匹配位置 | 原始回归配对集 | 典型步数 |
|---|---|---|---|
| DMD | 最终生成分布 | 需要，用来稳定和防漏模式 | 论文为 1 步 |
| DMD2 | 最终生成分布 | 主方法去掉大规模配对集；用 fake-score 高频更新与 GAN 补强。SDXL 一步仍用 10K 对短暂预热 | 1 步或多步 |
| SenseFlow | 同一 DMD2 主线 | 沿用无大规模配对主线；IDA 缩短 fake 追踪差、ISG 补段内时间监督、VFM 判别器补语义 | 主文为 4 步，附录扩到 2/1 步 |
| TDM | 去噪轨迹多个时刻的分布 | 取决于具体实现 | 灵活少步 |

## 链接

- [[dmd]] · 原论文完整公式、算法、配方、消融和局限
- [[dmd2]] · 去配对回归、5:1 fake-score 更新、真实图 GAN 与 backward simulation
- [[senseflow]] · 为什么 DMD2 搬到 8B / 12B flow 模型会失稳，以及 IDA / ISG / VFM 三处修补
- [[score-function]] · 对数密度梯度为什么是修改方向
- [[entropy-kl]] · DMD 最小化的反向 KL
- [[pushforward-distribution]] · 学生输出分布怎样由噪声和生成器共同决定
- [[lpips]] · 原始 DMD 的回归稳定器
- [[drifting-models]] · 同样有吸引/排斥结构，但实现不是两套扩散 score
- [[trajectory-distribution-matching]] · 从只看终点扩展到沿途多个时刻
