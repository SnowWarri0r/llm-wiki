---
name: batchnorm
type: concept
sources: [resnet, yolov4]
updated: 2026-07-13
---

# Batch Normalization · BN

## 一句话
对一个 mini-batch 在每个 channel 内做归一化（减均值/除方差），让中间层的分布**不要剧烈漂移**，间接稳住训练。

## 直觉
深网络训练时，每层输出的分布会随着上游 weight 更新而剧烈变化（叫 internal covariate shift）。下游层永远在追"昨天的分布"，导致：
- 学习率不敢调大（怕炸）
- 初始化敏感（一点偏差经过几层放大）
- 训练慢

**BN 的暴力做法**：每层 forward 前，对当前 batch 在 channel 维度内做 z-score 归一化 + 可学习的 scale/shift：
```python
mu = x.mean(dim=batch)
var = x.var(dim=batch)
x_hat = (x - mu) / sqrt(var + eps)
out = gamma * x_hat + beta   # gamma/beta 可学
```

forward 时这就让每层输入都是 0 均值 1 方差（再被 gamma/beta 调一下）。下游层的"任务"被解耦了。

## 在 ResNet 里的位置
原版 ResNet block：
```
conv → BN → ReLU → conv → BN → (+ x) → ReLU
```

后来的 pre-activation ResNet（同作者的 follow-up）：
```
BN → ReLU → conv → BN → ReLU → conv → (+ x)
```

效果更好，因为 `+ x` 这条 path 完全不过 BN/ReLU，identity 真正干净。

## 它的坑
- **batch size 小的时候不稳**（mean/var 估不准）→ 后来有 GroupNorm / LayerNorm 替代
- **训练和推理行为不同**（推理用 running mean/var）→ 容易出 train/test 不一致 bug
- **不适合序列模型**（每个 timestep 的 batch 不同）→ Transformer 用 [[layernorm]] 不是 BN

## Transformer 为什么不用 BN
- 序列长度可变，batch 维度不稳定
- 序列内的 token 分布差别大（早期 token vs 后期 token），不该混着归一化
- LayerNorm 在 feature 维度归一化，跟序列长度无关，更适合

## 链接
- [[normalization]] · 归一化家族对照(BN/LN/GN/RMSNorm 只差对哪根轴)+真数字例子
- [[resnet]] · BN 的早期高光场景
- [[layernorm]] · Transformer 用的替代品
- [[residual-connection]] · BN 跟残差是组合拳
