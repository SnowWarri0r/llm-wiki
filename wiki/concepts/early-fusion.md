---
name: early-fusion
type: concept
sources: [interaction-models-tml, physics-of-multimodal-pretraining]
updated: 2026-08-06
---

# Early Fusion · 早融合不只一种

## 一句话

**在模型还没把某一种模态的处理方式练死之前，就让多种模态进入同一个主干并共同更新。**它强调“什么时候开始一起学”；至于前面有没有视觉编码器，是另一条设计轴。

## 先拆掉一个常见误会

“早融合”在不同论文里至少有两种用法：

1. **训练时机上的早融合**：文字和图像从预训练早期就一起进入共享 Transformer。前面可以仍有冻结的 SigLIP、VAE 或 RAE；关键是主干没有先做完几千亿 token 的纯语言训练。
2. **输入结构上的 encoder-free early fusion**：尽量砍掉独立大编码器，只留 patchify、Mel 变换、小 MLP 等轻量预处理，让主 Transformer 更接近原始模态。

第二种比第一种更激进。一个模型可以“训练得很早”，却仍然有视觉编码器；也可以把编码器做得很轻，却在语言模型成熟后才接进去。不能把两件事混成一句“有没有 ViT”。

## 和 late fusion 对照

晚融合常见流程是：先把 LLM 练成熟，再接冻结视觉编码器和 projector，用一小段多模态训练把视觉特征塞进既有语言空间。它便宜、能复用成熟 LLM，但视觉容易变成外挂：模型碰到困难时，可能靠文本先验猜答案，而不是认真读取图像。

早融合则让语言和视觉表征一起成形。共享注意力从一开始就见过两种 token，视觉分支也有足够长的训练窗口学会承担任务。

## 论文里的三个证据层级

- 1T 固定总 token 的时间 sweep：视觉引入越晚，视觉能力越差；但越晚也意味着视觉 token 总量越少，所以它是现实配方对照，不是纯粹的“时机”因果实验。
- 固定 200B 联合训练的内部探针：只改变语言 checkpoint 的成熟程度，越晚接视觉，视觉 FFN 激活和图像注意力越弱。
- 2T 规模对照：早、晚方案看到同样多的视觉 token，只改变这些 token 是从头分散出现，还是集中到最后 40%；早融合仍更好。

## 代价

- 从头训练成本高，不能直接继承一个已经很强的闭源或开源 LLM 成品。
- 数据管线必须很早就能稳定供应多模态样本。
- 联合训练并不自动带来协同；若所有模态硬挤同一套 FFN，仍会争容量。

## 链接

- [[physics-of-multimodal-pretraining]] · 系统比较早引入、晚引入、顺序训练与联合训练
- [[interaction-models-tml]] · encoder-free early fusion 的更激进版本
- [[vision-laziness]] · 视觉接得太晚时，模型内部具体怎样“少看图”
- [[modality-synergy-competition]] · 什么时候一起训练会互相帮助，什么时候会抢容量
- [[unified-transformer]] · 把多种 token 放进同一 Transformer 的结构路线
