---
name: data-forcing-distillation
type: paper
source: https://arxiv.org/abs/2606.18478
upstream: https://github.com/csy2077/data-forcing-distillation
ingested: 2026-07-26
authors: Siyi Chen, Shaowei Liu, Yixuan Jia, Zian Wang, Huan Ling, Qing Qu, Jun Gao · arXiv v2 · 2026
year: 2026
---

# Data-Forcing Distillation · 让 DMD 的老师重新看到真实视频

DMD / DMD2 能把几十步视频扩散模型压成四步学生，但少步并不等于没有代价：换一个随机种子，结果可能仍像同一套构图；颜色和对比度也可能越训越重，最后不像真实视频。DFD 没有再造一套蒸馏框架，而是在 DMD2 已经训好的学生上做短暂后训练：冻结老师打分时，偶尔把输入从学生视频换成同条件的真实视频。

这看着只是一行代码，背后却有一条完整逻辑：反向 KL 只在学生已经到过的地方计算 → 漏掉的模式没有样本，也没有梯度 → 真实视频必须进入分布匹配的主梯度 → teacher score discrepancy 恰好把原式中的一项抵消 → 实现最终只需替换 teacher 的输入。

## 一句话

**DFD 让冻结老师偶尔在同条件真实视频上算 score，把真实数据从 GAN 的间接信号改成 DMD 主梯度里的直接信号。**

## 0. 先看完整拼图：训练多了一条真实数据支路，推理完全不变

训练时有三套网络：

1. `Gθ`：四步学生生成器；它是最终要部署的模型。
2. `sreal`：冻结的多步视频老师；它近似真实视频分布的 [[score-function|score]]。
3. `sfake`：在线更新的 fake-score 网络；它追踪学生当前生成分布。

一轮更新先由学生生成 `x̃=Gθ(z,c)`。fake-score 始终读取学生视频的带噪版本；teacher 则按概率 `p` 二选一：

```text
概率 1−p：teacher 读学生视频 → 原始 DMD
概率 p：  teacher 读同条件真实视频 → DFD
```

两条支路使用相同条件 `c`、扩散时刻 `t` 和高斯噪声 `ε`。算出 `sfake−sreal` 后，代码造一个冻结的伪目标，用普通 MSE 把预先计算好的方向传回 `Gθ`。训练期间 `sfake` 仍要持续更新。论文主方法说 GAN 可以删除；当前公开复现命令却仍继承 DMD2 的 GAN 配置，这项论文—代码差异在 §12 单独记录。

推理时只保留 `Gθ`。teacher、fake-score、真实视频和随机切换都删掉，所以 DFD 没有增加部署时的网络调用。

## 1. 痛点：为什么 DMD 容易少花样、颜色过重

DMD 最小化反向 KL：

\[
D_{\mathrm{KL}}\!\left(p_{\mathrm{fake}}\|p_{\mathrm{real}}\right)
=
\mathbb E_{\tilde x\sim p_{\mathrm{fake}}}
\left[
\log\frac{p_{\mathrm{fake}}(\tilde x)}
{p_{\mathrm{real}}(\tilde x)}
\right].
\]

这条式子回答“学生生成分布与目标分布差多少”：

- `pfake`：学生输出的概率分布；
- `preal`：老师所代表的目标视频分布；
- `x̃~pfake`：用于算平均值的样本来自学生，而不是来自真实数据；
- `log(pfake/preal)`：学生在某处放的概率相对目标多了还是少了；
- `E`：换许多学生样本后取平均。

关键不在 KL 三个字，而在采样位置。若真实分布有“近景”和“远景”两座岛，学生只会生成近景，那么训练批次里根本没有远景样本。损失仍会修学生已经到达的近景，却没有机会站到远景上发出“这里漏了”的梯度。

### 两个格子的数字例

把真实视频世界缩成两个构图：

```text
真实分布 P：近景 .50，远景 .50
塌缩学生 Q：近景 1.00，远景 0.00
```

反向 KL 按学生 `Q` 抽样：

```text
KL(Q||P)
= 1.00×ln(1.00/.50) + 0×ln(0/.50)
= ln 2
≈ .693
```

学生完全漏掉远景，代价仍是有限的 `.693`。第二项前面乘着 `Q(远景)=0`，漏掉的格子不贡献训练样本。若反过来算 `KL(P||Q)`，真实分布会以 `.5` 概率抽到远景，而 `ln(.5/0)` 趋向无穷大；这就是两种 KL 对漏模式态度不同的最小例子。

论文把多样性下降和过饱和都归因于这条 mode-seeking 主线。更谨慎地说：反向 KL 明确解释了“为什么漏掉的真实模式缺少直接惩罚”；过饱和则是作者在大规模视频蒸馏中观察到的另一类偏离真实数据的模式，DFD 的真实数据锚点在实验中明显缓解了它。

## 2. 前置概念：score 不是“真假分数”

score 定义为：

\[
s_p(x)=\nabla_x\log p(x).
\]

- `x`：一张图、视频或它们的 latent；
- `p(x)`：该位置附近的数据概率密度；
- `log`：把概率连乘变成相加，也让局部比例更容易求导；
- `∇x`：对 `x` 的每个元素求梯度；
- `sp(x)`：与 `x` 同形状的方向张量，指出怎样改动能更快走向高密度区域。

它不是“这张视频 82 分”的标量。若视频 latent 形状是 `[C,T,H,W]`，score 也是 `[C,T,H,W]`，每个元素都有自己的修改方向。

DFD 沿用 DMD 的两套 score：

- `sreal`：冻结 teacher 在真实视频上完成普通扩散训练后得到；DFD 阶段不再更新；
- `sfake`：用学生最新生成的视频训练，学生分布变化后它也要继续追。

两套网络结构可以相同，差别是它们学的是哪一批数据。完整训练过程见 [[score-function]]。

## 3. 原始 DMD 到底怎样走数据

给文本或首帧条件 `c`，学生把初始噪声 `z` 变成干净视频：

\[
\tilde x=G_\theta(z,c).
\]

再随机抽扩散时刻 `t` 和标准高斯噪声 `ε`，给学生视频加噪：

\[
\tilde x_t=\alpha_t\tilde x+\sigma_t\epsilon.
\]

- `θ`：学生参数；
- `z~N(0,I)`：学生的随机输入；
- `c`：文本、首帧或自回归历史；
- `t`：本轮随机噪声尺度；
- `αt`：保留多少干净视频；
- `σt`：加入多少噪声；
- `ε~N(0,I)`：与视频 latent 同形状的噪声；
- `x̃t`：两套 score 网络真正读取的带噪学生视频。

DMD 的理论梯度是：

\[
g_{\mathrm{DMD}}(\theta)
=
\mathbb E
\left[
\left(
s_{\mathrm{fake}}(\tilde x_t\mid c,t)
-
s_{\mathrm{real}}(\tilde x_t\mid c,t)
\right)
J_\theta
\right],
\qquad
J_\theta=\nabla_\theta G_\theta(z,c).
\]

这条式子算“学生参数应该往哪改”：

- `sfake(x̃t|c,t)`：当前学生分布在带噪学生视频处的方向；
- `sreal(x̃t|c,t)`：目标分布在**同一个位置**给出的方向；
- `Jθ`：生成器 Jacobian，把视频空间里的方向传回参数；
- 外层 `E`：对条件、初始噪声、扩散时刻和加噪噪声取平均。

梯度下降会减去 `gDMD`，所以效果可理解为靠近 real score，同时减去学生已经堆得太密的 fake score。

问题也在这里：teacher 只在学生自己的位置 `x̃t` 上回答问题。学生没去过的真实模式，仍不会自己走进公式。

## 4. DFD 的新信号：teacher score discrepancy

DFD 从同一条件抽一条真实视频：

\[
x\sim p_{\mathrm{real}}(\cdot\mid c).
\]

这里的竖线 `|c` 表示“已知条件 `c`”。文本是“海边奔跑的狗”时，真实视频也要对应这条描述；I2V 时，真实视频必须与输入首帧匹配。它不是从数据集任意抓一条无关视频。

真实视频和学生视频使用同一个 `t`、同一份 `ε`：

\[
x_t=\alpha_tx+\sigma_t\epsilon,\qquad
\tilde x_t=\alpha_t\tilde x+\sigma_t\epsilon.
\]

teacher score discrepancy 定义为：

\[
\Delta_{\mathrm{teacher}}
=
s_{\mathrm{real}}(x_t\mid c,t)
-
s_{\mathrm{real}}(\tilde x_t\mid c,t).
\]

这条式子只问一件事：**同一位冻结老师，在真实样本处和学生样本处给出的方向差多少。**

- 第一项把真实数据的位置带进训练；
- 第二项是原始 DMD 已经计算的 teacher score；
- 两项相减后，若学生分布已经与真实分布一致，二者在期望上相同，差值为零。

它并不要求某个随机种子 `z` 必须逐像素复刻这条真实视频 `x`。`x` 与 `Gθ(z,c)` 只共享条件；论文要求两者在后训练开始时已经足够接近，以控制梯度方差。

## 5. 为什么最后只剩 `sfake(学生) − sreal(真实)`

DFD 在 DMD 梯度上减去真实数据正则项：

\[
g_{\mathrm{DFD}}
=
g_{\mathrm{DMD}}
-
\mathbb E\left[
\Delta_{\mathrm{teacher}}J_\theta
\right].
\]

先把简称展开：

\[
\begin{aligned}
g_{\mathrm{DFD}}
&=
\mathbb E\left[
\bigl(s_{\mathrm{fake}}(\tilde x_t)
-s_{\mathrm{real}}(\tilde x_t)\bigr)J_\theta
\right]\\
&\quad-
\mathbb E\left[
\bigl(s_{\mathrm{real}}(x_t)
-s_{\mathrm{real}}(\tilde x_t)\bigr)J_\theta
\right].
\end{aligned}
\]

第二行前面有一个整体负号。把括号拆开后，`−sreal(x̃t)` 与后面产生的 `+sreal(x̃t)` 抵消：

\[
\boxed{
g_{\mathrm{DFD}}
=
\mathbb E\left[
\bigl(
s_{\mathrm{fake}}(\tilde x_t)
-
s_{\mathrm{real}}(x_t)
\bigr)J_\theta
\right]
}.
\]

这就是“一行代码”成立的代数原因。student 路径、fake-score 路径、加噪和伪损失都不用重写；只需让 teacher 偶尔从 `x̃t` 改读 `xt`。

### 同一组数验算抵消

把张量缩成标量，令：

```text
sfake(学生) = .2
sreal(学生) = 1.0
sreal(真实) = .4
Jθ = .5
```

先按“DMD 减正则”算：

```text
gDMD = (.2−1.0)×.5 = −.40
Δteacher = .4−1.0 = −.60
gDFD = −.40 − (−.60×.5)
     = −.10
```

再按抵消后的短公式直接算：

```text
gDFD = (.2−.4)×.5
     = −.10
```

两条路线得到同一个 `−.10`，说明抵消没有偷换符号。

## 6. 一行代码改变了哪一条数据流

论文伪代码的核心改动是：

```diff
- teacher_data = gen_data.detach()
+ teacher_data = data.detach() if rand() < p else gen_data.detach()
```

完整执行顺序是：

```text
1. gen_data = student(...)
2. teacher_data = 真实视频或 gen_data
3. perturbed_data = 加噪(gen_data, 同一 ε, 同一 t)
4. perturbed_teacher_data = 加噪(teacher_data, 同一 ε, 同一 t)
5. fake_score = fake_score_network(perturbed_data)
6. teacher_score = frozen_teacher(perturbed_teacher_data)
7. vsd_grad = fake_score − teacher_score
8. pseudo_target = gen_data − vsd_grad
9. MSE(gen_data, stopgrad(pseudo_target))
```

`detach` / `stopgrad` 只截断目标支路的梯度，不会把学生整体冻结。它的作用是把第 7 步算好的方向包装成自动求导能接收的 MSE。

### 伪目标从公式算到更新

官方实现用 teacher 与 fake-score 的 `x0` 预测构造归一化方向。为便于手算，令学生输出 `gen=1.2`，fake-score 预测 `.8`，teacher 预测 `1.0`：

\[
w_{\mathrm{norm}}
=
\frac{1}{|\,gen-teacher\,|+10^{-6}}
\approx
\frac{1}{|1.2-1.0|}
=5.
\]

```text
vsd_grad = (fake−teacher)×wnorm
         = (.8−1.0)×5
         = −1.0

pseudo_target = gen−vsd_grad
              = 1.2−(−1.0)
              = 2.2

L = 1/2×(gen−stopgrad(2.2))²
  = 1/2×(1.2−2.2)²
  = .5
```

把 `gen` 简化成可训练标量，梯度为：

```text
dL/dgen = 1.2−2.2 = −1.0
```

学习率 `.1` 时：

```text
gennew = 1.2−.1×(−1.0) = 1.3
Lnew（仍用本轮旧靶验方向）
= 1/2×(1.3−2.2)²
= .405
```

损失从 `.500` 降到 `.405`，也确实沿预先计算的方向移动。下一轮会重新生成视频、重算 score 和新伪目标。

## 7. 为什么要共享噪声，为什么不能从头直接训

### 7.1 共享噪声会把随机扰动抵消掉

取真实标量 `x=2`、学生输出 `x̃=1.5`、`α=.8`、`σ=.6`、`ε=−.5`：

```text
xt      = .8×2.0 + .6×(−.5) = 1.3
x̃t      = .8×1.5 + .6×(−.5) = .9
xt−x̃t   = .4
α(x−x̃) = .8×.5 = .4
```

同一份 `σε` 在相减时消失，所以两条带噪输入的距离只剩真实视频与生成视频的差。若各自采不同噪声，差值里还会混入 `σ(εreal−εfake)`，teacher discrepancy 会多一层无关随机波动。

### 7.2 成立条件控制的是方差，不是平均值

论文要求同一条件下的真实样本和生成样本已经足够接近：

\[
\mathbb E\left[
\|x-G_\theta(z,c)\|_2^2
\mid c
\right]
\le \delta(c)^2.
\]

- `||·||²₂`：对应元素作差、平方后求和；
- `E[·|c]`：固定条件 `c`，换不同真实视频和学生噪声后取平均；
- `δ(c)`：该条件允许的均方距离上界。

若 teacher score 在带噪路径上是 `L(c,t)`-Lipschitz，生成器 Jacobian 的算子范数不超过 `B`，论文给出 DFD 梯度与真实反向 KL 梯度的误差上界：

\[
\left\|
g_{\mathrm{DFD}}
-
\nabla_\theta D_{\mathrm{KL}}
\right\|_2^2
\le
B^2\alpha_t^2L(c,t)^2\delta(c)^2.
\]

- `L(c,t)`：输入改变 1 单位时，teacher score 最多改变多少；
- `B`：视频空间方向传回生成器参数时，最多被放大多少；
- `αt`：干净视频在当前带噪输入里保留的比例；
- `δ(c)`：真实与生成视频的距离上界。

例如 `B=.5、α=.8、L=1.5、δ=.5`：

```text
上界 = .5²×.8²×1.5²×.5²
     = .25×.64×2.25×.25
     = .09
```

这不是说实际误差一定等于 `.09`，而是说四个放大因子都受控时，误差不会超过该界。

因此 DFD 是 **post-training**：先让 DMD2 把学生训到能生成合理视频，再用真实数据修多样性和质感。论文从 teacher 初始化、跳过 DMD2 预训练的实验即使训练 1400 次仍失败；此时真实视频与噪声状学生相差太远，teacher discrepancy 方差太大。

## 8. 为什么默认一半 DMD、一半 DFD

论文并不要求每轮都把 teacher 输入换成真实视频，而是混合两种梯度：

\[
g(\theta)
=(1-w)g_{\mathrm{DMD}}(\theta)
+wg_{\mathrm{DFD}}(\theta),
\qquad w\in[0,1].
\]

实现时不在同一轮跑两遍，而是随机二选一：

\[
\nabla_\theta\mathcal L=
\begin{cases}
g_{\mathrm{DFD}}, & \text{概率 }p,\\
g_{\mathrm{DMD}}, & \text{概率 }1-p.
\end{cases}
\]

当 `p=w`，很多轮的平均梯度等于上面的加权和。设 `gDMD=−.4、gDFD=−.1、p=.5`：

```text
理论期望 = .5×(−.4)+.5×(−.1)=−.25

四轮恰好抽到：
DFD, DMD, DFD, DMD
平均 = [−.1−.4−.1−.4]/4 = −.25
```

单独四轮不保证恰好各两次；这里是用一组可核对样本说明“在期望上相同”。论文默认 `w=p=.5`，既保留 DMD 的快速收敛，也加入真实数据方向。`w=1` 的消融差异不大，但默认半混合更符合前面的距离条件。

## 9. 数据不是配角：真实数据进入梯度后，数据集就是方向来源

论文从约 96.6 万条带标注的 ViPE 视频开始，最终留下 3 万条 mixed-style 和 2 万条动画视频：

1. **三级描述**：Qwen3-VL-4B 一次前向同时生成长、中、短三种描述；视觉 token 只编码一次，作者估算比三次独立前向省约 3 倍；
2. **视觉特征**：每条视频均匀取 3 帧，用 CLIP ViT-B/32 编码，平均后做 L2 归一化，得到 512 维向量；
3. **聚类**：FAISS K-means，`K=1000`，迭代 50 次；
4. **候选展开**：每簇按到中心的距离排序，在百分位上均匀取 40 条，每条解码 5 帧；
5. **人工选择**：每簇挑 20 条“有代表性但彼此不同”的视频；全黑、解码失败等坏簇可以整簇丢弃；
6. **打包**：用 WebDataset 保存视频、三档描述和预先算好的文本 embedding。

这条数据管线解决的是一个新问题：DFD 已经会沿真实数据 score 学习，若真实批次重复、低质或条件不准，梯度也会把这些问题教给学生。聚类不是为了让训练更“高级”，而是防止随机抽样被大簇和近重复样本淹没。

这里的 `real data` 是相对学生分布而言的“参考数据样本”，不等于全部来自摄像机实拍。ViPE-Wild-1M 的源视频由 Wan2.1-14B 生成。DFD 证明的是把参考数据直接接进梯度有效，不能据此说它已经只靠自然实拍视频恢复真实世界分布。

## 10. 实验：质量、多样性和镜头运动要分开看

### 10.1 文生视频 · Wan2.1-1.3B

- 4 步学生；
- 70 条动画提示词 + 70 条 mixed-style 提示词；
- 每条提示词用 8 个随机种子，共 1120 条视频；
- 质量用 VBench，多样性用 CLIP / DINO 特征，镜头轨迹由 ViPE 估计。

关键原值：

| 方法 | VBench 平均 | CLIP 均值多样性 | DINO 均值多样性 | 镜头终点距离 | 镜头轨迹距离 |
|---|---:|---:|---:|---:|---:|
| Teacher | .899 | .178 | .301 | 30.571 | 26.651 |
| DMD2 | .901 | .120 | .190 | 9.148 | 4.284 |
| DP-DMD | .903 | .126 | .197 | 7.208 | 3.466 |
| DFD | **.906** | **.128** | **.205** | **18.513** | **19.256** |

DFD 在蒸馏模型里总体质量最好，四项视觉多样性均高于 DMD2 / DP-DMD，镜头轨迹差异也恢复很多。但它没有完全追平 teacher 的视觉多样性和镜头终点距离；“恢复”不等于“已经等同老师”。

### 10.2 图生视频 · Cosmos-Predict2.5-2B

- 348 张 VBench 测试图；
- 78 张从 ViPE 留出的测试图；
- 重点检查首帧主体、背景和后续时间一致性。

VBench 348 图平均分：

```text
Teacher .9285
DMD2    .9245
DP-DMD  .8843
DFD     .9303
```

DFD 平均分超过 teacher，背景一致性 `.9692`、美学质量 `.6371`、闪烁指标 `.9759` 等也优于对照。论文的定性案例还显示，DMD2 / DP-DMD 会在后续帧突然多出人物或破坏首帧结构，DFD 更稳定。

### 10.3 自回归视频

作者把 DFD 接到 Self Forcing，用 Wan2.1-1.3B 在 mixed-style 数据上训练。论文主要给定性证据：DMD2 长序列里会长出蟹状结构、断开的火车车厢等异常；DFD 的物体结构和物理连续性更稳。这里没有与前两项同等级的主表数字，不能把定性图写成已量化的全面领先。

## 11. 消融：哪些结论能说，哪些不能

### GAN 并非稳定增益

动画 T2V 消融中，去掉 GAN 后动态程度 `.3750→.5000`、成像质量 `.7210→.7452`；但闪烁和运动平滑略低。结论应是“没有一致收益，可以删掉以简化训练”，不是“GAN 在所有指标上都更差”。

### `w=.5` 与 `w=1` 差别小

两种权重各有胜负。`w=.5` 的动态程度与成像质量更高，`w=1` 的美学和运动平滑略高。论文选择 `.5` 主要因为它更稳妥地保留 DMD 信号，并非某张表证明 `.5` 全面最优。

### batch 16 → 128：平均更好，但不是每列都涨

平均分 `.9303→.9316`，主体一致性、美学、闪烁、运动平滑和 I2V 主体都提高；背景一致性 `.9692→.9685`、I2V 背景 `.9930→.9929` 略降。大 batch 可以降低随机 score discrepancy 的方差，但实验不支持“每项指标单调提升”。

### 真正硬的必要条件是 DMD2 预训练

跳过 DMD2、直接从 teacher 权重开始 DFD，训练 1400 次仍无法生成合理视频。这与理论条件一致，也是整篇最重要的负结果：DFD 是修复已经会生成的少步学生，不是取代 DMD2 的从零蒸馏目标。

## 12. 训练配方、开源实现和边界

论文表 4 的共同配置：

| 项目 | Wan T2V | Cosmos I2V |
|---|---:|---:|
| 帧数 | 81 | 81 |
| 分辨率 | 480p | 480p |
| 全局 batch | 16 | 16 |
| student / fake-score 学习率 | `1e-5` | `1e-5` |
| CFG scale | 5.0 | 3.0 |
| DMD2 预训练 | 25k 次 | 25k 次 |
| DFD 后训练 | 100 次 | 300 次 |
| GPU | 8×A100 | 16×A100 |

arXiv 摘要写 100–300 steps，正文 v2 §1 仍残留 50–100 的旧表述；论文表 4 和官方开源命令支持 `100 / 300`，本页按可复现配置记录，同时保留版本不一致。

本页核对官方仓库 commit `7281906026276dc46e23eb92b72238ebc050b463`：

- T2V / I2V 代码、数据地址、DMD2 checkpoint 与 DFD checkpoint 已公开；
- 训练开关是 `model.post_train=True` 和 `model.gen_real_replace_prob=.5`；
- 配置类里的 `gen_real_replace_prob` 默认值仍是 `.25`，官方 DFD 复现命令会显式覆盖成 `.5`；应以具体命令为准；
- 论文表 4 把 DFD 的判别器学习率标成 N/A，并主张可删除 GAN；但当前 README 命令没有覆盖 Wan / Cosmos 配置继承的 `gan_loss_weight_gen=.03`，还加载了 discriminator checkpoint。按该命令运行会继续训练并使用 GAN，除非显式把权重设为 0；
- 自回归 Self Forcing 实验在独立仓库；
- 实际 FastGen 实现保留完整 DMD2 脚手架，并非一个独立的极简 DFD 类。

### 局限

- 两步或更少时，快速运动仍会模糊，脸部细节会丢，视频还可能塌成近乎静止；
- DFD 需要条件匹配、质量高且有覆盖面的真实视频；
- 理论界依赖 teacher score 的 Lipschitz、生成器 Jacobian 有界及真实/生成样本足够接近；
- T2V 镜头与视觉多样性仍未完全追平 teacher；
- 论文的 AR 结果主要是定性证据；
- 更快生成会同步放大深伪、误导内容等风险，方法本身不提供安全过滤。

## 我的批注

- 最有价值的不是“一行代码”，而是作者先找到一项会与 DMD 原项精确抵消的正则，所以复杂理论最后才能落成一行输入替换。
- `data forcing` 容易被误解成 teacher forcing 式逐样本回归。DFD 并没有要求随机噪声 `z` 对应某条指定真实视频；真实视频提供的是分布方向。
- 真实数据进入 score 主梯度以后，数据选择从普通训练配方升级成算法的一部分。3 万条精选视频能否覆盖目标部署分布，直接决定能补回哪些模式。
- “超过 teacher”只发生在部分聚合质量指标；多样性表里 teacher 仍明显更强。不能把一个 Average 写成所有维度都超越。
- 它与 [[drifting-models]] 有相似精神：真实样本要进入方向计算，不能只让学生在自己的样本附近自我修正。但 DFD 仍依赖冻结扩散 teacher 与在线 fake-score，Drifting 则用样本和核现场造方向。

## 跟 wiki 里其他 paper 的关系

- [[dmd]] · 原始反向 KL score 蒸馏主线
- [[dmd2]] · 提供 DFD 的预训练学生、在线 fake-score 和代码底座
- [[senseflow]] · 修 DMD2 在大模型上的 fake-score 追踪与时间监督；DFD 修真实数据缺席和模式覆盖
- [[drifting-models]] · 不用 score 网络，直接用真实/生成样本构造吸引与排斥
- [[drift-ar]] · 把 Drifting 用到单步视觉解码；不是 DFD 的缩写或实现
- [[teacher-score-discrepancy]] · DFD 可跨任务复用的核心正则

## 历史定位

- 2023-12 [[dmd]] · 用 real / fake score 的反向 KL 把扩散模型蒸成一步
- 2024-05 [[dmd2]] · 用高频 fake-score 更新、GAN 与多步 backward simulation 去掉大规模配对集
- 2026-02 [[drifting-models]] · 直接从真实/生成样本构造单步生成方向
- 2026-06 **DFD** · 把真实样本 score 直接写回 DMD 主梯度，短后训练修多样性和过饱和
