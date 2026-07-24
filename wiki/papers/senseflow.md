---
name: senseflow
type: paper
source: https://arxiv.org/pdf/2506.00523v2
upstream: https://github.com/XingtongGe/SenseFlow
ingested: 2026-07-24
authors: Xingtong Ge, Xin Zhang, Tongda Xu, Yi Zhang, Xinjie Zhang, Yan Wang, Jun Zhang · ICLR 2026
year: 2026
---

# SenseFlow · DMD2 扩到 SD 3.5 与 FLUX，为什么突然训不动了

[[dmd2]] 已经能把 SDXL 蒸成少步生成器：让 fake-score 多更新几次追踪学生，再用 GAN 接触真实图。但把同一套配方搬到 8B 的 SD 3.5 Large 和 12B 的 FLUX.1 dev，fake 网络即使以 20:1 的频率追赶，训练仍会振荡，甚至只生成黑图。SenseFlow 的价值不只是“又做了一个四步模型”，而是把失稳拆成三个不同问题，再分别补上 IDA、ISG 和 VFM 判别器。

## 一句话

**IDA 让 fake 网络在每次学生更新后先跟进一小步，ISG 让四个 anchor 吸收各自整段的老师信息，VFM 判别器再补语义与真实感。**

## 推荐阅读顺序

```text
DMD2 的移动靶问题
→ 为什么大模型上 TTUR 仍追不上
→ IDA 怎样让 fake 网络软跟随生成器
→ ISG 怎样把整段时间信息压进四个 anchor
→ VFM 判别器怎样给语义和真实感
→ 三套损失如何进入同一轮训练
→ 实验、负结果、代码差异与边界
```

## 1. 先看完整系统：不是一个 loss，而是三层补丁

训练时有四个主网络：

| 网络 | 是否更新 | 当前职责 | 部署时保留吗 |
|---|---:|---|---:|
| `G_θ` | 是 | 最终四步生成器 | 是 |
| `μ_real` | 否 | 冻结老师，给 real score / 速度 | 否 |
| `μ_fake^φ` | 是 | 追踪学生当前分布，给 fake score | 否 |
| `D` | 只训小头 | 在 DINOv2 / CLIP 特征上给真假与语义反馈 | 否 |

SenseFlow 沿用 DMD2 的双 score 主线，又补三处：

1. [[implicit-distribution-alignment]]：生成器更新后，把 fake 参数向生成器参数插值一小步；
2. [[intra-segment-guidance]]：在每对 coarse timestep 之间随机抽中间点，把段内信息监督到 anchor；
3. [[vfm-discriminator]]：冻结视觉基础模型，只训练轻量判别头。

这三项不是互相替代。IDA 解决 fake-score 追踪滞后，ISG 解决稀疏时间点监督，VFM 判别器解决原判别器语义能力不足。

## 2. 先补 DMD 前置：为什么一定要有 fake 网络

目标是让学生在噪声时刻 `t` 的分布 `p_g(X_t)` 接近老师分布 `p_r(X_t)`：

- `X_t`：学生生成的干净 latent 加噪到时刻 `t` 后的随机变量；
- `p_g(X_t)`：学生在 `X_t` 附近的概率密度；
- `p_r(X_t)`：冻结老师代表的目标概率密度；
- `D_KL(p_g||p_r)`：从学生样本出发衡量两种分布差距的反向 KL；
- `E`：对时间和学生样本取平均。

\[
\min_{p_g}D_{\mathrm{KL}}(p_g\Vert p_r)
=\mathbb E_{t,X_t\sim p_g}
\left[\log p_g(X_t)-\log p_r(X_t)\right].
\]

`p_g` 的密度本身不好算，所以 DMD 训练一套 fake 网络 `p_f` 去追踪学生：

- `θ`：生成器参数；改变它会移动 `p_g`；
- `φ`：fake 网络参数；它要让 `p_f` 追上当前 `p_g`；
- `min_θ max_φ`：外循环让学生靠近老师，内循环先把 fake 追踪器校准。

\[
\min_\theta\max_\phi
V(\theta,\phi)
=\mathbb E_{t,X_t\sim p_g}
\left[\log p_f(X_t)-\log p_r(X_t)\right].
\]

在同一个 `X_t` 上，fake score 与 real score 的差给生成器更新方向；fake 网络再用最新学生样本学习去噪。详情见 [[dmd-distillation]] 和 [[score-function]]。

## 3. 真正的失稳点：内循环必须持续追上移动靶

先回忆 KL 定义：

\[
D_{\mathrm{KL}}(p\Vert q)
=\mathbb E_{X\sim p}\left[\log p(X)-\log q(X)\right].
\]

现在把上一节的括号 `log p_f−log p_r` 拆成两段。中间加上又减去同一个 `log p_g`，总值没有改变：

\[
\begin{aligned}
V(\theta,\phi)
&=\mathbb E_{p_g}
\left[
(\log p_g-\log p_r)-(\log p_g-\log p_f)
\right]\\
&=D_{\mathrm{KL}}(p_g\Vert p_r)
-D_{\mathrm{KL}}(p_g\Vert p_f).
\end{aligned}
\]

第一行到第二行只是把 KL 定义代回去，没有使用近似。现在能看到内循环的任务：

- `θ` 固定时，第一项与 `φ` 无关；
- `φ` 最大化 `V`，等价于把第二项 `KL(p_g||p_f)` 压到 0；
- 最优点是 `p_f=p_g`，这叫 inner best response。

如果 fake 网络落后，生成器实际最小化的是“目标 KL 减去一项追踪误差”，而不是干净的 `KL(p_g||p_r)`。fake score 可能因此给出过时甚至相反的方向。

DMD2 用 TTUR 让 fake 网络多更新。SenseFlow 在 SD 3.5 Large 上把 TTUR 提到 20:1，仍看到 FID 大幅振荡；官方附录还报告，直接实现的 DMD2 风格 SD 3.5 Large 会坍塌成几乎全黑图。问题不是单纯“再多训几次 fake 就好”，而是 8B / 12B 网络的每次内循环本身已经昂贵且难以充分收敛。

## 4. IDA：先把 fake 网络拉近，再继续做去噪训练

生成器完成一次更新后，IDA 执行：

- `θ`：刚更新完的生成器参数；
- `φ`：插值前的 fake 网络参数；
- `λ∈[0,1]`：fake 参数保留率；
- `1−λ`：从新生成器参数吸收的比例。

\[
\phi\leftarrow\lambda\phi+(1-\lambda)\theta.
\]

官方 SD 3.5 Large 代码取 `λ=.97`。把一整个网络缩成一个参数：

```text
θ = 2.000，φ = 1.500，λ = .97
φnew = .97×1.500 + .03×2.000 = 1.515
参数差：.500 → .485
```

这一步很小，但每次 generator step 都发生。fake 网络随后仍在稠密时间步上用去噪损失训练；所以 IDA 不是拿生成器覆盖 fake，而是先把移动靶造成的差距缩短一点。

### 为什么两套参数能混

生成器与 fake 网络都从同一个 teacher 复制，结构都是时间条件速度网络。生成器虽只在四个 anchor 上获得梯度，仍能在任意 `t` 前向。IDA 传递的是同一参数坐标里的小变化，不是把“生成头权重”硬塞给一种完全不同的 score 架构。

### 理论到底保证了多少

附录先用局部 Lipschitz 等假设把“参数接近”传成“速度场接近”，再假设速度差可控制 score 差和 KL。这里 `ε≥0` 是允许的平均追踪误差上限：越接近 0，fake 分布越贴近学生分布。最终得到：

\[
\mathbb E_tD_{\mathrm{KL}}\!\left(p_g(X_t)\Vert p_f(X_t)\right)\le\epsilon.
\]

代回上一节的分解：

\[
D_{\mathrm{KL}}(p_g\Vert p_r)-\epsilon
\le V(\theta,\phi_{\mathrm{IDA}})
\le D_{\mathrm{KL}}(p_g\Vert p_r).
\]

它的含义是：内循环不必每次精确达到 `p_f=p_g`，只要追踪误差控制在 `ε` 内，外循环优化的目标就不会偏离真实 KL 太远。注意这是带假设的局部结论，不是“权重平均天然保证分布相同”。

## 5. ISG：四个时间点不该只代表四个点

SenseFlow 使用四个 coarse anchor：

| 模型 | anchor |
|---|---|
| SDXL | `{249,499,749,999}` |
| SD 3.5 Large | `{.25,.50,.75,1.0}` |
| FLUX.1 dev | shifted sigma `{.512,.759,.904,1.0}` |

论文测量老师的一步重建误差：

\[
\xi(t)=
\mathbb E_{x_0,\epsilon}
\left[
\left\|\widehat x_0(x_t,t)-x_0\right\|_2^2
\right].
\]

- `x_0`：老师生成的干净样本；
- `x_t`：把 `x_0` 加噪到时刻 `t`；
- `x̂_0`：老师从 `x_t` 预测的干净样本；
- `ξ(t)`：老师在这个时刻的一步重建误差。

实验曲线不是随 `t` 平滑单调变化，而是在局部振荡，高噪声的 `.8–1.0` 尤其明显。固定 anchor 若恰好落在坏位置，学生会把一整段都学歪。

### 段内引导的四步

对一段 `τ_i→τ_{i-1}`：

1. 随机采 `t_mid∈(τ_{i-1},τ_i)`；
2. 老师从 `x_{τ_i}` 走到 `x_{t_mid}`；
3. 学生在冻结目标支路上从 `x_{t_mid}` 走到 `x_tar`；
4. 活跃学生直接从 `x_{τ_i}` 跳到 `x_{τ_{i-1}}`，并贴近 `stopgrad(x_tar)`。

- `x_{τ_{i−1}}`：活跃学生从段首直接跳到段尾的输出；
- `x_tar`：老师走前半段、学生走后半段得到的临时目标；
- `i`：第几段 coarse interval；
- `E`：对样本、噪声和随机中间点取平均；
- `stopgrad`：只冻结目标支路的梯度。

\[
\mathcal L_{\mathrm{ISG}}^{(i)}
=\mathbb E
\left[
\left\|
x_{\tau_{i-1}}-\operatorname{stopgrad}(x_{\mathrm{tar}})
\right\|_2^2
\right].
\]

`stopgrad` 不是把生成器永久冻结。它只冻结同一次前向里的目标支路，让误差只更新直接跨段的学生路径。

### 一组数字走完整段

取 `τ_i=.75、t_mid=.60、τ_{i-1}=.50、x_{τ_i}=.20`：

```text
老师前半段速度 = -2.0
xmid = .20 + (.60-.75)×(-2.0) = .50

目标支路学生速度 = -1.5
xtar = .50 + (.50-.60)×(-1.5) = .65

直接支路学生速度 = -1.0
xdirect = .20 + (.50-.75)×(-1.0) = .45

LISG = (.45-.65)² = .04
```

下一次随机换一个 `t_mid`，anchor 就吸收同一段里另一处的老师行为。它不是增加推理步数；这条绕路只在训练时造目标。

### 论文与代码的差异

论文 Eq. 12 写平方 L2。官方 commit `fafc81b7` 的 SD 3.5 / SDXL 训练器实际使用平滑绝对误差：

\[
\sqrt{(x_{\mathrm{direct}}-x_{\mathrm{tar}})^2+.001^2}-.001.
\]

代码还在 SD 3.5 的两个端点各留 50 个离散 index，再采 `t_mid`，并用 CFG=5 的老师走前半段。复现时应以对应版本代码为准，不能只照正文公式。

## 6. VFM 判别器：真实感与文字语义另开一条路

原 DMD2 判别器复用扩散 UNet 的 bottleneck。SenseFlow 改成：

```text
生成图 ─→ 可微增强 ─→ 冻结 DINOv2 多层特征 ─┐
真实参考图 ───────→ 冻结 DINOv2 多层特征 ─┼→ 可训练小头 → 真假 logits
prompt ───────────→ 冻结 CLIP 文本向量 ──┘
```

v2 附录纠正了正文的一处描述：参考图 `r` 也经过 DINOv2，不是 CLIP 图像编码器。

判别器使用 hinge loss：

- `D(x)`：判别头给图像的实数 logit；越大越像真实图；
- `x_real / x_fake`：真实参考图与当前生成图；
- `E_real / E_fake`：分别对两类 batch 求平均；
- `max(0,·)`：已经越过正确 margin 的样本不再继续受罚。

\[
\mathcal L_D
=\mathbb E_{\mathrm{real}}\max(0,1-D(x_{\mathrm{real}}))
+\mathbb E_{\mathrm{fake}}\max(0,1+D(x_{\mathrm{fake}})).
\]

若 `D(real)=.4、D(fake)=-.2`，两项分别为 `.6` 和 `.8`，总损失 `1.4`。判别器要把真实图推到 `≥1`，假图压到 `≤-1`。

生成器的对抗项为：

- `α_t=1−σ_t`：当前输入里保留的干净信号比例；
- `σ_t`：噪声比例；
- `E[D(x_fake)]`：判别头对当前学生图的平均评分；
- 前面的负号：最小化损失等价于把学生图评分推高。

\[
\mathcal L_G^{\mathrm{adv}}
=-\alpha_t^2\,\mathbb E[D(x_{\mathrm{fake}})],
\qquad \alpha_t=1-\sigma_t.
\]

`σ_t` 越大，图越接近噪声，`α_t²` 越小。比如 `σ=.8` 时权重 `.04`，`σ=.2` 时权重 `.64`。高噪声时主要信 DMD，接近干净图时才放大 GAN 的视觉判断。

## 7. 一轮训练到底按什么顺序

每个小步先选一个 coarse anchor，再以 50% 概率二选一：

- 从真实图前向加噪到 anchor；
- 从纯噪声用当前学生 backward simulation 到 anchor。

默认每 5 个小步更新一次生成器：

- `L_DMD`：双 score 分布匹配项；
- `L_G^adv`：VFM 判别器给生成器的对抗项；
- `L_ISG`：段内引导项；
- `λ_G、λ_ISG`：控制后两项相对强度的超参数。

\[
\mathcal L_G
=\mathcal L_{\mathrm{DMD}}
+\lambda_G\mathcal L_G^{\mathrm{adv}}
+\lambda_{\mathrm{ISG}}\mathcal L_{\mathrm{ISG}}.
\]

顺序是：

1. 算双 score 的 DMD 方向；
2. 算 VFM 对抗信号；
3. 用 ISG 造段内目标；
4. 三项合并更新 `G_θ`；
5. 立刻执行 IDA：`φ←λφ+(1-λ)θ`；
6. 每个小步都用最新学生图更新 fake 去噪网络；
7. 每个小步都用真实图和生成图更新 VFM 判别头。

部署时只保留 `G_θ`。IDA、ISG、老师、fake 网络、DINOv2、CLIP 和判别头都是训练脚手架。

## 8. 实验不要只看“多数指标第一”

### 4 步主结果

SenseFlow 在 SD 3.5 Large 上相对 Turbo 的 Patch FID-T 从 `22.88` 降到 `17.48`，HPSv2 从 `.2909` 升到 `.3016`，ImageReward 从 `1.0116` 升到 `1.1713`。在 FLUX 上，Euler 版本的 HPSv2 `.3008`、PickScore `23.26`、ImageReward `1.1424` 都高于列出的四步基线。

但 SDXL 不是所有指标都赢。相对 DMD2：

| SDXL 4-step | DMD2 | SenseFlow | 更好 |
|---|---:|---:|---|
| Patch FID-T ↓ | 18.72 | 21.01 | DMD2 |
| CLIP ↑ | .3277 | .3248 | DMD2 |
| HPSv2 ↑ | .2963 | .3010 | SenseFlow |
| PickScore ↑ | 22.98 | 23.17 | SenseFlow |
| ImageReward ↑ | .9324 | .9951 | SenseFlow |

这更像“把优化重心推向人类偏好和语义质量”，不是无条件支配。

### 三个组件各自贡献什么

SD 3.5 Large 的扩展消融：

| 配方 | FID-T ↓ | HPSv2 ↑ | ImageReward ↑ |
|---|---:|---:|---:|
| 完整 SenseFlow | 13.38 | .3015 | 1.1713 |
| 去 ISG | 17.00 | .2971 | 1.0186 |
| 去 IDA | 17.83 | .2800 | .9365 |
| IDA / ISG 都去掉 | 43.84 | .2555 | .3828 |

早期训练最能看出 ISG：1.5k iteration 时，完整模型 FID-T `14.48`，去 ISG 是 `138.2`。但完整模型到 3k 时也反弹到 `22.32`，所以 ISG 的证据是更快进入可用区并总体更稳，不是损失或 FID 单调下降。

### 代价

8×A100、总 batch 8 的报告口径下：

- SDXL：18k steps / 32 小时；
- SD 3.5 Large：27k / 56.3 小时；
- FLUX：12k / 23.4 小时。

ISG 平均每 iteration 增加 `3.23%–6.16%`；IDA 在去 ISG 基线之上增加 `.57%`（SD 3.5）或 `3.97%`（FLUX）。两者只在 generator step 执行，所以被 5:1 TTUR 摊薄。

## 9. 多样性、1–2 步与不要越过的结论

VFM 判别器提高人偏好指标，也可能重排分布模式。SDXL 的 LPIPS diversity 从 `.5960` 微升到 `.6002`，但 CLIP diversity 从 `.0985` 降到 `.0802`，约下降 `18.6%`。论文称变化温和；更准确的读法是：低层视觉差异没有缩小，但语义嵌入的变化范围确实收窄。

四步权重可以直接运行两步；一步结果则不是直接零成本得到。论文先从四步 checkpoint 出发，再为一步设置额外微调 6000 iteration。因此“一套四步模型天然就是一步模型”并不成立。

## 10. 配方、公开实现与边界

- 数据：过滤后的 LAION-5B，aesthetic score 至少 5.0，短边至少 1024；
- 优化：AdamW，`β1=.9、β2=.999`；SDXL / SD3.5 学习率 `1e-6`，FLUX `1e-5`；
- 并行：FSDP；报告训练使用 8×A100；
- 评测：COCO-2017 5k、GenEval、T2I-CompBench；COCO 每张图挑 CLIP 分数最高的 caption；
- 官方代码与权重已公开，仓库为 Apache-2.0，但底层 SD / FLUX 权重仍受各自许可证约束。

仍需保留的限制：

1. IDA 的理论依赖局部正则、步长收敛和 Fisher-to-KL 控制等强假设；
2. DMD2-SD3.5 baseline 是作者自实现且未进主表，因为它坍塌；没有公共实现可独立交叉验证；
3. VFM 提升人偏好指标的同时可能牺牲教师分布覆盖和部分 FID；
4. 训练仍要同时放置生成器、老师、fake 网络、VFM 与判别头，FSDP 只是分摊显存，不会把总计算消掉；
5. 论文没有提供不同随机种子的均值和方差，稳定性主要由曲线与单次消融支持。

## 核心贡献

1. **追踪稳定性**：[[implicit-distribution-alignment]] —— 用轻量参数插值近似内循环 best response。
2. **时间监督**：[[intra-segment-guidance]] —— 把段内老师行为压到少数 coarse anchor。
3. **视觉判别**：[[vfm-discriminator]] —— 用冻结 DINOv2 / CLIP 特征提供强语义与真实感监督。

## 关键概念

- [[dmd-distillation]] · SenseFlow 继承的双 score 分布匹配主线
- [[score-function]] · `s_fake-s_real` 为什么是生成器的方向
- [[flow-matching]] · SD 3.5 / FLUX 的时间条件速度网络
- [[ema]] · IDA 公式形似 EMA，但混合的是 fake 与 generator 两个网络
- [[distributed-training-parallelism]] · FSDP 在卡间切分参数、梯度与优化器状态

## 我的批注

- 最关键的洞察不是“EMA 能稳定训练”，而是先把 DMD 写成 `KL(g||r)-KL(g||f)`，指出 fake 追踪误差会直接污染外循环目标。
- IDA 有效依赖生成器和 fake 网络同构、同初始化；这不是任意两套模型都能套的通用技巧。
- ISG 的目标不是纯老师轨迹，而是“老师前半段 + 冻结学生后半段”，比正文一句“relocate timestep importance”更具体。
- v2 附录主动更正参考图编码器，并且官方代码的 ISG loss 与正文不同；这是复现时必须写下的版本事实。
- 主结果更偏向人类偏好指标，SDXL 的 Patch FID-T 与 CLIP 反而落后 DMD2；“SOTA”要带指标和教师范围。

## 跟 wiki 里其他 paper 的关系

- [[dmd]] · 提出 real / fake 双 score 的分布匹配
- [[dmd2]] · 去掉大规模配对回归，以 TTUR、GAN 和 backward simulation 扩展成少步生成
- [[flow-matching]] · SenseFlow 要蒸馏的 SD 3.5 / FLUX 主干采用速度场
- [[drifting-models]] · 同样匹配生成分布，但不训练 fake-score 网络

## 历史定位

- 2024-06 [[dmd]] · 一步分布匹配蒸馏
- 2024-11 [[dmd2]] · 去配对、加 TTUR / GAN / 多步
- 2026-04 **SenseFlow** · 把 DMD2 稳定扩到 SD 3.5 Large 与 FLUX.1 dev
