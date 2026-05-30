---
name: zero-shot-image-classification
type: concept
sources: [clip]
updated: 2026-05-28
---

# Zero-Shot Image Classification · 不训练新模型就能分新类

## 一句话
不再问"这是 1000 类里的哪一类", 而是问"我列的这几句话, 哪句话最配这张图" —— **分类变成了图文匹配**, 想分什么类直接写句话就行。

## 直觉 · 从"猜类别"到"配文字"

传统图像分类的工作流:

```
任务: 分 "猫 / 狗 / 飞机"
↓
做法: 标几千张图 (每张标对应 label) → train CNN → softmax 1000-way classifier
↓
想加一类 "兔子"? → 重新标兔子的图 → 重新训
```

CLIP 这条路:

```
任务: 分 "猫 / 狗 / 飞机"
↓
做法: 把 "a photo of a cat" / "a photo of a dog" / "a photo of a airplane" 喂给文本 encoder
     → 得到 3 个文本向量
     → 把图也喂给图像 encoder → 得到 1 个图像向量
     → 算 3 个相似度, 最大的那个就是答案
↓
想加一类 "兔子"? → 把 "a photo of a rabbit" 喂进去算一个向量就行
```

**核心区别**: CLIP 把"分类"问题转化成了"图文匹配"问题。所有类别都用自然语言描述, 而 CLIP 已经在 4 亿图文对上学会了"图跟文本怎么对齐" —— 拿来直接用就行, 不需要任何新训练。

## Prompt engineering 也来到视觉

既然类别用自然语言描述, 那**怎么描述也会影响效果**。这跟 NLP 的 prompt engineering 一模一样。

CLIP 论文里的实验:

| Prompt 模板 | ImageNet 准确率 |
|---|---|
| `{class}` (光是类名) | 64.2% |
| `a photo of a {class}` | 66.7% |
| `a photo of a {class}, a type of pet.` (加上下文) | 68.3% |
| **80 个模板做 ensemble** | **70.7%** |

为啥 "a photo of a dog" 比单写 "dog" 好? **因为网上的 caption 大多是完整句子**, 不是孤立的词。CLIP 训出来的文本 encoder 对完整句子更熟。

这是个有点哭笑不得的发现 —— **视觉模型的效果, 现在要靠文本提示词的写法**。

## 优势 vs 局限

**优势**:

1. **任意新类别零成本**: 想分什么类写句话就行, 不需要标数据
2. **细粒度更灵活**: 想区分"棕色金毛" vs "金色金毛"? 只要 CLIP 训练时见过相关 caption, 就能区分
3. **多语言**: CLIP 的文本 encoder 是多语言的 (虽然主要英文, 但有 LAION 的多语言版本)
4. **可解释**: 你看到的"分类决策"就是 5 个文本向量跟图算相似度, 一目了然

**局限**:

1. **细粒度分类弱**: 区分 "金毛" vs "拉布拉多" vs "古牧" 这种品种级别, CLIP 不如专门标注训练的分类器
2. **计数 / 空间关系弱**: "图里有几只猫" 经常错; "猫在桌子上还是桌子下" 也分不清
3. **训练分布偏见**: "a photo of a CEO" 给出的图像大多是白人男性 —— CLIP 反映训练数据偏见
4. **OCR 弱**: 图里的文字 CLIP 看得到一部分但不准
5. **绝对值 vs 相对值**: CLIP 输出的是相似度的相对排序, 不是真正的概率 —— "70% 是猫" 这个 70% 没有标定意义

## 工程上怎么用

```python
import clip
import torch
from PIL import Image

model, preprocess = clip.load("ViT-B/32")
image = preprocess(Image.open("dog.jpg")).unsqueeze(0)

# 1. 准备候选 label 文本
class_names = ["cat", "dog", "airplane", "car", "tree"]
text_prompts = [f"a photo of a {c}" for c in class_names]
text_tokens = clip.tokenize(text_prompts)

# 2. 跑双 encoder
with torch.no_grad():
    image_features = model.encode_image(image)        # (1, 512)
    text_features = model.encode_image(text_tokens)   # (5, 512)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    # 3. 算相似度
    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

# 4. 取最大
best = similarity.argmax()
print(f"This is a {class_names[best]}")
```

四步: tokenize 类名 → encode 图 + 文本 → 算相似度 → argmax。整个 inference 不用任何 fine-tune。

## 实际工程里它最常被用作哪种功能?

**Zero-shot 分类只是 CLIP 最简单的用法**。真实工程里它更多用于:

- **以图搜图 / 图文搜索**: encode 一次, 库里所有图存 embedding, 来个 query 算相似度
- **生成模型的 conditioning**: Stable Diffusion 用 CLIP 文本 encoder 把 prompt 转成 conditioning 向量
- **多模态 LLM 的视觉前端**: LLaVA / GPT-4V 用 CLIP 图像 encoder 把图转成 visual token 喂给 LLM
- **数据筛选**: 给定一组图, 用 CLIP 算"哪些跟某个文本最相关" —— LAION 等大数据集就是这么过滤出来的
- **开放词汇检测 / 分割**: 把 detector / segmentation 头跟 CLIP 文本端对齐, 实现"找出图中所有'红色花瓶'"这种 free-form 查询

## 链接
- [[clip]] · zero-shot 分类的源头
- [[contrastive-learning]] · 训出来的 joint space 是 zero-shot 的基础
- [[dual-tower-architecture]] · 图文两个 encoder 投影到同一空间
- [[in-context-learning]] · NLP 端类似的"不训新模型也能干新任务"思路
