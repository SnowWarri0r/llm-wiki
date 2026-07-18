---
name: bag-of-freebies-specials
type: concept
sources: [yolov4]
updated: 2026-07-13
---

# Bag of Freebies / Specials · 训练账和推理账分开算

## 一句话

Freebies 只加训练成本；Specials 用少量推理成本换精度。

## 直觉

改检测器像改赛车。训练增强和损失函数是调校：赛前多花时间，比赛时车没多装零件。SPP、注意力、PAN 这类模块是真装上车：每次推理都要跑，但只要精度收益值回那点延迟，也值得。

“免费”只针对部署账单，不代表训练不用算力，也不保证每个技巧都有收益。

## 怎么做的

~~~text
先问：这项改动会不会改变推理计算图？

不会 → Bag of Freebies
  数据增强、标签、损失、学习率、正样本分配

会，但增量不大且精度提升明显 → Bag of Specials
  感受野模块、特征融合、注意力、后处理
~~~

YOLOv4 把 Mosaic、SAT、CIoU、标签平滑、DropBlock 放进 Freebies；把 Mish、SPP、SAM、PAN、DIoU-NMS 放进 Specials。

## 数字例子

假设基线每张图推理 10ms，训练 100 小时：

~~~text
加 Mosaic：训练变 120 小时，推理仍 10ms
→ 训练多 20%，部署延迟 +0ms，属于 Freebie

加一个 neck 模块：训练 125 小时，推理变 10.5ms
→ 部署延迟 +0.5ms；若 AP 收益值得，属于 Special
~~~

✓ 分类看的是推理图有没有变，不是训练有没有付钱。

## 链接

- [[yolov4]] · 用这套分类法筛选完整检测配方
- [[mosaic-augmentation]] · 典型 Freebie
- [[spp-panet-neck]] · 典型 Special
- [[complete-iou-loss]] · 换损失，不增加推理图
