---
name: pooling
type: concept
sources: [cnn]
updated: 2026-06-09
---

# Pooling · 池化 · 把 feature map 缩小、抓重点

## 一句话
在小窗口里取**最大值（max）或平均值（avg）**代表那一片 —— 把 feature map 分辨率砍半，留下"有没有这个特征"、丢掉"它精确在第几个像素"。

## 直觉 · 认猫不需要数清每根毛

卷积出来的 feature map 还很大、很细。但做识别时，你关心的是"**这片有没有竖边**"，不是"竖边精确落在第 137 个像素"。Pooling 就是把一小片（比如 2×2）压成一个数：

- **Max pooling**：取这 4 个里最大的 → "这片只要有一处强响应就留住"，最常用。
- **Avg pooling**：取平均 → 更平滑，常用在最后一层（global avg pooling）把整张图压成一个向量。

2×2、stride 2 的 pooling 把宽高各砍一半（面积 1/4）。

## 怎么做的

```
feature map 4×4         max-pool 2×2, stride 2 → 2×2
[ 1  3 | 2  0 ]
[ 4  2 | 1  1 ]   每个 2×2 块取最大          [ 4  2 ]
[ 0  1 | 5  2 ]   ─────────────────▶        [ 6  5 ]
[ 6  3 | 1  4 ]
```

没有可学参数，就是个固定的下采样算子。

## 它换来什么 · 三个好处
- **降计算**：分辨率砍半，后面层算得快、占显存少。
- **扩感受野**：缩小后，同样 3×3 的核能"看到"原图更大一片（见 [[receptive-field]]）—— 这是 CNN 逐层"看得越来越宽"的主力。
- **一点平移鲁棒**：特征在小窗口里挪一两格，max 结果不变 → 对微小位移不敏感。

## 为什么现代网络在少用它

代价是**丢空间信息**（max 把"在哪"扔了）。所以：
- 检测/分割这种要精确定位的任务，激进 pooling 会害事。
- 很多现代骨干改用 **stride=2 的卷积** 来下采样（既缩尺寸又可学），把 pooling 换掉；但 **global avg pooling**（最后把每张 feature map 压成一个数）几乎人人还在用——它替掉了老式 CNN 末端那坨全连接，省一大把参数。

## 代码出处
- `nn.MaxPool2d(2)` / `nn.AvgPool2d` / `nn.AdaptiveAvgPool2d(1)`（global avg pool）
- 经典用法见 [[resnet]] 末端的 global average pooling

## 链接
- [[convolution]] · pooling 夹在卷积层之间下采样
- [[receptive-field]] · pooling 是扩感受野的主力
- [[cnn]] · 卷积+池化堆成的完整网络
- [[resnet]] · 末端 global avg pooling 替掉全连接
