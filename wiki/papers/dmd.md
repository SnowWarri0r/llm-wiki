---
name: dmd
type: paper
source: https://arxiv.org/abs/2311.18828
upstream: https://tianweiy.github.io/dmd/
ingested: 2026-07-22
authors: Tianwei Yin, Michaël Gharbi, Richard Zhang, Eli Shechtman, Frédo Durand, William T. Freeman, Taesung Park · CVPR 2024
year: 2024
---

# DMD · 不抄老师每一步，只让学生交出的整批图像像老师

DMD（Distribution Matching Distillation，分布匹配蒸馏）把需要几十到几百次网络前向的扩散模型，蒸成一次前向的生成器。它不要求同一份噪声必须复刻老师的逐步去噪轨迹，而是要求学生生成的整批图像，在质量和多样性上接近老师的输出分布。

## 一句话

**冻结的真实 score 负责把学生图像拉向老师分布，动态 fake score 负责防止学生挤进少数模式，离线配对回归再守住老师的粗结构。**

## 1. 一次生成到底省了什么

扩散老师从高斯噪声开始，反复调用同一个去噪网络。EDM 的 ImageNet 实验用 512 次前向，Stable Diffusion 文生图基线用 50 步；DMD 的学生 `G_θ` 只运行一次：

```text
老师：z → 去噪₁ → 去噪₂ → … → 去噪₅₀ → y
学生：z ───────────── Gθ 一次前向 ───────────→ x
```

NFE（Number of Function Evaluations）就是一次生成调用神经网络多少次。DMD 原论文是 **one-step / 1 NFE**；后续系统把 DMD 家族用于 4 步或 8 步，不应反过来把原始 DMD 写成“四步方法”。

学生沿用老师去噪器的网络结构，但不再接收时间步。参数从老师在最大噪声端 `t=T-1` 的权重初始化：

```math
G_\theta(z)\leftarrow \mu_{\text{base}}(z,T-1)
```

- `z`：从标准高斯 `N(0,I)` 采出的噪声张量；
- `G_θ`：参数为 `θ` 的一步生成器；
- `μ_base(x_t,t)`：冻结的扩散老师，输入带噪图和噪声时刻，预测干净图；
- `T=1000`：论文推导使用的离散扩散时间总数。

没有发生“去噪权重突然变成生成权重”。卷积或 attention 仍做同样的特征变换；变化的是时间条件被拿掉、输出目标改成从纯噪声直接得到图像，随后所有参数在新损失下继续学习。

## 2. 为什么只回归老师的答案还不够

最直接的蒸馏是预先保存很多 `(噪声 z, 老师最终图 y)`，再训练 `G_θ(z)≈y`。问题有两个：

1. 每造一个 `y`，老师都要完整跑几十或几百步；配对集很贵。
2. 一步网络很难逐点拟合“同一份噪声经过长轨迹后得到哪张图”这张复杂映射。只盯逐样本误差，生成结果容易变糊或失真。

DMD 放松要求：同一个 `z` 不必对应老师那张 `y`，只要很多 `z` 生成的一批图整体分布接近老师即可。不过论文并没有彻底丢掉配对回归，而是把它降为稳定训练的辅助项。

## 3. 分布匹配目标：先看整批图像是否来自同一个分布

学生把噪声分布推成输出分布 `p_fake`；目标分布记作 `p_real`。这里的“real”是扩散老师所学习的目标图像分布，不是训练时必须重新读取真实图片。

DMD 最小化反向 KL：

```math
D_{\mathrm{KL}}(p_{\mathrm{fake}}\Vert p_{\mathrm{real}})
=\mathbb E_{x\sim p_{\mathrm{fake}}}
\left[\log p_{\mathrm{fake}}(x)-\log p_{\mathrm{real}}(x)\right]
```

- `p_fake(x)`：学生当前在图像 `x` 附近放了多少概率密度；
- `p_real(x)`：老师目标分布在同一位置的密度；
- `log`：把概率比值变成差，数值也更稳定；
- `E`：对学生生成的大量样本求平均；
- 条件顺序 `fake || real` 很重要：平均点来自学生，而不是老师。

密度值本身算不出来，但训练只需要“把参数往哪里调”的梯度。

## 4. KL 梯度为什么变成两个 score 相减

[[score-function]] 是对数密度对图像的梯度：

```math
s_{\mathrm{real}}(x)=\nabla_x\log p_{\mathrm{real}}(x),\qquad
s_{\mathrm{fake}}(x)=\nabla_x\log p_{\mathrm{fake}}(x)
```

它不是一个“这张图有多真”的标量分数，而是和图像同形状的向量，告诉每个像素或 latent 往哪里改，密度会上升最快。

把 `x=G_θ(z)` 代入 KL，再用链式法则：

```math
\nabla_\theta D_{\mathrm{KL}}
=\mathbb E_z\left[
\left(s_{\mathrm{fake}}(x)-s_{\mathrm{real}}(x)\right)
\frac{\partial G_\theta(z)}{\partial\theta}
\right]
```

第一步，对 `log p(x)` 求 `x` 的导数，得到 score；第二步，乘 `∂G/∂θ`，把“图像该怎么改”传回生成器参数。`p_fake` 还会随 `θ` 改变，但它显式依赖参数的那一项在期望下为零：`E_{p_fake}[∇_θ log p_fake]=∇_θ∫p_fake(x)dx=∇_θ1=0`。

梯度下降会减去上式，所以效果是：

- `+s_real`：把样本拉向老师的高密度区域；
- `−s_fake`：抵消学生自己已经堆得很高的区域，避免所有噪声都挤向同一个模式。

只用 `s_real` 仍可能塌到最近的一个峰；两个 score 相减能摊开样本，但反向 KL 仍偏向覆盖已有高密度区，所以论文再加配对回归保护容易漏掉的模式。

## 5. 为什么先给学生图片加噪声

训练早期，学生图片可能离真实图像区域很远。未加噪时，两个分布可能根本不重叠，`p_real(x)=0` 会让 `log p_real(x)` 和 score 无法稳定计算。

DMD 随机采一个时间 `t`，给学生输出 `x` 加高斯噪声：

```math
x_t=\alpha_t x+\sigma_t\epsilon,qquad \epsilon\sim\mathcal N(0,I)
```

- `α_t`：保留原图的比例；
- `σ_t`：加入噪声的强度；
- `ε`：和图像同形状的标准高斯噪声；
- `I`：各维独立、方差为 1；
- `t`：论文从 `[0.02T,0.98T]` 均匀采样，避开两个极端端点。

加噪会把两团尖锐且分离的分布抹宽，让它们在 `x_t` 空间重叠。代价是梯度只是在多个噪声尺度上近似原始分布匹配，而不是直接拿干净图密度做精确 KL。

## 6. 扩散去噪器怎样给出 score

若一个扩散模型 `μ(x_t,t)` 预测带噪输入对应的干净图，那么它隐含的 score 是：

```math
s(x_t,t)=-\frac{x_t-\alpha_t\mu(x_t,t)}{\sigma_t^2}
```

分子是“当前带噪图”和“模型认为的干净图重新加权后”之间的残差；除以噪声方差，是把不同噪声尺度换到可比较的单位。

DMD 同时运行两个去噪器：

- `μ_real`：冻结的扩散老师，估计目标分布 score；
- `μ_fake^φ`：参数为 `φ` 的辅助去噪器，持续用学生最新生成的图训练，估计学生当前分布 score。

因为 `G_θ` 每轮都在变，`p_fake` 也在变，fake-score 模型必须追着它更新：

```math
L_{\mathrm{denoise}}^\phi=
\left\|\mu_{\mathrm{fake}}^\phi(x_t,t)-\operatorname{stopgrad}(x)\right\|_2^2
```

`stopgrad(x)` 的数值仍是 `x`，但反向传播到此为止。这个损失只训练 `φ`，不能顺手把生成器也往“更容易被 fake-score 拟合”的方向推。

最终给生成器的近似梯度是：

```math
\nabla_\theta D_{\mathrm{KL}}\approx
\mathbb E\left[
w_t\alpha_t
\left(s_{\mathrm{fake}}(x_t,t)-s_{\mathrm{real}}(x_t,t)\right)
\frac{\partial G_\theta(z)}{\partial\theta}
\right]
```

`w_t` 会归一化不同噪声时刻的梯度大小。论文公式使用：

```math
w_t=\frac{\sigma_t^2}{\alpha_t}\,
\frac{CS}{\left\|\mu_{\mathrm{real}}(x_t,t)-x\right\|_1}
```

`C` 是通道数，`S` 是空间位置数，`CS/||·||₁` 等于“每个元素绝对误差的倒数”。附录伪代码改用 `mean(abs(x-pred_real))` 做分母，并明确说它与正文公式略有差异。

## 7. 一条数字例：从噪声算到一次参数更新

用一个标量代替整张图和几亿参数。设：

```text
Gθ(z)=θ+z，初始 θ=0.7，z=0.5，所以 x=1.2
α=.8，σ=.6，ε=−.5
```

第一步，给学生输出加噪：

```text
x_t = .8×1.2 + .6×(−.5) = .66
```

假设两个去噪器在这次前向给出：

```text
μ_real(x_t,t)=1.5
μ_fake(x_t,t)=0.9
```

第二步，分别换成 score：

```text
s_real = −(.66−.8×1.5)/.6² = 1.5
s_fake = −(.66−.8×0.9)/.6² = 1/6 ≈ .1667
```

第三步，算时间权重。标量例里 `C=S=1`：

```text
w = .6²/.8 × 1/|1.5−1.2| = .36/.8/.3 = 1.5
```

第四步，`∂G/∂θ=1`，所以 KL 梯度：

```text
g = 1.5×.8×(.1667−1.5)×1 = −1.6
```

若学习率是 `.1`：

```text
θ_new = .7 − .1×(−1.6) = .86
同一个 z 再生成：x_new=.86+.5=1.36
```

学生输出从 `1.2` 向 real denoiser 认为更合理的 `1.5` 移动。符号也对上了：梯度是负数，梯度下降减去负数，因此参数增大。

## 8. 伪损失与 stopgrad：怎样把算好的方向塞进自动求导

附录 Algorithm 2 不直接计算一个可微 KL 标量，而是先算出目标梯度 `g`，再构造：

```math
L_{\mathrm{pseudo}}=\frac12
\left\|x-\operatorname{stopgrad}(x-g)\right\|_2^2
```

沿用上例，`x=1.2, g=-1.6`，冻结目标是 `x-g=2.8`：

```text
L=.5×(1.2−2.8)²=1.28
dL/dx=1.2−2.8=−1.6=g
```

这条损失的数值本身没有“KL 是 1.28”的含义；它只借自动求导把预先算好的 `g` 送回 `G_θ`。若不 stopgrad，右边的 `x` 会跟左边一起变化，`x-(x-g)=g` 变成常数，梯度会抵消成 0。

计算 `μ_real` 和 `μ_fake` 时也关闭梯度：更新生成器这一拍只把它们当方向计算器；下一拍才单独用去噪损失更新 fake-score 模型。

## 9. 回归损失为什么仍然不能删

DMD 预先用确定性求解器生成小型配对集 `D={(z_ref,y_ref)}`。同一份噪声 `z_ref` 经老师多步采样得到 `y_ref`，学生用 [[lpips]] 比较感知特征：

```math
L_{\mathrm{reg}}=
\mathbb E_{(z_{\mathrm{ref}},y_{\mathrm{ref}})\sim D}
\left[\operatorname{LPIPS}(G_\theta(z_{\mathrm{ref}}),y_{\mathrm{ref}})\right]
```

它不是为了逐像素复刻，而是守住主体、布局和老师对同一噪声的粗映射。分布梯度让图片更真、分得更开；回归损失减少漏模式和训练漂移。只留其中任何一条都不够。

最终更新生成器：

```math
L_G=D_{\mathrm{KL}}+\lambda_{\mathrm{reg}}L_{\mathrm{reg}},qquad
\lambda_{\mathrm{reg}}=0.25\ \text{（多数实验）}
```

两项使用不同数据流：KL 项吃学生刚生成的未配对样本，回归项吃离线配对样本。附录还用 L2 替代 LPIPS：CIFAR-10 FID `2.78`，略差于 LPIPS 的 `2.66`，说明回归项并不只在一种距离函数下有效。

## 10. 一轮训练的真实执行顺序

1. `G` 和 `μ_fake` 都从冻结老师 `μ_real` 复制权重。
2. 采新噪声 `z`，得到当前学生图 `x=G(z)`；另取配对样本 `(z_ref,y_ref)`。
3. 随机采 `t`，给 `x` 加噪；冻结两个 score 网络，计算 `s_fake-s_real`。
4. 用伪损失把分布匹配梯度传回 `G`。
5. 用 `LPIPS(G(z_ref),y_ref)` 算回归梯度；两项相加，更新 `G`。
6. 把 `x` 当作冻结目标重新加噪，用普通去噪 MSE 单独更新 `μ_fake`。
7. 下一轮重新生成新的 `x`；fake score 继续追踪已经变化的学生分布。

推理时只保留 `G`。冻结老师、fake-score 模型、离线配对集、加噪和两套训练损失全部消失，所以训练很重不妨碍一次前向生成。

## 11. Classifier-Free Guidance 怎样蒸进一次前向

[[classifier-free-guidance]]（CFG）通常要分别跑有条件和无条件预测，再放大两者差值。DMD 固定一个 guidance scale：先用带 CFG 的老师生成离线 `(z,y)` 配对；算 real score 时也用 guided teacher 的均值预测；fake score 公式不变。

这样学生把指定 CFG 强度下的结果学进权重，推理只跑一次。代价是 guidance scale 被固定；想在推理时自由调强弱，不能直接沿用这一版单模型。

## 12. 训练配方与复现账

| 任务 | 老师 / 配对集 | 训练配置 | 结果 |
|---|---|---|---|
| CIFAR-10 class-cond | EDM；100K 对；18-step Heun | 7 GPU，batch 392，300K iter，lr `5e-5` | FID 2.66 |
| ImageNet 64×64 | EDM；25K 对；256-step Heun | 7 GPU，batch 336，350K iter，lr `2e-6` | FID 2.62 |
| LAION-Aesthetic 6.25+ | SD1.5；500K 对；50-step PNDM；CFG 3 | 72 A100，DM batch 2304 / reg 1152，20K iter，约 36h | COCO FID 11.49 |
| LAION-Aesthetic 6+ | SD1.5；最终扩到 12M 对；CFG 8 | 约 80 A100，约两周，训练中多次改配方 | COCO FID 14.93 / CLIP .320 |

LAION 6+ 的训练日志从 2.5M 配对、`λ_reg=.1` 一路改到 12M、`.25`，还更换 VAE 和最大 DM 时间步。作者明确说这条日程受时间和算力限制，未必最优。它不是一张可以原样复用的干净 recipe。

## 13. 实验和消融应该怎样读

ImageNet 64×64：DMD 1 次前向 FID `2.62`，EDM 老师 512 次前向 `2.32`；Consistency Model 1 步 `6.20`。这里的“512×”是网络调用次数，不等于所有硬件上的端到端延迟都恰好快 512 倍。

COCO 30K、CFG 3：DMD `0.09s / FID 11.49`，SD1.5 老师 `2.59s / 8.78`，延迟约快 `28.8×`，FID 仍差 `2.71`。论文另报 FP16 可到约 20 FPS，但不能和表内 `.09s` 当成同一测速口径。

关键消融：

| 配方 | CIFAR FID ↓ | ImageNet FID ↓ | 说明 |
|---|---:|---:|---|
| 去掉分布匹配 | 3.82 | 9.21 | 结构和逼真度明显受损 |
| 去掉回归损失 | 5.58 | 5.61 | 训练不稳，出现模式坍缩 |
| 完整 DMD | 2.66 | 2.62 | 两项组合最好 |

时间权重在 CIFAR 上也有独立消融：DreamFusion 权重 `3.60`，ProlificDreamer 权重 `3.71`，DMD 的归一化权重 `2.66`。

## 14. 局限、后续版本和一句话带走

1. 一步学生仍略逊于高步数老师，尤其复杂文生图分布。
2. 训练时同时保留生成器、冻结老师和可训练 fake-score 模型，显存很高。
3. fake-score 模型要追逐不断变化的学生分布；追不上时，分布梯度会失真。
4. 稳定训练仍依赖离线老师配对集；LAION 6+ 最终用了 12M 对，绝非“完全无数据蒸馏”。
5. 反向 KL 和 score 近似仍可能漏模式，回归项只是缓解，不是数学保证。
6. 固定 CFG 能换来单次前向，但牺牲推理时自由调 guidance 的能力。

后来的 DMD2 去掉回归配对集，加入 two-time-scale 更新、GAN 损失和多步训练；TDM 把终点分布匹配扩展到轨迹中间点。它们解决的是原始 DMD 暴露出的新问题，不能倒过来写成原论文已经具备的能力。

一句话记住：**DMD 不是让一步学生照抄老师五十步，而是用冻结老师 score 与动态学生 score 的差，直接修改学生的出图分布；再用少量逐噪声回归拴住结构和模式。**

## 关键概念

- [[dmd-distillation]] · DMD 家族速查与版本边界
- [[score-function]] · 两个 score 为什么是图像修改方向
- [[entropy-kl]] · 反向 KL 在匹配什么
- [[pushforward-distribution]] · 噪声经 `G_θ` 后怎样形成 `p_fake`
- [[lpips]] · 回归项为什么不只比像素
- [[classifier-free-guidance]] · 被固定进一次前向的 guidance
- [[gradient-backprop]] · 链式法则、stopgrad 与伪损失

## 我的批注

- 最值得记的不是“score 相减”，而是训练里有三个模型、两条数据流、两次不同的 stopgrad；少一个都可能把方向说反。
- 原论文标题的 one-step 是严格的一次前向。把后续产品的 4-NFE 统一叫“DMD 原理”可以，把原论文写成四步不可以。
- “不逐样本对齐”也不能说成“完全不需要老师配对”：原始 DMD 恰恰靠回归配对稳定训练，DMD2 才专门处理这项限制。
- Algorithm 2 的 MSE 是梯度注入器，不是可以解释数值大小的真实 KL loss；这点对读实现尤其重要。
- DMD 和 [[drifting-models]] 都有吸向目标、排斥当前分布的结构，但前者靠两套扩散 score，后者靠核加权样本漂移，不能只因箭头相似就当成同一个算法。

## Sources

- [One-step Diffusion with Distribution Matching Distillation](https://arxiv.org/abs/2311.18828)
- [CVPR 2024 Open Access](https://openaccess.thecvf.com/content/CVPR2024/html/Yin_One-step_Diffusion_with_Distribution_Matching_Distillation_CVPR_2024_paper.html)
- [作者项目页](https://tianweiy.github.io/dmd/)
