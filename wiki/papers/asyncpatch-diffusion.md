---
name: asyncpatch-diffusion
type: paper
source: raw/papers/asyncpatch-diffusion/2606.07079v1.pdf
upstream: https://arxiv.org/abs/2606.07079
ingested: 2026-08-14
authors: Samuele Papa, Valentin De Bortoli, Guillaume Couairon, Daniel Sýkora, Romuald Elie, Klaus Greff · arXiv 2026
---

# AsyncPatch Diffusion · 不再让整张图共用一只去噪时钟

标准扩散让整张图共享同一个噪声时刻。AsyncPatch Diffusion 把时刻改成一张与空间对齐的图：已知区域可以保持干净，待生成区域从噪声开始，不同 patch 还能按不同顺序去噪。因此，一个无条件 U-Net 在不重训任务头的情况下，同时得到整图生成、补图、空间自回归与细节引导。

## 一句话
**把单个扩散时刻改成空间时刻图，同一个联合 score 网络就能按区域决定“哪里固定、哪里先生成”。**

## 它要解决的痛点

- 普通扩散每步只接受一个标量时刻，整张图只能一起变干净；补图必须在采样器外另加 mask 逻辑。
- 若粗暴地给每个像素独立抽时刻，大量时刻的均值会几乎总卡在 0.5；模型很少看到“整张接近干净”或“大块区域同时纯噪声”这些推理必需状态。
- 方法的代价是更复杂的时刻采样和空间调制；论文也只验证到 256×256 的 U-Net，不能直接外推到现代高清文生图 DiT。

## 核心贡献

1. **联合扩散**：[[joint-diffusion]] —— 每个 token 独立加噪，网络仍联合看整张图，从而学到带有空间条件的联合 score。
2. **AsyncPatch 时刻采样**：[[asyncpatch-timestep-sampling]] —— 先均匀选全图平均噪声，再在以它为中心的区间内给 patch 分配时刻，修掉“均值总在 0.5”的训练缺口。
3. **可控的时间路径**：[[spatial-diffusion-schedule]] —— 推理时用一组单调下降的局部时钟，同一模型可在同步生成、补图和空间自回归之间切换。
4. **Input Guidance**：[[input-guidance]] —— 同一状态在“较干净输入”和“较噪输入”下各算一个 score，外推两者的差，强化已知细节对待生成区域的影响。

## 关键概念

- [[diffusion-timestep-conditioning]] · 标准扩散如何把一个时刻送进每层；AsyncPatch 将它升级为二维时刻图。
- [[score-function]] · score 不是图像得分，而是和图像同形的局部修改方向。
- [[classifier-free-guidance]] · CFG 放大文本条件差；Input Guidance 放大空间输入条件差，两者可叠加。
- [[pixel-space-diffusion]] · 论文同时验证像素空间和 latent 空间，两类结果不能混着横比。

## 我的批注

- 这篇最值钱的不是“又一个补图模型”，而是把 mask 重写成时间边界条件：已知区域的时钟永远在 0，未知区域的时钟从 1 降到 0。
- 它真正修的是训练分布。“每块独立抽时刻”看似自由，但 patch 一多，均值反而被大数定律锁在中间；AsyncPatch 先选均值，再选局部差异。
- 论文说采样“按构造具有选定均值”。严格说，若各 patch 只是独立从对称区间抽样，有限个 patch 的样本均值只在期望上等于选定均值，会有小幅波动。
- ELBO 定理证明这不是任意的多时钟损失：把时间超立方中的单调路径做平均，可得到一组正权重，使 score 损失成为数据对数似然的变分下界。这是理论保底，不是训练时多跑一个模块。
- 最严格的主表只支持“生成质量基本保住，并多出任务灵活性”，不支持“全面超越专用模型”。

## 跟 wiki 里其他 paper 的关系

- [[diffusion-unet]] · 沿用 U-Net 去噪骨干，但把标量时刻调制改成空间可变调制。
- [[mrt]] · MRT 用干净 / 噪声 region token 统一分层任务；AsyncPatch 更底层，直接给每个空间单元安排时间坐标。
- [[dmd]] · 两者都能减少或重排生成路径，但 AsyncPatch 不做少步蒸馏；它改的是空间时刻自由度。

## 历史定位

- 2015–2022 传统扩散 · 整张图共享一个时刻，补图主要由外部 mask 采样策略完成。
- 2023–2025 异质时刻 / spatial masking · 多个工作让不同 token 位于不同噪声水平，但统一的似然解释仍不完整。
- 2026-06 **AsyncPatch Diffusion** · 给出可操作的 patch 采样器、多种推理路径与显式 ELBO 权重存在性证明。
