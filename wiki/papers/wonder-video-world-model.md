---
name: wonder-video-world-model
type: paper
source: https://arxiv.org/abs/2607.26037
upstream: https://wonder-world-model.github.io/
ingested: 2026-07-29
authors: Jiacong Xu, Hanwen Jiang, Zhixin Shu, Kalyan Sunkavalli, Vishal M. Patel, Yiqun Mei · Adobe Research / Johns Hopkins University · arXiv v1
year: 2026
---

# Wonder · 把图片或视频变成能实时移动相机的生成世界

普通视频生成器一次交付一段固定镜头。Wonder 要做的更像一台生成式摄影机：给一张图，可以边移动相机边探索画外区域；给一段已有视频，可以保留原来的动作，再换一条镜头轨迹重拍。真正难的不是“再生成几帧”，而是同时守住四件事：镜头听指挥、走远后还记得旧场景、每段都能实时生成、把多步双向老师的能力压进四步因果学生。

论文的答案不是一个孤立模块，而是一套联动设计：先把相机轨迹渲染成像素对齐的彩色网格视频；再把完整历史保存成 KV，只激活初始、最近和检索出的少量旧块；训练时提前随机断开可选历史边，让学生适应稀疏记忆；最后用三个分阶段学生和一项低频相机 GAN 正则修补少步蒸馏的容量与漂移问题。

## 一句话

**Wonder 把相机动作画成模型能直接读的“控制视频”，再用稀疏完整记忆和四步分阶段学生，把双向视频扩散模型改成 16 FPS 的实时交互世界。**

## 先看完整拼图

```text
图片 / 原视频 + 目标相机轨迹 + 文本
        ↓
合成 3D 网格 + 无限远环境球 → OpenGL 渲染控制视频
        ↓
Wan2.1-I2V-14B 双向 teacher
        ↓  ODE 初始化 + Sparse Context Forcing
因果 student：只看过去，按视频块流式生成
        ↓  Self-Forcing + DMD
3 个分阶段 student：G1 → G2 → G3 → G3
        ↓  GAN Control Regularization
稀疏检索历史 KV + 4 步生成 + VAE 解码
        ↓
I2V 可探索世界 / V2V 换机位重拍
```

训练期还会出现冻结的双向 teacher、DMD critic、控制判别器和真实视频。部署后真正留下的是三个 14B student、控制视频渲染器、稀疏 KV 记忆与流式运行时。

## 论文覆盖地图

| 原文章节 | 本页落点 |
|---|---|
| 1 Introduction | 从“固定短片”到“边按键边出画面”的四个矛盾 |
| 2 Related Work | 融进相机控制、因果生成、记忆和蒸馏的对照 |
| 3 Training Data | 真实/合成 I2V、成对 V2V、标注、平滑、增强和双重过滤 |
| 4.1 Teacher | 像素空间坐标场、Wan 输入拼法、5→10→20 秒课程 |
| 4.2 Student | ODE 初始化、DMD、自回归、稀疏上下文、MoS、控制 GAN |
| 4.3–4.4 Runtime / Infra | kernel、缓存、并行、滚动位置、32×H200 训练 |
| 5 Experiments | I2V 1000×5、V2V 500×6、VBench、RPE 与完整表格 |
| 6 Conclusion | 能力边界、复现缺口与“世界模型”称呼的限度 |

## 1. 它究竟拿来做什么

Wonder 支持两种入口：

1. **图片到世界（I2V）**：首帧固定，用户不断给 6-DoF 相机轨迹；模型补出画外区域并保持回访一致。
2. **视频到世界（V2V）**：原视频提供人物、车辆等动态事件；目标轨迹指定新机位，模型在保留动作的同时重画新视角。

“世界”在这里不是显式 mesh、物理引擎或可查询物体表，而是一个会根据相机动作续写视频、并通过历史 KV 维持外观记忆的生成模型。它能学到几何、遮挡和动态规律，不等于内部拥有可验证的 3D 状态。

## 2. 四个矛盾为什么必须一起解决

- **控制**：位姿向量很紧凑，但每帧所有空间 token 拿到同一个数，模型还得自己学“向右平移会让近物移动更快”；重建点云控制更直观，却走出已观察区域就变成空洞。
- **记忆**：保留全部历史 KV 能回忆细节，可全量 attention 会随历史线性变慢；只留滑窗速度稳，却会忘记走远前见过的门窗。
- **速度**：双向多步 teacher 一次看完整段、画得好，但不适合实时输入；四步因果 student 能流式出图，却容易丢多样性和细节。
- **蒸馏**：DMD 擅长修局部纹理，镜头轨迹属于低频整体变化，监督太弱就会一段一段积累成相机漂移。

所以不能只把 teacher 压到四步，也不能只加一块 memory。控制信号若在蒸馏时先丢了，记忆再完整也只是记住一条走偏的轨迹。

## 3. 数据管线：先把“画面—相机—动作”对齐

I2V 真实数据主要来自 DL3DV；作者再用 Unreal Engine 渲染急转、横移、后退和复合动作，补真实采集里偏平滑的轨迹。V2V 需要“同一动态事件、不同机位”的成对视频：公开 MultiCamVideo / CamXTime 多为约 5 秒，于是作者用 Blender 渲染更长的标准配对、变速和 bullet-time 片段。

原视频切成 5、10、20 秒三档。规则先删损坏文件、黑帧、失败渲染、碰撞和无效轨迹；Qwen3-VL 为整段与短子段分别写 caption；Depth Anything 3 估计内外参，再把连续轨迹离散成相机动作。高频位姿抖动先做 Gaussian smoothing，随后用倒放、变速重采样平衡动作。最后再让 VLM 删画质差、镜头不自然、时间动态不一致的样本。

报告没有公开真实/合成视频条数、总时长、数据混合比例、过滤阈值和 VLM 最终淘汰率。

## 4. Pixel-Space Coordinate Field：不要只给相机六个数，把后果画出来

[[pixel-space-coordinate-field]] 构造一个与输入场景无关的合成相机空间：

- 相机周围放密集 3D lattice；相机平移后，近格点比远格点在屏幕上移动得更多，直接显出视差与尺度。
- 无限远处放彩色环境球；相机旋转时颜色图案跟着横移，直接显出朝向。

OpenGL 以 150 FPS 沿目标轨迹渲染这些控制帧。控制视频经过同一个 VAE，和带噪场景 latent 沿通道拼接后进入 DiT。它比纯位姿 embedding 多了像素对齐的局部线索，又不像重建输入点云那样受原视野限制。

一个最小投影例：焦距取 100，点 `(X,Z)=(2,4)` 投到 `u=100×2/4=50`。相机向右 1 后，相对横坐标变成 1，投影变为 25，屏幕左移 25。若另一个点只有 2 米深，位移会变成 50；这组“近处动得快、远处动得慢”的格线变化，就是模型直接能看的平移证据。

## 5. 一条公式把 I2V 与 V2V 装进同一个输入

先定义：

- \(z^s\)：可选的干净源视频 latent；I2V 没有这一段。
- \(z^a\)：干净目标锚帧；I2V 就是输入图片的首帧。
- \(z^p\)：等待生成的目标帧 latent。
- \(\alpha_\tau,\sigma_\tau\)：扩散时刻 \(\tau\) 的信号与噪声系数。
- \(\epsilon\sim\mathcal N(0,I)\)：与目标 latent 同形状的高斯噪声。
- 下标 \(T\) 表示沿时间拼接，下标 \(C\) 表示沿通道拼接。
- \(m\) 是 source/target mask；\(c\) 是相机控制 latent。

模型输入是：

\[
u_\tau=
\left[
\left[z^s,z^a,\alpha_\tau z^p+\sigma_\tau\epsilon\right]_T,
\left[0_m^s,1_m^a,1_m^p\right]_T,
\left[0_c^s,z^{c,a},z^{c,p}\right]_T
\right]_C.
\]

时间块把源视频、锚帧和带噪目标排成一条序列；通道块再补“哪里要生成”的 mask 与“相机怎样走”的控制视频。源视频保持干净，且相机控制只作用于目标轨迹。

数值化成标量：取 `z^s=.4, z^a=.8, z^p=2, α=.75, σ=.25, ε=-2`，带噪目标为 `.75×2+.25×(-2)=1`。三条时间流分别是场景 `[.4,.8,1]`、mask `[0,1,1]`、相机 `[0,c_a,c_p]`。I2V 只需删掉开头 `.4/0` 那一格，模型接口不变。

底座是 Wan2.1-I2V-14B：3D causal VAE 在空间压 8 倍、时间压 4 倍，DiT 处理 patchified latent；umT5 文本通过 cross-attention 注入。teacher 先联合训 5 秒 I2V/V2V，再扩到 10、20 秒，RoPE 用 YaRN 外推。长阶段多数 V2V 仍保留 5 秒，I2V 扩长；因为前者重点学“同一事件换机位”，后者更便宜地承担长程相机控制。

## 6. 从多步双向 teacher 到四步因果 student

双向 teacher 的优势是整段互相看、去噪步数多；缺点是必须等未来帧，无法边操作边生成。student 从 teacher 权重初始化，然后经历两层适配：

1. **ODE 初始化**：在四个去噪时刻回归 teacher 预先算好的 ODE 轨迹，让因果 student 先学会四步大致落点。
2. **Self-Forcing + DMD**：student 用自己的旧输出继续 rollout；加噪后交给冻结 teacher 和可训练 critic 估 score 差，再用 DMD 更新生成器。这样训练时也会遇到自己的误差，不再只吃永远干净的历史。

[[dmd-distillation]] 负责让学生生成分布靠近目标分布，但它本身不保证相机控制不漂。因此 §8 还会补一项专门看低频布局的监督。

## 7. 记忆：完整存，少量看

[[sparse-context-forcing]] 把“保存历史”和“本轮计算”拆开：

- 每个历史 chunk 保存完整 K/V，另存一个 pooled key 摘要；
- 当前 query 也池化成摘要；
- 本轮一定看 chunk 0、最近 \(r=2\) 块；
- 中间历史只选摘要相似度最高的 top-k；
- 真正 attention 时，取被选块的完整 K/V，而不是压缩摘要。

正式选择式：

\[
\mathcal A_t=\{0\}\cup\mathcal N_r(t)\cup
\operatorname{TopK}_k
\left\{\operatorname{sim}(\bar Q_t,\bar K_c)\mid c\in\mathcal M(t)\right\}.
\]

\(\mathcal A_t\) 是本轮激活块；\(\mathcal N_r(t)\) 是最近块；\(\mathcal M(t)\) 是去掉首块和最近块后的中段历史；横线表示池化摘要。随后把这些块的完整 K/V 按原时间顺序拼成 attention 上下文。

取历史 0–7、当前 `t=8`、`r=2`、`k=2`。最近块固定为 `{6,7}`；中段 1–5 的相似度若是 `[.15,.82,.20,.76,.11]`，top-2 选 `{2,4}`，最终激活 `{0,2,4,6,7}`。以后历史涨到 100 块，激活数仍是 5；但完整历史 KV 的存储仍增长，摘要检索也不是数学意义上的零成本。

## 8. 为什么训练时要先随机“断掉远处记忆”

若 student 一直用完整历史训练，部署时突然只给它 top-k，输入分布会变。Sparse Context Forcing 在 ODE 初始化阶段就把非局部历史边随机丢掉：

\[
M^{(\ell)}_{ij}
=
\mathbf 1[a(i,j)\in\mathcal R]
+b^{(\ell)}_{ij}\mathbf 1[a(i,j)\in\mathcal O],
\qquad
b^{(\ell)}_{ij}\sim\operatorname{Bernoulli}(1-p_\ell).
\]

- \(M^{(\ell)}_{ij}\)：第 \(\ell\) 层里，query 块 \(i\) 能否读 K/V 块 \(j\)。
- \(a(i,j)\)：基础因果关系。
- \(\mathcal R\)：必须保留的边，自身、首帧、最近历史等。
- \(\mathcal O\)：可选远端历史边。
- \(b\)：一次伯努利抽样；以 \(1-p_\ell\) 的概率保留可选边。

必须边前面的指示函数恒为 1；可选边只有抽到 \(b=1\) 才保留。长视频用更高 drop rate，逼模型从少数历史块里找关键线索。这不是推理时的 top-k 本身，而是让 student 提前适应 top-k 输入条件的训练课程。

## 9. Mixture of Students：四步各有分工，不让一套权重包办

单个因果四步 student 既要从大噪声搭结构，又要在最后补纹理，容量容易不够。[[mixture-of-students]] 用三套 14B generator 接力：

\[
\hat x_0=
G_3^{(4)}\circ G_3^{(3)}\circ G_2^{(2)}\circ G_1^{(1)}(x_{\tau_1}).
\]

从右往左执行：\(G_1\) 做第 1 步粗结构，\(G_2\) 做第 2 步结构修正，\(G_3\) 包办最后两步细节与重建。网络调用次数仍是 4，因此论文说不增加 denoising latency；但模型参数和驻留显存显然比单 student 大。三套 generator 不各养一份历史，统一复用 \(G_3\) 产生的自回归 KV cache。

## 10. GAN Control Regularization：DMD 修纹理，另一项损失盯镜头

DMD score 残差更容易抓边缘和纹理，镜头走快了、方向偏了属于低频整体布局。作者不用逐像素 L2 强拉 student，因为回归会收缩分布、把未知区域平均成模糊图；而是新增 [[gan-control-regularization]]：

1. 给真实 latent \(z_0\) 与 student rollout \(\hat z_0\) 加同一份高噪声；
2. 同一相机条件下送进冻结 teacher；
3. 取第 1 层与 3 个中层特征；
4. 线性投影到同空间，计算“中层减第 1 层”，再用 stride conv 压低高频纹理；
5. 三枚 register token 分别 cross-attend 三张低频图，汇总为 real/fake 控制 logit；
6. 相对 softplus GAN 让判别器拉开 real/fake，让 student 把 fake logit追上 real。

核心损失是：

\[
\mathcal L^D_{\mathrm{ctrl}}
=\mathbb E[\operatorname{softplus}(d^f-d^r)],
\qquad
\mathcal L^G_{\mathrm{ctrl}}
=\mathbb E[\operatorname{softplus}(d^r-d^f)].
\]

\(\operatorname{softplus}(x)=\log(1+e^x)\)；\(d^r,d^f\) 是相机一致性分数。若 `d^r=1.2,d^f=.3`，生成器损失为 `softplus(.9)=1.241`；student 改好后 fake 分数升到 `1.0`，损失变成 `softplus(.2)=.798`。总生成器目标是 \(\mathcal L_{\mathrm{DMD}}+\lambda_{\mathrm{ctrl}}\mathcal L^G_{\mathrm{ctrl}}\)：一项对齐画面分布，一项补相机控制。

## 11. 实时不是一个 kernel：运行时怎样把账压下来

- 编译并复用重复预测/缓存更新的 GPU kernel，重放固定执行图，少付 kernel launch 开销；
- self-attention 缓存历史 K/V，文本 cross-attention 缓存 prompt K/V，检索另存 pooled key；
- 使用 FlashAttention-3、fused QKV、BF16 RMSNorm、缓存 RoPE 和 timestep modulation；
- 推理时 FFN/cross-attention 按序列切，self-attention 按 head 切，NCCL All-to-All 在两种布局间转换；
- KV cache 也按 head 分到各 GPU；umT5 与 VAE 从主生成 GPU 卸载，输出用 Tiny VAE 解码；
- 超过 20 秒训练窗后，活跃 cache 只组织为 sink、top-k、recent，并按相对距离把 frame index 映射回训练位置范围。

训练一个双向 teacher 加三个 14B student，要用 FSDP2、sequence parallel、tensor parallel、activation checkpointing、梯度累积和 replayed back-propagation。公开配置是 32 张 H200、global batch 64；推理使用多 GPU，但报告没给卡数、分辨率、显存和逐模块延迟。

## 12. 实验：强项是“画得好且镜头听话”，不是每列都赢

I2V benchmark 有 1000 张开源图片，每张 5 条不同平移尺度/旋转速度轨迹。V2V 有 500 段动态视频，每段 6 条 retreat、follow、free 轨迹。画质用 VBench 五项；镜头轨迹先由 DA3 和 ViPE 估计、取平均，再用 Umeyama 对齐坐标系与尺度，最后算平移/旋转 RPE，越低越好。

I2V 中 Wonder 平均画质 `.8558` 最高，平移/旋转 RPE `.0132/.0784` 最低；但 HY-WorldPlay 的 aesthetic、motion、flickering 更高，SANA-WM 的 dynamic 更高。V2V 只与当时唯一开放的长时 baseline Inspatio-World 比，平均画质 `.8374→.8527`，平移 RPE `.0436→.0187`，旋转 RPE `.2470→.1119`。

这里还有一个值得保留的核算注记：表下注明 `Avg.` 是五项画质指标的算术平均，但 Wonder I2V 一行按表中已打印的五个数重算得到 `.85638≈.8564`，不是表里的 `.8558`。可能是作者用未四舍五入的原始值计算，也可能是排版笔误；没有原始评测文件时，本页保留论文原数，不擅自改表。

定性回访实验是“右移看目标 → 左移离开 → 再右移回同一机位”，比较前后同位置画面。官方项目页给出大量 I2V/V2V 视频，适合看外观记忆、动态保留与走出原视野后的补全。

## 13. 证据边界

- 没有消融表，无法从数字中分别量化 coordinate field、sparse memory、MoS 和控制 GAN 各贡献多少。
- I2V Wonder 行的五个已打印分项均值约为 `.8564`，与论文给出的 `.8558` 不一致；v1 没提供原始评测文件，无法判断是未舍入原数还是表格笔误。
- 16 FPS、0.5 秒 constant latency 来自项目页；报告未公开对应分辨率、推理 GPU 型号/数量、batch、首帧延迟和测速方法。
- 数据总量、授权构成、训练步数、优化器、学习率、top-k、pooling/similarity、\(p_\ell\)、高噪声区间、\(\lambda_{\mathrm{ctrl}}\) 都未公开。
- benchmark 是作者自建，I2V 图像和 V2V 视频列表未随 v1 开放；VLM 自动写 caption/导航键，轨迹准确率又依赖 DA3/ViPE 估计。
- 完整历史 K/V 保真不等于内存恒定。固定的是本轮 active attention；历史 KV 存储与摘要检索怎样扩展、是否在一分钟后淘汰，报告没说清。
- “合理补出画外区域”是生成，不是恢复真实相机没拍到的事实；回访一致也不等于显式 3D 几何或物理正确。
- 截至 2026-07-29，项目页仍标注代码和 Hugging Face 权重 coming soon。

## 关键概念

- [[pixel-space-coordinate-field]] · 把相机轨迹渲染成像素对齐的控制视频
- [[sparse-context-forcing]] · 完整存历史、摘要选块，并在训练时随机断远端边
- [[mixture-of-students]] · 三套 student 分担四个去噪阶段
- [[gan-control-regularization]] · 用冻结 teacher 的低频特征专门监督镜头一致性
- [[dmd-distillation]] · 分布匹配蒸馏的主损失
- [[kv-cache]] · 流式生成保存历史表示的账本
- [[sparse-attention]] · 只激活少数相关历史块
- [[distributed-training-parallelism]] · FSDP2、序列并行与张量并行的分工

## 我的批注

- 最漂亮的点是把抽象相机数变成“控制视频”。它不重建输入世界，却把平移、旋转和视差的结果先画给模型看，正好卡在隐式位姿与显式点云之间。
- memory 的关键不是稀疏本身，而是“摘要只负责找，完整 KV 才负责读”。这和搜索引擎先用索引定位、再打开原文是同一笔账。
- Sparse Context Forcing 说明稀疏推理不能最后一天才打开；模型必须在能力还容易塑形的 ODE 初始化阶段就习惯缺历史。
- MoS 没少做一步，只是让每一步由更合适的权重负责。它换来的不是计算次数下降，而是同样四次前向下更大的参数容量。
- v1 更像强系统报告而不是完整科学拆解：主结果亮眼，但没有 ablation、公开 benchmark 和测速明细，机制归因仍需等代码与后续版本。

## 跟 wiki 里其他 paper 的关系

- [[minwm]] · 同样从 Wan/HY 双向视频扩散改造成四步因果 student；Wonder 进一步补像素控制、稀疏全历史记忆与 MoS
- [[solaris-multiplayer-world-model]] · Solaris 解决多玩家同步观察；Wonder 解决单视角相机自由探索与 V2V 重拍
- [[interactive-video-world-modeling-survey]] · Wonder 正好落在综述的动作注入、长时记忆、实时反馈三条主轴交点
- [[dmd2]] · Wonder 的 DMD 主线与控制 GAN 都建立在 DMD/DMD2 家族上，但判别器刻意盯低频镜头布局
- [[sana-video-2]] · 两者都关心视频长序列的稀疏计算；SANA-Video 2.0 稀疏的是模型内部 attention，Wonder 稀疏的是可激活历史块

## 历史定位

- 2025 · Self-Forcing / CausVid · 把双向多步视频扩散压成少步因果生成
- 2025–2026 · RELIC / LingBot-World / DreamX-World / SANA-WM · 分别推进实时、记忆和长时交互
- 2026-07 · **Wonder** · 像素控制场 + 全保真稀疏历史 + MoS + 低频控制 GAN 的系统联动
