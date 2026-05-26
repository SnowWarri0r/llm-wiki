---
name: relative-position-encoding
type: concept
sources: [rope]
updated: 2026-05-25
---

# Relative Position Encoding · 相对位置编码

## 一句话
不告诉模型"你在第 5 个位置"，而是告诉模型"你跟那个词差 3 个位置" —— **相对距离比绝对地址有用得多**。

## 直觉
你写代码时引用变量，用的是"当前作用域往上第 2 层"这种相对引用，还是"内存地址 0x7F3A"这种绝对地址？

自然语言也一样。"the dog that bit me" 里 "bit" 跟 "dog" 的关系不取决于它们在句子里的绝对位置（第 2 个和第 5 个），取决于它们**之间差几个词**。把整个句子往后平移 10 个位置，语义一点不变。

绝对位置编码（sinusoidal PE / learned PE）让模型自己从两个绝对地址里做减法推出相对距离。**能学会，但费力且不直接**。

相对位置编码直接把距离喂给 attention score。

## 几种主要做法

| 方法 | 原理 | 代表 |
|---|---|---|
| **T5 relative bias** | 在 attention score 上加一个可学习的距离偏置矩阵 | T5 / mT5 |
| **ALiBi** | 在 attention score 上减去 `slope × distance`（线性惩罚远距离） | BLOOM |
| **RoPE** | 旋转 Q/K，点积天然包含相对距离 | LLaMA / Mistral / Qwen / GPT-NeoX |
| **Transformer-XL 式** | 修改 attention 公式加 relative key/value | Transformer-XL / XLNet |

RoPE 是目前（2024-2025）最主流的方案 —— 零参数、不改 attention 公式、跟 KV cache / Flash Attention 完美兼容。

## 为什么相对位置好

1. **平移不变**：句子整体往后移 N 个位置，所有相对距离不变 → attention pattern 不变
2. **天然支持变长**：不依赖固定的 max_position_id
3. **更容易外推**：训练时见过"差 3 个位置"的注意力模式，推理时"差 3 个位置"不管在序列哪个绝对位置都一样好用

## 链接
- [[rotary-position-embedding]] · 当前主流的相对位置方案
- [[positional-encoding]] · PE 家族全景（含绝对方案）
- [[self-attention]] · attention 为什么需要位置
