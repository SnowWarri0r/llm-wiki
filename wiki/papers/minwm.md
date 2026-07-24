---
name: minwm
type: paper
source: https://arxiv.org/abs/2605.30263
upstream: https://github.com/shengshu-ai/minWM
ingested: 2026-07-24
updated: 2026-07-24
authors: Min Zhao, Hongzhou Zhu, Bokai Yan, Zihan Zhou, Yimin Chen, Wenqiang Sun, Kaiwen Zheng, Guande He, Xiao Yang, Chongxuan Li, Fan Bao, Jun Zhu
year: 2026
---

# minWM · 把离线视频扩散模型改造成可操控、能逐段输出的世界模型

普通文生视频模型像一家电影工作室：收到剧本后，关门渲染完整段视频，最后一次性交片。交互式世界模型更像游戏引擎：你按下“向左转”，它要立刻给出下一小段画面，之后还能接着响应新动作。

minWM 不是提出一套从零训练的新基础模型，而是公开一条改造流水线：从 Wan2.1 或 HunyuanVideo 1.5 这类双向视频扩散模型出发，先加入相机控制，再改成因果生成，接着蒸馏到四步，最后让学生在自己生成的历史上练习。论文、代码、训练脚本、阶段 checkpoint 和复现文档共同构成了它的主要贡献。

## 一句话

**minWM 用 PRoPE 把相机轨迹写进双向视频模型，再依次经过 teacher-forcing AR、causal ODE 或 causal consistency initialization、asymmetric DMD，把高质量但离线的多步模型改造成四步因果视频生成器。**

## 0. 先看完整拼图：它到底改了哪五件事

```text
带相机轨迹的数据
      ↓
双向视频扩散 + PRoPE
先学会“镜头该怎么动”
      ↓
Stage 1 · Teacher Forcing AR
从整段一起去噪改成只看过去、逐段生成
      ↓
Stage 2a · Causal ODE ─┐
或 Stage 2b · Causal CD ├→ 把多步压到 4 步
                        ↓
Stage 3 · Asymmetric DMD + self-rollout
用双向模型的分布质量修正因果学生
      ↓
按 4 个 latent frame 一段，逐段输出
```

这里有两个“4”，意思不同：

- **4 latent frames per chunk**：一次自回归提交多少个 latent 时间位置；
- **4 denoising steps**：每个 chunk 调用几次去噪网络。

前者决定时间分块，后者决定每块的采样成本。

## 1. 普通视频生成离交互还差三步

### 1.1 要能听动作

文本“一辆车驶过街道”只能规定大意，不能在生成到一半时精确执行“现在左转、停住、再后退”。minWM 选择相机轨迹作为动作接口，目标是让每一帧都服从给定相机内参与外参。

### 1.2 要因果

双向视频扩散一开始就拿到整段 noisy latent，每轮去噪时前后帧互相修改，容易保持整体一致；但它必须等整段生成完才能交付第一帧。交互模型必须只读过去，先交付第一段，再生成后续段。

### 1.3 要少步

即便改成 AR，如果每个 chunk 仍跑几十步去噪，第一段还是慢。minWM 再把多步因果模型蒸成四步学生。

因此论文解决的不是一个孤立模块，而是三个连续约束：

```text
可控 ── 镜头听不听
因果 ── 能不能先出前段
少步 ── 每段能不能尽快出
```

## 2. 数据：相机 pose 不准，控制监督就会自相矛盾

每个训练样本除了视频，还要给每帧相机内参 `K_i` 和 world-to-camera 外参 `T_i^{cw}`。若画面明明向右移动，估计出的相机却写成向左，模型看到的就是互相打架的监督。

论文比较了三种来源：

1. **SpatialVid 的感知估计 pose**：在作者当前训练设置下，即使过滤后也没得到可靠控制；作者明确说这不证明 SpatialVid 天生不适用；
2. **DL3DV 重建后沿指定轨迹重新渲染**：轨迹是人为规定的，模型学会了控制；
3. **开源版本**：从 OpenVid 等来源取图，再让 WorldPlay 按指定轨迹生成视频，也能提供一致的轨迹监督。

核心不是“合成一定优于真实”，而是动作标签必须与画面变化吻合。真实视频若只有噪声很大的估计 pose，可能反而不如可控生成或重渲染数据。

## 3. PRoPE：不是额外塞一串 pose token，而是改 attention 的坐标系

### 3.1 先把相机写成 4×4 投影矩阵

第 `i` 帧有：

- `K_i`：3×3 相机内参，包含焦距和主点；
- `T_i^{cw}`：4×4 world-to-camera 外参，把世界坐标转换到相机坐标；
- `e_4=(0,0,0,1)^T`：补齐齐次坐标最后一行。

PRoPE 合成：

\[
\widetilde P_i=
\begin{bmatrix}
[K_i\;0]T_i^{cw}\\
e_4^\top
\end{bmatrix}
\in\mathbb R^{4\times4}.
\]

这一步的意义是把“相机在哪里、朝哪看、焦距多少”整理成一个可参与线性变换的矩阵。

### 3.2 一个 token 同时需要相机位置和画面内位置

第 `t` 个视觉 token 属于第 `i(t)` 帧，二维坐标为 `(x_t,y_t)`。PRoPE 构造分块矩阵：

\[
D_t^{\mathrm{PRoPE}}=
\begin{bmatrix}
I_{d/8}\otimes\widetilde P_{i(t)}&0\\
0&
\begin{bmatrix}
\mathrm{RoPE}_{d/4}(x_t)&0\\
0&\mathrm{RoPE}_{d/4}(y_t)
\end{bmatrix}
\end{bmatrix}.
\]

- `d`：一个 attention head 的特征维度；
- `I_{d/8}`：`d/8` 维单位矩阵；
- `⊗`：Kronecker product，这里可理解为把同一个 4×4 相机矩阵重复铺到若干特征块；
- `RoPE_{d/4}(x_t)`、`RoPE_{d/4}(y_t)`：分别编码横向、纵向位置；
- 外层分块：一部分特征负责相机投影，另一部分保留二维画面位置。

### 3.3 为什么最后留下的是相对相机关系

论文把该变换放进 Q/K/V attention：

\[
\operatorname{Attn}_{\mathrm{PRoPE}}(Q,K,V)=
D\odot\operatorname{Attn}
\left(D^\top\odot Q,D^{-1}\odot K,D^{-1}\odot V\right).
\]

这里的 `⊙` 表示把对应分块变换施加到特征，不是把两个同形标量矩阵简单逐元素相乘。两个帧的 token 做 attention 时，关键交互项会包含：

\[
\widetilde P_{i_1}\widetilde P_{i_2}^{-1}.
\]

这就是从第 2 帧相机坐标换到第 1 帧相机坐标的相对投影变换。

### 3.4 只平移 1 米的数字例子

为简化，令内参为单位矩阵；第 1 帧相机不动，第 2 帧相机沿世界 `x` 轴移动 `+1`。world-to-camera 外参要把世界反向平移 `−1`，所以相对项为：

\[
\widetilde P_1\widetilde P_2^{-1}
=
\begin{bmatrix}
1&0&0&1\\
0&1&0&0\\
0&0&1&0\\
0&0&0&1
\end{bmatrix}.
\]

右上角的 `+1` 直接记录两台相机的相对水平位移。真实情况还会同时出现三维旋转、平移和不同内参。

### 3.5 论文公式与当前开源实现的边界

论文用一条 GTA 形式公式描述 PRoPE。官方仓库在 Wan 与 HY 两个 backbone 中保留普通 RoPE attention 路径，同时增加独立 PRoPE attention 路径，再通过**零初始化输出投影**把新分支逐渐加回主干。这意味着训练刚开始时模型近似原始 backbone，不会突然被随机相机分支扰乱。它是实现层的稳定化设计，不能简单缩写成“直接把原 attention 全部换掉”。

## 4. Stage 1：先教会模型按时间往前生成

视频 latent 按时间切成 chunk。假设当前训练第三段 `C`：

```text
真实 A + 真实 B + noisy C → 还原真实 C
```

因果 attention mask 让 `C` 只能读取 `A、B`，不能偷看未来 `D`。论文把干净视频和 noisy counterpart 拼在一起训练，这是视频扩散版 [[teacher-forcing-video-diffusion|teacher forcing]]。

它解决了“会不会从左到右生成”，却留下两个问题：

1. 仍需多步去噪，延迟高；
2. 训练历史是真实 `A、B`，推理历史却是模型自己生成的 `Â、B̂`，即 exposure bias。

Stage 2 解决第一条，Stage 3 的 self-rollout 主要处理第二条并补质量。

## 5. Stage 2：两条路都把多步老师压成四步学生

### 5.1 方案 A · Causal ODE：先把慢老师的中间作业全部存下来

AR diffusion 老师先跑 PF-ODE 去噪轨迹，离线保存中间 noisy latent。学生随机取一个预定少步时刻，直接回归干净 chunk：

\[
\theta^*=
\arg\min_\theta
\mathbb E\left[
\left\|
G_\theta(x_t^i,x_{\mathrm{gt}}^{<i},t)-x_0^i
\right\|_2^2
\right].
\]

- `θ`：少步学生参数，`θ*` 是最小化损失后的参数；
- `i`：当前自回归 chunk 编号；
- `x_t^i`：当前 chunk 在噪声时刻 `t` 的中间状态；
- `x_gt^{<i}`：第 `i` 段之前的真实干净历史；
- `G_θ`：少步因果学生；
- `x_0^i`：当前 chunk 的干净目标；
- `‖·‖_2²`：每个元素误差平方后求和；
- 外层 `E`：对历史、时刻、chunk 和中间状态采样后取平均。

二维例子：目标 `x_0=[1,1]`，学生预测 `[.8,1.4]`：

```text
L = ‖[.8,1.4] − [1,1]‖²
  = (.8−1)² + (1.4−1)²
  = .04 + .16
  = .20
```

若代码用 mean MSE，两个元素再除以 2 得 `.10`；论文写的是平方范数，因此这里按求和得到 `.20`。

这条路监督直观，但生成慢老师轨迹耗时，中间 latent 也占磁盘。

### 5.2 方案 B · Causal CD：不存整条轨迹，只现场走一小步

Causal Forcing++ 用 [[causal-consistency-distillation|causal consistency distillation]] 代替离线 ODE 数据：

\[
\theta^*=
\arg\min_\theta\mathbb E\!\left[
w(t)\,
d\!\left(
G_\theta(x_t^i,x_\mathrm{gt}^{<i},t),
G_{\theta^-}(\hat x_{t-\Delta t}^i,x_\mathrm{gt}^{<i},t-\Delta t)
\right)
\right].
\]

- `\hat x_{t-Δt}^i`：因果老师从 `x_t^i` 沿 ODE 走一小步后的状态；
- `G_{θ^-}`：当前学生参数的 EMA 副本，停止梯度，提供较稳定目标；
- `w(t)`：噪声时刻权重；
- `d(a,b)`：两个预测的距离。

若左边预测 `.60`、EMA 目标 `.55`、`d` 为平方差、`w=2`：

```text
L = 2 × (.60−.55)² = .005
```

目标是让同一条去噪轨迹上相邻时刻都指向相同干净结果。它不需要保存整条 ODE 轨迹，但训练时要在线运行老师和 EMA 学生；成本没有消失，只是从数据准备/磁盘换成了训练计算。

### 5.3 为什么 Stage 2 还不能结束

两条方案都由**因果 AR 老师**提供监督。学生最多学到这位老师的质量上限，而原始双向模型能看整段，通常质量更好。因此还需要 Stage 3，让双向模型重新做质量老师。

## 6. Stage 3：因果学生自己往前跑，双向模型负责纠偏

学生先 self-rollout 生成完整视频 `\tilde x`。再随机加噪成 `\tilde x_t`，交给两套双向 score 网络：

- `s_real`：冻结的高质量、相机可控双向模型，描述真实/目标分布该往哪改；
- `s_fake`：在线训练的双向模型，描述学生当前生成分布；
- 两套 score 都收到与学生相同的相机条件，否则纠偏方向可能与控制轨迹冲突。

论文写出的 DMD 梯度为：

\[
\nabla_\theta
\mathbb E_t\!\left[
D_{\mathrm{KL}}(p_{\theta,t}\|p_{\mathrm{data},t})
\right]
=-
\mathbb E\!\left[
\left(s_{\mathrm{real}}(\tilde x_t,t)-
s_{\mathrm{fake}}(\tilde x_t,t)\right)
\frac{\partial\tilde x}{\partial\theta}
\right].
\]

- `p_{θ,t}`：学生输出加噪到时刻 `t` 后的分布；
- `p_data,t`：目标数据加相同噪声后的分布；
- `D_KL`：两个分布的 KL 差异；
- `∂\tilde x/∂θ`：参数变化怎样改变学生输出；
- `E`：对学生视频、噪声时刻和加噪样本取平均。

一个标量方向例子：

```text
s_real = 1.2
s_fake = 0.4
∂x/∂θ = 0.5

梯度 = −(1.2−0.4)×0.5 = −0.4
若 θ=1、学习率=.1：
θ_new = 1 − .1×(−.4) = 1.04
```

参数增加的方向会让输出更接近 real score 指出的区域，同时扣掉学生分布已经过密的方向。完整 DMD 直觉见 [[dmd-distillation]]。

这里“asymmetric”的核心是角色不对称：

```text
生成者：因果、四步、逐段 self-rollout
评判者：双向、多步、整段看视频的 real/fake score
```

高质量老师不必具有可部署的因果结构，只需在训练时提供更好的分布方向。

## 7. 部署：先出第一段，不等于整段视频已经更快 200 倍

论文在单张 A800 上报告第一帧延迟，且排除了 VAE 时间：

| Backbone | 多步双向 | 多步 AR | 四步 AR | 相对双向 |
|---|---:|---:|---:|---:|
| HY1.5 | 771.041 s | 81.014 s | 3.446 s | 223.75× |
| Wan2.1 | 269.055 s | 28.651 s | 1.137 s | 236.64× |

为什么倍率这么大？多步双向模型要先完成整个 77 帧序列，第一帧才能交付；AR 模型生成首个 chunk 后就能交付。因此这张表衡量的是**用户多久看到第一批结果**，不是同等条件下生成完整视频的总 wall-clock。

还要保留三条口径：

1. 只测单张 A800；
2. 排除了 VAE 编解码；
3. 论文没有报告端到端 FPS、完整视频总时长或服务并发。

官方仓库已经开放四步 DMD 推理、按 chunk 因果生成、KV cache 和多卡 sequence parallel；README 同时把“inference acceleration”标成 TBD。因此“能逐段生成”与“已经交付完整的流式服务运行时”不能画等号。

## 8. 两种 backbone 为什么都能接

minWM 实例化了两条模型线：

| Backbone | 架构 | 参数量 | 输入 | 四阶段训练 |
|---|---|---:|---|---|
| Wan2.1-T2V | DiT + cross-attention | 1.3B | 文本→视频 | 已开放 |
| HY1.5-TI2V | MMDiT | 8B | 文本+图像→视频 | 已开放 |

框架把 dataset、loss、stage 与模型 wrapper 分开，让同一条训练逻辑可以接不同 backbone。但“结构上可扩展”不等于接第三个模型只改配置：新 backbone 仍需对齐 latent 形状、attention、相机注入、KV cache、并行和 checkpoint。

训练基础设施还包括：

- Wan 数据常编码进 LMDB；
- HY 预编码 latent 以每样本 `.pt` 加索引保存；
- HY 脚本使用 sequence parallel 与分片数据并行；
- Stage 2a 需要额外 ODE 数据，Stage 2b 与 Stage 3 可复用原训练条件数据。

这些是“full-stack”的实际含义：不止一条 loss，还有数据格式、分布式训练、阶段 checkpoint 和推理入口。

## 9. 论文配方与当前脚本默认值不要混读

论文报告的实验配方：

| Backbone | batch | lr | 双向相机控制 | Stage 1 | Stage 2 | Stage 3 |
|---|---:|---:|---:|---:|---:|---:|
| HY1.5 | 32 | 1e−5 | 8K | 4K | 1.5K | 500 |
| Wan2.1 | 32 | 2e−6 | 5K | 4K | 2K | 200 |

HY 有一个重要脚注：8K 双向 checkpoint 用于 Stage 3 的 `s_real/s_fake`，Stage 1 则从 5K checkpoint 初始化。

当前官方仓库的部分通用脚本把 `max_steps` 设得比论文实际训练步数大，Wan 默认 YAML 的 total batch 也不总是 32。这些值更像可继续训练的上限/模板，不是论文表中实验的逐字复制。复现论文结果时应以论文配方、对应 stage 文档和实际启动参数三者共同核对，不能只看一个 YAML。

## 10. 实验真正证明了什么

### 10.1 已有直接数字

- 两个 backbone 的第一帧延迟显著下降；
- HY 相机控制在 1–2K steps 仍不可控，约 5K 开始出现，8K 较强；
- Wan batch `<4` 常失败，batch 8 明显改善但仍不稳，batch 16 能完成整条流程。

后两组是论文样例图得出的实践观察，不是带多随机种子、置信区间的定量规律，不能推广成所有数据和 backbone 的硬阈值。

### 10.2 主要依赖定性样例

论文用生成视频展示相机控制保持住了，但没有报告：

- FID / FVD；
- 相机轨迹误差；
- 动作跟随成功率；
- 长 rollout 漂移；
- 与其他实时世界模型的统一 benchmark。

因此“框架跑通并降低首帧等待”证据较强，“四步模型与双向老师质量等价”则没有被定量证明。

## 11. 当前开放边界：哪些能跑，哪些仍是路线图

截至官方仓库提交 `df522a26cd4409d3e3e8f269cc98eac069b5df47`：

### 已开放

- Wan2.1 与 HY1.5 的双向相机控制、Stage 1、Stage 2a/2b、Stage 3；
- 中间 checkpoint、数据处理、训练和四步推理脚本；
- PRoPE 相机条件；
- KV cache、sequence parallel 等基础组件。

### README 仍标 TBD

- 在已有世界模型上直接 finetune 的入口；
- human-pose condition；
- latent concat 与 cross-attention 条件注入；
- inference acceleration。

论文摘要与示意图把 streaming inference 纳入完整愿景；当前代码已经能因果分块输出，但仓库仍明确把进一步推理加速列为 TBD。读论文时应把“研究框架的目标”与“当前版本交付状态”分开。

## 12. 怎么评价 minWM

### 最有价值的地方

它把过去分散在多篇论文里的步骤连成可执行路径：PRoPE 负责控制，teacher forcing 负责因果结构，ODE/CD 负责少步初始化，DMD 负责重新贴近高质量双向分布。每阶段都有输入输出 checkpoint，研究者可以替换其中一段，而不必从论文公式猜出完整训练工程。

### 最大的证据缺口

页面标题里的“real-time”主要由排除 VAE 的第一帧延迟支撑。Wan 的 1.137 秒和 HY 的 3.446 秒能显著减少等待，却不等同于高帧率实时交互。缺少端到端 FPS、完整 rollout 时延和长期一致性评测。

### 最容易带走的通用方法

当离线生成模型要改造成在线系统时，可以按三层拆问题：

1. **条件是否精确**：动作标签与画面变化是否一致；
2. **生成顺序是否可部署**：双向全局计算能否改成因果 chunk；
3. **每个 chunk 是否够快**：少步蒸馏、缓存和运行时加速分别贡献多少。

minWM 给出的不是唯一答案，但提供了一条难得完整、可检查、可替换的基线。

## 关系

- [[interactive-video-world-modeling-survey]] · 把 minWM 放回动作、记忆、速度三角
- [[autoregressive-vs-bidirectional-video-diffusion]] · 为什么双向老师与因果学生分工
- [[projective-rope]] · PRoPE 的独立概念页
- [[teacher-forcing-video-diffusion]] · Stage 1 与 exposure bias
- [[causal-consistency-distillation]] · Stage 2b 为什么能省去离线 ODE 数据
- [[dmd-distillation]] · Stage 3 的 real/fake score
- [[ode-vs-sde]] · PF-ODE 轨迹是什么
- [[ema]] · causal CD 的稳定目标
