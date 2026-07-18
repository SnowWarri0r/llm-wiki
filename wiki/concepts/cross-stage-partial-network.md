---
name: cross-stage-partial-network
type: concept
sources: [yolov4]
updated: 2026-07-13
---

# CSP · 特征分两路，别让所有通道重复深加工

## 一句话

一部分特征过残差块，一部分走旁路，末尾再拼接融合。

## 直觉

普通残差 stage 让整份特征反复经过同一串块，很多通道会传播相似的梯度。CSP 像把一批原料分成两车：一车进加工厂，一车保留直达通道，出厂口再合流。网络仍能拿到原始信息，但不必让全部通道重复走重活。

## 怎么做的

~~~text
输入特征 x
  ├─ 加工支路 → residual blocks → a'
  └─ 旁路 --------------------→ b
concat(a', b) → 1×1 卷积融合 → 输出
~~~

YOLOv4 把这套 cross-stage partial 结构接到 Darknet-53 的残差 stage 上，得到 CSPDarknet53。

## 数字例子

取一个位置的 4 通道特征：

~~~text
x = [1,2,3,4]
加工支路 a=[1,2]，旁路 b=[3,4]

残差块学到修正 [+0.5,-0.5]
a' = [1.5,1.5]

concat(a',b) = [1.5,1.5,3,4]
1×1 融合权重都取 0.25
输出 = 0.25×(1.5+1.5+3+4)=2.5
~~~

✓ 两路都进了输出，但深加工只落在一部分特征上。

论文 512 输入的硬件表里，CSPDarknet53 是 52 BFLOPs / 66 FPS，CSPResNeXt50 是 31 BFLOPs / 62 FPS。运算更多的一方反而更快，说明规整数据流和 GPU 利用率不能只看 BFLOPs 猜。

## 链接

- [[yolov4]] · 使用 CSPDarknet53 作为骨干
- [[darknet-53]] · 被 CSP 改造的上游骨干
- [[residual-connection]] · 加工支路里的基础块
- [[receptive-field]] · 检测骨干还要覆盖更大的空间范围
