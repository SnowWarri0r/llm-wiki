---
name: dmd2
type: paper
source: https://arxiv.org/pdf/2405.14867
upstream: https://tianweiy.github.io/dmd2/
ingested: 2026-07-23
authors: Tianwei Yin, Michaël Gharbi, Taesung Park, Richard Zhang, Eli Shechtman, Frédo Durand, William T. Freeman · NeurIPS 2024 Oral
year: 2024
---

# DMD2 · 拆掉昂贵的配对稳定器，再把一步分布匹配扩成可用的少步生成器

DMD2（Improved Distribution Matching Distillation）不是“DMD 后面再加一个 GAN”这么简单。原始 [[dmd]] 用冻结的真实 score 和在线训练的 fake score，把几十步扩散模型蒸成一步生成器；但为了防止训练失控，它还需要老师提前生成海量 `(噪声, 最终图像)` 配对。DMD2 先找到训练失控的直接原因，再用更快的 fake-score 更新补上稳定性；随后接入真实图像上的 GAN 监督，并设计 backward simulation，让同一个学生既能一步生成，也能按固定时间表运行多步。

## 一句话

**DMD2 让 fake-score 以 5:1 的频率追上学生，再用 GAN 接触真实数据、用 backward simulation 对齐多步训练和推理，从而摆脱大规模老师配对集。**

## 1. 先看整套系统：四个网络，两个更新阶段

训练时有四个角色：

- `G_θ`：最终部署的学生生成器，参数为 `θ`；
- `μ_real`：冻结的扩散老师，用来估计目标分布的 score；
- `μ_fake^φ`：在线训练的 fake 去噪器，参数为 `φ`，估计学生当前输出分布的 score；
- `D_ψ`：真假分类头，参数为 `ψ`，接在 `μ_fake` 的 UNet bottleneck 上。

每个训练小步分成两段：

1. **需要更新生成器时**：学生出图；DMD 梯度给出“往老师分布靠、从学生过密处散开”的方向；GAN 再告诉学生怎样更像真实图。两项一起更新 `θ`。
2. **每个小步都更新辅助网络**：用最新学生图训练 `μ_fake^φ`；同时用真实图和学生图训练 `D_ψ`。默认配置里，这段会执行 5 次，生成器才更新 1 次。

部署时只留下 `G_θ`。老师、fake-score、分类头、真实图数据和所有损失都属于训练脚手架。

## 2. DMD 原来为什么要一套昂贵的配对数据

原始 DMD 的主目标是分布匹配。学生先生成 `x=G_θ(z)`，再给 `x` 加噪：

\[
x_t=F(x,t)=\alpha_t x+\sigma_t\epsilon,\qquad
\epsilon\sim\mathcal N(0,\mathbf I).
\]

这条式子回答“怎样把学生的干净输出放到第 `t` 个噪声尺度上”：

- `z`：标准高斯噪声，学生的初始输入；
- `x`：学生生成的干净图或 latent；
- `t`：随机抽到的扩散时刻；
- `α_t`：保留干净信号的比例；
- `σ_t`：加入随机噪声的强度；
- `ε`：与 `x` 同形状的标准高斯噪声；
- `F`：前向扩散，也就是加噪函数。

两个扩散去噪器分别估计目标分布和学生分布的 score：

\[
s(x_t,t)=\nabla_{x_t}\log p_t(x_t)
=-\frac{x_t-\alpha_t\mu(x_t,t)}{\sigma_t^2}.
\]

- `p_t(x_t)`：第 `t` 个噪声尺度下的数据概率密度；
- `∇_{x_t}`：对带噪输入的每个元素求梯度；
- `μ(x_t,t)`：去噪器预测的干净样本；
- `s(x_t,t)`：与 `x_t` 同形状的修改方向，不是 0 到 1 的“真假分”。

DMD 的生成器梯度来自两个 score 的差：

\[
\nabla_\theta\mathcal L_{\mathrm{DMD}}
=
\mathbb E_t\!\left[
\left(s_{\mathrm{fake}}(x_t,t)-s_{\mathrm{real}}(x_t,t)\right)
\frac{\partial G_\theta(z)}{\partial\theta}
\right].
\]

- `s_real`：冻结老师给出的目标分布方向；
- `s_fake`：在线 fake 去噪器给出的学生分布方向；
- `∂G_θ/∂θ`：链式法则，把“图该怎么改”传回生成器参数；
- `E_t`：对随机噪声时刻取平均。

梯度下降会减去上式，所以实际效果是吸向 `s_real`，同时避开 `s_fake` 已经很拥挤的位置。

问题在于：学生每更新一次，`p_fake` 就会变；fake-score 稍微跟不上，两个 score 的差就会失真。原始 DMD 用一条配对回归当稳定器：

\[
\mathcal L_{\mathrm{reg}}
=\mathbb E_{(z,y)}\!\left[d\!\left(G_\theta(z),y\right)\right].
\]

- `(z,y)`：老师提前生成的配对；`y` 是老师从同一份噪声 `z` 多步采样得到的最终图；
- `d`：图像距离；原始实现使用 LPIPS；
- `E_(z,y)`：对配对数据批次求平均。

这条线能稳住模式和结构，却有两笔代价。第一，SDXL 每生成一对数据约需 5 秒；覆盖 1200 万条 LAION 6.0 提示词约需 700 个 A100·天，超过 DMD2 总训练算力的 4 倍。第二，它重新要求学生追随老师的确定性采样路径，学生质量很难越过老师。

## 3. 第一项改动：删掉回归项，究竟删掉了什么

DMD2 的主训练不再使用 `L_reg`：

\[
\mathcal L_G
=\mathcal L_{\mathrm{DMD}}
+\lambda_{\mathrm{GAN}}\mathcal L_G^{\mathrm{GAN}}.
\]

这不是把老师删掉。`μ_real` 仍然存在，仍给 DMD score；删掉的是“同一份 `z` 必须对应老师指定的 `y`”这条逐样本约束，以及为它离线生成的大规模配对集。

删掉以后：

- **不变**：学生仍从老师权重初始化；real score 仍来自冻结老师；fake score 仍在线训练；
- **消失**：大规模 `(z,y)` 老师采样集和 LPIPS 回归；
- **新增**：更密集的 fake-score 更新，以及真实图像上的 GAN 分布监督。

直接删会让 ImageNet FID 从 `2.62` 变成 `3.48`，生成图的平均亮度也会周期性摆动。这说明回归项原来不只是“让图更像老师”，还在掩盖 fake-score 追踪不及时的问题。

## 4. TTUR：为什么 fake-score 要更新 5 次，学生才走 1 步

这里的 TTUR（Two Time-scale Update Rule，双时间尺度更新）不是“两个学习率一定不同”。DMD2 的核心实现是**更新频率不同**：

```text
小步 1：更新 Gθ；更新 μfake / D
小步 2：不更新 Gθ；更新 μfake / D
小步 3：不更新 Gθ；更新 μfake / D
小步 4：不更新 Gθ；更新 μfake / D
小步 5：不更新 Gθ；更新 μfake / D
然后进入下一组
```

`μ_fake` 面对的是移动靶：生成器一变，学生分布就变。如果两边 1:1 更新，fake-score 还没学清上一版学生，生成器已经根据这份过时的方向再次移动。误差会进入 `s_fake−s_real`，于是生成器收到有偏梯度。

5:1 的作用不是让 fake 网络“更聪明”，而是让它在生成器两次移动之间多看几批最新学生样本，把当前 `p_fake` 拟合得更准。论文附录比较了：

- `1:1`：亮度与 FID 明显振荡；
- `5:1`：稳定性和收敛速度折中最好；
- `10:1`：很稳，但墙钟时间更慢；
- fake 学习率直接放大 5 倍：不如多做 5 次真实更新。

所以 `5` 是 ImageNet / SDXL 上的经验值，不是理论常数。论文建议换数据集或骨干后，监控亮度等总体统计量，取“刚好不再振荡”的最小更新次数。SD v1.5 实际用了 `10:1`。

## 5. 第二项改动：GAN 为什么不是重复做一遍 DMD

DMD 的 `s_real` 来自老师。老师自己只是对真实分布的近似；如果老师某些纹理、颜色或细节没学好，学生只看老师 score 就无法纠正。

DMD2 让 GAN 分类器直接看两类数据：

- 正样本：真实训练图像 `x_real`；
- 负样本：当前学生图像 `x_fake=G_θ(z)`。

官方实现用 logits `a=D_ψ(x)` 和 softplus 写标准非饱和 GAN。为了把两个优化方向分清，可以写成：

\[
\mathcal L_D
=
\mathbb E_{x_{\mathrm{real}}}
\left[\operatorname{softplus}(-a_{\mathrm{real}})\right]
+
\mathbb E_{x_{\mathrm{fake}}}
\left[\operatorname{softplus}(a_{\mathrm{fake}})\right],
\]

\[
\mathcal L_G^{\mathrm{GAN}}
=
\mathbb E_{x_{\mathrm{fake}}}
\left[\operatorname{softplus}(-a_{\mathrm{fake}})\right].
\]

- `ψ`：分类器参数；
- `a_real`：真实图的未归一化 logit，越大越像真图；
- `a_fake`：学生图的 logit；
- `softplus(u)=log(1+e^u)`：平滑的非负损失；
- `L_D`：只更新分类器和它共享的 fake-UNet encoder；
- `L_G^GAN`：只通过学生图回传到生成器。

若写成概率 `D(x)=sigmoid(a)`，同一件事就是：

\[
\mathcal L_D
=-\mathbb E[\log D(x_{\mathrm{real}})]
-\mathbb E[\log(1-D(x_{\mathrm{fake}}))],
\qquad
\mathcal L_G^{\mathrm{GAN}}
=-\mathbb E[\log D(x_{\mathrm{fake}})].
\]

论文 Eq. 4 把两方训练压在一条式子里，容易看不出谁最大化、谁最小化；官方实现分成了上面两条损失。

### 为什么分类前还要随机加噪

分类器实际接收：

\[
\tilde x_t=F(x,t)=\alpha_t x+\sigma_t\epsilon.
\]

真实图和学生图都先按同一个随机噪声时刻 `t` 加噪。高频细节被适度抹平以后，真假分布有更多重叠，分类器不会只靠早期的简单瑕疵瞬间满分，生成器也更容易收到连续梯度。

## 6. DMD 与 GAN 各管什么：少一项都不完整

两项都是“分布级”监督，但来源和长处不同：

| 监督 | 参照物 | 擅长 | 单独使用的缺口 |
|---|---|---|---|
| DMD | 冻结扩散老师 + 在线 fake score | 稳定的语义方向、自然接入固定 CFG | 继承老师 score 的近似误差，不直接看真实图 |
| GAN | 真实图 vs 学生图 | 真实感、纹理和老师没覆盖好的细节 | 训练更容易不稳，文本对齐和 CFG 接入不如扩散 score 自然 |

SDXL 消融里，去掉 DMD 后 FID 反而从 `19.32` 降到 `13.77`，但 CLIP 从 `.332` 跌到 `.307`，主观上文字对齐和美感也明显变差。这个结果不能读成“纯 GAN 更好”：FID 只看整批图像统计，不检查图是否忠实响应提示词。

去掉 GAN 后，FID / Patch FID 变成 `26.90 / 27.66`，并出现过饱和、过平滑。完整 DMD2 用 DMD 管语义与稳定方向，用 GAN 接触真实图像，二者并不重复。

## 7. 第三项改动：把一步学生扩成固定时间表的多步学生

一步生成要求一个网络把纯噪声直接变成 1024×1024 的复杂图像。SDXL 上，这个映射对容量和优化都太苛刻。DMD2 固定 `N` 个去噪时刻：

\[
\{t_1,t_2,\ldots,t_N\}.
\]

四步 SDXL 使用：

```text
t₁=999 → t₂=749 → t₃=499 → t₄=249
```

每一步先预测干净样本：

\[
\hat x_{t_i}=G_\theta(x_{t_i},t_i),
\]

若还没到最后一步，再把它重新加噪到下一时刻：

\[
x_{t_{i+1}}
=\alpha_{t_{i+1}}\hat x_{t_i}
+\sigma_{t_{i+1}}\epsilon_i,
\qquad
\epsilon_i\sim\mathcal N(0,\mathbf I).
\]

- `N`：学生总去噪次数；
- `t_i`：第 `i` 次调用使用的时间条件；
- `x_ti`：这一步收到的带噪 latent；
- `x̂_ti`：学生对干净 latent 的预测；
- `ε_i`：每一步重新采的新噪声。

这不是把一步网络简单重复四遍。网络训练时必须见过这些中间输入，并且推理必须使用训练时同一套时刻；官方 README 特别提醒，LCM scheduler 的默认时间表不同，要显式传入 `[999,749,499,249]`。

## 8. 训练—推理输入为什么会错位

常见多步蒸馏训练会拿真实图 `x_real` 加噪，造出中间输入：

\[
x_t^{\mathrm{train}}
=\alpha_t x_{\mathrm{real}}+\sigma_t\epsilon.
\]

但推理时第二步以后的输入来自学生自己的上一轮输出：

\[
x_{t_{i+1}}^{\mathrm{infer}}
=\alpha_{t_{i+1}}
G_\theta(x_{t_i}^{\mathrm{infer}},t_i)
+\sigma_{t_{i+1}}\epsilon_i.
\]

两者不是同一个分布。训练时模型看到“真实图附近的带噪 latent”，推理时却看到“学生自己生成、带着学生误差的 latent”。一旦第一步有偏差，后面每一步都在陌生输入上工作，误差会累积。

## 9. Backward simulation：训练时真的先跑几步学生

DMD2 的解法是：训练某个中间时刻以前，先从纯噪声开始，用当前学生模拟推理路径。

官方实现每个 batch 先随机抽一个目标步 `k∈{0,…,N−1}`，然后：

1. 从纯噪声 `x_t1` 开始；
2. 用当前 `G_θ` 依次跑完第 `1…k−1` 步；
3. 每步后按时间表重新加噪；
4. 把得到的学生中间状态当作第 `k` 步训练输入；
5. 再用 DMD + GAN 监督第 `k` 步输出。

模拟路径放在 `no_grad` 里：前面几步只负责造出真实推理会遇到的输入，不把一条很长的计算图保留到反向传播。最终被训练的当前步仍正常保留梯度。

### 一维数字例：错位到底有多大

假设训练第 2 步，真实干净值 `x_real=2.0`；第一步学生从纯噪声 `x_999=1.0` 只预测出 `x̂_999=.4`。下一时刻取 `α_749=.7`、`σ_749=.714`，并固定 `ε=-.5`。

传统“真实图加噪”得到：

```text
x₇₄₉(train)
= .7×2.0 + .714×(−.5)
= 1.400 − .357
= 1.043
```

真实推理路径得到：

```text
x₇₄₉(infer)
= .7×.4 + .714×(−.5)
= .280 − .357
= −.077
```

第 2 步训练时看 `1.043`，部署时却收到 `−.077`，相差 `1.120`。backward simulation 用当前学生先算出 `.4`，再造出 `−.077`，让第 2 步在自己将来真正会遇到的输入上学习。

这些数只用于解释数据流，不是论文的 latent 数值；公式和执行顺序与官方实现一致。

## 10. 一组训练小步的完整执行顺序

假设 `dfake_gen_update_ratio=5`：

```text
01 采 prompt、噪声；若是多步模型，先 backward-simulate 到随机目标时刻
02 Gθ 对当前时刻做一次去噪，得到学生图 xfake
03 仅在第 1/5 个小步：冻结 μreal、μfake、D，算 DMD + GAN 生成器损失，更新 θ
04 把 xfake detach，随机加噪，训练 μfake 预测噪声
05 真实图和 xfake 各自随机加噪，训练 Dψ 分真假
06 重复下一小步；连续更新 5 次 μfake / D 后，Gθ 再走一步
```

“冻结”是按当前更新阶段切换：更新 `G_θ` 时不改辅助网络；更新 fake-score / 分类器时，学生输出 detach。不是把某个网络从训练开始到结束永久冻结。

## 11. GAN 分类头接在哪里

DMD2 没有再训练一套完整判别器。`μ_fake` 本来就是一套 UNet；作者复用它的 encoder 和 bottleneck 特征，在中间块上接一个小分类头：

```text
fake UNet bottleneck
→ 4×4 stride-2 conv + GroupNorm + SiLU
→ 重复下采样到 4×4
→ 4×4 stride-4 conv，压成 1×1
→ 1×1 conv / 线性投影
→ 一个真假 logit
```

以 SDXL 为例，bottleneck 是 `1280×32×32`；三层 stride-2 卷积把空间尺寸变成 `16→8→4`，再用一层 `4×4` 卷积压到 `1×1`。这样，fake-score 的编码特征同时服务于去噪和真假分类。

共享带来两面性：

- 好处：不用再放一套大型图像判别器，特征天然带时间和文本条件；
- 代价：`μ_fake` 同时追学生分布、做真假分类，优化更耦合；官方实现要仔细清空两边梯度，避免生成器阶段残留的分类器梯度混入下一步。

## 12. 训练配方：三套骨干不是同一张配置

### ImageNet 64×64

- 老师：EDM；
- 一步学生；
- AdamW，学习率 `2×10⁻⁶`，weight decay `.01`，β=`(.9,.999)`；
- batch `280`，7 张 A100，`200K` iter，约 2 天；
- fake-score : generator = `5:1`；
- GAN 生成器权重 `3×10⁻³`。

扩展训练先关闭 GAN 跑 `400K`，再从最佳 FID checkpoint 开启 GAN，把学习率降到 `5×10⁻⁷`，继续 `150K`；总计约 5 天。

### Stable Diffusion v1.5

- 300 万条 LAION-Aesthetic 6.25+ 提示词；
- 50 万张 LAION-Aesthetic 5.5+ 真实图训练判别器，过滤小于 1024² 和不安全内容；
- 第一阶段无 GAN：学习率 `10⁻⁵`，fake:generator=`10:1`，CFG=`1.75`，batch `2048`，64 张 A100，`40K`；
- 第二阶段开 GAN：权重 `10⁻³`，学习率 `5×10⁻⁷`，再跑 `5K`；
- 总计约 26 小时。

### SDXL

- 一步和四步模型都从 SDXL 蒸馏；
- 学习率 `5×10⁻⁷`，fake:generator=`5:1`，CFG=`8`；
- batch `128`，64 张 A100；
- 四步 `20K`，一步 `25K`，约 60 小时；
- 四步不需要回归预热，使用 backward simulation；
- 一步模型出现块状噪声，作者把条件时刻改为 `399`，并用仅 `10K` 对数据短暂回归预热。

最后一条是重要边界：论文的主方法消除了大规模配对集，但 SDXL 一步配置仍用了小规模配对 warm-up。不能把它写成所有设置都严格“零配对”。

## 13. 主结果：速度、FID 和老师比较要对齐口径

### ImageNet 64×64

| 方法 | 前向次数 | FID ↓ |
|---|---:|---:|
| 原始 DMD | 1 | 2.62 |
| DMD2 | 1 | 1.51 |
| DMD2 + longer training | 1 | **1.28** |
| EDM teacher · ODE | 511 | 2.32 |
| EDM teacher · SDE | 511 | 1.36 |

`1.28` 超过 ODE 老师，也略好于 SDE 老师的 `1.36`。这里的“约 500×”来自前向次数 `511→1`，不是在任意硬件上都严格快 511 倍。

### SD v1.5 · COCO 30K

| 方法 | 步数 | 延迟 | FID ↓ |
|---|---:|---:|---:|
| DMD | 1 | .09s | 11.49 |
| DMD2 | 1 | .09s | **8.35** |
| SD v1.5 teacher · 50-step ODE | 50 | 2.59s | 8.59 |
| SD v1.5 teacher · 200-step SDE | 200 | 10.25s | 7.21 |

DMD2 一步超过 50 步 ODE 老师，但仍没超过 200 步 SDE 老师。两套老师的 CFG 和采样器不同，不能只说“全面超过老师”。

### SDXL · COCO 10K

四步 DMD2 的 `FID / Patch FID / CLIP` 是 `19.32 / 20.86 / .332`；100 次前向的 SDXL teacher（CFG 6）是 `19.36 / 21.38 / .332`。四步学生在三项指标上与老师相当或略好。

人评使用 128 条 PartiPrompts，每组比较由 5 位评审判断。论文报告四步 DMD2 在 24% 的样本上画质优于老师，文本对齐相当；这不是“24% 总胜率”，因为其余样本还包含老师胜和并列。

## 14. 消融：每个零件补的是哪一个洞

### ImageNet

| DMD | 去回归 | TTUR | GAN | FID ↓ |
|:---:|:---:|:---:|:---:|---:|
| ✓ |  |  |  | 2.62 |
| ✓ | ✓ |  |  | 3.48 |
| ✓ | ✓ | ✓ |  | 2.61 |
| ✓ | ✓ | ✓ | ✓ | **1.51** |
|  |  |  | ✓ | 2.56 |
|  |  | ✓ | ✓ | 2.52 |

读表顺序：

1. 直接删回归：`2.62→3.48`，说明训练确实失稳；
2. 加 5:1 TTUR：`3.48→2.61`，几乎补回原 DMD；
3. 再加 GAN：`2.61→1.51`，直接接触真实数据带来 1.10 FID 改善；
4. 纯 GAN 的 `2.56` 已经不错，但不及两项合用；
5. 纯 GAN 加 TTUR 只从 `2.56→2.52`，说明 TTUR 主要是在修复 DMD 的动态 fake-score，而不是通用 GAN 增益。

### SDXL 四步

- 无 GAN：`FID 26.90 / Patch FID 27.66 / CLIP .328`；
- 无 DMD：`13.77 / 27.96 / .307`；
- 无 backward simulation：`20.66 / 24.21 / .332`；
- 完整 DMD2：`19.32 / 20.86 / .332`。

backward simulation 对整图 FID 只改善 `1.34`，但 Patch FID 改善 `3.35`，说明训练—推理输入对齐尤其影响高分辨率局部细节。

## 15. 局限、实现事实与别过度外推的地方

- SDXL 四步模型的多样性分数 `.61`，低于老师 `.64`；速度与质量提升没有免费保住全部多样性。
- 最大 SDXL 仍需 4 步才能达到老师水平；一步更快，但质量更差，而且需要 10K 配对 warm-up。
- CFG 在训练时固定，部署时 `guidance_scale=0` 是因为引导已蒸进学生，不代表用户还能自由调 CFG。
- GAN 权重会影响多样性与文本对齐。作者观察到加大 GAN 权重可提高多样性，但最佳平衡没有解决。
- 训练大型生成器仍昂贵：SDXL 用 64 张 A100 跑约 60 小时。
- 官方代码 commit `8d8fa556` 的 README 明确记录：当前 SDXL FSDP 训练很慢；LoRA 训练反而比全量微调慢，而且显存相同。这是当时实现状态，不是算法必然结论。
- 论文公开了训练数据来源、batch、更新比例和主要超参数，但没有给出 TTUR 稳定性的理论收敛证明；`5:1` 来自实验。

## 关键概念

- [[dmd-distillation]] · 两个 score 的分布匹配梯度，以及 DMD / DMD2 / TDM 的边界
- [[score-function]] · `∇log p(x)` 为什么是图像空间里的修改方向
- [[entropy-kl]] · DMD 近似最小化的反向 KL
- [[classifier-free-guidance]] · 训练时固定进学生的文本引导
- [[lpips]] · 原始 DMD 配对回归使用的感知距离
- [[pushforward-distribution]] · 学生参数改变时，输出分布为什么跟着移动

## 我的批注

- DMD2 最关键的诊断不是“GAN 能提质”，而是把原始 DMD 的失稳定位到 fake-score 追不上移动的学生分布。只有先修好这条估计链，删除回归才成立。
- TTUR 与 GAN 的分工可由消融直接验证：TTUR 对 DMD 有效，对纯 GAN 几乎没用；GAN 则在 TTUR 恢复稳定后继续降低 FID。
- backward simulation 很像 on-policy 数据：学生用自己的中间状态训练下一步，而不是只在干净真实图的加噪邻域里练习。它不改变 DMD 损失本身，改变的是训练输入从哪里来。
- “超越老师”要分清老师版本。DMD2 超过 ODE 老师或特定 CFG 的 SDXL 老师，不代表超过所有更慢、更随机的 SDE 采样配置。
- 去掉大规模配对集的表述总体成立，但 SDXL 一步的 10K 配对预热必须保留；这恰好说明极限一步蒸馏仍比四步更难。

## 跟 wiki 里其他 paper 的关系

- [[dmd]] · 前作；DMD2 保留双 score 梯度，替换掉大规模配对稳定器
- [[drifting-models]] · 同样有“吸向目标、离开自身过密区”的结构，但用样本核漂移，不训练 fake diffusion
- [[trajectory-distribution-matching]] · 后续把终点分布匹配扩到去噪轨迹多个时刻
- [[pid-pixel-diffusion]] · 把 DMD2 用于像素扩散解码器的四步蒸馏
- [[krea-2]] · 在 DMD / DMD2 / TDM 等少步路线中做工程取舍

## 历史定位

- 2023-11 [[dmd]] · 用双 score 做终点分布匹配，但依赖大规模配对回归
- 2024-05 **DMD2** · 去大规模回归集，引入 TTUR、GAN 和 backward simulation
- 2024+ [[trajectory-distribution-matching]] · 从终点分布继续扩展到轨迹分布
