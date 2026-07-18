---
name: mixture-of-transformers
type: concept
sources: [cosmos-3, sensenova-vision]
updated: 2026-07-17
---

# Mixture-of-Transformers · MoT · 按 token 类型分开的两套 Transformer 权重

## 一句话
每个 Transformer 层有两套完整权重；token 按类型只走其中一套，但两类 token 仍在同一条序列里互相注意。

## 直觉
痛点：同一个模型既要预测下一个文字 token，又要把一整块带噪图像 latent 还原出来。前者用交叉熵，后者用流匹配或扩散式回归；两种目标需要的计算方式和特征并不相同。如果所有 token 都挤进同一套 Transformer 权重，训练时更容易互相干扰。

MoT 的解法是：**给两种工作模式各配一套完整 Transformer 权重**，包括注意力投影、FFN 和归一化层。文本与语义视觉 token 走理解专家；待生成的图像 latent token 走生成专家。这叫**硬路由**：token 的类型已经决定去哪里，不需要再由一个门控网络打分。

最容易误解的是“共享注意力”。这里并不是说两类 token 共用同一套 Q/K/V 权重，而是说它们被放进**同一条多模态序列**，注意力计算时可以把另一类 token 产生的 key/value 当上下文。因此：

- **各走各的权重**：避免文字预测与图像生成争抢同一套参数；
- **仍能看见对方**：图像 token 可以读取文字和输入图像提供的条件；
- **不是两套互不通信的模型**：两路在每层注意力中持续交换信息。

跟两个容易混的东西划清界限：
- **vs [[moe]]**：MoE 是在 FFN 那层养很多"专家"，每个 token 按内容路由到少数几个专家，**注意力是共享的**，目的是**省算力**（总参大、激活小）。MoT 是养**整条 transformer 通路**（连注意力投影都独立），按**模态/任务**路由，目的是**消解多模态冲突**。一个为效率，一个为统一。
- **vs [[unified-transformer]]**：unified-transformer 也用"文本走因果 + 生成走双向"的混合注意力，但**只有一套权重**。MoT 在它之上把权重**拆成两塔**——这是 MoT 的新增点。

## 怎么做的
```
一条 token 序列 = [ AR 子序列(语言+理解) | 扩散子序列(要生成的图/视频/动作) ]

每个 decoder 层：
  文本 / 语义视觉 token → understanding expert 的 Q/K/V、FFN、Norm
  图像 latent token     → generation expert 的 Q/K/V、FFN、Norm

  计算注意力时：
  图像 latent 的 query 可以读取文字 / 语义视觉 token 的 key/value
  因而生成路仍然知道 prompt 在说什么、输入图里有什么
```

具体“谁能看谁”仍由 attention mask 决定，不是 MoT 这三个字自动规定的。Cosmos 3 与 Bagel 都使用这种双专家思路，但它们的 token 类型和 mask 细节并不完全相同。

## 数字例子
Cosmos 3 的 Nano 档：稠密底座是 8B（一个完整 VLM 的参数量）。MoT 给 reasoner 和 generator **各**一套 ≈8B 的权重：

```
reasoner 塔  ≈ 8B   (理解/AR)
generator 塔 ≈ 8B   (生成/扩散)
─────────────────────────────
总参         ≈ 16B   = 2 × 稠密底座
```

✓ 自检：Super 档底座 32B → 总参 64B，正好也是 ×2，对得上"每层两套权重"。但**激活量≈单塔**——因为一个 token 只过它该走的那一塔（AR token 只过 reasoner，扩散 token 只过 generator），不是两塔都过。所以总参翻倍、单 token 计算量没翻倍。对比 MoE：MoE 是 100B 总参可能只激活 5B（省算力）；MoT 是 16B 总参激活≈8B（不为省算力，为分工）。

SenseNova 使用的 Bagel-7B-MoT 也是同一原则：总参数约 14B，每次前向活跃约 7B。文本和 SigLIP2 视觉 token 走理解专家，VAE latent token 走生成专家。SenseNova 所说“不新增任务 head”，指没有再为检测、深度、分割、相机位姿各接一个 decoder；**并不等于把 Bagel 原有的两套模态专家合并成一套。**

## 链接
- [[cosmos-3]] · 用 MoT 把理解+生成+动作统一的 paper
- [[sensenova-vision]] · 基于 Bagel-7B-MoT，把视觉任务改写成文本、图像与混合输出
- [[moe]] · 对照：FFN 专家、按 token 路由、共享注意力、为省算力
- [[unified-transformer]] · 最近亲：混合注意力但单套权重；MoT 拆成双塔
- [[diffusion-transformer]] · generator 塔干的活
- [[qwen3-vl]] · 两塔的初始化来源
