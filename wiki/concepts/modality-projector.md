---
name: modality-projector
type: concept
sources: [minimind-o, qwen3-asr]
updated: 2026-06-14
---

# Modality Projector · 把别的模态翻译进 LLM 的隐空间

## 一句话
一个小 MLP，把**冻结的外部编码器**吐出的语音/图像特征，投影成 LLM 听得懂的 hidden 向量，塞进序列里的占位符位置 —— 让一个纯文本 LLM 不改主干就能"看图听音"。

## 直觉 · 给 LLM 配翻译官，别重训它

要让 minimind-o 的语言主干处理图像和语音，最省的办法不是从头训一个多模态大模型，而是：
1. **借现成的、冻结的编码器**抽特征（图用 SigLIP2、语音用 SenseVoice）——这些模型已经很会"看"和"听"，没必要重训。
2. **训一个小 projector**，把它们的输出**翻译成 LLM 隐空间的向量**。
3. LLM 主干基本不动，只在序列里给图像/语音留**占位符 token**，projector 的输出填进去。

类比：LLM 是个只懂中文的专家，SigLIP2/SenseVoice 是懂"图像语""语音语"的人。你不用让专家重新学外语，只要配个**翻译官（projector）**把外语转成中文递进去。翻译官很小、很好训。

## 怎么做的 · 两层 MLP + 占位符注入

minimind-o 的两个 projector 都是**两层 MLP**，只改维度、对齐分布：

```
图像 ─[SigLIP2, 冻结]─▶ 64 个 patch 特征(768) ─[Vision projector 768→768]─▶ 填进图像占位符
语音 ─[SenseVoice, 冻结]─▶ 语音特征(512)      ─[Audio projector 512→768]─▶ 填进语音占位符
文本 ───────────────────────────────────────────────────────────────────▶ 直接进主干
```

最后三种模态的 token **落到同一条序列**里，一起做 self-attention（这就是 early fusion 的思路，见 [[early-fusion]]）。占位符位置原本是空槽，projector 把对应模态的向量灌进去。

训练时编码器**始终冻结**，只更新 projector（和按阶段更新主干）。所以视觉对齐阶段可以只开 `vision_proj` 模式——只训视觉 projector，避免图像数据把已经学好的语言/语音能力冲掉。

## 为什么 projector 能这么小还管用

因为重活都被冻结编码器干完了：SigLIP2 已经把图压成富语义的 patch 特征，projector 只需做"**换坐标系**"——把一个语义空间线性地搬到 LLM 的语义空间。minimind-o 里 vision projector 才 1.18M、audio projector 0.99M，相比冻结的 SigLIP2(94M)/SenseVoice(234M) 几乎不占参数。这是"小投影层撬动大冻结编码器"的典型省法。

## 代码出处
- minimind-o `MMVisionProjector`(768→768) / `MMAudioProjector`(512→768)
- 谱系：LLaVA 的 vision projector、minimind-v 的视觉注入，都是同一招

## 链接
- [[early-fusion]] · 多模态 token 落同一条序列一起 attention
- [[thinker-talker]] · projector 注入的是 Thinker 侧
- [[patch-embedding]] · 视觉编码器把图切 patch 的前一步
- [[cross-attention]] · 另一种融合多模态的方式（这里用的是 early fusion + projector）
- [[minimind-o]] · 用两个 projector 接图/音
- [[qwen3-asr]] · 音频 projector 接 AuT 耳朵到 Qwen3 LLM（生产级）
