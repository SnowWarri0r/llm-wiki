---
name: degradation-problem
type: concept
sources: [resnet]
updated: 2026-05-21
---

# Degradation Problem · 深网络反而变差

## 一句话
深网络（比如 56 层）在**训练集**上的表现比浅网络（20 层）还差——不是过拟合，是 SGD 学不到"白送的好解"。

## 直觉
理论上：56 层网络至少能复刻 20 层网络的能力——把多出的 36 层学成恒等映射就行。

实际上：56 层 plain net 训练 loss 比 20 层还高。**网络甚至学不会"什么都不做"**。

这不是梯度消失（BatchNorm 已经基本解决了纯数值层面的梯度爆炸/消失），是更深层的优化几何问题：**SGD 在 "identity is a sweet spot" 这种局部结构里找不到路**。

## 实验证据（ResNet 论文 Fig 1）
CIFAR-10 上同一套 plain CNN 架构跑：
- 20 layer · train error ~9% · test error ~9.5%
- 56 layer · train error ~13% · test error ~13.5%

加上残差连接后：
- 20 layer ResNet · train error ~8.5%
- 56 layer ResNet · train error ~6.5% （越深越好）

**关键**：plain net 在 train 上就掉点了，所以不是模型容量不够也不是过拟合，**是优化器找不到好解**。

## 为什么残差能解决
[[residual-connection]] 让 identity 变成 layer 的默认输出。如果某一层暂时不需要做事，只要 F 把所有权重学成 0（容易），就自动是 identity。相当于把优化路径**默认对齐**到一个本来就该是的局部最优附近，剩下的训练只在"小修小补"层面操作。

## 链接
- [[resnet]] · 提出和解决问题的论文
- [[residual-connection]] · 解决方案
- [[batchnorm]] · 之前以为问题是梯度消失，BN 部分缓解但根本没解决 degradation
