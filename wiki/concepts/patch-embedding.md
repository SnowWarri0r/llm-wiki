---
name: patch-embedding
type: concept
sources: [vit, clip]
updated: 2026-05-28
---

# Patch Embedding · 图像切块成 token

## 一句话
把图片切成固定大小（如 16×16）的方块, 每块拉平成一个向量, 通过一个 linear 层投影到 hidden dim —— **图像就这样变成了一串 token**。

## 直觉 · 为什么不一个像素一个 token

最朴素的想法: 一张 224×224 的 RGB 图, 50176 个像素, 每个像素当一个 token, 喂给 Transformer。

不行, 三个理由:

1. **算不动**: self-attention 是 O(N²), N=50176 直接爆显存
2. **没意义**: 单个像素信息量极低, 单看一个 RGB 三元组完全不知道这是脸还是猫
3. **太长了**: 50176 个 token 序列, 模型学不到长程结构

中间方案: **把图切成 patch, 每个 patch 当 token**。

224×224 切成 16×16 的 patch → 14×14 = **196 个 token**。这个数量 Transformer 处理得动, 而且每个 patch 自带局部信息（一个 patch 已经能看出"这是耳朵还是眼睛"了）。

## 具体怎么做

```python
# 输入: (B, 3, 224, 224) 的图像 batch
# 切 patch + 拉平 + 投影 (用一个 Conv2d 一步搞定, 等价于切+拉平+linear)
patch_size = 16
hidden_dim = 768

# Conv2d 的 stride=patch_size, 等价于"不重叠切块"
patch_embed = Conv2d(
    in_channels=3,
    out_channels=hidden_dim,
    kernel_size=patch_size,
    stride=patch_size,
)

# 输出: (B, 768, 14, 14) → 拉平最后两维 → (B, 196, 768)
x = patch_embed(image)             # (B, 768, 14, 14)
x = x.flatten(2).transpose(1, 2)   # (B, 196, 768)

# 加 [CLS] token, 跟 BERT 一样
cls = nn.Parameter(torch.zeros(1, 1, 768))
x = torch.cat([cls.expand(B, -1, -1), x], dim=1)   # (B, 197, 768)

# 加位置编码（学习式, 不是 sin/cos）
pos_embed = nn.Parameter(torch.zeros(1, 197, 768))
x = x + pos_embed
```

到这一步, 一张图就变成了一个 (197, 768) 的"token 序列", 后面塞给标准的 Transformer encoder 就行。

**关键洞察**: 那个 `Conv2d` 不是真的在做卷积特征提取, 它就是 "切块 + 拉平 + 线性变换" 三步合一的工程实现。可以理解成 "**唯一的卷积层, 只用一次, 用完就再也不用了**"。

## 跟 NLP token embedding 的对应

| NLP (BERT/GPT) | ViT |
|---|---|
| 把字符串 tokenize → token id | 把图切成 patch |
| Embedding 矩阵 `(vocab_size, hidden)` 查表 | Linear 投影 `(patch_size² × 3, hidden)` |
| 加位置编码（学习式 or RoPE） | 加位置编码（学习式 1D 或 2D） |
| `[CLS]` token 用于分类 | `[CLS]` token 用于分类 |
| 输出: (B, seq_len, hidden) | 输出: (B, num_patches+1, hidden) |

**完全同构**。所以 ViT 实现上可以直接复用 BERT 的代码, 只换 embedding 这一层。

## Trade-off · patch size 怎么选

| Patch size | Token 数 (224×224) | 计算量 | 细节保留 |
|---|---|---|---|
| 32×32 | 49 | 极小 | 丢细节 |
| 16×16 | 196 | 中等（ViT 默认） | 平衡 |
| 14×14 | 256 | 略大 | 略好 |
| 8×8 | 784 | 很大 | 接近像素级 |

ViT 选 16×16 是工程妥协: 再小算不动, 再大丢细节。后来 Swin Transformer 用层次化窗口注意力, 才能做到 4×4 patch。

## 为什么这个抽象很重要

ViT 之前, 视觉跟语言是两个完全不同的世界 —— 一边是 CNN + 卷积, 一边是 Transformer + token。Patch embedding 把它们抹平了:

**"图像和文本都是 token 序列, 区别只是 token 怎么来的"**。

这一抽象立起来之后, 多模态（CLIP / DALL-E / Flamingo / LLaVA）就成了顺理成章的事 —— 图像 patch token 和文本 token 都进同一个 Transformer, 跨模态学习就是给两边的 token 做对齐。**ViT 真正的影响力在这里, 不在分类准确率本身**。

## 链接
- [[vit]] · 这个概念的源头
- [[inductive-bias]] · patch 切完后, 空间信息怎么靠 PE 恢复
- [[self-attention]] · patch 之间怎么交互
- [[positional-encoding]] · ViT 用学习式 2D PE
