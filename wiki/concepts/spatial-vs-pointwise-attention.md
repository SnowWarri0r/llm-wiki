---
name: spatial-vs-pointwise-attention
type: concept
sources: [yolov4]
updated: 2026-07-13
---

# Spatial-wise vs Point-wise Attention · 一张共享地图 vs 每个元素自己的门

## 一句话

原 spatial-wise attention 对每个空间位置只给一个权重，所有通道共享；YOLOv4 所说的 point-wise attention 给 <code>C×H×W</code> 中每个元素一个权重，所以同一位置的不同通道可以一升一降。

## 先把“point”说准确

设输入特征为 <code>F ∈ R^(C×H×W)</code>：

- <code>C</code>：通道数，可理解为不同类型的特征响应。
- <code>H,W</code>：空间网格的高和宽。
- <code>F[c,h,w]</code>：第 <code>c</code> 个通道、位置 <code>(h,w)</code> 的一个标量。

这里的 **point-wise** 指最后那个标量级元素 <code>(c,h,w)</code> 各自有门，不是只按二维坐标 <code>(h,w)</code> 给门。它也不要和“pointwise convolution 是 1×1 卷积”混为同一个定义；YOLOv4 的实现恰好用 1×1 卷积生成门控，但名字强调的是权重粒度。

## 原版 spatial-wise：先压掉通道，只留下“哪里重要”

原 SAM 先沿通道做 average pooling 和 max pooling，得到两张 <code>1×H×W</code> 地图，再拼接、卷积、sigmoid：

~~~text
A_sp = sigmoid(conv(concat(avg_c(F), max_c(F))))
A_sp ∈ R^(1×H×W)

Y[c,h,w] = F[c,h,w] × A_sp[h,w]
~~~

- <code>avg_c</code>：同一空间位置沿 C 个通道取平均。
- <code>max_c</code>：同一空间位置沿 C 个通道取最大。
- <code>conv</code>：根据两张摘要图生成空间分数。
- <code>sigmoid</code>：把分数压到 0~1，当成门的开度。
- <code>A_sp[h,w]</code>：位置 <code>(h,w)</code> 唯一的空间权重。

由于通道已经被压成两张摘要图，同一位置的所有通道只能乘同一个数。它擅长回答“哪里重要”，但不能说“这里的轮廓通道保留、纹理通道压低”。

## YOLOv4 point-wise：保留通道，让每个元素自己开门

修改后的结构直接生成与输入同形状的门控张量：

~~~text
A_pt = sigmoid(conv1×1(F))
A_pt ∈ R^(C×H×W)

Y[c,h,w] = F[c,h,w] × A_pt[c,h,w]
~~~

1×1 卷积在每个空间位置混合通道，输出 C 个 logit；sigmoid 再把每个 logit 变成 0~1 的门。最终每个通道、每个位置都可以有不同权重。

## 两通道 2×2 完整手算

输入有两个通道：

~~~text
F₁ = [2 4]    F₂ = [8 2]
     [1 3]         [6 4]
~~~

### Spatial-wise：两通道共享同一张门

~~~text
A_sp = [0.25 0.80]
       [0.50 0.10]

Y₁ = F₁ ⊙ A_sp = [0.5 3.2]
                   [0.5 0.3]

Y₂ = F₂ ⊙ A_sp = [2.0 1.6]
                   [3.0 0.4]
~~~

左上角无论是通道 1 的 2，还是通道 2 的 8，都只能乘 0.25。

### Point-wise：第二通道可以用另一张门

~~~text
A₁ = [0.25 0.80]    A₂ = [0.75 0.20]
     [0.50 0.10]         [0.90 0.60]

Y₁ = F₁ ⊙ A₁ = [0.5 3.2]
                 [0.5 0.3]

Y₂ = F₂ ⊙ A₂ = [6.0 0.4]
                 [5.4 2.4]
~~~

同样在左上角，通道 1 仍乘 0.25，通道 2 却能乘 0.75。**这就是修改真正增加的能力：同一个空间位置可以按通道区别对待。**

## 为什么这么改，代价是什么

- spatial-wise 门只有 <code>H×W</code> 个值，便宜、解释直接，强调“哪里”。
- point-wise 门有 <code>C×H×W</code> 个值，表达更细，可以同时编码“哪里”和“哪类特征”，但门控张量与生成它的 1×1 卷积都更贵。

论文 Table 5 中 SPP/PAN 基线为 42.4 AP，加 SAM 后为 42.7 AP；这只能说明该组合里加入 SAM 得到 +0.3 AP，**不能**严格证明 point-wise 一定比原 spatial-wise 高 0.3，因为论文没有给两种 SAM 的一对一消融。

## 论文结构与公开 cfg 的版本提醒

论文 Fig. 5 明确画了 modified SAM。官方 Darknet 的 <code>sam_layer.c</code> 也逐元素执行 <code>output[i] = input[i] × from[i]</code>；实验配置 <code>yolov4-sam-mish-csp-reorg-bfm.cfg</code> 会先用 1×1 卷积和 logistic 生成同形状门控。

但当前官方仓库标准 <code>yolov4.cfg</code> 并没有 <code>[sam]</code> 层。阅读“YOLOv4 架构”时要区分论文的方法/实验清单与某个具体 commit 下的默认配置。

## 链接

- [[yolov4]] · 论文中的修改位置、消融和版本差异
- [[pooling]] · 原 spatial-wise SAM 为什么先沿通道做 average/max pooling
- [[spp-panet-neck]] · 同一节里的 SPP 与 PAN
