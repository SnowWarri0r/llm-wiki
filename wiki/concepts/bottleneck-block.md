---
name: bottleneck-block
type: concept
sources: [resnet]
updated: 2026-05-22
---

# Bottleneck Block · 瓶颈残差块

## 一句话
用 `1×1 → 3×3 → 1×1` 先降维、再做空间卷积、再升维，让深层 ResNet 便宜很多。

## 直觉
直接在 256 个通道上做 3×3 卷积很贵。Bottleneck 先用 1×1 把通道压到 64，在小空间里做最贵的 3×3，再用 1×1 扩回 256。像先把大文件压缩、处理、再解压。

残差支路外面仍然保留 identity 快车道，所以省算力不等于破坏可训练性。

## 怎么做的
```text
x
├─ identity / projection shortcut
└─ 1×1 conv reduce channels
   3×3 conv spatial mixing
   1×1 conv restore channels
→ add
```

50/101/152 层 ResNet 主要靠这个 block 把深度做上去。

## 代码出处
ResNet 原论文中 "bottleneck architecture"；具体实现见常见 torchvision ResNet Bottleneck。

## 链接
- [[resnet-architecture]] · 它被重复堆在哪里
- [[residual-connection]] · 外层 `+ x`
- [[batchnorm]] · 每个卷积后常配 BN
