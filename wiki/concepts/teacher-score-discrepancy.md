---
name: teacher-score-discrepancy
type: concept
sources: [data-forcing-distillation]
updated: 2026-07-26
---

# Teacher Score Discrepancy · 同一位老师在真实样本与学生样本处的方向差

## 一句话

它用冻结 teacher 比较“真实视频处的 score”与“学生视频处的 score”，把真实数据直接接进 DMD 梯度。

## 直觉

原始 DMD 只带学生作品去问老师：“我站在这里，应该怎么改？”如果学生从没生成过某类构图，老师也不会在那类真实样本附近回答。

Teacher score discrepancy 多问一次：在同一文本或首帧条件下，老师面对真实视频会给出什么方向？两次回答的差，就是学生当前缺少的真实数据信号。

它不是把一条参考视频当成这份随机噪声的像素级标准答案。两条视频只要求条件相同，并且在 DFD 后训练开始时已经足够接近。

这里的 `real` 是相对学生分布而言的“参考数据分布”，不保证素材一定由摄像机拍摄。DFD 实验采用的 ViPE 源视频本身由 Wan2.1-14B 生成；关键是它们来自学生要追赶的训练集，而不是学生当前输出。

## 怎么做的

真实视频 `x` 和学生视频 \(\tilde{x}=G_\theta (z,c)\) 共享条件 `c`、噪声时刻 `t` 与高斯噪声 \(\epsilon\)：

\[
x_t=\alpha_tx+\sigma_t\epsilon,\qquad
\tilde x_t=\alpha_t\tilde x+\sigma_t\epsilon.
\]

冻结 teacher 的 score discrepancy 是：

\[
\Delta_{\mathrm{teacher}}
=s_{\mathrm{real}}(x_t\mid c,t)
-s_{\mathrm{real}}(\tilde x_t\mid c,t).
\]

- `x`：从真实条件分布抽到的视频；
- `x̃`：学生生成的视频；
- \(\alpha t / \sigma t\)：当前噪声尺度的信号与噪声系数；
- \(\epsilon\)：两条支路共用的标准高斯噪声；
- `sreal`：冻结扩散 teacher 估计的目标分布 score；
- \(\Delta teacher\)：两处 score 的差，与视频 latent 同形状。

DFD 用它修正 DMD：

\[
g_{\mathrm{DFD}}
=g_{\mathrm{DMD}}
-\mathbb E[\Delta_{\mathrm{teacher}}J_\theta].
\]

展开后，DMD 里的 \(-sreal(\tilde{x}t)\) 与正则产生的 `+sreal(x̃t)` 抵消：

\[
g_{\mathrm{DFD}}
=
\mathbb E[
(s_{\mathrm{fake}}(\tilde x_t)
-s_{\mathrm{real}}(x_t))J_\theta].
\]

所以实现只需把 teacher 的输入从学生视频换成真实视频；fake-score 仍读取学生视频。

## 数字例子

令：

```text
sfake(学生) = .2
sreal(学生) = 1.0
sreal(真实) = .4
Jθ = .5
```

先走长公式：

```text
gDMD = (.2−1.0)×.5 = −.40
Δteacher = .4−1.0 = −.60
gDFD = −.40−(−.60×.5)=−.10
```

再走抵消后的短公式：

```text
gDFD = (.2−.4)×.5 = −.10
```

两条路线对上。

共享噪声也可直接验算。取 `x=2、x̃=1.5、α=.8、σ=.6、ε=−.5`：

```text
xt  = .8×2+.6×(−.5)=1.3
x̃t  = .8×1.5+.6×(−.5)=.9
xt−x̃t=.4=.8×(2−1.5)
```

相同的噪声项相减后消失，score 差不会再混入两份无关噪声。

## 跟 DMD2 GAN 的对照

| 项目 | DMD2 GAN | Teacher score discrepancy |
|---|---|---|
| 真实数据怎样进入 | 判别器学真假，再把分类梯度传给学生 | teacher 直接在真实带噪视频上算 score |
| 这条信号本身是否需要对抗博弈 | 是 | 否 |
| 是否属于 DMD 主方向 | 额外损失 | 直接替换 real-score 项 |
| 训练前提 | 可与 DMD2 联合使用 | 更适合 DMD2 已经收敛后的短后训练 |

论文报告 DFD 可以不再使用 GAN，但当前官方复现命令仍保留了 DMD2 的非零 GAN 权重；这是配方选择，不改变 teacher score discrepancy 本身不依赖判别器。

## 链接

- [[data-forcing-distillation]] · 提出并验证该正则
- [[dmd-distillation]] · 被修正的 DMD 主梯度
- [[score-function]] · score 为什么是与样本同形状的修改方向
- [[entropy-kl]] · 反向 KL 为什么会偏向已有模式
