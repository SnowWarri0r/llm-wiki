---
name: wan-animate-2
type: paper
source: https://arxiv.org/pdf/2608.06009v2
upstream: https://humanaigc.github.io/wan-animate-2/
ingested: 2026-08-12
authors: Guangyuan Wang 等（通义实验室，阿里巴巴集团）· arXiv v2 · 2026
year: 2026
---

# Wan-Animate 2 · 不先提骨架，直接让参考视频教角色怎么动

这篇工作的价值不只是把一个人物动画模型做得更快。它同时处理了三件原本互相牵制的事：直接保留驱动视频里的细表情与非刚体动作、把参考视频注意力从全量两两比较改成按时间对齐、再把整段生成蒸馏成可以分块流式运行的少步模型。

## 一句话

让目标视频在每个时刻只读取驱动视频的对应帧，再用误差缓冲与分块 Self-Forcing 把模型蒸馏成实时版本。

## 先分清 Base、Lite 与公开权重

- **Base** 解决动作保真与身份保持：双分支 DiT 直接接收参考人物图和驱动视频，不再先提取骨架或 SMPL。
- **Lite** 解决长视频与实时生成：每 8 帧一块，先做因果 Teacher Forcing，再用 Error Buffer 和分块 Self-Forcing 蒸馏。
- 论文中的实时系统是 **3 步、4 张 GPU、400×720、24 FPS**。截至 2026-08-12，官方仓库公开的蒸馏示例则推荐 **10 步**；两者不是同一个运行点。

## 核心贡献

1. **直接视频驱动**：[[diffusion-transformer]] —— 干净参考视频与带噪目标视频走双分支 DiT，参考 K/V 可缓存复用。
2. **时间对齐**：[[time-align-rope]] 与 [[sparse-reference-attention]] —— 同时刻的目标帧和参考帧共享时间坐标，跨分支注意力只看对应帧。
3. **视角解耦**：[[lora]] —— 用 48 个离散视角的合成多视图数据，只训练交叉注意力 LoRA，让输出镜头不再被驱动视频的机位锁死。
4. **流式蒸馏**：[[error-buffer-training]] 与 [[chunk-wise-self-forcing]] —— 先让训练历史带上“像模型会犯的错”，再以整段 score 指方向、分块反传梯度。

## 数据闭环：旧版 Wan-Animate 又是怎么训练的

旧版不需要“驱动 A + 参考 B + B 做 A 的动作”这种跨身份三元组。它在 Wan-I2V 上继续训练，并用单人、身份稳定的真人视频做自我重建：从同一片段取人物参考图，用 VitPose 提逐帧骨架，按骨架裁逐帧脸部图像，原视频本身就是目标。身体控制只保留骨架；脸部控制会压成一维特征并加入缩放、颜色与噪声扰动，尽量削弱驱动身份。因此旧版可以在同身份真视频上学习“身份看参考图、动作看控制信号”，推理时再把两者拆开组合。

Wan-Animate 2 直接读取完整驱动视频，情况变了。若仍用同一人的视频同时充当驱动输入和目标，驱动分支已经包含脸、衣服与体型，模型只要照抄驱动者就能降低损失，可能完全不看人物参考图。因此二代才需要跨身份、逐帧对齐的目标；旧版用已经学会的骨架/表情控制替二代合成这份目标。两代的数据依赖不是循环：<strong>旧版靠低身份控制信号做自监督，二代靠旧版合成的跨身份视频学习直接视频驱动。</strong>

## 关键数字

- 每个流式块 8 帧。
- 视角控制为 12 个方位角 × 4 个俯仰角 = 48 类。
- 论文实时演示为 400×720、24 FPS、3 个去噪步、4 张 GPU。
- 用户研究只公布胜/平/负比例，没有参与人数、样本数与统计显著性。对 Wan-Animate 的 overall 胜率为 78.5%；对 Dreamina 为 32.3%；对 Kling-MotionControl 为 25.9%。

## 论文覆盖地图

| 原文章节 | 本页落点 |
|---|---|
| 1 Introduction | 三条旧路线为什么分别丢细节、串身份或算不动 |
| 2 Data | 配对视频合成、三类过滤、UE 多视图数据与未公开规模 |
| 3.1–3.4 Base | 总览、双分支 DiT、Time-Align RoPE、Sparse-Ref Attention |
| 3.5 Viewpoint LoRA | 48 个离散视角、文本标签与只训 cross-attention LoRA |
| 4.1–4.2 Lite | 8 帧分块、因果 Teacher Forcing、exposure bias 与 Error Buffer |
| 4.3 + Algorithm 1 | 两阶段 Self-Forcing、整段 score、分块梯度累积与 stop-gradient |
| 5.1–5.5 | 定性比较、视角控制、用户研究、4-GPU 实时流水线 |
| 6 Conclusion | 能证明的结论、没有消融支持的归因与配方缺口 |

## 我的批注

- 最实用的结构不是“又加一个动作编码器”，而是把驱动视频当成按时间索引的外部记忆：目标第 <code>t</code> 帧只去读参考第 <code>t</code> 帧。
- Sparse-Ref 没有把目标视频自己的全局注意力裁掉；它只裁剪目标与参考之间的连边。因此动作细节省算力，目标视频内部仍能全局协调。
- Error Buffer 很像给训练时过于干净的历史“做旧”：模型预测与真值的残差被加回历史，让后续块提前见到推理时会遇到的小漂移。
- Self-Forcing 的关键不是简单地“每块各算各的”。score 网络先看完整序列给出全局方向，生成器才按块重放并累加梯度；否则分块省显存会同时切断长程质量信号。
- 论文没有 Base/Lite 的统一量化对照，也没有模块消融，因而不能从现有实验单独算出 Time-Align RoPE、Sparse-Ref、Error Buffer 各贡献多少。
- 官方开源代码显示参考 K/V 在去噪循环前计算并缓存；这让“参考分支只算一次”不只是架构示意，而是实际推理路径。
- “旧版合成二代数据”并没有把数据来源无限往前推：旧版论文的数据源是收集并过滤的真实单人视频；骨架、脸部区域、人物 mask 与 caption 分别由 VitPose、裁切流程、SAM2 与 Qwen2.5-VL 自动产生。旧版 Relighting LoRA 另用 IC-Light 构造换背景、换光照的训练对。

## 相关概念

- [[diffusion-transformer]]
- [[time-align-rope]]
- [[sparse-reference-attention]]
- [[lora]]
- [[teacher-forcing-video-diffusion]]
- [[error-buffer-training]]
- [[dmd-distillation]]
- [[chunk-wise-self-forcing]]

## 来源与证据边界

- 论文：方法、训练算法、用户研究比例和 3 步实时系统。
- 官方项目页：定性视频与视角控制样例。
- 官方 GitHub（检查于 2026-08-12，提交 <code>3ad2fef</code>）：Base / Distillation 权重、参考 K/V 缓存、稀疏 mask 和公开推理配置。
- 论文没有附录；也没有公开数据规模、过滤阈值、完整训练超参数、用户研究人数或逐模块消融。
