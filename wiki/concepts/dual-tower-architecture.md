---
name: dual-tower-architecture
type: concept
sources: [clip]
updated: 2026-05-28
---

# Dual-Tower Architecture · 双塔架构

## 一句话
两个独立的 encoder, 一个跑图、一个跑文本, **各跑各的最后把输出投影到同一个向量空间** —— 工程上两边可以独立放大缩小, 推理时一边可以预先算好缓存。

## 直觉 · 为什么不用一个大模型直接吃图+文本

最朴素的设计: 一个大 Transformer, 把图像 patch token 和文本 token 拼在一起喂进去, 让 attention 跨模态学。这种叫 **single-tower** (或 fusion-style)。

但 CLIP 选了反过来的设计 —— **dual-tower**, 两个独立 encoder, 各跑各的, 最后只算两个 embedding 的点积。

为什么? 三个工程原因:

1. **推理时可以预先算好一边**
   - 比如做"以图搜图": 库里 1 亿张图都预先 encode 成向量存起来, 用户给个 query 图只算一次 encoding 就行。Single-tower 每次都要把 query 图跟库里每张图一起跑一遍, 算力爆炸
2. **训练时两边可以独立放大缩小**
   - 图像端模型变大跟文本端模型变大互不影响, 工程上好优化
3. **训练目标更纯**
   - Dual-tower + 对比学习 = "两个 embedding 算点积" —— 训练信号特别干净。Single-tower 加上 cross-attention 后训练动态复杂得多

## 工程上怎么实现

```python
class CLIPModel(nn.Module):
    def __init__(self):
        self.image_encoder = VisionTransformer(...)   # 比如 ViT-B/32
        self.text_encoder = TextTransformer(...)       # 比如 12-layer BPE Transformer
        # 两边各自的最后一层投影到同一维度 (比如 512)
        self.image_projection = nn.Linear(image_hidden, 512)
        self.text_projection = nn.Linear(text_hidden, 512)
        self.temperature = nn.Parameter(torch.ones([]) * np.log(1/0.07))

    def encode_image(self, image):
        x = self.image_encoder(image)              # (B, image_hidden)
        x = self.image_projection(x)               # (B, 512)
        return x / x.norm(dim=-1, keepdim=True)    # 单位向量

    def encode_text(self, text):
        x = self.text_encoder(text)                # (B, text_hidden)
        x = self.text_projection(x)                # (B, 512)
        return x / x.norm(dim=-1, keepdim=True)

    def forward(self, image, text):
        img_emb = self.encode_image(image)
        txt_emb = self.encode_text(text)
        sim = img_emb @ txt_emb.T * self.temperature.exp()
        return sim   # 训练时跟对角线 label 做 cross entropy
```

**关键设计**:

- 两边的 encoder 内部完全独立 —— 图像 encoder 不知道文本 encoder 的存在, 反之亦然
- **唯一的交互发生在最后** —— 两边各自投影到同一维度, 然后算点积
- 投影后做 L2 normalize, 让点积 = cosine similarity (取值 [-1, 1])
- 温度参数 `temperature` 是个可学的标量, 控制 softmax 的尖锐度

## 跟 single-tower / fusion 模型对比

| 维度 | Dual-Tower (CLIP) | Single-Tower (Flamingo / LLaVA / GPT-4V) |
|---|---|---|
| 架构 | 两个独立 encoder + 末端对齐 | 一个 Transformer 同时处理图+文本 |
| 跨模态交互时机 | 末端 (late fusion) | 早期或全程 (early/mid fusion) |
| 推理效率 | 高 (一边可缓存) | 低 (每次重算) |
| 表达力 | 中 (只能算"配/不配") | 高 (能生成、能问答、能推理) |
| 训练 | 对比学习, batch 越大越好 | next-token prediction, 跟 LLM 训练一致 |
| 代表 | CLIP / SigLIP / ALIGN / Open-vocabulary segmentation | LLaVA / GPT-4V / Flamingo / DALL-E (跟 CLIP 配合) |

简单说: **检索 / 对齐 / 表征用 dual-tower; 生成 / 推理 / 对话用 single-tower (或 dual-tower 当前端 + LLM)**.

## 现在最常见的混合用法

实际系统里 CLIP 经常**当 single-tower 模型的视觉前端**:

```
图像 → CLIP image encoder (dual-tower 的一半) → 图像 token 序列
                                                  ↓
文本 → tokenizer → 文本 token 序列            和图像 token 拼起来
                                                  ↓
                                          喂给一个 LLM (single-tower) → 输出
```

LLaVA / GPT-4V / Qwen-VL 都是这种结构。**Dual-tower 用来表征图像 (低成本、可缓存), single-tower LLM 用来推理 (高表达力)** —— 两套架构各取所长。

## 双塔的更广义形态

Dual-tower 不只用在图文。任何"两端语义对齐"的场景都可以用:

| 场景 | Tower 1 | Tower 2 |
|---|---|---|
| 图文匹配 (CLIP) | 图像 encoder | 文本 encoder |
| 句子语义相似度 (SBERT) | 文本 encoder | 文本 encoder (孪生) |
| 多语言对齐 (LASER) | 英文 encoder | 法/中/日 encoder |
| 推荐系统 | user encoder | item encoder |
| 代码搜索 (CodeBERT) | code encoder | natural language encoder |

**Dual-tower 是"高效检索 / 向量化对齐" 这一类问题的通用解**。

## 链接
- [[clip]] · 双塔在多模态的标杆
- [[contrastive-learning]] · 双塔最常用的训练目标
- [[zero-shot-image-classification]] · 双塔出来的 joint space 直接拿来用
