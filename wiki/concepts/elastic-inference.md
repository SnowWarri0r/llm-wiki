---
name: elastic-inference
type: concept
sources: [elt]
updated: 2026-06-10
---

# Elastic Inference · 一个模型，多档算力

## 一句话
一次训练出一**族**模型，推理时按手头算力**临时挑一档**（快但糙 ↔ 慢但好），不必为每个预算单独训一个模型。

## 直觉 · 别为每块设备各训一个

部署一个模型要面对千差万别的预算：手机要快、服务器能慢工出细活。传统做法是训一堆不同大小的模型（small/base/large），各训各的、各存各的，贵且难维护。

Elastic（弹性）的思路：**训一个，内部自带多档**。推理时一个旋钮一拨，就在"快而糙"和"慢而精"之间滑动，沿**质量-算力的 Pareto 前沿**走。Matryoshka（套娃）系列把这个旋钮做在"宽度/维度"上；[[looped-transformer]] 的 ELT 把它做在**循环圈数 L** 上——多套几圈就多算、更准。

## 怎么做的 · 训练时就把每一档都练好

难点不在推理，在训练：怎么保证"中途退出"那些档也好用，而不是只有满配能用？

ELT 用 **Intra-Loop Self Distillation（ILSD）**：
- **teacher 路**：跑满 L_max 圈，出最好结果。
- **student 路**：随机在中间某圈 L_int 提前退出。
- **loss**：满配的真值 loss + 中途档的真值 loss（加权）+ **蒸馏 loss**（让中途档去对齐 teacher 的表征，teacher 那侧 stop-grad）。
- 两条路**更新同一套共享 block 参数**。

于是这套参数被逼着"**每一圈退出都得是个像样的模型**"，弹性就出来了。

## 它换来什么
- **一次训练，覆盖多端**：一个权重文件，手机跑 2 圈、服务器跑 10 圈。
- **Any-Time 推理**：算力紧就早退、宽裕就多算，运行时动态权衡。
- 代价：训练更复杂（要同时照顾所有档），而且每一档未必比"专门为这档训的单模型"更强——换的是**部署的灵活和省事**。

## 代码出处
- ELT / ILSD：arXiv 2604.09168
- 谱系：Matryoshka Representation Learning、MatFormer（Kusupati 等同一条弹性思路）

## 链接
- [[looped-transformer]] · ELT 把弹性旋钮做在循环圈数上
- [[elt]] · 用 ILSD 训出一族深度的视觉生成模型
- [[diffusion-transformer]] · 被做成弹性的底座
