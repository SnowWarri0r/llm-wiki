---
name: perceptual-loss
type: concept
sources: [hidream-o1, drifting-models, dmd]
updated: 2026-07-22
---

# Perceptual Loss · LPIPS / DINO · 在"特征空间"里比两张图像不像

## 一句话
不逐像素比两张图，而是把它们都喂进一个**预训练的"懂图"网络**、比深层激活的距离 —— 这比"看不看得像"更接近人眼。**LPIPS** 和 **DINO loss** 就是用两种不同网络特征来比。

## 直觉 · 像素 L2 是个烂的"像不像"

直接比像素（L2 / MSE）作为"两张图像不像"的尺子很差：
- 把图**整体平移 1 个像素** → 看着一模一样，但逐像素 L2 **巨大**。
- 一张**糊**的图 → 像素值平均下来跟清晰版接近、L2 **小**，但人一眼看出不对。

根因：人不是逐像素看图的，是看**纹理、结构、语义**。所以把两张图都过一个**预训练网络**，比它们的**深层特征**——特征近 = 网络（也大致是人）觉得像。这就是 perceptual loss。

类比：像素 L2 = **逐字母**比两篇文章；perceptual loss = 让一个**读者读完两篇、比"意思像不像"**。读者不同，比的侧重也不同。

## 两种特征 · LPIPS vs DINO loss

用哪个网络的特征，决定了你比的是"哪种像"：

- **[[lpips]]**（Zhang 2018）：用预训练 CNN（VGG/AlexNet）多层特征 + 一组拿**人类 2AFC 判断**校准的线性权重。偏**纹理 / 局部结构 / 风格**。是这套思想最经典的奠基实例。
- **DINO loss**：用 **[[dino]]**（自监督 ViT，无标签自蒸馏训出来的）的特征比。DINO 特征出了名地**抓语义和物体结构**，所以偏**高层语义 / 全局连贯**。[[hidream-o1]] 用它正是因为像素扩散细节够、缺的是长程语义连贯。

> 一句话分工：**LPIPS 管"纹理/风格像不像"，DINO 管"语义/结构像不像"。** 各自细节见 [[lpips]] / [[dino]] 专页。

## 怎么当 loss 用
训练时，除了主目标（[[flow-matching]] 预测速度场），还把模型**解出来的预测图**跟 ground-truth 图算 LPIPS + DINO 距离，一起反传。**感知网络（VGG / DINO）全程冻结**，只当一把"会看图的尺子"，不更新。

## 代码出处
- LPIPS：Zhang et al. 2018，`lpips` 包是标准实现（详见 [[lpips]]）
- DINO：Caron et al. 2021，自监督 ViT（详见 [[dino]]）
- 用法见 HiDream-O1-Image arXiv 2605.11061（flow matching + LPIPS + perceptual DINO loss）

## 链接
- [[lpips]] · 最经典的实例（VGG 特征 + 人类校准）
- [[dino]] · DINO loss 的特征来源（自监督 ViT，偏语义）
- [[pixel-space-diffusion]] · 像素空间为何需要它补语义连贯
- [[hidream-o1]] · flow matching 之外加 LPIPS + DINO
- [[flow-matching]] · 主训练目标，perceptual 是附加监督
