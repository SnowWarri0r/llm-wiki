---
name: genception
type: paper
source: https://arxiv.org/pdf/2607.09024
upstream: https://genception.github.io/
ingested: 2026-07-26
authors: Letian Wang, Chuhan Zhang, Rishabh Kabra, Jasper Uijlings, Steven Waslander, Andrew Zisserman, Joao Carreira, Kaiming He, Misha Andriluka, Eduard Gabriel Bazavan, Andrei Zanfir, Cristian Sminchisescu · Google DeepMind 等 · ECCV 2026
year: 2026
---

# GenCeption · 视频生成模型也能成为通用视觉骨干

语言模型先靠“预测下一个 token”学会世界知识，再通过后训练完成问答、写作和工具调用。GenCeption 追问：视频模型为了生成合理运动、透视、遮挡和材质，已经被迫学会了不少视觉规律，能不能也把这些生成知识拿来做深度、法线、分割、相机姿态和人体关键点？

它的答案不是另接一排任务专用大头，而是尽量保留 WAN 2.1 的 VAE、文本编码器和 DiT：输入干净视频，时间设为零，只跑一次 DiT；文字提示决定当前输出什么；密集任务尽量改写成 RGB 视频，稀疏坐标才增加少量可学习 token。

## 一句话

**把视频生成器的“会画”通过一次前向和统一目标格式，转成“会看”。**

## 推荐阅读顺序

```text
为什么生成视频会顺带学会视觉规律
→ WAN 原来怎样从噪声生成视频
→ 为什么输入干净视频、设 t=0、再把速度取反
→ 深度 / 法线 / 分割 / 相机姿态怎样统一成 RGB
→ 关键点为什么必须走另一条 token 支路
→ 统一 L2 如何成立
→ 合成数据、训练配方、推理成本
→ 实验真正证明了什么，又没有证明什么
```

## 它要解决的痛点

- **视觉模型仍按任务拆家**：深度、法线、分割、相机姿态通常各有不同输出头和损失，新增任务就继续加工程分支。
- **视频理解预训练未必对生成细节负责**：掩码重建、对比学习能学表征，但不一定被迫还原每个像素的几何、运动和遮挡。
- **扩散生成太慢**：WAN 原本要迭代去噪；感知任务需要确定、快速的答案，不能每次深度估计都采样几十步。
- **统一不是免费的**：密集像素任务容易塞回生成模型原生的 RGB 空间；稀疏坐标要新增 token，联合训练时反而明显退化。

## 核心贡献

1. **生成到感知**：[[generation-to-perception]] —— 把整流流视频 DiT 改成一次前向的感知骨干，输入干净 latent、固定 `t=0`，并把速度输出取反。
2. **目标格式统一**：[[rgb-task-representation]] —— 深度、掩码、法线和 DensePose 都编码成三通道 `[0,1]` 视频，让同一个 VAE decoder 和 L2 loss 处理。
3. **相机姿态像素化**：[[raymap]] —— 把每像素六维射线的起点和方向拆成两块三通道画面，绕开专用矩阵回归头。
4. **合成监督扩规模**：用 800 个 RenderPeople 人体、200 段 CMU 动作和 Blender 多渲染通道生成 7,500 个多标签视频。

## 关键概念

- [[video-vae]] · 把 81 帧视频在空间和时间上压缩成 latent，训练和推理都不直接在原像素上跑 DiT。
- [[diffusion-transformer]] · GenCeption 复用的主干；原来预测生成速度，后训练后改为输出感知目标。
- [[flow-matching]] · 解释速度 `v = ε - x₀`、时间 `t` 和为什么取反不是“精确恢复目标”。
- [[generation-to-perception]] · 区分预训练提供的视觉先验、符号取反提供的初始化方向，以及后训练真正完成的任务适配。
- [[rgb-task-representation]] · 为什么“统一 loss”依赖先统一目标数据，而不是所有任务天然相同。
- [[raymap]] · 相机六维射线场与 “Rothko” 三通道打包。
- [[mrope]] · 新增关键点 token 仍要带时间和空间位置。

## 论文覆盖地图

| 原文章节 | 本页对应内容 |
|---|---|
| 1–2 Introduction / Related Work | 为什么把生成预训练视作视觉预训练 |
| 3.1 Methodology | 完整系统图与三条设计原则 |
| 3.2 From Diffusion Pre-training to Perception Finetuning | `t=0`、速度取反、最终层特征 |
| 3.3 Unified Task Representation | 密集 RGB、Rothko raymap、稀疏 token |
| 3.4 Scalable Synthetic Data Generation | 7,500 段多标签合成视频 |
| 3.5 Training Recipe | L2、深度中位数归一化、对数映射 |
| 4.1–4.3 Implementation / Cost / Protocol | 配置、梯度保护、成本和指标 |
| 4.4–4.5 SOTA / Ablations | 专家与通才、预训练和数据效率 |
| 4.6 Emergent Behaviors | 合成到真实、多实例、未见类别 |
| 5 Conclusion | 结论与证据边界 |

## 我的批注

- **最重要的不是负号，而是接口没有被破坏**：最终层仍能接原 VAE decoder，密集任务仍像“生成一段目标视频”。负号只是让初始输出方向更像干净数据；任务能力来自后训练。
- **“一个 loss”其实把复杂度搬到了数据端**：深度先做尺度归一化和对数压缩，相机姿态先变成 raymap。工程没有消失，只是从 loss/head 转移到 target formatter。
- **联合训练结果并不整齐**：前景分割受益，深度和相机姿态多有小幅回退，新增 token 的 3D 关键点严重退化。它证明了统一框架可行，也暴露了“尽量不改预训练接口”的边界。
- **数据效率比较值得看，但口号要降温**：同一深度数据上，WAN 初始化明显优于 V-JEPA 和 VideoMAE V2；然而不同专用模型的数据、架构和训练流程并不完全同口径。
- **“世界模型”仍是解释，不是结论**：猫须、多人和动物泛化主要是定性图；它们支持生成预训练带来强先验，但不足以证明模型掌握了通用物理因果。
- **截至 2026-07-26，项目页代码仍标为 TBA**：论文没有公开深度映射系数 `α` 的取值规则、梯度裁剪/丢弃阈值、任务混合比例和 L2 的具体 reduction，复现仍缺关键细节。

## 跟 wiki 里其他 paper 的关系

- [[sensenova-vision]] · 同样把深度、法线等视觉目标放进生成模型的连续 latent；GenCeption 更强调复用完整视频生成骨干和一次前向。
- [[drifting-models]] · 生成模型怎样提供可迁移的 score / 速度知识；GenCeption 不做蒸馏，而是直接后训练骨干。
- [[dmd2]] · DMD2 把多步扩散蒸成少步生成；GenCeption走另一条路，把任务变成确定性感知，因此只做一次前向。
- [[qwen3-vl-report]] · 另一条通才路线：把视觉变成语言 token，再由自回归模型回答；GenCeption尽量把视觉任务留在连续像素空间。

## 历史定位

- 2022–2024 · V-JEPA / VideoMAE 等视频表征学习，把视频预训练用于下游理解。
- 2025 · WAN 2.1 将大规模开源视频生成骨干扩到 1.3B / 14B。
- 2025 · Vision Banana 等工作展示图像生成器可被改造成视觉通才。
- 2026-07 · **GenCeption** 将这条路线扩到原生视频域，统一密集与稀疏感知，并做系统基准评估。
