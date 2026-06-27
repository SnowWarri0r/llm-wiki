---
name: qwen3-vl
type: concept
sources: [ideogram-4, qwen-image-2, cosmos-3, qwen-image-bench]
updated: 2026-06-15
---

# Qwen3-VL · 当文本编码器用的视觉语言模型

> 本页只讲"**把它当文生图文本编码器**"这一面；这个 VLM **本身怎么看图**（三件套 / DeepStack / Interleaved-MRoPE / 训练 / 能力）见 paper 页 [[qwen3-vl-report]]。

## 一句话
阿里 Qwen 团队的多模态大模型（图+文+视频）。[[ideogram-4]] 把它**当文本编码器**用——不是因为要看图，而是因为一个见过图文世界的大脑，比纯文本编码器更"懂"prompt 在说什么画面。

## 直觉 · 翻译官的水平决定画师的上限

T2I 模型是个"画师"，但它不直接读你的字。中间有个"翻译官"——**文本编码器**——把 prompt 翻成画师能用的向量。翻译官水平有多高，画师就能多听懂你。

老一代翻译官（CLIP text encoder、T5）有局限：
- **CLIP**：只学过"图配一句短描述"的对齐，句子一长、关系一复杂就跟不上。
- **T5**：纯文本编码器，语言懂得多，但**从没见过画面**，对"红色在蓝色左边"这种空间关系没有视觉常识。

Ideogram 4 的赌注：**换一个本身就是视觉语言模型（VLM）的大脑当翻译官**。Qwen3-VL 训练时同时吃过海量图和文，它对"画面里东西怎么摆、什么颜色、文字长什么样"有内化的理解。哪怕推理时**只喂文字**（text-only 模式），这份"见过世界"的底子也让它把 prompt 理解得更接近画面。

## 它本身是什么 · 一个 VLM 的三件套

Qwen3-VL 完整体是能看图的多模态模型，结构是经典 VLM 三件套：

```
图像 ──▶ [ViT 视觉编码器 SigLIP-2] ──▶ [MLP merger 投影]
                                              │
文字 ──────────────────────────────────────▶ [Qwen3 transformer 解码器] ──▶ 输出
```

- **视觉编码器**（SigLIP-2 ViT）：把图切 patch 编码。
- **MLP merger**：把视觉 patch 投影到语言模型的维度，让图像 token 和文字 token 进同一个序列。
- **Qwen3 解码器**：在文图混合序列上做 attention，这里用了 [[mrope]]（Interleaved-MRoPE）给图像 token 标 (t,h,w) 坐标、[[qk-rmsnorm]] 稳训练。

Ideogram 用的是它的语言侧（Qwen3-VL-8B-Instruct，text-only），视觉那一路在当编码器时不走。

## Ideogram 的用法 · 不取最后一层，取 13 个中间层

最值得记的细节：DiT 不是拿 Qwen3-VL **最后一层**的输出，而是**抽 13 个中间层的 hidden state 拼起来**喂给生成。

为什么？transformer 不同深度的层编码不同抽象度的信息：
- 浅层 → 偏词法、表面 token
- 中层 → 偏语义、实体关系
- 深层 → 偏任务特定的高度抽象

只取最后一层 = 只拿一个抽象度。**拼 13 层 = 把从词到语义到抽象的全光谱都喂给画师**，让生成能同时照顾"写了哪几个字"和"整体讲什么"。这是"把更深的语言理解灌进生成"的具体手段。

## 为什么这条路在 2025-26 成主流

T2I 圈这两年的共识转向：**文本编码器的语言理解力，是 prompt following 的瓶颈**。于是大家从 CLIP/T5 往"拿大 LLM / VLM 当编码器"走。Ideogram 4 用 Qwen3-VL 是这条线的一个样本——9.3B 的画师配一个真正懂语言和画面的翻译官，把"听话程度"顶到开源第一。呼应 [[structured-caption-conditioning]]：翻译官越强，越能消化结构化的复杂 prompt。

## 代码出处
- Qwen3-VL 技术报告：arXiv 2511.21631（2025-11）
- 仓库：github.com/QwenLM/Qwen3-VL，权重在 HuggingFace `Qwen/Qwen3-VL-*`
- 在 Ideogram 4 里作为 text-only 文本编码器，取 13 个中间层 hidden state

## 链接
- [[ideogram-4]] · 把 Qwen3-VL 当文本编码器的 9.3B 单流 DiT
- [[mrope]] · Qwen3-VL 的 Interleaved-MRoPE 位置编码
- [[qk-rmsnorm]] · Qwen3-VL attention 里的稳训手段
- [[structured-caption-conditioning]] · 强编码器才吃得动结构化 caption
- [[transformer-architecture]] · VLM 的解码器主干
- [[lumine]] · 把 VLM(Qwen2-VL)当游戏 agent 的大脑，看图出键鼠
