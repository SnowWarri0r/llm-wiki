---
name: lora
type: concept
sources: [omnieraser]
updated: 2026-06-17
---

# LoRA · 低秩适配 · 不动底模，只训一个小增量

## 一句话
微调时**冻结底模权重不动**,只在旁边训一个**低秩的小增量矩阵** `ΔW = B·A`(秩 r 很小);推理时用 `W + BA`。几十 MB 就给大模型加一个专门技能,可插拔、一个底模能挂很多个。

## 直觉 · 别重训整本书，夹张便利贴

全参数微调一个大模型:要更新**所有**权重,显存吃不消、每个任务存一整份几个 GB 的权重,贵。

LoRA(Hu et al. 2021)的观察:**微调带来的权重改变量 `ΔW` 其实是低秩的**([[matrix-rank]]:改动只活在少数几个独立方向上)——可以用两个**瘦长的小矩阵相乘**近似出来。于是:
- 底模权重 `W` **冻结不动**;
- 旁边学一个 `ΔW = B·A`,其中 `A` 是 `r×k`、`B` 是 `d×r`,**秩 `r` 很小**(常 8/16/32);
- 前向变成 `y = Wx + B(Ax)`,只训 `A`、`B`。

类比:不重印整本教科书,只在页边**夹一叠便利贴**写批注。底书不变,便利贴几十 KB,想换主题换一叠便利贴就行。

## 怎么做的 · 低秩 = 省在哪
```
原始:   y = W x                 # W 是 d×k，冻结
LoRA:   y = W x + B (A x)        # A:r×k  B:d×r   只训 A,B（秩 r 小）
        ΔW = B·A                 # 用时可合并进 W，零额外推理开销
```
举个数:`W` 是 4096×4096 ≈ **1678 万**参数。取 `r=16`,则 `A`+`B` 只有 `4096×16×2` ≈ **13 万**参数 —— **省约 128×**。所以一个 LoRA 常只有几十 MB,而底模是几个 GB。

好处:
- **省显存/省存储**:只训&存那点小矩阵。
- **可插拔**:一个底模挂多个 LoRA(画风A/画风B/某技能),按需加载、甚至加权混合。
- **不伤底模**:底模权重没动,卸掉 LoRA 就回到原样。

## 跟全量微调的关系
LoRA 属于 **PEFT(参数高效微调)**家族,是 [[pretrain-finetune-paradigm]] 里"finetune"那步的省钱版:不动预训练底座,只学一个小适配器。文生图圈尤其常见——SD/[[flux-1]]/[[qwen-image-2]] 上一堆社区 LoRA(画风、人物、某种特效)。

## 代码出处 / 来源
- LoRA:Hu et al. 2021《LoRA: Low-Rank Adaptation of Large Language Models》
- 生态:diffusers / PEFT;ModelScope、Civitai 上海量文生图 LoRA

## 链接
- [[matrix-rank]] · "low-rank" 的秩到底在模型里起什么作用
- [[pretrain-finetune-paradigm]] · LoRA 是 finetune 那步的参数高效版
- [[gaussian-splatting]] · 那个"高斯泼溅"就是挂在 [[qwen-image-2]] 上的一个 LoRA
- [[qwen-image-2]] · [[flux-1]] · 文生图底模,社区常挂 LoRA 加技能
