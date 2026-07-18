---
name: darknet-53
type: concept
sources: [yolov3, yolov4]
updated: 2026-07-13
---

# Darknet-53 · 把残差接进 YOLO 骨干

## 一句话

用 1×1/3×3 卷积、stride-2 下采样和残差捷径，换来接近 ResNet-152 的分类精度与约两倍速度。

## 直觉

Darknet-19 很快，但容量不够；ResNet-152 很准，却太重。Darknet-53 沿用 Darknet 擅长的规整卷积，再把 ResNet 的 shortcut 接进来：主路学习变化，捷径保留原特征，深度加上去时梯度不必层层硬闯。

## 怎么做的

五个 stage 逐步减半空间、增加通道，残差块重复次数是：

~~~text
1 → 2 → 8 → 8 → 4
总计 23 个 residual blocks
每块包含 1×1 降/整通道 + 3×3 提特征，再加回输入
~~~

分类版在全局平均池化后用 1×1 卷积输出 1000 类；检测版拿掉分类头，把不同 stage 的特征交给三尺度检测头。

## 数字例子

论文的 256×256 ImageNet 单裁剪结果：

~~~text
Darknet-53 vs ResNet-152
Top-5: 93.8 vs 93.8
速度: 78 FPS vs 37 FPS
速度倍率 = 78 / 37 ≈ 2.11×

Darknet-53 vs ResNet-101
Top-1: 77.2 vs 77.1
速度: 78 FPS vs 53 FPS
速度倍率 = 78 / 53 ≈ 1.47×
~~~

✓ 一组是相同 Top-5 下快约 2.1 倍，另一组是相近 Top-1 下快约 1.5 倍。

## 链接

- [[yolov3]] · 使用 Darknet-53 作为特征提取骨干
- [[resnet]] · shortcut 的来源
- [[residual-connection]] · 深网络的恒等梯度通道
