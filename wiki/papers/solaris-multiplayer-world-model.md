---
name: solaris-multiplayer-world-model
type: paper
source: https://arxiv.org/pdf/2602.22208
upstream: https://solaris-wm.github.io/
ingested: 2026-07-24
updated: 2026-07-24
authors: Georgy Savva, Oscar Michel, Daohan Lu, Suppakit Waiwitlikhit, Timothy Meehan, Dhairya Mishra, Srivats Poddar, Jack Lu, Saining Xie
year: 2026
---

# Solaris · 两个人同时行动时，视频世界模型怎样维护同一个 Minecraft

普通可交互视频模型只需回答：“我按下 W 后，我眼前会出现什么？”多人模型还得同时回答：“你向前走时，你的画面怎样变，队友又应该在他的画面里看见什么？”第二个问题要求模型把多路视角当成**同一个世界的不同观察**，而不是两段互不相干的视频。

Solaris 围绕这个难点补齐了三块：采集同步的双人视频与动作、让两个玩家的视觉 token 在共享注意力里交换信息、用 Checkpointed Self Forcing 训练可长时间滚动的因果生成器。它是两人 Minecraft 视频世界模型，不是带显式方块状态和物理规则的游戏引擎。

## 一句话

**Solaris 给视频 latent 加一维 `player`，让各玩家 token 在共享 self-attention 中交换信息；再从双向单人、双向多人、因果多人一路训练到 Self Forcing，使模型能根据两套键鼠动作同步续写两路画面。**

## 0. 先把整张拼图摆出来

一次推理可以拆成这条链：

```text
玩家 1 初始画面 + 动作序列 ─┐
                            ├→ 冻结 3D VAE → 双人 latent
玩家 2 初始画面 + 动作序列 ─┘
                                      ↓
                         multiplayer DiT
          每人独立读动作 / 两人视觉 token 共享注意力
                                      ↓
                     逐段生成两路未来 latent
                                      ↓
                            VAE 解码成两路视频
```

训练时还要多两位角色：

- **双向 teacher**：整段视频一起看、一起去噪，质量高，但不能实时逐帧生成；
- **因果 student**：只能看过去并维护滚动 KV cache，最后真正部署的是它。

因此四个训练阶段不是四套模型，而是一条能力迁移路线：

```text
Matrix Game 2.0
  → 单人完整动作
  → 双人联合建模
  → 只能看过去的流式生成
  → 在自己的生成历史上继续训练
```

## 1. 为什么“把两路画面拼起来”还不够

假设玩家 A 放下一块火把，玩家 B 正站在旁边看：

1. A 的画面应出现放置动画；
2. A 的物品栏数量应减一；
3. B 的画面应在对应位置同时出现火把；
4. 若天气转雨，两边画面也应同时下雨。

单路模型只需维持一条视频的时间连续性。双路模型还要维持**跨视角一致性**：同一事件在两个相机中必须是同一件事。

最简单的基线是把两位玩家的画面沿通道维拼接，再交给普通模型。它能看见两路像素，却没有显式告诉网络“这些 token 属于玩家 1，那些属于玩家 2”，也没有专门设计跨玩家信息交换。论文结果里，这个基线在 Movement 的 VLM 分数反而更高，但会在无动作时凭空制造动作，长视频画质也明显更差。

## 2. 数据不是两段录像，而是同一时钟下的两套“画面—动作”

多人世界模型首先缺的不是网络，而是同步数据。SolarisEngine 把一个逻辑玩家拆成两个进程：

- **controller bot** 决定走路、转头、攻击、放置等动作；
- **camera bot** 使用官方 Minecraft Java 客户端渲染第一人称画面。

自定义服务器插件复制状态与动作，时间戳再把视频帧和低层动作对齐。这样既保留 Mineflayer 适合自动化控制的能力，也得到官方客户端的真实画面。

### 为什么不用 CPU 渲染

作者发现 libOSMesa 在复杂森林场景以 20 FPS 采集时，最多会重复 4 帧。对普通录像这只是卡顿；对世界模型却会变成错误监督：“角色已经移动，画面却没变。”因此采集改用 GPU 渲染，并用 NVENC 降低 CPU 编码压力。

### 数据规模

- `9,240` 个双人 episode；
- 每位玩家 `6.32M` 帧，共 `12.64M` 帧；
- `20 FPS`；
- 4 类活动：building、combat、movement、mining；
- 14 种 episode；
- 多数片段为 `128–512` 帧，即 `6.4–25.6` 秒；
- Superflat 与 Normal 世界约各一半。

动作空间包含 WASD、跳跃、冲刺、潜行、yaw/pitch、攻击、使用、放置、挖掘、骑乘、切换物品栏等。高层 bot 指令最终会记录成 VPT 兼容的低层动作。论文未包含打开背包和原始鼠标位移。

### 自动采集也要处理失败

Docker Compose worker 并行启动多局。任一 bot 卡死时，故障检测器会终止这一局的所有 bot，再启动新 episode，避免一条已经错位的玩家轨迹继续污染数据。作者还用 HUD 气泡训练线性分类器清理水下片段；在抽查的 6,000 个 Normal episode 中发现 340 个水下片段，该分类器在其验证集上达到 100%，但这只是特定过滤任务的内部结果。

## 3. 模型究竟多了什么：一维 player + 一处共享注意力

### 3.1 先读懂张量形状

单人 latent frame 通常写成：

\[
x_t \in \mathbb R^{H\times W\times C}.
\]

Solaris 在最前面加一维玩家：

\[
\mathbf x_t=\{x_t^1,\ldots,x_t^P\}\in
\mathbb R^{P\times H\times W\times C}.
\]

一整个 batch 的视频和动作分别是：

\[
\mathbf x\in\mathbb R^{B\times P\times T\times H\times W\times C},
\qquad
\mathbf a\in\mathbb R^{B\times P\times T\times D}.
\]

每个符号都对应一个问题：

| 符号 | 意义 |
|---|---|
| `B` | 一批有多少段双人片段 |
| `P` | 玩家数；本文实验固定为 2 |
| `T` | 每段有多少个时间位置 |
| `H,W` | latent 特征图的高和宽，不是原图分辨率 |
| `C` | 每个 latent 位置的通道数 |
| `D` | 每位玩家每一时刻的动作向量维度 |

例如 `B=2, P=2, T=3` 时，一批共有 2 局，每局 2 位玩家，每人 3 个时间位置。`P` 不是把 batch 翻倍：同一局的两位玩家必须互相交换信息。

### 3.2 自回归目标说了什么

\[
p_\theta(\mathbf x)
=\prod_{t=1}^{T}
p_\theta(\mathbf x_t\mid \mathbf x_{<t},\mathbf a_{<t}).
\]

- `θ`：Solaris 的参数；
- `x_t`：时刻 `t` 所有玩家的联合画面；
- `x_<t`：此前所有联合画面；
- `a_<t`：此前所有玩家的动作；
- 乘号：把每一步条件概率连成整段视频的概率。

人话是：**下一时刻不是分别预测两张图，而是一起预测“此刻两位玩家分别看见什么”。**

### 3.3 哪些模块共享，哪些模块分开

Solaris 从 Matrix Game 2.0 的单人 DiT 改来：

1. **动作模块按玩家独立运行。**实现上把 `B P T D` 临时整理为 `(B P) T D`；玩家 1 的 W 不会被当成玩家 2 的动作。
2. **视觉 token 在序列维交错后进入共享 self-attention。**这里才发生跨玩家信息交换。
3. **每位玩家独立使用 3D RoPE。**时间和空间坐标不会因为另一位玩家插入 token 而错位。
4. **加入 learned player-ID embedding。**模型能分辨“这块视觉 token 属于谁”。
5. **首帧 cross-attention 仍按玩家独立。**每一路画面读取自己的初始条件。
6. **其余模块跨玩家共享权重。**不是给每位玩家复制一整套 DiT。

共享注意力的作用可以用一句话概括：玩家 A 放方块时，A 的动作先影响 A 的视觉表示；共享 attention 再让玩家 B 的视觉 token 读取这条变化，从而在 B 的视角中同步反映。

这仍然不是显式 3D 状态。模型学到的是视频 token 间的统计关联，没有一张永久保存所有方块和玩家坐标的世界表。

## 4. Flow Matching：模型训练时究竟在猜什么

Solaris 不直接让网络一次猜干净 latent，而是先把真实 latent `x` 和高斯噪声 `ε` 混在一起：

\[
\mathbf x_{\boldsymbol\sigma}
=(1-\boldsymbol\sigma)\mathbf x
+\boldsymbol\sigma\boldsymbol\epsilon,
\qquad
\boldsymbol\epsilon\sim\mathcal N(0,I).
\]

- `x`：真实双人视频 latent；
- `ε`：与 `x` 同形状的随机高斯噪声；
- `σ`：噪声比例，0 是完全干净，1 是完全噪声；
- `x_σ`：混合后的训练输入。

从 `x` 沿直线走到 `ε`，整条路的速度不变：

\[
\mathbf v^\star=\boldsymbol\epsilon-\mathbf x.
\]

网络学习这个速度：

\[
\mathcal L_\theta
=\mathbb E_{\mathbf x,\mathbf a,\boldsymbol\sigma,\boldsymbol\epsilon}
\left[
\left\|
v_\theta(\mathbf x_{\boldsymbol\sigma},
\boldsymbol\sigma,\mathbf a)
-(\boldsymbol\epsilon-\mathbf x)
\right\|_2^2
\right].
\]

- `v_θ(...)`：模型预测的速度张量；
- `a`：告诉模型当前动作，速度因此能随动作改变；
- `||·||²₂`：把每个位置的预测误差平方后相加；
- `E`：对许多视频、动作、噪声时刻与随机噪声取平均。

### 用一个数算到底

把一整张 latent 缩成一个数：

```text
真实 latent x = 2
随机噪声 ε = −1
噪声比例 σ = .25
```

先混合：

\[
x_\sigma=(1-.25)\times2+.25\times(-1)=1.25.
\]

正确速度：

\[
v^\star=\epsilon-x=-1-2=-3.
\]

若模型预测 `v_θ=-2.6`，这一项损失为：

\[
L=(-2.6-(-3))^2=.16.
\]

在这条直线路径上，从带噪状态还原干净值可写为：

\[
\hat x_0=x_\sigma-\sigma v_\theta.
\]

若预测完全正确：

\[
\hat x_0=1.25-.25\times(-3)=2.
\]

它正好回到原来的 `x=2`。更多背景见 [[flow-matching]]。

### 双向与因果的区别藏在 `σ` 怎么抽

- **双向模型**：所有玩家和所有帧共用一个 `σ~U(0,1)`，整段一起去噪；
- **因果模型**：每个玩家、每个时间位置独立抽 `σ_{p,t}`，即 Diffusion Forcing；不同帧可以处于不同去噪进度，模型才能学习“前面较干净、后面较嘈杂”的滚动生成。

## 5. 四阶段训练：每一步只解决一个新问题

| 阶段 | 初始化与数据 | 训练目标 | 为什么不能跳 |
|---|---|---|---|
| 0 | Matrix Game 2.0 `base_distilled_model` | 已会单人游戏视频 | 提供视觉与游戏动态基础 |
| 1 | VPT 超过 2,000 小时人类单人 Minecraft | 120K 步，双向，33 帧上下文 | 学完整 MineRL 动作；论文消融证明预训练重要 |
| 2 | Solaris 双人数据 | 120K 步，双向多人 | 学跨玩家一致性，并得到高质量 teacher |
| 3 | Stage 2 的 60K 中间点 | 60K 步，因果 mask + Diffusion Forcing | 学会只读过去、维护滚动 cache |
| 4 | Stage 3 student + Stage 2 120K teacher | Checkpointed Self Forcing | 让 student 适应自己生成的历史并蒸成少步 |

Stage 3 的滑动窗口是 6 个 latent frame；Matrix Game 2.0 的 VAE 每个 latent 对应 4 个真实帧，因此最多看 24 个真实帧。它也限制了推理时滚动 [[kv-cache]] 的最大长度。

训练配置中，前三阶段学习率均为 `1e-4`；Self Forcing 的 generator 为 `3e-6`、critic 为 `3e-7`。冻结的 3D VAE 贯穿所有阶段。论文实验依赖 TPU v5p，正文未给出完整训练算力成本。

## 6. 为什么还要 Self Forcing：训练看真历史，推理看自己的历史

Teacher Forcing 训练因果模型时，上一帧来自数据集。部署后，上一帧却是模型自己生成的。一个小错误会进入下一步条件，再被继续放大，这叫 exposure bias。

Self Forcing 的做法是：训练时就让 student 自己向前生成，再让高质量 teacher / distribution matching 纠正整段输出。于是 student 学到的输入分布更接近部署时真正遇到的输入。

一次简化 rollout：

```text
第 1 帧：student 根据初始帧生成 x̂₁
第 2 帧：不再喂真值，而是根据 x̂₁ 生成 x̂₂
第 3 帧：根据 x̂₁,x̂₂ 生成 x̂₃
……
```

原始 Self Forcing 为省显存，只让最后一个截断去噪步骤保留梯度，并对缓存的 KV 停梯度。Solaris 还面对另一个问题：student 只看短滑窗，teacher 可以看更长上下文。逐帧保留每个重叠窗口的计算图会爆显存。

## 7. Checkpointed Self Forcing：先无梯度跑一遍，再并行重算最后一步

设：

- `L_s`：student 每次能看的上下文长度；
- `L_t`：本次要生成的总长度。

朴素滑窗会保存：

```text
帧 1…L_s
帧 2…L_s+1
帧 3…L_s+2
……
```

相邻窗口几乎完全重复，却都要为反向传播保留激活，显存随 `O(L_t L_s)` 增长。

Solaris 把训练拆成两遍。

### 第一遍：只生成，不留计算图

自回归跑完整段，缓存两类值：

- 每帧的干净估计 `X_0={x̂_0^1,…,x̂_0^N}`；
- 抽中训练噪声位置的状态 `X_s={x_s^1,…,x_s^N}`。

随后对两者 `stop_gradient`。这不是说它们永远不参与训练，而是避免保存第一遍滚动生成的巨大计算图。

### 第二遍：把所有帧的最后去噪步一次并行重算

\[
X_{\text{in}}=[X_0,X_s].
\]

序列长度暂时翻倍。自定义 attention mask 保证：

- noisy frame 只看自己和窗口内更早的 clean frames；
- clean frame 只看窗口内过去的 clean frames；
- clean frame 绝不偷看 noisy frame。

这样，一次并行 forward 就复现了每个时间位置“最后一步去噪时能看到的上下文”。反向传播只穿过这次重算，显存降为 `O(L_t)`。

### 为什么这不等于“梯度被全切断”

第一遍的历史值确实冻结；第二遍重新计算的 Q/K/V 和输出仍有完整计算图。论文甚至让梯度通过重算后的 KV 表示，这是原始 Self Forcing 没做的。消融显示它显著改善 FID，但部分动作跟随分数会下降，因此不是所有指标都单调变好。

## 8. 评测到底在测什么

作者构造了训练中完全没出现的 episode 类型：

| 任务 | 场景 | VLM 被问什么 |
|---|---|---|
| Movement | 一人移动/转头，另一人观察 | 观察者画面中的位置是否正确 |
| Grounding | 一人转身看不见队友，再转回来 | 转开时看不见、转回时能否看见 |
| Memory | 两人都转开，再转回来 | 两边是否都恢复正确相对位置 |
| Building | 一人搭方块，另一人观看 | 观察者是否看到建成的结构 |
| Consistency | 两人同时向同侧或异侧转 90° | 同侧画面应相似、异侧应不同 |

两类指标互补：

- **FID 越低越好**：比较生成视频帧与真实帧的视觉分布；
- **VLM accuracy 越高越好**：让 VLM 回答可验证问题，测任务语义是否完成。

VLM 不是裁判真理。即使对真实视频，它在 Memory 上也只有 `92.71±1.47`，Consistency 的 opposite 条件为 `93.75±4.42`。模型表中的标准差来自重复 3 次 VLM 评测后估计的 1 个标准差。

## 9. 结果：Solaris 赢在哪里，又没赢在哪里

| 方法 | Move VLM / FID | Ground VLM / FID | Memory VLM / FID | Build VLM / FID | Consistency VLM / FID |
|---|---:|---:|---:|---:|---:|
| Frame concat | **77.1** / 68.9 | 53.1 / 66.6 | **37.5** / 74.4 | 0.0 / 103.2 | 49.5 / 129.4 |
| Solaris 无单人预训练 | 69.3 / 42.5 | 29.2 / 49.9 | 18.8 / 67.8 | 0.0 / 86.6 | 49.5 / 121.4 |
| Solaris | 68.2 / **38.5** | **62.5** / **38.0** | **37.5** / **55.1** | **20.8** / **83.6** | **71.4** / **99.4** |

应当这样读：

1. Solaris 在五类任务上都拿到最低 FID，说明长时间画质最稳定。
2. 真正需要跨视角关系的 Grounding、Building、Consistency，Solaris 的 VLM 分数领先。
3. Frame concat 的 Movement VLM 更高，不能抹掉；作者观察到它在 no-op 时会产生动作幻觉，说明单个语义指标没有覆盖所有失败。
4. 去掉单人预训练后，Grounding、Memory 和 Consistency 明显退化，Stage 1 不是可有可无的热身。

### Self Forcing 消融

最值得看的对照是同样从 Causal FT 初始化：

| Pre-DMD | KV 反传 | Move VLM / FID | Ground VLM / FID | Build VLM / FID | Consistency VLM / FID |
|---|---|---:|---:|---:|---:|
| 否 | 否 | **78.6** / 60.3 | **72.9** / 55.2 | 15.6 / 87.4 | 70.8 / 105.1 |
| 否 | 是 | 68.2 / **38.5** | 62.5 / **38.0** | **20.8** / **83.6** | **71.4** / **99.4** |

KV 反传明显改善五项 FID，也提高 Building / Consistency；但 Movement、Grounding、Memory 的 VLM 分数下降。这说明优化视觉分布与精确动作响应之间存在真实张力。论文选择后一行作为 Solaris，是质量与难任务一致性的取舍，不是全面碾压。

作者还发现 CausVid 式 ODE regression 初始化和预先 few-step DMD 没有带来更好的最终结果；简单的 causal finetuning 已足够成为 Self Forcing 初始化。

## 10. 边界：它已经像世界，却还没有“世界状态”

1. **只有两人实验。**架构张量可以扩到 `P>2`，但论文没有证明更多玩家下的质量、显存和吞吐。
2. **没有持久记忆。**玩家离开彼此视野后，共享上下文逐渐消失，两条轨迹会分叉。
3. **世界只由两张初始帧指定。**没有 Minecraft 引擎那种永久保存的方块、天气、背包和坐标状态。
4. **数据全是合成 Minecraft。**动作分布和画面分布都可能与人类真实玩法有差距。
5. **指标仍不完整。**FID 不懂动作，VLM judge 也会误判；论文没有报告真实玩家盲测或长时间可玩性成功率。
6. **实时性没有完整报告。**它是可滚动生成器，但论文没有给出端到端 FPS、硬件和延迟表。

所以更准确的定位是：Solaris 证明了“把多位玩家的画面与动作作为联合视频状态训练”是可行的，并解决了 Self Forcing 的一项显存瓶颈；它还没有替代显式多人游戏引擎。

## 与第二篇综述怎么接

[[interactive-video-world-modeling-survey]] 把可交互视频世界模型拆成三个瓶颈：

- **动作可控性**：Solaris 用每人独立动作模块；
- **长期一致性**：Solaris 用短 KV 窗口 + Checkpointed Self Forcing，但仍无持久记忆；
- **实时响应**：Solaris 做了因果与少步生成，论文却没报告完整速度。

Solaris 正好是综述“多人、Forcing 训练、无显式长期世界状态”这一格的具体案例。

## 链接

- [[interactive-video-world-modeling-survey]] · 把 Solaris 放回整个交互式视频世界模型版图
- [[world-foundation-model]] · 世界模型和普通视频生成的目标差异
- [[flow-matching]] · 为什么预测速度能从噪声还原数据
- [[autoregressive-vs-bidirectional-video-diffusion]] · 双向 teacher 与因果 student 的根本区别
- [[kv-cache]] · Stage 3 滚动窗口到底缓存了什么
- [[diffusion-transformer]] · Solaris 的生成主干

## 原始来源

- [论文 PDF](https://arxiv.org/pdf/2602.22208)
- [arXiv 摘要页](https://arxiv.org/abs/2602.22208)
- [项目页](https://solaris-wm.github.io/)
