---
name: contrastive-learning
type: concept
sources: [clip]
updated: 2026-05-28
---

# Contrastive Learning · 对比学习

## 一句话
不告诉模型"这张图是什么类别", 只告诉它"这张图配这句话, 不配那 N 句话" —— **靠正样本互相吸引、负样本互相推开**, 让模型自己学出语义对齐。

## 直觉 · 为什么"对比"比"分类"更好

传统分类的训练目标: 模型预测一个 1000 类的概率分布, 跟 ground truth one-hot 算交叉熵。

这种训练方式有两个根本问题:

1. **类别要预先定死**: 你训了 1000 类, 模型就只认 1000 类。来了第 1001 类完全不会
2. **监督信号太稀**: 一张图配一个 label "dog", 模型只学到"图 → dog"的映射。**这张图里的其他信息（金毛、在草地上、阳光、戴项圈）全被扔了**

对比学习换一种思路 —— **不预测具体类别**, 而是判断"这两个东西配不配"。

- 给你一张猫图 + 一句话 "a photo of a cat", 模型说: 配
- 给你同一张猫图 + 一句话 "a photo of a car", 模型说: 不配

这种训练方式不需要"猫"这个 label 存在 —— **它只关心两个东西的语义对齐**。任何一对"语义相关"的数据都可以做训练样本: (图, caption) / (英文句子, 法文句子) / (视频, 字幕) / (图, 同一个图的不同裁剪)。

## 怎么训出来

CLIP 的具体做法 (in-batch contrastive)<br>

```python
# 一个 batch 有 N 个图文对: (image_1, text_1), ..., (image_N, text_N)
# 注意 text_i 是 image_i 在网上配套出现的那个 caption (天然 pair)

img_embeds = image_encoder(images)    # (N, D)
txt_embeds = text_encoder(texts)      # (N, D)

# normalize 到单位向量
img_embeds = img_embeds / img_embeds.norm(dim=-1, keepdim=True)
txt_embeds = txt_embeds / txt_embeds.norm(dim=-1, keepdim=True)

# 算所有图跟所有文本的相似度: 一个 N×N 矩阵
sim = img_embeds @ txt_embeds.T       # (N, N)
sim = sim * temperature_scale         # 学一个温度参数

# 标签: 对角线是正样本 (image_i 跟 text_i 配)
labels = torch.arange(N)

# 两边都做 cross entropy (图→文 + 文→图, 对称)
loss = (
    F.cross_entropy(sim, labels) +
    F.cross_entropy(sim.T, labels)
) / 2
```

关键洞察:

- **正样本**: 对角线那 N 对 (image_i, text_i) —— 这些是网上天然配在一起的
- **负样本**: 非对角线的 N²-N 对 —— 用 batch 里的其他文本当负样本, 不用单独构造
- **训练目标**: 让对角线 sim 高、非对角线 sim 低 —— softmax + cross entropy 一行搞定

**一个 batch 同时贡献 N² 个判断**, 数据效率高得多。

## In-batch negatives · 为什么 batch 要大

对比学习的一个关键工程细节: **batch size 必须很大**。

- batch = 32: 每个图只跟 31 个负样本对比 → 模型很容易学
- batch = 32768 (CLIP 实际用的): 每个图跟 32767 个负样本对比 → 模型必须学到很精细的语义区别才能做对

直观理解: **越多负样本越能逼模型学到细节**。区分"金毛" vs "汽车"很简单, 区分"金毛" vs "拉布拉多" 难得多 —— 但只有当 batch 里同时出现这两种相似的样本时, 模型才会被迫学到这个区别。

工程代价: 这要求**分布式训练 + gradient checkpointing + 大显存**, 不是随便能复现的。SigLIP (2023) 用 sigmoid loss 替代 softmax-style 对比损失, 据说能在小 batch 上跑得动。

## 跟 cross entropy 分类的对比

| 维度 | Cross Entropy 分类 | Contrastive Learning |
|---|---|---|
| 标签形态 | 固定 K 个类的 one-hot | 任意一对 "配 / 不配" |
| 监督信号密度 | 一张图一个 label | 一张图跟 N-1 个负样本对比, 信号 N-1 倍 |
| 类别可扩展 | 类别变就要重训 | 任何新类别只要写一句话就行 |
| 数据要求 | 干净人工标注 | 网上爬的弱配对就够 |
| 工程难度 | 中 | 高 (大 batch + 分布式) |

## 对比学习的家族

CLIP 不是第一个对比学习的方法, 但它把这思路推到了语言-视觉对齐的极致。其他重要变种:

- **SimCLR / MoCo (2020)** · 在<strong>同一张图</strong>上做不同的数据增强, 增强后的两版本互相做正样本 —— **自监督**视觉表示学习, 不需要 caption
- **CLIP (2021)** · 跨模态对比, 4 亿图文对
- **DINOv2 (2023)** · 纯视觉自监督 + 多种对比损失, 训出强大的图像表示
- **SigLIP (2023)** · 用 sigmoid loss 代替 softmax-style, 对 batch size 不敏感

## 链接
- [[clip]] · 对比学习在跨模态对齐上的最经典应用
- [[zero-shot-image-classification]] · 对比学习训出来的 joint space 直接拿来做 zero-shot
- [[dual-tower-architecture]] · 对比学习常用的双塔结构
- [[bitter-lesson]] · 弱监督 + 大数据 > 精标注 + 小数据
