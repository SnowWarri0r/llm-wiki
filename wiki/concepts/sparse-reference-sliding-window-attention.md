---
name: sparse-reference-sliding-window-attention
type: concept
sources: [unlimited-ocr-2]
updated: 2026-10-27
---

# SR-SWA · 稀疏参考滑窗注意力 · 只看正在抄的那页，再按预算瞟几眼

## 一句话

在 R-SWA 的"全部参考 + 最近 n 个输出"之上，把"全部参考"换成"当前页候选块 → top-k 块"的两级筛选，每个 query 的可见集大小与页数无关。

## 直觉

一代 [[reference-sliding-window-attention]] 把人抄书的"刚写的几个字"做成了滑窗，但"源书"那一半仍是整本摊开：抄到第 150 页，模型每写一个字还要把 150 页的视觉 token 全扫一遍。人不是这样——眼睛盯着当前页，碰到跨页的表格、续行才瞟一眼前一页。多页文档的视觉依赖是**页间稀疏、页内集中**的。

SR-SWA 把这个习惯做成两道闸：
- **Page Gate**：先按"你在抄哪一页"把候选缩到那一页涉及的块（块和页边界不对齐，跨页块也进候选）。
- **Token Sieve**：候选里再按预算挑 top-k 个块，挑法是可学习的路由（见 [[routing-bias-sparse-router]]）。

它替代的是 R-SWA 里"视觉段永远全可见"那一条。线性注意力也能把视觉成本压成常数，但会把图像特征揉成紧凑状态，认字和跨页检索的细节保不住——SR-SWA 仍是直接读原 token，只是读得少。

## 怎么做的

```
输入 X_t = Concat(V_1..V_N, y_<t)      # N 页视觉 token + 已生成文本
切固定块 {B_b}；每个 query q 固定局部窗 L(q)（最近的输出 token）

Page Gate：
  C_page(q) = { b : B_b ∩ V_g(q) ≠ ∅ }    # 只留与 query 所在页有交集的块
  位置 p_{i,j} = [p_page_i, p_intra_{i,j}]  # 页坐标 0/1 交替（有界），页内坐标单调

Token Sieve：
  每块摘要键 k̄_b；s_b = q̃ᵀ k̄_b / √d
  π = α-entmax({s_b}_{b∈C_page})；S(q) = TopK(π, k)
  β_b = log π_b − mean_{b'∈S} log π_b'      # 去均值 log 先验，只对选中块

保留集 R(q) = L(q) ∪ ⋃_{b∈S(q)} B_b          # 大小 = |L| + k·块长，与 N 无关
注意力 α_j = softmax_{j∈R(q)}( qᵀk_j/√d + 1[b(j)∈S(q)]·β_{b(j)} )
```

局部窗里的 token 用普通 logit；选中远程块里的 token 额外加上该块的路由偏置。

## 数字例子

**可见集有多大**。200 页、每页 256 个视觉 token（DeepEncoder 16× 压缩后）：
- R-SWA：每个 query 看 200×256 + 128 = **51,328** 个 token，页数翻倍它翻倍。
- SR-SWA：按仓库给的例子"512 个工作参考 token"+ 128 滑窗 = **640**，200 页还是 640，2,000 页还是 640。两者相差 80×；论文实测百页级每步延迟 7.0×（对全注意力）、5.6×（对 R-SWA）——没到 80× 是因为每步还有 MoE 前馈等和注意力无关的成本。

**位置坐标怎么有界**。四页各 3 个 token：

| 页 | 页坐标 p_page | 页内坐标 p_intra |
|---|---|---|
| 1 | 0 | 1,2,3 |
| 2 | 1 | 1,2,3 |
| 3 | 0 | 1,2,3 |
| 4 | 1 | 1,2,3 |

页坐标永远只有 0/1，第 300 页也不会出现模型没见过的大位置；代价是模型只知道"本页 / 相邻页"的奇偶，不知道"第 7 页离第 150 页多远"。

路由打分、entmax、偏置怎么算的完整手算在 [[routing-bias-sparse-router]]。

## 跟近亲的对照

| 做法 | 远程参考怎么定 | 可见集随长度 |
|---|---|---|
| 全注意力 | 全部 | 线性涨 |
| R-SWA（一代） | 视觉全部 + 文本滑窗 | 视觉段线性涨 |
| 线性 / 循环注意力 | 压成状态 | 常数，但细节糊 |
| CSA / MiniMax Sparse Attention | 硬 top-k，要辅助监督或 warmup | 常数 |
| SR-SWA | 页门缩候选 + entmax 路由 top-k，偏置进 logit 端到端训 | 常数 |

## 链接

- [[unlimited-ocr-2]] · 提出；MarathonDocBench 77.06 vs 第二名 33.74
- [[reference-sliding-window-attention]] · 被升级的一代
- [[routing-bias-sparse-router]] · Token Sieve 的路由与偏置
- [[unlimited-horizon-decoding]] · 配套的分块显存方案
- [[sparse-attention]] · 块稀疏家族
- [[kv-cache]] · 这次视觉段也钉成常数
