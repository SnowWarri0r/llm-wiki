---
name: pooling
type: concept
sources: [cnn, x-vector, yolov4]
updated: 2026-07-13
---

# Pooling · 池化 · 用一个窗口汇总邻域

## 一句话

Pooling 让一个窗口里的多个数变成一个数；**窗口怎么移动**由 kernel、stride、padding 决定，所以池化可以下采样，也可以像 YOLOv4 的 SPP 一样只扩大视野、不改变宽高。

## 先别把“池化”和“缩小”画等号

池化做两件彼此独立的事：

1. 在一个 <code>k×k</code> 窗口内汇总数值；max pooling 取最大值，average pooling 取平均值。
2. 按 stride 移动窗口。stride 大于 1 才会跳格，通常才会缩小输出。

因此，“2×2、stride 2 的 max pool 会把宽高减半”是一个常见配置，不是 pooling 的定义。YOLOv4 的 SPP 用 5×5、9×9、13×13 的大窗口，却把 stride 固定为 1，再补 padding，输出空间尺寸完全不变。

## 一次 max pooling 到底怎么算

输入只有一个通道：

~~~text
X = [ 1  2  0 ]
    [ 3  4  1 ]
    [ 0  2  9 ]
~~~

使用 <code>kernel=3</code>、<code>stride=1</code>、<code>padding=1</code>。为了让边缘也有完整的 3×3 窗口，外围补上不会抢到最大值的 <code>−∞</code>。

左上角输出看到的窗口是：

~~~text
[ −∞  −∞  −∞ ]
[ −∞   1    2 ]  → max = 4
[ −∞   3    4 ]
~~~

中心输出看到整张原图，最大值是 9。窗口每次只移动一格，完整输出为：

~~~text
maxpool(X) = [ 4  4  4 ]
             [ 4  9  9 ]
             [ 4  9  9 ]
~~~

这一步没有可学习权重。它只问：“这个邻域里，这个通道最强的激活是多少？”每个通道独立做同样操作，pooling 本身不混合通道。

## 为什么输出还能保持 3×3

一维长度的输出公式是：

~~~text
L_out = floor((L_in + 2p − k) / s) + 1
~~~

- <code>L_in</code>：输入高度或宽度。
- <code>k</code>：池化窗口大小。
- <code>s</code>：stride，窗口每次移动多少格。
- <code>p</code>：两侧 padding 的格数。
- <code>floor</code>：向下取整。

上例代入 <code>L_in=3, k=3, s=1, p=1</code>：

~~~text
L_out = floor((3 + 2×1 − 3) / 1) + 1 = 3
~~~

对奇数窗口，只要 <code>s=1</code> 且 <code>p=(k−1)/2</code>，输出长度就等于输入长度。YOLOv4 的 13×13 特征图正是这样：

~~~text
k=5,  p=2  → (13+4−5)+1  = 13
k=9,  p=4  → (13+8−9)+1  = 13
k=13, p=6  → (13+12−13)+1 = 13
~~~

## Max 和 Average 分别保留什么

- **Max pooling** 保留窗口里的最强响应。若某个通道代表“竖边”，它近似回答“附近有没有很强的竖边”。强响应在窗口内挪动一两格，结果可能不变，因此带来一点局部平移鲁棒性。
- **Average pooling** 保留整体水平。它更像回答“附近平均有多强”，不会只被一个峰值支配。Global average pooling 则把每个通道的整张特征图平均成一个数。

二者都丢信息：max 不告诉你最大值具体在哪，average 不告诉你各点如何分布。检测和分割需要精确定位，所以不宜无节制地下采样；但这不妨碍 SPP 用 stride 1 的 max pooling 收集上下文。

## 两种典型配置不要混

| 用途 | kernel / stride / padding | 输出变化 | 目的 |
|---|---|---|---|
| CNN 下采样 | 2 / 2 / 0 | 4×4 → 2×2 | 降计算、牺牲细位置 |
| YOLOv4 SPP | 5、9、13 / 1 / same | 13×13 → 13×13 | 不降采样，只扩大每个位置看到的邻域 |
| 分类末端 GAP | 覆盖整张图 | H×W → 1×1 | 每通道汇总成一个全局数 |

## 链接

- [[spp-panet-neck]] · YOLOv4 怎样把三档 stride-1 max pooling 并排拼接
- [[receptive-field]] · 窗口变大为何能引入更宽上下文
- [[convolution]] · 卷积有可学习权重，pooling 是固定汇总
- [[cnn]] · 经典卷积网络里的下采样池化
- [[resnet]] · 末端 global average pooling 的典型用法
