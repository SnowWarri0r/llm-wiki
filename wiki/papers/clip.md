---
name: clip
type: paper
source: https://arxiv.org/abs/2103.00020
upstream: https://arxiv.org/abs/2103.00020
ingested: 2026-05-28
authors: [Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, Gretchen Krueger, Ilya Sutskever]
year: 2021
---

# CLIP · Learning Transferable Visual Models from Natural Language Supervision

## 一句话
不用人工打标签, 直接从互联网爬 4 亿张"图 + caption"对子, 让图像和文本在同一个向量空间里对齐 —— **图片识别从"判断这是什么类别"变成"哪句话最配这张图"**, 顺手解锁 zero-shot 分类和所有现代多模态。

## 它要解决的痛点

ImageNet 时代视觉训练的标准流程是: **人工标注**。1400 万张图, 雇人一张一张标"这是猫 / 这是狗 / 这是飞机"。优点是干净, 缺点也很明显:

1. **死贵**: 标 1400 万张图花了 ImageNet 团队几年时间, 每张图几美分
2. **类别固定**: 训练集是 1000 类 "cat/dog/airplane", 模型就只认这 1000 类。换个任务（医学图像 / 卫星图 / 商品图）就得**重新标 + 重新训**
3. **信号穷**: 一张图配一个标签 "dog" —— 但这张图实际上还包含"金毛、在草地上、阳光、年轻、戴红色项圈"这些信息全被扔了

NLP 那边 GPT-2/3 已经证明: **完全跳过人工标注、直接拿互联网原文做训练, 反而效果更好**（[[gpt-3]] 的核心思想）。视觉为什么不能也来这一套？

**因为视觉没有"原文"** —— 你不能像读维基百科一样把图像当文本读。但 OpenAI 注意到一个事实: **互联网上有数十亿张图配着 caption**（alt 文本、图说、社交媒体配文）。这些 caption 不是为训练写的, 是网友自然产生的"图说话"。

CLIP 就是把这些**天然图文对**当训练数据 —— **从 4 亿个图文对里学习"哪句话配哪张图"**。一旦学会, 你就不需要再单独标分类训练集了 —— 想分什么类直接喂文本进去就行。

## 核心贡献

1. **对比学习当训练目标**: 一个 batch 里 N 个图文对, 让 image_i 跟 text_i 在向量空间里最像, 跟其他所有 text_j 都远离。**Loss 不依赖任何手工标签**

2. **Dual-tower 架构**: 一个图像 encoder（[[vit]] 或 ResNet）+ 一个文本 encoder（Transformer）, 各跑各的, 最后两边都投影到同一个向量空间。**两边可以独立放大缩小**

3. **WIT 数据集 · 4 亿图文对**: 从互联网爬 4 亿个"图 + 它周围出现的 caption" 对子（OpenAI 没开源, 但 LAION-400M / LAION-5B 后来开源复刻了这个想法）

4. **Zero-shot 图像分类**: 训完之后, 你想分 "猫/狗/飞机"? 直接把这些词包成 "a photo of a {cat}" / "a photo of a {dog}" 喂进文本 encoder, 跟图像 embedding 算相似度。**不用 fine-tune, 不用看任何标注**。在 27 个数据集上 zero-shot 平均跟 ResNet-50 finetune 持平

5. **解锁所有现代多模态**: DALL-E 2 / Stable Diffusion 用 CLIP 文本 encoder 做 conditioning; LLaVA 用 CLIP 图像 encoder 喂给 LLM; open-vocabulary 检测、视频理解、机器人视觉 —— **全都是 CLIP 这个 joint embedding space 立起来之后的衍生品**

## 关键概念 → 概念页链接

- [[contrastive-learning]] · CLIP 的训练目标; 拉近正样本, 推开负样本
- [[zero-shot-image-classification]] · 把分类问题改写成"哪句话配这张图"
- [[dual-tower-architecture]] · 两个独立 encoder 投影到同一空间
- [[patch-embedding]] · CLIP 的图像 encoder 用 ViT 时, 就是 patch embedding
- [[scaling-laws]] · 4 亿对子是视觉-语言端 scaling 故事的开端
- [[bitter-lesson]] · 又一个"通用方法 + 大数据 + 弱监督" 干掉 "精标注 + 专用结构" 的例子

## 我的批注 / 疑问

- **CLIP 真正的影响力远超论文本身**。论文的 benchmark 结果 (zero-shot 跟 ResNet-50 持平) 其实不算特别炸; 但它**立起来的那个 joint embedding space** 是后来所有多模态系统的地基。Stable Diffusion 用 CLIP 文本 encoder, LLaVA 用 CLIP 图像 encoder, DALL-E 2 用 CLIP 做 prior —— 没有 CLIP 就没有 2022 之后的整个生成 AI 浪潮
- **对比学习 + 大数据 = scaling**: 跟 [[gpt-3]] 是同一个故事。GPT-3 证明 "next token prediction + 大数据" 学出来的表示能 zero-shot 任何 NLP 任务。CLIP 证明 "contrastive image-text + 大数据" 学出来的表示能 zero-shot 任何视觉任务。**OpenAI 在两个领域同时把这条路走通了**
- 工程细节: CLIP 的 batch 必须**很大**才能跑得动（论文用 batch_size = 32768, 因为对比学习的"负样本"就是 batch 内的其他样本, batch 小了负样本不够; 这是分布式训练的工程挑战）
- 局限性: CLIP 不擅长**细粒度区分**（区分 "金毛" 和 "拉布拉多" 不如专门标注的分类器）, 也不擅长**计数**（"图里有几只猫"通常错）, 还有**有名的 bias**（"a photo of a CEO" → 大多数白人男性, 反映训练数据偏见）
- 用户角度: 现在跑任何"以图搜图" / "图说话" / "看图问答" 服务, 底层多半是 CLIP 或它的开源复刻 (OpenCLIP / SigLIP)
- 疑问: SigLIP (2023 Google) 用 sigmoid loss 替代 softmax-style contrastive, 据说效果更好、对 batch size 要求更低 —— CLIP 的对比学习是不是有更好的损失函数版本？应该是的
