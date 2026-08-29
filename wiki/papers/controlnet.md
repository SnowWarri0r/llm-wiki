---
name: controlnet
type: paper
source: https://arxiv.org/abs/2302.05543
upstream: https://github.com/lllyasviel/ControlNet
ingested: 2026-08-24
authors: Lvmin Zhang · Anyi Rao · Maneesh Agrawala · ICCV 2023
year: 2023
---

# ControlNet · 文字管“画什么”，条件图管“画在哪”

Stable Diffusion 能照文字画图，却很难只靠提示词复现一条指定轮廓、一套人体姿态或一张深度布局。ControlNet 给冻结的扩散 U-Net 接上一条可训练旁路：主干保住原有画质，旁路专门把边缘、姿态、分割、深度等空间条件翻译成 13 组多尺度修正。

## 一句话

**冻结原 Stable Diffusion，只复制 U-Net 的 12 个编码块与中间块来学空间条件；零初始化的 1×1 卷积保证训练刚开始时旁路修正严格为零。**

## 它要解决的痛点

1. **文字擅长说“是什么”，不擅长钉死“在哪里”**：提示词可以写“一个人抬起右手”，却很难精确指定每个关节坐标。
2. **特定条件的数据远少于文生图预训练数据**：论文举例，专门任务常只有约 10 万张，而 Stable Diffusion 用到的 LAION-5B 大约有 50 亿条；直接全参微调容易过拟合并忘掉原能力。
3. **轻量旁路不一定看得懂复杂条件**：只接几层随机初始化卷积虽便宜，但在没有完整提示词时很难从草图判断“这是一栋房子”。

## 核心贡献

1. **空间条件旁路**：[[spatial-conditioning]] —— 把 512×512 的边缘、骨架、分割或深度图压成与 latent 对齐的特征，再在 U-Net 多尺度位置注入。
2. **冻结主干 + 可训练副本**：[[frozen-backbone-side-network]] —— 原主干不更新；副本从同样的预训练编码器出发，只承担控制修正。
3. **零卷积起步**：[[zero-convolution]] —— 输出门从严格 0 开始，先学会“该放多少修正”，再把梯度逐步放进条件分支。
4. **训练与推理仍沿用扩散模型**：[[noise-prediction-objective]] · [[classifier-free-guidance]] —— 没另造生成目标；仍预测噪声，并在推理时组合有条件与无条件预测。

## 关键结构账

- Stable Diffusion U-Net 共 25 个块；ControlNet 只复制 12 个编码块和 1 个中间块，不复制 12 个解码块。
- 13 路输出分别加到 12 条 skip connection 与中间块，覆盖 64×64、32×32、16×16、8×8 四个尺度。
- 原论文报告：相对直接优化 Stable Diffusion，单张 A100 PCIe 40GB 上显存增加约 23%，每步训练时间增加约 34%。
- 官方实现 commit `ed85cd1` 的条件编码器使用三次 stride-2，把 512×512 压到 64×64；这与论文正文“4 个 4×4 stride-2 卷积”的描述不一致。

## 训练与实验

- 损失仍是噪声均方误差；训练时随机把 50% 文本提示替换为空串，逼旁路直接读懂条件图。
- 条件数据从 20K ADE20K 到 3M Canny / HED / depth 都能训练；补充材料报告统一学习率 1e-5、不使用 EMA。
- 12 人草图用户研究中，ControlNet 的图像质量平均排名 4.22、条件忠实度 4.28，均高于 ControlNet-lite 的 3.93 / 4.09。
- ADE20K 条件重建 IoU 为 0.35，ControlNet-lite 为 0.32；FID 为 15.27，优于 lite 的 17.92，但不如没有空间约束的普通 Stable Diffusion 6.09。论文明确提醒：FID 不能单独评价控制模型。

## 我的批注

- ControlNet 最关键的不是“多接了一张图”，而是把两笔风险拆开：冻结主干保画质，深副本保理解力，零卷积保起步稳定。
- “零卷积会不会学不动”要沿链式法则看：第一步输入梯度确实被挡住，但零卷积自己的权重梯度不为零；输出门先打开，后面的副本与条件入口才开始收到梯度。
- 论文的条件编码器尺寸描述算不闭合；官方代码才给出 512→256→128→64 的三次下采样。这类实现事实不能拿论文一句话硬圆。
- 多 ControlNet 的输出可以相加，但“能相加”不等于条件永不冲突；论文只展示姿态+深度，没有系统分析互相矛盾的条件。
- 1K 数据“不崩”只证明架构稳，不等于小数据能学出与 3M 数据同样丰富的条件语义。

## 跟 wiki 里其他页的关系

- [[diffusion-unet]] · ControlNet 冻结并复制的具体骨架
- [[noise-prediction-objective]] · 训练目标没有变化，变化的是 U-Net 多收一张空间条件图
- [[classifier-free-guidance]] · 为什么条件只放进 conditional 分支时会被 CFG 放大
- [[convolution]] · 1×1 卷积只混通道、不混相邻位置
- [[semantic-segmentation]] · 论文的一类输入条件与 IoU 评测来源

## 历史定位

- 2022 **Latent Diffusion / Stable Diffusion** · 把文生图去噪搬进 latent，并用 cross-attention 接文字
- 2023-02 **ControlNet** · 冻结主干、复制编码器、用零卷积学习可插拔空间控制
- 2023-02 **T2I-Adapter** · 同期更轻的条件适配路线
- 2023-04 **ControlNet 1.1** · 官方仓库后续加入 lineart、softedge、shuffle、inpaint 等模型；不属于原论文方法贡献

