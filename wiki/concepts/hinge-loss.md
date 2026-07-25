---
name: hinge-loss
type: concept
sources: [senseflow]
updated: 2026-07-24
---

# Hinge Loss · 过了安全边界就不再追

## 一句话

Hinge loss 不要求真假 logit 无限增大或减小；真实样本到 `+1`、假样本到 `-1` 后，这一项损失就归零。

## 判别器的两条式子

\[
\begin{aligned}
\ell_{\mathrm{real}}&=\max(0,1-D(x_{\mathrm{real}})),\\
\ell_{\mathrm{fake}}&=\max(0,1+D(x_{\mathrm{fake}})).
\end{aligned}
\]

- `D(x)`：判别器输出的 logit，不是 0 到 1 的概率；
- `x_real`：真实训练图；
- `x_fake`：生成器输出；
- `max(0,·)`：若样本已跨过 margin，就把损失截到 0。

因此真实图的目标是 `D≥1`，假图的目标是 `D≤-1`。

## 数字例

```text
D(real)=.4  → max(0,1-.4)=.6
D(fake)=-.2 → max(0,1-.2)=.8
总损失 = 1.4
```

若后来 `D(real)=1.3、D(fake)=-1.4`，两项都为 0。判别器把精力留给还在边界内的难样本。

## 生成器不是最小化同一条式子

生成器通常最小化：

\[
\mathcal L_G=-\mathbb E[D(x_{\mathrm{fake}})].
\]

它要把假图的 logit 往高处推。判别器与生成器看同一个 `D(x_fake)`，优化方向相反；不能把两者的 loss 写成同一条箭头。

## 链接

- [[senseflow]] · 用时间权重缩放生成器的 hinge 对抗信号
- [[vfm-discriminator]] · 冻结 DINOv2 后如何训练真假头
