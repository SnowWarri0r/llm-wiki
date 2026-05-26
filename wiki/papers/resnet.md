---
name: resnet
type: paper
source: https://arxiv.org/abs/1512.03385
upstream: https://arxiv.org/abs/1512.03385
ingested: 2026-05-21
authors: He, Zhang, Ren, Sun (Microsoft Research Asia) · CVPR 2016 best paper
---

# Deep Residual Learning · 残差连接的起源

CV 领域的奠基论文之一，也是后来 Transformer 能堆深的基础结构。"H(x) = F(x) + x" 一行公式，把"网络越深越好"从口号变成现实。ImageNet 一举从 22 层（GoogLeNet）跳到 152 层。

## 一句话
**别让网络从零学一个映射，让它学跟"输入直接复制过去"的差距**——加一条 `+ x` 的"快车道"，让深层网络的梯度有路可走、参数有路可不学。

## 它要解决的痛点
2015 年大家都在堆深。VGG 19 层、GoogLeNet 22 层。但堆到 56 层时反而**比 20 层还差**——而且不是过拟合（训练集上也更差）。

这叫 **degradation problem**：理论上 56 层只要把多出来的 36 层学成"恒等映射"就能复刻 20 层网络的表现；可实际上 SGD 学不到这种解。**深网络甚至学不会"什么都不做"**。

## 核心贡献
1. **机制**：[[residual-connection]] —— 每个 block 输出 `y = F(x) + x`，让"什么都不做" = F 输出零这种好学的解
2. **训练实操**：[[batchnorm]] + 合适初始化，让深网络 BN-ReLU-Conv 顺序能稳定 backward
3. **架构**：[[resnet-architecture]] —— stage-by-stage 把空间分辨率减半、通道翻倍，配合 [[bottleneck-block]] (1×1 → 3×3 → 1×1) 节省算力
4. **结果**：152 层 ResNet 在 ImageNet top-5 错误率 3.57%（人类 ~5%），同等深度比 VGG 快、比 plain net 显著好

## 关键概念
- [[residual-connection]] · 跳连 / 残差 / shortcut · 核心机制
- [[degradation-problem]] · 深网络反而变差的怪现象
- [[bottleneck-block]] · 50/101/152 层用的省算力模块
- [[batchnorm]] · 配套训练技巧
- [[resnet-architecture]] · 整体堆叠模式

## 我的批注
- 最反直觉的洞察：**让网络更难学的是"恒等映射"，不是新映射**。残差连接其实就是把"恒等"作为默认起点，让 F 只学差量
- 不只是 trick：跳连是后续 **transformer block** 里 `x + Attention(LN(x))` 的同款结构 → 没有 ResNet 的 idea，Transformer 也堆不深
- "残差"这个名字误导很多人。它跟统计意义的 residual 没啥关系，就是个工程命名。本质是 **gradient highway** + **identity-as-default**
- 后续 DenseNet 把 `+` 改成 `concat` 进一步加强这个思路，但参数太大没流行
- 它真正改变了 ML 工程师对"加层"的态度：从前"加层 = 可能掉点"，之后"加层 + 残差 = 一定不会变差"

## 跟 wiki 里其他 paper 的关系
- [[attention-is-all-you-need]] · Transformer block 里的 `+ x` 就是 ResNet 同款，连命名都没换
- [[transformer-architecture]] · Encoder 和 Decoder 每个 sublayer 都是 `LayerNorm(x + Sublayer(x))`
- 这两篇是"砍掉序列串行限制"和"砍掉深度衰减限制"的两根支柱。结合起来才有今天 100B+ 参数的 LLM

## 历史定位
- 2014 GoogLeNet · 22 层 · 已经在"如何继续加深"上挣扎
- 2014 VGG · 19 层 · 极简但训不动更深
- 2015 ResNet · 152 层 · 把"深度"从瓶颈变成廉价资源
- 2016 Identity Mappings · 同一团队的后续，把 `+ x` 改成 pre-activation 顺序
- 2017 Transformer · 同款残差结构在 NLP 上结果（attention sublayer + FFN sublayer 都包 residual）
