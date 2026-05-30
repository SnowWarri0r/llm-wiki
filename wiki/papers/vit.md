---
name: vit
type: paper
source: https://arxiv.org/abs/2010.11929
upstream: https://arxiv.org/abs/2010.11929
ingested: 2026-05-28
authors: [Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, Jakob Uszkoreit, Neil Houlsby]
year: 2021
---

# ViT · An Image is Worth 16×16 Words

## 一句话
把图片切成 16×16 的小块，每块当一个"词"，剩下的事全交给 Transformer —— **CNN 不是必需品，Transformer 也能干视觉**，前提是数据够多。

## 它要解决的痛点

2012 年 AlexNet 之后，视觉领域 CNN 一统天下，没人怀疑。但 NLP 这边 2017 年 Transformer 起来后，BERT/GPT 把 CNN 时代留下的所有 NLP 架构全推平了。问题就来了：

**视觉为什么不能也用 Transformer？**

之前有人试过，但全是"混搭" —— 留一部分 CNN 做前置特征提取，后面接 attention。没人敢直接拿原图喂给 Transformer，因为：

1. **像素数太多**。一张 224×224 的图有 50176 个像素，每个当 token 的话，self-attention 是 O(N²)，算不动
2. **CNN 有"祖传家产"**：局部性（邻近像素相关）、平移不变性（猫在左上角和右下角都是猫）—— 这些都是写进卷积结构里的归纳偏置，Transformer 没有

ViT 的回答：**别一个像素一个 token，切成 16×16 的 patch 一个 token**。224×224 的图就剩 14×14=196 个 token，Transformer 算得动了。至于归纳偏置 —— **数据量够大就不需要**。

## 核心贡献

1. **Patch as token**：把图切成固定大小（16×16 或 14×14）的方块，每块拉平 + 线性投影 = 一个 token。**视觉问题被强行翻译成了 NLP 问题**

2. **纯 Transformer 做视觉分类**：除了 patch embedding 那一层，里面跑的就是标准的 Transformer encoder，跟 BERT 几乎一模一样。包括 [CLS] token + 学习式位置编码 + 多头自注意力

3. **数据驱动的归纳偏置替代**：
   - 在 ImageNet-1k（130 万张）上训练 → ViT 输给同等规模的 ResNet
   - 在 ImageNet-21k（1400 万张）上 → 持平
   - 在 JFT-300M（3 亿张, Google 内部数据集）上 → **ViT 反超**, 而且算力效率比 ResNet 高得多

   **结论**: 当你有 CNN 没见过的数据规模时, "祖传家产"反而是包袱

4. **图像也吃 scaling law**：跟 NLP 那边一个剧本 —— 数据越多、模型越大、训练越久, 效果越好, 而且看不到尽头

5. **可视化归纳偏置的"重新发现"**：训练好的 ViT 早期 layer 学到的注意力模式, 居然自己长出了类似 CNN 的局部性 —— 不是因为有人手写, 而是因为这种结构对视觉确实有用, 数据足够多模型自己学得到

## 关键概念 → 概念页链接

- [[patch-embedding]] · 把图切成 token 的核心操作
- [[inductive-bias]] · CNN 的"祖传家产" vs Transformer 的"无知"
- [[self-attention]] · ViT 跟 BERT 共享的注意力机制
- [[positional-encoding]] · ViT 用的是学习式绝对 PE（跟 BERT 一样, 不是 RoPE 那种）
- [[scaling-laws]] · ViT 把 NLP 的 scaling 故事搬到了视觉

## 我的批注 / 疑问

- **ViT 在工程上最深远的影响不是分类做得多好, 而是把"图像 = 一串 token"这个抽象立起来了**。之后所有的多模态（CLIP、DALL-E、Flamingo、LLaVA）都用 ViT 风格的图像 encoder, 因为它跟语言端的 Transformer 能直接对齐 —— 一边是文本 token, 一边是 patch token, 都是 token 都进 Transformer, 就这么简单
- 16×16 patch 是个工程妥协。再小算不动, 再大丢细节。后面 Swin Transformer 用层次化的窗口注意力让 patch 可以做小一些
- ViT 出来时业内有不少声音说"这只是大力出奇迹, 没意思" —— 跟 GPT-3 出来时一样的反应。但事实是: 它确实奏效了, 而且把 CNN 的护城河彻底填平了
- 真正训练 ViT 的工程坑: 数据少的时候非常吃 augmentation 和 regularization（DeiT 这篇就是讲怎么在 ImageNet-1k 上把 ViT 训起来的）。所以"ViT 比 CNN 好"这个结论严格说是"在足够多数据下"
- 一个很反直觉的点: 把图片切碎成 196 个独立 patch 喂进去, 中间 attention 就把它们重新关联回去了 —— **结构层面把空间信息打散, 让模型自己用 attention + PE 重新组织**。这跟 BERT 把句子打成 token、然后让模型自己学语法是同一套思路
- 疑问: 如果 patch 大小不固定（多尺度）, ViT 怎么处理? → 后来的 Swin / DINOv2 给出了不同答案, 但 ViT 原文只玩固定 16×16
