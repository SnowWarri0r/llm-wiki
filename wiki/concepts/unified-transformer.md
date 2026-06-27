---
name: unified-transformer
type: concept
sources: [hidream-o1, cosmos-3]
updated: 2026-06-10
---

# Unified Transformer · 一个 transformer 同时当 LLM 和 DiT

## 一句话
把文本、条件图、要生成的像素**全塞进一条 token 序列**，用**混合注意力**——文本/条件 token 走 causal（像 LLM 读 prompt）、生成 token 走 full（像 DiT 双向去噪）——一个 transformer 同时干理解和生成，不要独立文本编码器。

## 直觉 · 别让"读 prompt"和"画图"分两个空间

传统 T2I 是拼起来的：一个**文本编码器**（T5/CLIP/或 VLM）把 prompt 编码，再喂给一个**单独的图像生成器**。两个模型、两套语义空间，对齐全靠中间那点接口，容易**语义错位**（编码器理解的和生成器吃到的不是一回事）。

Unified Transformer（HiDream-O1 的 UiT）的办法：**取消这个分界**。文本、条件图、生成像素都变成 token，**放进同一条序列、过同一套 attention**——理解和生成在一个空间里联合发生，语义天然对齐。它的 backbone 干脆**直接是一个 LLM**（HiDream 8B 从 [[qwen3-vl]]-8B-Instruct 初始化），文本走 LLM 自己的原生词表 embedding——所以"没有独立文本编码器"= **LLM 自己就是编码器**。

## 怎么做的 · 三类 token + 混合注意力 mask

```
一条序列： [ 文本 token y | 条件图 token c | 生成 token x_t ]
              causal          causal           full
            （只看左边）     （只看左边）    （双向, 每个 patch 看所有）
```

- **文本 token**：用 backbone（Qwen3）原生词表 embedding。
- **条件 token**（编辑/personalization 的输入图）：SigLIP-2 编码 → 一层投影对齐进共享空间。
- **生成 token**：噪声样本切 patch（见 [[pixel-space-diffusion]]）→ 投影进同一空间。
- **混合注意力**：文本/条件用 **causal mask**（自回归式，像 LLM 读输入）；生成 token 用 **full attention**（双向，像 [[diffusion-transformer]] 一起去噪）。

为什么这么分：文本和条件是"**给定的、要被理解**"的——causal 像顺着读 prompt（[[causal-language-model]]）；生成像素是"**要一起被去噪**"的——full 像 DiT 让每个 patch 互看。一条流里两种 mask，等于把 LLM 和 DiT 缝进同一个 transformer。

## 它买到什么
- **无语义错位**：文图在一个空间，不用跨两个模型对齐。
- **一套架构多任务**：T2I / 指令编辑 / 主体personalization / storyboard 都变成"在 context 里推理生成"，同一个模型吃下，不为每个任务单训。

## 跟单流 DiT 的区别
[[ideogram-4]] 也叫"单流"，但它的"单流"指文本+图像 token 共享投影，**文本编码器仍是外挂的 Qwen3-VL**。HiDream 更彻底：**连文本编码器都收进主干**，backbone 本身就是 LLM，且用混合 mask 区分理解/生成。

## 代码出处
- HiDream-O1-Image：arXiv 2605.11061（Unified Transformer，hybrid attention）

## 链接
- [[pixel-space-diffusion]] · 生成 token 怎么从原始像素来
- [[self-attention]] · 混合的是它的 mask（causal vs full）
- [[causal-language-model]] · 文本/条件那半的 causal 来历
- [[diffusion-transformer]] · 生成那半的 full attention 来历
- [[qwen3-vl]] · backbone 直接用它初始化
- [[ideogram-4]] · 也叫单流，但文本编码器仍外挂，对照
- [[hidream-o1]] · 用 UiT 的统一生成模型
