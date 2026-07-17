---
name: sensenova-vision
type: paper
source: https://arxiv.org/abs/2607.06560
upstream: https://github.com/OpenSenseNova/SenseNova-Vision
ingested: 2026-07-13
authors: Xiaoyang Han et al. · arXiv 2026
---

# SenseNova-Vision · 不接任务专用头，怎样让一个模型同时写框、画深度、生成 mask

检测要框，OCR 要文字，分割要 mask，深度要连续场，多视图 3D 还要 point map 和相机位姿。过去的“统一视觉模型”大多统一 backbone，却保留一排 task-specific head。SenseNova-Vision 的做法更激进：**不再为这些任务分别设计预测头，而是复用 Bagel 已有的文字生成与图像生成能力，把不同答案改写成可解码的文本、图像或混合响应。**

## 一句话

**自然语言负责说清任务和输出协议；稀疏答案写成文本，稠密答案生成图像，语义+像素答案先写颜色图例再生成 mask。一个 7B active / 14B total 的 Bagel MoT 模型因此覆盖结构化视觉、稠密几何、分割和多视图 3D，而不新增任务专用 head。**

## 它真正改了什么

先解释“**head（输出头）**”：共享 backbone 把图像变成特征，检测 head 再把特征变成类别与框，分割 decoder 把特征变成 mask，深度 head 把特征变成连续深度。每种任务都要单独设计结构、loss 和解码。SenseNova-Vision 不再新增这些**任务专用**模块：Bagel 本来就会生成文字和图像，于是把框写成文字坐标，把深度编码成灰度图，把分割写成“文字图例 + 彩色 mask”。

这里有个必须先划清的边界：**“不新增任务 head”不等于“内部只有一套权重”。** Bagel 本来就有理解专家、生成专家、SigLIP2 视觉编码器和冻结的 VAE。SenseNova 复用了这些通用的模态通路，没有把它们删掉，也没有把两套专家合成一套。

它不是提出了一个更强的检测 head 或分割 decoder，而是改了任务接口：

| 旧组织方式 | SenseNova-Vision |
|---|---|
| 检测 / 分割 / 深度各有专用输出头 | 复用 Bagel 已有的文本与图像生成通路 |
| 任务名常由调用哪颗 head 决定 | instruction 明说任务、目标和解码规则 |
| 新任务要设计结构、loss、decoder | 先找可生成、可逆的输出表示 |
| 跨任务知识容易被各自的 head 隔开 | 同一模型在共享上下文中学习文字、像素与对应关系 |

这就是 [[unified-multimodal-generation]]。统一的是模型、调用入口与原生生成空间；内部的模态专家、benchmark 指标与解码协议仍然存在。

## 先拆开底座 · Bagel 里面不是“一条完全相同的通路”

SenseNova 从 off-the-shelf **Bagel-7B-MoT** 开始微调。这个名字里的 `7B` 是一次前向大约激活的参数量；总参数约 14B，因为每层有理解与生成两套 Transformer 权重。数据流可以压成四步：

```text
输入文字 ── tokenizer ─────────────→ text tokens ─────────→ 理解专家
条件图片 ── SigLIP2 / ViT ────────→ ViT tokens ──────────→ 理解专家
条件图片 ── frozen VAE encoder ───→ clean VAE tokens ────→ 生成专家
目标图片 + 噪声 ───────────────────→ noised VAE tokens ───→ 生成专家

两类专家的 Q/K/V、FFN、Norm 不同
但所有 token 位于同一条序列，注意力时可以读取对方的 key/value
```

每个部件到底做什么：

- **SigLIP2 / ViT**：把条件图变成偏语义的 token，回答“图里有什么、各部分如何对应文字”。这些 token 与文字一样走理解专家。
- **VAE encoder**：把 RGB 图压缩成连续 latent；论文使用的 VAE 空间按宽高各缩小 8 倍、每个位置 16 个通道。同一张条件图可以同时有 ViT 表示和 clean VAE 表示：前者偏语义，后者保留重建像素所需的信息。
- **理解专家**：处理文字与 ViT token，用自回归方式生成 bbox、OCR、颜色图例、相机 token 等文字答案。
- **生成专家**：处理带噪 VAE latent，用 rectified flow 预测如何把噪声推回目标图像 latent。
- **共享注意力上下文**：生成专家的图像 query 能读取文字与输入图产生的 key/value，因此它知道“要生成的是 depth 还是 mask、指定对象是谁”。共享的是信息上下文，不是专家权重。

这就是 [[mixture-of-transformers]] 的关键分工。与 MoE 不同，它不是根据 token 内容临时选择多个 FFN 专家；token 类型直接做硬路由，而且连注意力投影也属于各自专家。

举个只看 token 数的例子：一条序列有 100 个文字 / ViT token 和 400 个 VAE token。前 100 个只经过理解专家，后 400 个只经过生成专家，不是 500 个 token 都把两套网络各跑一遍。所以总参数约从 7B 变成 14B，但每个 token 仍只激活约 7B 那一侧的计算。它省下的是“同一个 token 重复跑两套专家”的开销；500 个 token 之间的注意力交互仍然要按可见性规则计算。

## 一个混合样本到底怎样跑 · 以全景分割为例

假设用户输入街景图，并要求“给道路和每个行人生成全景分割”。一条样本从头到尾这样走：

1. **编码条件**：instruction 变成文字 token；街景经过 SigLIP2 变成 ViT token。二者都走理解专家，并在注意力里组成条件上下文。
2. **先生成文字计划**：模型自回归写出 `road → (20,190,240)`、`person-1 → (245,80,120)`。每生成一个 token，都根据此前文字和输入图预测下一个 token。
3. **再生成 mask latent**：系统进入图像段，把一块随机噪声 latent 交给生成专家。图像 token 在多步 rectified-flow 采样中不断读取前面的 instruction、输入图和颜色图例，逐渐变成彩色 mask 的 latent。
4. **还原 RGB mask**：冻结的 VAE decoder 把 latent 解码成彩色图。
5. **确定性解析**：普通程序读取文字图例，把 mask 中的 RGB 区域映射回 `road`、`person-1` 等类别与实例，最后计算 PQ / mIoU。

所以“文本 + 图像混合输出”不是把两种 loss 随手相加，也不是文字生成完就换到另一台独立扩散模型。它是在**同一条多模态序列里先写计划、再生成像素结果**；两段使用不同专家，但后段能持续读取前段。

## 谁能看谁 · 为什么需要 generalized causal attention

如果整条序列完全双向，训练时回答文字就可能偷看后面的真实 mask；如果整条序列严格因果，同一张图的 patch 又不能充分互相沟通。Bagel 因此按“段”控制注意力：

| 当前 token | 允许读取什么 |
|---|---|
| 回答文字 | 之前的文字、输入图等已给定条件 |
| 同一张图的带噪 VAE token | 之前条件 + 同一图像段内的全部 VAE token |
| 后续文字或下一张图 | 已完成图像的干净 VAE / ViT 表示；不能读取训练时的带噪答案块 |

这叫 [[generalized-causal-attention]]。训练一张输出图时会同时出现三种容易混淆的表示：SigLIP2 token 负责语义，干净 VAE token 代表已经完成、可供后续引用的图，带噪 VAE token 是当前 flow 要还原的变量。推理完成一张图后，模型用完成后的干净表示继续后面的序列，而不是永远拿那块噪声当上下文。

## 论文的完整骨架

1. Introduction：为什么视觉仍是“专家模块集合”，以及文本+图像生成为何可能成为共同接口。
2. Related Works：序列化统一、视觉基础模型、生成式稠密感知、MLLM+任务模块四条路线各缺什么。
3. Data：四大任务族如何改写成 instruction-response；SN-VC 与公开的 SN-VC-50M 怎么构造。
4. Training：从 Bagel-7B-MoT SFT，文本用 CE、图像 latent 用 rectified flow，同时混入 VQA / T2I / I2I 保能力。
5. Experiments：结构化视觉、稠密几何、分割、多视图几何、generalist 对照、收敛与组合任务。
6. Conclusion：继续做 in-context 任务定义、视频时序、扩大模型与语料、接更强语言模型。
7–9. Appendix：逐数据集构造、公开语料清单、额外定性结果和失败案例。

## 三条输出通道 · 先判断答案长什么样

### 1. 文本：稀疏、符号化、长度可变

检测、grounding、OCR、布局、GUI、关键点和相机参数都写成结构化文本。普通语义仍是普通 token，空间字段用轻量 marker 划界：

```text
<p>person</p><bbox>[0.100,0.200,0.700,0.800]</bbox>
<p>nose</p><kpt>[0.420,0.315]</kpt>
<p>SUBMIT</p><polygon>...</polygon>
```

为什么不把框也画成图？因为一张图里 12 个对象的类别、OCR 字符串、属性和框，本质更像一张长度可变的记录表。文字能直接枚举，解析器再还原成 benchmark 记录。

### 2. 图像：每个像素都有答案

深度、法线、二值 mask 和 point map 与输入像素一一对齐，正适合“生成另一张图”：

- depth：metric depth → inverse depth → normalized grayscale；
- surface normal：`(nx,ny,nz)` → RGB；
- single-target mask：固定前景/背景色；
- point map：归一化 `(X,Y,Z)` → RGB。

共同做法是：**如果每个像素的答案不超过三个数，就把这些数编码进 RGB 通道。** 深度只有一个数，因此编码成灰度；法线是三维单位向量 `(nx,ny,nz)`，把各分量从 `[-1,1]` 线性映射到 `[0,255]`；point map 在每个像素保存 3D 坐标 `(X,Y,Z)`，同样映射到 RGB。四种任务的目标因此都成为一张确定编码规则的 RGB 图，再交给已有的 VAE 和图像生成通路。详见 [[decodable-vision-representation]]。

### 3. 文本 + 图像：先定义图例，再铺像素

semantic、panoptic 和 GCG 分割既要说明“这块是谁”，又要保留像素边界。模型先生成：

```text
<p>road<color>(20,190,240)</color></p>
<p>person-1<color>(245,80,120)</color></p>
```

再生成颜色 mask。文字把 label / instance 绑定到 RGB，图像负责每个像素。论文从 RGB 立方体用 greedy farthest-point sampling 取 200 个颜色 anchor，黑色留作背景，尽量让实例颜色彼此远离。见 [[color-legend-mask]]。

## 数字例一 · 一个框怎样写进去、再读回来

设输入图 `W=640, H=480`，人物像素框 `[64,96,448,384]`。归一化公式是：

```text
b_norm = [x0/W, y0/H, x1/W, y1/H]
       = [64/640, 96/480, 448/640, 384/480]
       = [0.100, 0.200, 0.700, 0.800]
```

参数逐个说清：

- `x0,y0`：左上角像素坐标；`x1,y1`：右下角；
- `W,H`：输入图的像素宽高；
- 除以宽高是为了让不同分辨率共享 `[0,1]` 坐标系；
- 论文保留三位小数并截到 `[0,1]`，当前官方解析器进一步截到 `[0,0.999]` 的可视半开区间。

解码反乘：`[0.1×640,0.2×480,0.7×640,0.8×480]`，正好回到 `[64,96,448,384]`。如果生成成 `0.701`，右边界就变成 `448.64px`；这就是文本数值量化带来的可测误差。

## 数字例二 · 深度为何先取倒数

三个像素的 metric depth 为 `d=[1,2,4]m`：

```text
inverse depth z = 1/d = [1.00, 0.50, 0.25] m⁻¹
```

远处从 2m 到 4m 的变化，在原深度里差 2；倒数后差 0.25。近处从 1m 到 2m，倒数差 0.5。逆深度把更多灰度动态范围留给近处结构，也自然实现“近亮远暗”。

若只为演示而在这三个值内部做 min-max：

```text
gray = 255 × (z-z_min)/(z_max-z_min)
     = [255, 85, 0]
```

`z_min=0.25,z_max=1` 是这个玩具例的端点，**不是论文公开的固定端点**。论文只明确“有效 metric 值转 inverse depth，再归一化成灰度”，没有给完整归一化公式；真实复现必须跟数据转换脚本或已发布标注走，不能照抄玩具 min-max。

## 多视图 3D · 图像通道写点，文本通道写相机

先拆几个词：**多视图**是从同一场景的多个拍摄角度（最多 10 张图）恢复 3D；**参考坐标系**给所有 3D 点规定共同原点，这里使用第一帧；**内参（intrinsics）**描述焦距与主点，结合像素 `(u,v)` 和深度可恢复相机坐标中的 3D 点；**外参（extrinsics）**描述相机的旋转与平移，用于把各相机坐标中的点变换到第一帧；**point map** 与输入图等大，但每个像素保存 `(X,Y,Z)` 而不是普通颜色。

每个训练样本最多随机取 10 个 view。第一个 view 是参考坐标系，其他 view 的点都变换到它的坐标系；所有 view 共同做中心化和尺度归一化。无效深度像素（例如没有有限深度的天空）沿相机射线映射到单位立方体边界的 skybox，这样 point map 仍保持每个像素都有合法值，不必再引入额外的有效性输出通路。当前官方数据代码对应流程是：

```text
像素 + depth + intrinsics → 当前相机坐标 3D 点
→ camera-to-world → 世界坐标
→ 变换到 frame-0 坐标
→ 全序列共享中心 / 尺度归一化
→ XYZ 写入 point-map RGB
```

相机 pose 则走文本。论文复用词表最后 2,009 项：2,001 个数值 token `<-1000>…<1000>`，8 个结构 token。旋转用四元数，平移拆成单位方向 `u` 和厘米尺度 `s_cm`：

```text
q=(0,0,0,1)       → <quat><0><0><0><1000></quat>
u=(0.6,0,0.8)     → <offset><600><0><800></offset>
s=1.25m=125cm     → <scale><125></scale>

t = (u_token/1000) × s_cm / 100
  = (0.6,0,0.8) × 125 / 100
  = (0.75,0,1.00)m
```

`u` 长度是 1，`t` 长度因此正好是 1.25m。完整协议见 [[camera-pose-tokenization]]。

## 数据 · 50M 不是把原图全打包重发

SN-VC 是完整可复现语料的名字：公开数据能直接转换的部分提供 source list、prompt template、规则和例子；需要生成或人工整理的子集以 SN-VC-50M 发布。后者有 50M examples、73 个 dataset-task entry、10 种 task type：

| 任务族 | 发布帧数 | 占 50M |
|---|---:|---:|
| 结构化视觉 | 18.9M | 37.8% |
| 稠密几何 | 17.3M | 34.6% |
| 多视图几何 | 12.5M | 25.0% |
| 分割 | 1.3M | 2.6% |
| 合计 | 50.0M | 100% |

同一张源图做不同任务会保留为独立样本，因为 instruction 和 target 不同。发布包不重复分发公共数据集原始 RGB，只存路径。重叠 benchmark 保留官方 split，并排除对应评测图与标注。

数据还不是同一种可信度：

- 公开标注能直接转就直接转；
- depth / normal 用 MoGe-2 补稠密伪标签并过滤；
- 稀疏多视图 depth 用 LingBot-Depth 补全，再过滤无效深度、缺相机和元数据不一致；
- structured 部分沿用 Rex-Omni 数据引擎生成一部分检测与 OCR；
- GCG 等混合样本要人工/规则整理文字图例与 mask 对齐。

所以 50M 更准确的说法是“可生成、可解码的 instruction-response 条目数”，不等于 50M 张独立原图，也不等于全部是真值标注。

## 训练 · 同一次训练混合两类样本，不是每个 token 共用同一种 loss

底座是 off-the-shelf Bagel-7B-MoT。SFT 混合 SN-VC 与通用 VQA、text-to-image、image-to-image，后者用来减轻视觉专训对理解、指令遵循和生成能力的侵蚀。

训练数据按权重混合结构化视觉、稠密几何、分割、多视图任务，以及用于保能力的 VQA / T2I / I2I。论文说一个 mini-batch 可以包含多种任务类别；这不代表每条样本都同时拥有文字和图像目标。**某个输出位置属于文字，就算交叉熵；属于图像 latent，就算 flow MSE；混合响应才会在同一条样本里依次触发两段。**

文本 token 的目标：

```text
L_text = - Σ_t log pθ(y_t | y_<t, instruction, images)
```

`t` 是输出 token 位置；`y_t` 是真实 token；`pθ` 是模型在参数 `θ` 下给它的概率。若正确 token 概率从 0.2 提到 0.8，单 token loss 从 `-ln0.2=1.609` 降到 `-ln0.8=0.223`。见 [[cross-entropy]]。

图像先被 frozen VAE encoder 压成 clean latent `x0`，采噪声 `ε` 与时间 `τ`，构造直线路径上的中间点：

```text
xτ = (1-τ)x0 + τε
v* = ε - x0
L_image = E ||vθ(xτ,τ,condition) - v*||²
```

`xτ` 是时刻 `τ` 的中间 latent；`v*` 是从数据指向噪声的恒定目标速度；`vθ` 是模型预测。取一维例 `x0=2, ε=-1, τ=0.25`：`xτ=1.25`，目标速度 `v*=-3`。若模型预测 `-2.5`，平方误差是 `(-2.5+3)²=0.25`。这正是当前开源 `bagel.py` 里的 `target=noise-packed_latent_clean`。见 [[flow-matching]]。

联合训练可概括为：

```text
L = λ_text L_text + λ_image L_image
```

这里的加号表示优化器在同一次训练中汇总当前 batch 中实际存在的文字 loss 和图像 loss；它不表示每个 token 同时计算两项。梯度会更新各自经过的专家，也会更新它们共同依赖的跨模态对齐部分。论文没有报告两项权重，不能凭这条概括式倒推出比例。当前官方仓库 `beea1f7` 的训练脚本设 `λ_text=0.25`，图像 MSE 沿用默认 `λ_image=1.0`；这是当前代码配方，不是论文表里独立消融出的结论。

## 论文训练配方 vs 当前开源脚本

| 项目 | 论文 v1 | 官方仓库 `beea1f7` 当前脚本 |
|---|---|---|
| steps | 50K | 200K |
| warm-up | 500 | 500 |
| learning rate | `2.5e-5`（PDF 可见；HTML 转换吞掉公式） | `2.5e-5` |
| weight decay | 0 | optimizer 明确设 0 |
| EMA | 0.995，EMA eval | 0.995 |
| 每 rank packed tokens | 32K–36K | expected 32K，max 36,864 |
| 单样本 context | 论文写 max 32K | 脚本 max 24,064 token |
| dropout text / ViT / VAE | .05 / .1 / .1 | .05 / .1 / .1 |
| VAE visual encoder | frozen | frozen 路径保留 |

论文还把 SigLIP2 输入上限提到 980，用于理解和 image-conditioned generation，尤其照顾分割的细粒度条件。当前复现必须保存 commit 与 YAML；只记模型名不够。

## 实验一 · 结构化视觉是最强的一块

SenseNova-Vision 在 COCO-Common 56.6、LVIS 54.8、Dense200 66.8、VisDrone 43.3、HierText 62.9、ICDAR15 31.2、COCO keypoint 34.6；HumanRef / RefCOCOg val/test 为 80.2 / 79.6 / 80.5。它在表中多数 structured benchmark 领先。

但 ScreenSpot-V2 是 85.9，低于 Qwen3-VL-8B 的 90.5、Qwen3.5-9B 的 92.2 和 Rex-Omni 的 88.4。不能把“structured 整体强”写成“每项第一”。另外该表混用 F1@mIoU、F1@Point、click accuracy 与 F1@mOKS，横向看覆盖面可以，不能把不同列数值直接平均成一个总分。

## 实验二 · 稠密几何接近专家，但仍有明确差距

深度用 affine-invariant 指标；法线看 mean angular error（越低越好）与阈值准确率（越高越好）。代表结果：

| benchmark | SenseNova | 强专家 | 读法 |
|---|---:|---:|---|
| NYUv2 depth AbsRel↓ | 4.0 | MoGe-2 3.5 | 差 0.5 |
| KITTI depth AbsRel↓ | 5.9 | MoGe-2 5.5 | 差 0.4 |
| ScanNet depth AbsRel↓ | 3.9 | MoGe-2 3.4 | 差 0.5 |
| DIODE depth AbsRel↓ | **20.6** | MoGe-2 23.0 | SenseNova 更好 |
| ScanNet normal mean↓ | **12.8** | MoGe-2 12.8 | 持平 |
| NYUv2 normal mean↓ | **14.4** | MoGe-2 14.7 | 略好 |

它明显强于多数 generation-based baseline，却不能据此说普遍超过 geometry specialist。

## 实验三 · 分割最能暴露“通用 vs 专用”的交换

和 X-SAM 对比：

| 任务 | SenseNova | X-SAM | 差值 |
|---|---:|---:|---:|
| panoptic PQ | 48.8 | 54.7 | -5.9 |
| semantic mIoU | 64.0 | 66.5 | -2.5 |
| RefCOCOg cIoU | 80.3 | 83.8 | -3.5 |
| ReasonSeg val gIoU | **63.2** | 56.6 | +6.6 |
| GCG test mIoU | 66.2 | 69.0 | -2.8 |
| interactive box mIoU | **73.9** | 70.0 | +3.9 |

生成接口在 reasoning 与 box-guided interaction 上有优势，但 mask 专用先验仍让 X-SAM 在 generic、referring、point interaction 等多项占优。论文自己也明确承认 SAM / Mask2Former 一类预训练 mask 模型的优势。

## 实验四 · 多视图 3D 能做，但专家几何先验仍值钱

SenseNova 在 7Scenes reconstruction 是 `0.028 / 0.026 / 87.9`（accuracy / completeness / F1），ETH3D 是 `0.301 / 0.175 / 72.2`；Re10K pose 是 `99.8 / 94.2 / 77.3`，CO3Dv2 是 `97.4 / 95.4 / 80.1`。

DepthAnything3 对应为 `0.020 / 0.026 / 90.5`、`0.228 / 0.212 / 76.6`、`100.0 / 96.4 / 89.6`、`99.3 / 98.0 / 91.8`。多数关键项仍有差距，尤其 pose AUC。更准确的结论是：一个没有几何专用 head 的通用生成模型已经进入可比较区间，但没有抹平专用结构的收益。

## 通用能力有没有被练坏

相对 Bagel：

```text
MMVP understanding: 83.3 → 79.0  = -4.3
GenEval T2I:         0.82 → 0.85 = +0.03
```

这证明的不是“完全无遗忘”，而是能力交换相对温和：理解指标确实下降，生成指标略升。只有两个 benchmark，也不足以概括全部通用能力。

Generalist 对照还要注意协议：Vision Banana 的 ReasonSeg 是 Gemini-assisted；它的 depth 使用 absolute-depth protocol，而 SenseNova 用 affine-invariant，论文已标成仅供参考，不能做直接胜负结论。

## 收敛不是齐步走

论文把每项指标除以最终 step 的数值，只比较相对进度，因此图 6 不能用来比较任务绝对强弱。观察到的次序是：

1. depth / normal 最快：输出与输入空间对齐，也最像预训练阶段见过的 image generation/editing；
2. generic detection / segmentation 居中；referring segmentation 更慢，因为多一道语言指代；
3. multi-view reconstruction 还要跨 view 对齐；camera pose 又有新 token；
4. dense detection 最慢：小目标多、列表长、坐标精确，自回归串行错误更容易累积。

这是一种合理解释，不是严格因果消融。论文没有冻结单一因素来证明“空间对齐”或“新 token”各贡献多少。

## 真正有意思的后续能力 · 训练块能不能重新组合

论文把 referring 的 `<p>…</p>` 与 structured task 的 `<point>[x,y]</point>` 拼起来，要求模型直接从**文本坐标**生成二值 mask：

```text
<p><point>[0.372,0.641]</point></p> → binary mask
```

这个精确 prompt 没出现在 segmentation 训练协议里。模型需要把文本数值定位到图像平面，再调用学过的 mask 生成能力。定性案例可行，说明跨任务对应能组合；但没有 benchmark、样本量和失败率，所以它仍是 qualitative probe，不能写成稳定 zero-shot 能力。

更自由的实验还包括：检测式 instruction 要求密集实例 mask、文字坐标指定 VGD reference、自然语言指定颜色、把单词或字母当 mask。论文最诚实的结果在附录：

- 指定十六进制颜色时，区域大体对，RGB 与边界不总准确；
- structured text 多报/漏报实例会直接污染后续 mask；
- 人工修复实例列表或补足颜色槽后，mask 会明显改善；
- 透明、反射、视觉错觉场景的 depth / normal 会跟着外观线索跑偏；
- CFG 配置不同会把组合输出推向 depth-like、normal-like 或 segmentation-like。

这暴露出混合生成的关键误差链：`instruction → structured plan → visual rendering`。中间计划可编辑是优点；错误也会跨模态放大。

## 论文没有回答的几件事

1. **缺少核心架构消融**：没有比较“相同数据 + 专用 head”和“原生生成通道”，所以不能把所有收益归因于统一生成形式。
2. **缺少大规模 mixture 消融**：VQA/T2I/I2I 各自对保能力与视觉任务的贡献没有拆开。
3. **伪标签上限未分离**：MoGe-2 与 LingBot-Depth 参与数据生成，学生结果与教师覆盖面的关系没有系统分析。
4. **生成成本没有主表**：文本长列表和图像 flow sampling 的 latency / memory 没与一次前向专用 head 对齐比较。
5. **组合任务主要是定性**：新 prompt 能成功，但还不知道稳定性、校准性和失败率。
6. **指标繁多**：跨任务覆盖很广，却没有一个能公平归一不同任务与协议的总指标。

## 怎样读“matches leading specialists”

最稳妥的结论分三层：

- **确证**：一个 Bagel-7B-MoT、无新增 task head，能用原生 text/image generation 覆盖四大视觉族，并在全部任务上生成可解码答案。
- **强证据**：structured 任务广泛领先；generation-based dense perception 很强；reasoning segmentation 与若干几何项有竞争力。
- **仍有差距**：specialized segmentation 与 multi-view geometry 在多项明显更强；自由组合能力还是定性且不稳定。

## 一句话带走

SenseNova-Vision 最重要的不是“一个模型刷了多少榜”，而是把视觉任务设计问题从“该接什么 head”改成了“答案能否翻译成文本、图像或两者混合，并且还能确定地解码回来”。这条路换来可组合性和统一训练，也把新的瓶颈暴露得很清楚：格式错误、颜色漂移、自回归长列表、生成延迟，以及专用几何/掩码先验的缺失。

## 来源与版本

- 论文：arXiv:2607.06560v1，2026-07-07，48 页；训练学习率以官方 PDF 第 9 页为准。
- 底座结构：Bagel，arXiv:2505.14683v3；MoT 路由、SigLIP2 / VAE 双视觉表示和 generalized causal attention 均按其方法章节核对。
- 官方仓库：`OpenSenseNova/SenseNova-Vision`，本文源码核对基于 `master@beea1f7`。
- 论文数字取 Tables 1–5、Figure 6 与 Appendix Tables 6–19；自由组合与失败分析取 Figures 8–22。
