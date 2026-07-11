---
name: yolo
type: paper
source: https://arxiv.org/abs/1506.02640
upstream: https://pjreddie.com/darknet/yolov1/
ingested: 2026-07-09
authors: Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi (CVPR 2016)
---

# YOLO · 看一眼就把框和类一起吐出来

## 一句话
把目标检测从"先找候选框、再一个个分类"的多步流水线,改成**一个神经网络、一次前向**直接从整张图回归出所有框的坐标 + 类别——"You Only Look Once",于是能做到实时(45 FPS)。

## 它要解决的痛点
之前的检测器慢且绕:R-CNN 那套是"先提上千个候选区域(region proposal)→ 每个区域各跑一遍分类 → 再回归框 → 再去重",一张图要跑几秒。而且分类器只看**候选框里那一小块**,看不到全图上下文,容易把背景误当物体。想要实时检测,得把这条流水线拍扁成一步。

## 核心贡献
- **检测 = 单次回归**:一个 CNN 一次前向,直接从整张图输出所有框 + 类别概率,没有候选框、没有逐块重复分类。
- **网格分工**:把图切成 S×S=**7×7** 网格,物体中心落在哪个格子,就由哪个格子负责预测它。每格预测 B=**2** 个框(各 5 个数:x,y,w,h,置信度)+ C=**20** 类概率 → 输出张量 7×7×**30**。
- **置信度 = Pr(有物体) × IOU**:框的置信度既表达"这里有没有东西",又表达"框得准不准"。
- **全图上下文**:一次看整张图 → 比只看候选块的 R-CNN **背景误检少得多**(但定位更粗、localization 错误多)。
- **实时**:base YOLO 63.4% mAP @ **45 FPS**;Fast YOLO 52.7% @ **155 FPS**(是当时其它实时检测器 mAP 的两倍多)。对比 Faster R-CNN VGG-16 73.2 mAP 但只 7 FPS。
- **泛化强**:从自然图迁到艺术画(Picasso/People-Art)明显好过 DPM、R-CNN。

## 关键概念 → 概念页链接
- [[one-stage-detection]] — 单次回归 vs 两阶段候选框,YOLO 的分水岭
- [[iou-intersection-over-union]] — 两个框重叠多少,置信度与 NMS 都用它
- [[non-max-suppression]] — 一堆重叠框去重,留最有把握的那个
- [[mean-average-precision]] — 检测通用指标 mAP 是怎么算出来的
- [[resnet]] — 同期 CV 主干思路对照(YOLO 主干 24 卷积层,承 GoogLeNet)

## 我的批注 / 疑问
- YOLO 的漂亮是**把"检测"重新表述成"回归"**:不再"提议—验证"两步,而是让一个网格直接对号入座。这种"把多步流水线拍成一次前向"的思路,跟端到端 TTS(见 [[vits]] 治两段失配)是同一种品味。
- 代价很诚实:每格只出 2 个框 + 1 套类别 → **一群小物体(如成群的鸟)会漏**,定位也偏粗。速度换来的精度差,后续 v2/v3… 才逐步补回。
- 置信度里塞进 IOU 这一手很关键:让"有没有物体"和"框得准不准"共用一个训练信号,推理时按 Pr(类)×IOU 排序 + [[non-max-suppression]] 去重就得到干净结果。
