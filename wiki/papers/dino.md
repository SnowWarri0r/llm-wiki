---
name: dino
type: paper
source: https://arxiv.org/abs/2104.14294
ingested: 2026-06-10
authors: [Mathilde Caron, Hugo Touvron, Ishan Misra, Hervé Jégou, Julien Mairal, Piotr Bojanowski, Armand Joulin]
year: 2021
---

# DINO · 自监督 ViT · 自蒸馏无标签

## 一句话
不用任何标签，让一个 student ViT 去对齐一个 teacher ViT 的输出，而 teacher 是 student 自己的滑动平均——自己教自己。训出来的特征强在语义/结构，注意力无监督就落在物体上。

## 它要解决的痛点
监督学习要海量人工标签。自监督想从数据本身造监督信号，但"同一图两视角输出该一致"有个作弊解：全输出常数（坍缩）。DINO 在不用负样本、不用标签的前提下把这件事做稳。

## 核心贡献
- **自蒸馏 + EMA teacher**：student 梯度更新去对齐 teacher 的输出分布（交叉熵）；teacher = student 的指数滑动平均（动量、stop-grad）。student 追一个更稳更慢的自己。
- **multi-crop**：每图 2 全局 + 8 局部裁剪，student 看全部、teacher 只看全局 → 逼"局部预测出全局语义"。
- **centering + sharpening 防坍缩**：两个相反的力（推平 vs 推尖）平衡，不用负样本就稳住。
- **涌现属性**：ViT [CLS] 注意力无监督聚焦物体 ≈ 免费分割；k-NN 特征强分类；下游通吃。
- **谱系**：DINOv2(2023) scale 成通用视觉基座；DINO 特征被 [[perceptual-loss]] 借作 "DINO loss"。

## 关键概念 → 概念页
- [[perceptual-loss]] · DINO 特征当 "DINO loss" 补语义连贯
- [[contrastive-learning]] · 同是自监督，但 DINO 无负样本
- [[self-attention]] · 涌现的物体注意力来自它
- [[patch-embedding]] · ViT 的输入
- [[elt]] · ILSD 也是自蒸馏（student 对齐更强的自己）

## 我的批注 / 疑问
- "自蒸馏"在我学的东西里出现了两次：DINO（对齐 EMA teacher）+ ELT 的 ILSD（中途退对齐满配）。共同骨架=让网络追一个更稳/更强版本的自己。
- DINO 特征强在语义/结构，所以 HiDream-O1 拿它当 perceptual loss 补"长程语义连贯"——这条线串起来了。
- 待查：DINOv2 相比 DINO 的具体改动（更大数据 + 一些训练稳定性 trick）。
