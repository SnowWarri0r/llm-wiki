---
name: mixture-of-transformers
type: concept
sources: [cosmos-3]
updated: 2026-06-24
---

# Mixture-of-Transformers · MoT · 混合 transformer（双塔）

## 一句话
每个 transformer 层养两套完整权重（"塔"），不同模态/任务的 token 走不同塔，但所有 token 共用一次注意力对齐。

## 直觉
痛点：让一个 transformer 同时干"理解"（语言/推理，要**因果**注意力、像 LLM）和"生成"（高保真图像视频，要**双向**注意力、像扩散）——这两种工作模式对权重的要求很不一样，硬塞进同一套权重会互相打架、谁都学不好。

MoT 的解法干脆：**给每种工作模式配一套自己的完整 transformer 权重**（注意力投影、FFN、norm 全独立），叫一个"塔"。理解的 token 走 reasoner 塔，生成的 token 走 generator 塔。但关键是——它们**在同一次注意力里相遇**（联合注意力），所以生成塔能看到理解塔算出的文字 prompt、保持对齐。分权重避免打架，共注意力保证统一。

跟两个容易混的东西划清界限：
- **vs [[moe]]**：MoE 是在 FFN 那层养很多"专家"，每个 token 按内容路由到少数几个专家，**注意力是共享的**，目的是**省算力**（总参大、激活小）。MoT 是养**整条 transformer 通路**（连注意力投影都独立），按**模态/任务**路由，目的是**消解多模态冲突**。一个为效率，一个为统一。
- **vs [[unified-transformer]]**：unified-transformer 也用"文本走因果 + 生成走双向"的混合注意力，但**只有一套权重**。MoT 在它之上把权重**拆成两塔**——这是 MoT 的新增点。

## 怎么做的
```
一条 token 序列 = [ AR 子序列(语言+理解) | 扩散子序列(要生成的图/视频/动作) ]

每个 decoder 层:
  AR token      → reasoner 塔(独立权重)  · 因果自注意力(只看前面的 AR)
  扩散 token    → generator 塔(独立权重) · 双向注意力(看 [AR; 扩散] 全部)
  ↑ 两塔权重不同, 但在同一次 attention 里 AR 当 key/value 喂给扩散 token
AR 永不被扩散 token 更新(保住因果, 文本生成能力不坏)
```
两塔都从一个预训练 VLM（Cosmos 3 用 [[qwen3-vl]]）初始化，所以一上来就有语言+视觉底子，再学生成。

## 数字例子
Cosmos 3 的 Nano 档：稠密底座是 8B（一个完整 VLM 的参数量）。MoT 给 reasoner 和 generator **各**一套 ≈8B 的权重：

```
reasoner 塔  ≈ 8B   (理解/AR)
generator 塔 ≈ 8B   (生成/扩散)
─────────────────────────────
总参         ≈ 16B   = 2 × 稠密底座
```

✓ 自检：Super 档底座 32B → 总参 64B，正好也是 ×2，对得上"每层两套权重"。但**激活量≈单塔**——因为一个 token 只过它该走的那一塔（AR token 只过 reasoner，扩散 token 只过 generator），不是两塔都过。所以总参翻倍、单 token 计算量没翻倍。对比 MoE：MoE 是 100B 总参可能只激活 5B（省算力）；MoT 是 16B 总参激活≈8B（不为省算力，为分工）。

## 链接
- [[cosmos-3]] · 用 MoT 把理解+生成+动作统一的 paper
- [[moe]] · 对照：FFN 专家、按 token 路由、共享注意力、为省算力
- [[unified-transformer]] · 最近亲：混合注意力但单套权重；MoT 拆成双塔
- [[diffusion-transformer]] · generator 塔干的活
- [[qwen3-vl]] · 两塔的初始化来源
