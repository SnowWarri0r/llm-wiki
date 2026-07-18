---
name: classifier-free-guidance
type: concept
sources: [ideogram-4, flux-1, diffusionnft, viitorvoice, ltx-2]
updated: 2026-07-17
---

# Classifier-Free Guidance · CFG

## 一句话
让模型同一步算两遍 —— 一遍看着 prompt、一遍蒙着眼，再把"看着 prompt 多走的那部分"放大，逼它更听话。

## 直觉
扩散模型每一步要预测"往哪个方向去噪"。问题：光按 prompt 算一遍，模型对 prompt 的"听话程度"不够。CFG（Ho & Salimans 2022）的招很贼：

- **条件支**：带着 prompt 算一个方向 `v_cond`
- **无条件支**：不给 prompt 算一个方向 `v_uncond`
- **放大差值**：`v = v_uncond + w · (v_cond − v_uncond)`，`w` 是 guidance scale

`v_cond − v_uncond` 就是"因为有了 prompt 而多走的那部分"。把它乘 `w`（常 7 左右）放大，模型就更贴 prompt。代价是 `w` 太大画面会过饱和、失真。

**为什么叫"classifier-free"**：早期要靠一个单独的分类器算梯度来引导，CFG 把它去掉了，只用模型自己的条件/无条件两次前向。

## 非对称 CFG（Ideogram 4 的变体）
标准 CFG 的无条件支是"把文本换成 padding"。Ideogram 4 改成 **把文本 token 整个丢掉**，无条件支只在图像 token 上跑（单流架构天然能这么做）。好处：

- 两支可以**独立调**，把"prompt 听话程度"和"画质"分开 schedule
- 例：`V4_QUALITY_48` 跑 45 步 gw=7（强听话）+ 3 步 polish gw=3（收细节不过饱和）

## 怎么做的
```python
v_cond   = dit(z_t, t, text_tokens)     # 看着 prompt
v_uncond = dit(z_t, t, no_text)         # 非对称: 文本整个 drop
v = v_uncond + w * (v_cond - v_uncond)  # 放大差值
z_next = euler_step(z_t, v, t)          # flow matching 积分一步
```

## 链接
- [[ideogram-4]] · 非对称 CFG + polish tail
- [[ltx-2]] · 把文本 guidance 与跨模态 guidance 拆成两个 scale
- [[modality-aware-cfg]] · 音视频双条件版本的完整公式与手算
- [[flow-matching]] · CFG 作用在速度场上
- [[diffusion-transformer]] · 条件/无条件两支都跑 DiT
- [[guidance-distillation]] · 把这两遍前向蒸成一遍([[flux-1]] dev)
