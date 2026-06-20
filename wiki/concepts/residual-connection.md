---
name: residual-connection
type: concept
sources: [resnet, attention-is-all-you-need]
updated: 2026-05-21
---

# Residual Connection · 残差连接 / Skip Connection

## 一句话
在每个 block 里加一条 `+ x` 的"快车道"，让网络默认输出 = 输入，layer 只学**跟默认值的差**。

## 直觉
深网络反向传播时梯度要穿过每一层的权重链式相乘，层数多了几乎必衰减到零（梯度消失）或爆炸。

**两个并发的好处**：
1. **梯度高速路**：`y = F(x) + x` 求导出来是 `dy/dx = dF/dx + 1`，那个 `+1` 让梯度永远有一条不衰减的路回上游。100 层照样训得动。
2. **identity 是默认值**：如果某 layer 完全没用，它只要把 F 的所有权重学成 0 就行（很容易），输出自动等于输入。**SGD 学"什么都不做"比学"恒等映射"简单得多**——这是 ResNet 论文的核心洞察。

类比：办公楼里如果每层都必须重新设计电梯井，盖到 50 层就完了；如果有一条贯穿所有楼层的固定电梯井（identity path），每层只考虑自己的"装修"，就能盖到 152 层。

## 怎么做的
```
# block 内部
def residual_block(x):
    out = conv1(x)         # F 的第一部分
    out = bn(out)
    out = relu(out)
    out = conv2(out)       # F 的第二部分
    out = bn(out)
    return relu(out + x)   # 关键：+ x 这条快车道
```

如果 `out.shape` 跟 `x.shape` 不同（比如 stride=2 或通道变了），加一条 1×1 conv 的投影 `W·x`，论文叫 projection shortcut。

## 在 Transformer 里
完全同款，只是 F 换成 attention/FFN：
```python
def transformer_sublayer(x, sublayer):
    return layernorm(x + sublayer(x))
```

每个 encoder/decoder layer 里都有两个这样的 sublayer（多头 attention + FFN），都包了 residual。

## 后续变种
- **DenseNet**：不是 `+`，是 `concat`（沿通道方向拼），更激进
- **Highway Network**：早于 ResNet，用 gate `T(x)·F(x) + (1-T(x))·x` 控制比例。ResNet 等于把 T 固定成 0.5
- **Pre-activation ResNet (Identity Mappings)**：原版是 `relu(F(x) + x)`，改成 `F(x) + x` 不过 relu，BN 和 ReLU 挪到 F 内部 → 训得更稳

## 链接
- [[resnet]] · 起源论文
- [[attention-is-all-you-need]] · 在 transformer block 里复用
- [[transformer-architecture]] · 怎么嵌入 sublayer
- [[degradation-problem]] · 残差连接解决的问题
- [[batchnorm]] · 配套训练技巧
- [[gradient-backprop]] · 它给梯度修的"高速路"治的就是连乘消失
