---
name: resnet-architecture
type: concept
sources: [resnet]
updated: 2026-05-22
---

# ResNet Architecture · 残差网络堆叠结构

## 一句话
ResNet 按 stage 堆叠残差块：空间分辨率逐级减半，通道数逐级翻倍，深度靠重复 block 拉上去。

## 直觉
CNN 处理图像时，前面看细节，后面看语义。ResNet 的 stage 就像逐层缩小地图：从高清街景变成城市路网，像素少了、通道多了，每个位置能表达更抽象的东西。

残差连接让这些 stage 可以堆得很深，不至于越深越难训。

## 怎么做的
- 开头用卷积 + pooling 降低分辨率
- 每个 stage 重复多个 [[residual-connection]] block
- stage 之间 stride=2，把空间尺寸减半
- 通道数通常翻倍，补偿空间变小后的表达容量
- 50/101/152 层版本用 [[bottleneck-block]] 控制算力

## 代码出处
ResNet 原论文的 ImageNet 架构表；当前 wiki 以概念解释为主。

## 链接
- [[resnet]] · 来源 paper
- [[bottleneck-block]] · 深层 ResNet 的基本块
- [[degradation-problem]] · 为什么需要残差架构
