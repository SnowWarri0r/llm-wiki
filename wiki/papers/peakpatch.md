---
name: peakpatch
type: paper
source: raw/papers/peakpatch/peakpatch.pdf
upstream: https://arxiv.org/abs/2607.23271
ingested: 2026-08-17
authors: Chen-Yi Lu, Yueh-Shao Chen, Somali Chaterji · Purdue University · arXiv 2026
---

# PeakPatch · CLIP 中层懂“没有”，最后一层却把它忘了

CLIP 把“有一只狗”和“没有狗”压成几乎相同的文本向量。PeakPatch 没有把这件事简单归咎于数据不足，而是逐层检查文本编码器：中间层已经拉开肯定句与否定句，靠近输出时，这个差别又被图文对齐目标压回去了。作者把这个过程叫作表征坍缩，并在冻结 CLIP 的前提下，从信息最完整的中层抽回否定信号。

## 一句话
**CLIP 不是从没看懂否定，而是最终向量为了匹配物体，把中层已经形成的否定结构覆盖掉了。**

## 它要解决的痛点

- CLIP 的最终余弦相似度几乎只看见“dog”这个物体词，分不清“a dog”和“not a dog”；NegBench VOC 上肯定句 80.9%，否定句只有 3.0%。
- 整个编码器微调虽然能补否定，但会改动被大量下游系统依赖的预训练权重；只改最终分数又无法给检索或文生图提供可复用的新 embedding。
- 一个共享向量空间难以同时满足物体、属性绑定、空间关系与否定的全部几何约束。PeakPatch 因此分两层补：ECN 修 embedding，SCN 再修少数难分的成对分数。

## 核心贡献

1. **逐层诊断**：[[layerwise-compositional-divergence]] —— 同时画出肯定/否定分离度和图文对齐度，定位“先学会、后忘掉”的拐点。
2. **表征补丁**：[[peakpatch-ecn]] —— 从组合信息最强的中层读 token，预测一个小偏移量，加回最终文本向量。
3. **分数补丁**：[[peakpatch-scn]] —— 对图片与候选句子的余弦分数再加一个受限小偏移，专门处理 MCQ 的近似平局。
4. **语义边界**：[[set-valued-negation]] —— “不是狗”不是另一个具体物体，而是一个很大的补集；否定句不该被硬塞成新的物体类别。

## 关键概念

- [[contrastive-learning]] · CLIP 为什么会优先保留高频物体词，而不保留网页图文里少见的否定关系。
- [[cross-attention]] · ECN 用一个可学习 query 从中层整段 token 中找否定词和被否定对象。
- **余弦相似度** · CLIP 的标准接口；PeakPatch 保留这套接口，而不是换成专用分类器。
- **困难负样本** · 同一图片的否定改写最难区分，因此直接放进对比损失分母。

## 我的批注

- 最有价值的不是 74.3 这个榜分，而是诊断链：先证明信息在中层出现，再证明它在末层消失，最后让修复模块只读取那个拐点。
- 论文把“坍缩是 InfoNCE 的直接结果”说得偏强。逐层曲线和控制实验支持相关机制，但并没有通过更换训练目标的因果消融单独证明 InfoNCE 必然导致这条曲线。
- ECN 和 SCN 不是重复模块。ECN 产出能给检索、分类、生成继续用的 embedding；SCN 只能回答“这张图与这句话该加减几分”，所以 MCQ 很强、检索几乎不动。
- 论文主表没有把解析器方法放进同一张表。附录显示 SpaceVLM 和规则解析法在 VOC 上分别达到 81.1% 和 78.6%，明显高于 PeakPatch 的 65.5%；PeakPatch 赢在无需额外解析器、COCO 更强、部署更轻。
- “冻结主干”不等于无需访问主干内部。PeakPatch 必须拿到中间层 token，只有最终 embedding 的黑盒 CLIP API 无法使用。

## 跟 wiki 里其他 paper 的关系

- [[clip]] · PeakPatch 直接修补 CLIP 双塔最后向量对组合语义不敏感的问题。
- [[vit]] · 文本端同样是逐层 Transformer；方法依赖中间层 hidden state，而不只读最终输出。
- [[qwen3-vl-report]] · 现代 VLM 也大量复用冻结视觉语言编码器；上游表示里的组合缺陷会一路传给下游。

## 历史定位

- 2021 CLIP · 把图像和文本压到同一余弦空间，换来通用检索与零样本迁移。
- 2023–2025 NegCLIP / NegationCLIP / NegBench · 系统暴露否定盲区，并用数据微调或专用打分修补。
- 2025 几何不可能性与机制分析 · 说明单一 embedding 空间的组合约束，以及少量否定选择性 attention head 的存在。
- 2026-07 **PeakPatch** · 冻结 CLIP，从中层把即将消失的否定结构抽回，并同时修 embedding 与成对分数。
