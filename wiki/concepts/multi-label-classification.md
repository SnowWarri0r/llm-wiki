---
name: multi-label-classification
type: concept
sources: [yolov3]
updated: 2026-07-13
---

# 多标签分类 · 一个框可以同时叫“女人”和“人”

## 一句话

每个类别独立做 sigmoid，不再用 softmax 强迫所有类别互斥。

## 直觉

Softmax 像单选题，所有类别争夺总和为 1 的概率；多标签分类像一排独立开关，每个标签单独回答“是或不是”。当标签会重叠时，“Woman”和“Person”都应该能打开。

## 怎么做的

对每个类别 logit <code>z_k</code> 独立计算：

~~~text
p_k = sigmoid(z_k)
loss_k = -[y_k·ln(p_k) + (1-y_k)·ln(1-p_k)]
总分类损失 = 所有类别 loss_k 相加
~~~

<code>y_k</code> 可以同时有多个 1，因此类别间不需要归一化到总和 1。

## 数字例子

一个框的 logit 是 Person=2.2、Woman=1.4、Dog=-2.0：

~~~text
独立 sigmoid:
Person = 0.900
Woman  = 0.802
Dog    = 0.119
→ Person 与 Woman 可以同时高分

若硬做 softmax:
exp值约为 9.025、4.055、0.135，总和 13.215
概率约为 0.683、0.307、0.010
→ Woman 会被 Person 抢走概率
~~~

目标若是 <code>[1,1,0]</code>，二元交叉熵约为：

~~~text
-ln(0.900) - ln(0.802) - ln(1-0.119)
≈ 0.105 + 0.221 + 0.127
= 0.453
~~~

✓ 两个正标签都被奖励，Dog 低分也被奖励，没有“只能选一个”的冲突。

## 链接

- [[yolov3]] · 检测头从 softmax 改成独立 logistic 分类器
- [[cross-entropy]] · 二元交叉熵的损失直觉
- [[hierarchical-classification]] · YOLO9000 用标签树解决层级类别，路线不同
