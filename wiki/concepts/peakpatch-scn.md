---
name: peakpatch-scn
type: concept
sources: [peakpatch]
updated: 2026-08-17
---

# SCN · 在余弦相似度上再做一次受限微调

## 一句话
当几个候选分数几乎打平时，再给每个图文对加减不超过 0.2 分。

## 直觉
ECN 改的是通用地址，适合检索和生成；选择题只关心几个候选谁排第一。SCN 像最后一位裁判：同时看中层组合信号、ECN 后的向量和图片，只在接近打平时做小幅重排。

## 怎么做的

SCN 拼接三类输入：峰值层与图片的相似度、ECN 向量与图片的相似度；峰值层和 ECN 向量的差异摘要；图片与 ECN 向量逐元素相乘后的跨模态摘要。MLP 输出经过 tanh，再乘上限 \(\alpha_{\max}=0.2\)：

\[
\Delta s=\alpha_{\max}\tanh(\mathrm{MLP}_{\mathrm{SCN}}(\cdot)),\qquad
\hat s=\cos(f_I,\hat f_T)+\Delta s.
\]

## 数字例子

若 ECN 后余弦分数是 0.631，SCN 的 MLP 对一个否定冲突样本输出 -0.75：

\[
\Delta s=0.2\tanh(-0.75)\approx0.2\times(-0.635)=-0.127,
\]

最终 \(\hat s=0.631-0.127=0.504\)。tanh 保证无论 MLP 输出多大，修正都不会越过 \([-0.2,0.2]\)。

## 跟 ECN 的对照

ECN-only 把 COCO 检索 R@5 从 47.9 提到 58.2，SCN-only 只有 48.1；但 MCQ 平均分分别是 51.2 和 71.6。SCN 擅长重排，不会产出可供下游复用的新文本 embedding。

## 链接

- [[peakpatch]] · 联合训练时，SCN 的梯度还会回到 ECN。
- [[contrastive-learning]] · SCN 修的是 CLIP 对比学习空间里原本的余弦分数。
