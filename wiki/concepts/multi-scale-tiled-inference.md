---
name: multi-scale-tiled-inference
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Multi-Scale, Multi-Tile Inference · 先定全局，再重叠分块精修

## 一句话

低分辨率一次看全局，高分辨率只看重叠小块，融合后再解码。

## 直觉

1080p 视频 latent 一次放进模型，峰值显存会随空间、时间 token 快速增长。直接把画面切块虽省显存，但每块不知道邻居画了什么，边缘容易出现接缝。

解决办法是先在低分辨率生成完整故事板，确保构图、运动和音视频时间关系一致；再放大 latent，并用重叠块只补局部高频细节。重叠区域像两块拼图多留一圈缓冲，最后做加权平均。

## 怎么做的

```text
约 0.5MP base latent
→ latent upscaler（增加空间分辨率）
→ 沿 x/y/time 切 overlapping tiles
→ 同一个 foundation model 分别 refine
→ overlap 内按窗函数加权融合
→ Video VAE decode 到 1080p
```

它主要降低峰值显存，不减少必须生成的总细节；重叠部分还会重复计算。

## 数字例子

一维玩具 latent 长 8，tile 长 5、overlap 2：

```text
tile A 覆盖位置 0..4，预测 overlap(3,4) = [10, 12]
tile B 覆盖位置 3..7，预测 overlap(3,4) = [14, 10]

若位置3权重 A/B=.75/.25：.75×10 + .25×14 = 11
若位置4权重 A/B=.25/.75：.25×12 + .75×10 = 10.5
```

输出从 A 平滑过渡到 B；硬切会在边界直接从 12 跳到 14 或 10。真实系统会同时沿空间和时间切块，blend window 也更平滑。

## 跟整图推理对比

| | 峰值显存 | 全局上下文 | 额外计算 |
|---|---:|---:|---:|
| 整图高分辨率 | 高 | 完整 | 无重叠重复 |
| 独立无重叠 tiles | 低 | 弱 | 较少但易接缝 |
| **低清全局 + 重叠精修** | 较低 | base 阶段保留 | overlap 重复计算 |

## 链接

- [[ltx-2]] · 1080p 推理策略
- [[video-vae]] · 切分和融合发生在 video latent 空间
