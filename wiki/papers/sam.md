---
name: sam
type: paper
source: https://arxiv.org/abs/2304.02643
upstream: https://segment-anything.com
ingested: 2026-06-23
authors: Kirillov, Mintun, Ravi, Mao, ... Dollár, Girshick (Meta AI / FAIR) · ICCV 2023
year: 2023
---

# Segment Anything · 给"分割"造一个可提示的基础模型

Meta AI 2023 的里程碑。它把 NLP 那套"基础模型 + 提示（prompt）+ 零样本迁移"搬到图像分割：训一个**可提示**的分割模型，给它一个点/框/文字，就能把对应的东西抠出来，还能零样本迁移到没见过的图和任务。它的图像编码器（SAM-ViT）后来被 DeepSeek-OCR 的 DeepEncoder 借去当前半段，是 [[unlimited-ocr]] / [[optical-context-compression]] 那条 OCR 压缩线的上游。

## 一句话
**把分割重新定义成"给任意提示返回一个合理掩码"的可提示任务，配一个能自我滚雪球的数据引擎造出 11 亿掩码，于是一个模型零样本分割万物。**

## 它要解决的痛点
- **分割模型都是"专才"**：传统分割模型一个数据集训一个、换个领域就得重训重标。NLP 早就靠基础模型 + prompt 做到一个模型通吃，视觉分割却还没有。
- **分割数据太贵**：像素级标注比打标签贵几个数量级，没有"互联网规模"的分割数据，就训不出基础模型。这是先有鸡还是先有蛋——SAM 用[[sam-data-engine]]破局。
- **一个点指代不清**：你点在一个人的衬衫上，到底想要衬衫、这个人、还是这群人？以前的模型只能给一个答案。SAM 把**歧义**正面当成设计目标。

## 核心贡献
1. **可提示分割任务**：[[promptable-segmentation]] —— 给任意 prompt（点/框/掩码/文字）返回**至少一个合理**的掩码，哪怕 prompt 有歧义。这个任务定义是一切的地基，让模型能像 LLM 那样被"组合"进下游任务。
2. **三件套架构 + 重/轻拆分**：重型图像编码器（[[vit]] ViT-H，MAE 预训练，~6.3 亿参数）每张图**只跑一次**出 embedding；提示编码器 + 轻量掩码解码器（2 层）每换一个 prompt 只重跑这截，**~50ms** 在浏览器里就能交互。
3. **数据引擎**：[[sam-data-engine]] —— 模型帮标注、标注再训模型的飞轮，三阶段滚出 **SA-1B：11M 图 / 1.1B 掩码**（99.1% 全自动）。
4. **零样本迁移**：[[zero-shot-transfer]] —— 不微调，靠 prompt 组合就能干边缘检测、物体提议、实例分割、文字→掩码等没专门训过的任务。

## 关键概念
- [[promptable-segmentation]] · 核心任务定义 + 歧义输出 3 个掩码 + IoU 排序
- [[sam-data-engine]] · 模型在环的标注飞轮，造出 SA-1B
- [[zero-shot-transfer]] · 一个模型靠 prompt 组合迁移到多任务（同 CLIP 的精神）
- [[vit]] · 图像编码器是 MAE 预训练的 ViT-H
- [[clip]] · 文字 prompt 那截借 CLIP 文本编码器；零样本迁移的思路也承自 CLIP
- [[optical-context-compression]] · SAM-ViT 被 DeepEncoder 借去当前半段（窗口注意力看清细节）

## 我的批注
- 最值得记的设计：**重编码器跑一次、轻解码器随便重跑**。这不是性能优化，是产品形态——正因为换 prompt 只要 50ms，标注员才能实时交互，数据引擎的飞轮才转得起来。架构和数据互为因果。
- 把"歧义"当成 feature 而不是 bug：一个点输出 3 个掩码（整体/部分/子部分）+ IoU 分挑最好。承认"一个 prompt 本来就可能指多个东西"，比硬猜一个更聪明。
- SA-1B 的 99.1% 是全自动标的——但前提是前两阶段用人把模型喂到足够好。**飞轮的头几圈靠人推，后面才自转**。这跟 [[unlimited-ocr]] 用 PaddleOCR 自动标注、[[whisper]] 用弱监督是同一个母题：大规模数据靠模型自己造。
- SAM 抠的是"哪一块"（mask），不认识"这是什么"（无语义标签）。它是个纯粹的**分割**基础模型，语义要靠下游接别的模型（比如接 CLIP 做文字→掩码）。这点常被误解。

## 跟 wiki 里其他 paper 的关系
- [[clip]] · 一对姊妹：CLIP 把"图文对齐 + 零样本分类"做成基础模型，SAM 把"可提示分割 + 零样本迁移"做成基础模型
- [[vit]] · 直接拿 ViT 当骨架；SAM 是 ViT 在分割上的旗舰落地
- [[unlimited-ocr]] / [[optical-context-compression]] · SAM 的图像编码器被 DeepEncoder 复用，是这条 OCR 线的上游

## 历史定位
- 2021 **CLIP** · 图文对比 → 零样本分类基础模型，证明"prompt + 零样本"在视觉可行
- 2022 **MAE** · 掩码自编码预训练 ViT，给 SAM 提供了现成的图像编码器底子
- 2023-04 **SAM（本篇）** · 把基础模型范式带进分割：可提示任务 + 数据引擎 + SA-1B
- 2024+ **SAM 2 / 各种 SAM-Adapter** · 扩到视频、医疗等领域；图像编码器被大量下游（含 OCR）借用
