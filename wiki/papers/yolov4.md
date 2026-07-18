---
name: yolov4
type: paper
source: https://arxiv.org/abs/2004.10934
upstream: https://github.com/AlexeyAB/darknet
ingested: 2026-07-13
authors: Alexey Bochkovskiy · Chien-Yao Wang · Hong-Yuan Mark Liao · arXiv 2020
---

# YOLOv4 · 把实时检测器改装成一台完整赛车

YOLOv3 定下三尺度检测头后，下一步不缺新零件，缺的是一套选件方法：Mosaic、CSP、SPP、PAN、Mish、CIoU、DropBlock……哪些真有用，哪些只在分类上好看，哪些会拖慢推理？YOLOv4 的价值不是某一招横空出世，而是把骨干、特征融合、训练增强和框损失放进同一张实验清单，拼出一套普通单卡也能训练的实时检测器。

## 一句话

**保留 YOLOv3 检测头，用 CSPDarknet53 + SPP/PAN 重搭骨干和 neck，再把一包训练技巧与推理组件逐项筛进最终配方。**

## 它要解决的痛点

- **论文技巧太多，不能看见 SOTA 就全装**：有些只对分类有效，有些组合后反而掉点，必须在大数据集和完整检测器上实测。
- **低 BFLOPs 不等于 GPU 真跑得快**：分组卷积、碎片化算子可能省理论运算，却喂不满 GPU；生产部署看的是实测吞吐。
- **高精度检测器太吃训练资源**：大 batch、SyncBN 和多卡训练把复现门槛抬高。YOLOv4 明确把单张 1080 Ti / 2080 Ti 当约束。
- **YOLOv3 的框仍有两处别扭**：中心靠近格子边界时 sigmoid 饱和；框回归分开管坐标，没有直接把重叠、中心距离和长宽比一起优化。

## 核心贡献

1. **组件分类法**：[[bag-of-freebies-specials]] 把“只增加训练成本”和“少量增加推理成本”的技巧分开记账。
2. **骨干改造**：[[cross-stage-partial-network]] 把特征通道分成加工支路与旁路，组成 CSPDarknet53。
3. **特征融合**：[[spp-panet-neck]] 先用多档池化扩感受野，再让高低层特征上下双向汇合。
4. **训练增强**：[[mosaic-augmentation]] 一张训练画布拼四张图，顺手混入四种上下文；另加 SAT、DropBlock、标签平滑等训练技巧。
5. **框损失**：[[complete-iou-loss]] 同时处罚重叠不足、中心偏移和长宽比不合。

## 论文的真实骨架

全文按这条线展开：

1. Introduction：实时、单卡、生产吞吐是目标。
2. Related Work：检测器拆成 backbone / neck / head，再盘点 BoF 与 BoS 候选。
3. Methodology：选 CSPDarknet53、SPP、PAN，改 CmBN / SAM / PAN，引入 Mosaic 与 SAT。
4. Experiments：先做 ImageNet 分类组件实验，再做 COCO 检测消融、骨干与 mini-batch 对照。
5. Results：在 Maxwell、Pascal、Volta 三类 GPU 上分别比较速度与精度。
6. Conclusions：强调 anchor-based 一阶段检测仍有生命力，且整套模型可在普通单卡训练。

## 先把检测器拆成三段

YOLOv4 没换掉 YOLOv3 的 anchor-based 三尺度 head。真正重搭的是前两段：

~~~text
Backbone: CSPDarknet53
    负责从像素提取多层特征

Neck: SPP + PAN
    负责扩感受野，并让深层语义与浅层位置来回汇合

Head: YOLOv3
    继续在三个尺度预测框、物体性和类别
~~~

这套拆法也解释了为什么“分类最准的骨干”不一定“检测最好”。分类最后只要一个全局答案；检测要在一张图里同时找很多大小不同的物体，更吃输入分辨率、感受野、层数和多尺度特征。论文 Table 1 里，CSPDarknet53 的分类并不压倒 CSPResNeXt50，却有更大的 725×725 感受野、29 个 3×3 卷积和 27.6M 参数，最终更适合 COCO 检测。

## CSPDarknet53 · 一部分深加工，一部分保留直路

CSP 的直觉不是“随便把通道砍半”，而是别让全部特征都穿过同一串残差块、重复产生高度相似的梯度。一个 stage 先分流：一支进残差块深加工，一支走较短的旁路，末尾再拼回去并用 1×1 卷积融合。

用一个像素位置的 4 通道特征演示数据流：

~~~text
输入 x = [1, 2, 3, 4]

分流：
加工支路 a = [1, 2]
旁路     b = [3, 4]

假设残差块给 a 学到修正 [+0.5, -0.5]
加工后 a' = [1.5, 1.5]

拼接 [a', b] = [1.5, 1.5, 3, 4]
若后面的 1×1 融合权重都是 0.25：
输出 = 0.25×(1.5+1.5+3+4) = 2.5
~~~

✓ 两支信息都进入下一 stage，但只有一支承担了深加工。真实网络对整张特征图做同样的分流与拼接，不是只算一个像素。

论文的硬件表也提醒了一件反直觉的事：512 输入时，CSPDarknet53 是 52 BFLOPs、66 FPS；CSPResNeXt50 只有 31 BFLOPs，却是 62 FPS。理论运算少了，不代表 GPU 上一定更快。

## SPP + PAN · 先看宽，再把位置送回来

SPP 在最深的 13×13 特征上保留一条原特征直通支路，再并排做 5×5、9×9、13×13 最大池化；三个池化的 stride 都是 1，padding 保持尺寸不变。把直通支路看成“1×1 视野”，四路各有 512 通道：

~~~text
4 路 × 512 channels = 2,048 channels
空间仍是 13×13
~~~

大池化核让同一个位置看见更宽的上下文，又没有继续缩小网格。之后 PAN 先走 v3 熟悉的自顶向下路线：13→26→52，把深层语义送给细网格；再补一条自底向上路线：52→26→13，把精确位置重新送回深层。YOLOv4 还把原 PAN 的 shortcut 加法改成 concat，让两路特征先并排保留，再交给卷积决定怎么混。

论文还改了 SAM：从原来的 spatial-wise attention 改成 point-wise attention。换句话说，它不再只为整张空间位置生成一张共享注意力图，而是在每个位置、每个通道上做逐点门控。原文只给了修改后的结构图，没有把这项修改单独做严格消融；能直接读出的证据是 Table 5 中 SPP/PAN 基线 42.4 AP，加 SAM 后 42.7 AP。

## Freebies 与 Specials · “免费”只是不加推理账单

[[bag-of-freebies-specials]] 是整篇最耐用的阅读框架：

| 类别 | 改什么 | 训练成本 | 推理成本 | YOLOv4 例子 |
|---|---|---:|---:|---|
| Bag of Freebies | 数据、损失、训练策略 | 会增加 | 不增加 | Mosaic、SAT、CIoU、标签平滑、DropBlock |
| Bag of Specials | 网络模块或后处理 | 会增加 | 少量增加 | Mish、SPP、SAM、PAN、DIoU-NMS |

“Free”不是不要钱：Mosaic 要做拼图，SAT 甚至多跑一轮前向/反向。它只表示部署后的检测图没有因此多一层，FPS 账单不跟着涨。

论文 §3.4 最终留下的不是上表两行泛称，而是下面四份明确清单：

- **Backbone 的 BoF**：CutMix、Mosaic、DropBlock、标签平滑。
- **Backbone 的 BoS**：Mish、CSP、MiWRC。MiWRC 是 multi-input weighted residual connections：让多个输入残差分支带着可学习权重汇入当前层，而不是把每条残差一视同仁地直接相加。
- **Detector 的 BoF**：CIoU、CmBN、DropBlock、Mosaic、SAT、消除网格敏感、一个真值分配多个 anchor、余弦退火、遗传搜索超参数、随机训练尺寸。
- **Detector 的 BoS**：Mish、SPP、SAM、PAN、DIoU-NMS。

这四组不能只背缩写：同一个 Mish 同时出现在 backbone 与 detector 的 Specials 里；Mosaic 同时服务于分类预训练和检测训练；而 CIoU 属于训练目标，DIoU-NMS 属于推理后处理，名字接近但作用阶段完全不同。

## Mosaic · 一张画布同时塞进四种上下文

[[mosaic-augmentation]] 把四张训练图缩放、裁剪后拼到一张画布。先用最规整的 640×640 例子看坐标怎么搬：把四张 320×320 图放进四个象限。左上图里一个框是 <code>[80,40,240,280]</code>；右上图整体向右平移 320，所以同样的框变成：

~~~text
x1' = 80 + 320 = 400
y1' = 40
x2' = 240 + 320 = 560
y2' = 280

新框 = [400,40,560,280]
~~~

左下图则给 y 坐标统一加 320。真实 Mosaic 还会随机改变拼接十字、缩放和裁剪，所以超出画布的框要截断，太小或无效的框要丢掉。

它一次混入四种背景，小物体也会因缩放更常出现。论文还指出，每张 Mosaic 样本在各层包含四张图的激活分布，因此能缓解小 mini-batch 下 BN 统计太窄的问题。这个解释是论文动机，不等于 Mosaic 可以在所有任务里替代大 batch。

## SAT · 先让模型自己把目标藏起来，再逼它找回来

Self-Adversarial Training 分两段：

~~~text
阶段 1：冻结网络权重，反向修改输入图像
目标：让模型更难看见原本的物体

阶段 2：固定被修改的图像，正常更新网络权重
目标：仍然把物体检测出来
~~~

它和普通“对抗样本攻击”差别在目的：这里不是测试模型能不能被打垮，而是把模型自己的薄弱点即时做成训练数据。代价也很直接——训练更慢，但推理图不变，所以被归到 Freebies。

## 消除网格敏感 · 让边界不必靠无限大的 logit

YOLOv3 的格内中心偏移是 <code>sigmoid(t_x)</code>，范围在 0 到 1。若真值中心落在格内 0.99 的位置：

~~~text
t_x = logit(0.99)
    = ln(0.99 / 0.01)
    ≈ 4.595
~~~

越贴近格子边界，所需 logit 越大，sigmoid 梯度又越小。YOLOv4 的公开实现给 sigmoid 加缩放与回中：

~~~text
offset = s × sigmoid(t_x) - 0.5 × (s - 1)
~~~

<code>s</code> 是 <code>scale_x_y</code>。以细尺度检测头的 <code>s=1.2</code> 为例，要得到 offset=0.99：

~~~text
sigmoid(t_x) = (0.99 + 0.1) / 1.2
             = 0.90833
t_x = logit(0.90833) ≈ 2.293
~~~

同一个 0.99，logit 从 4.595 降到 2.293；输出范围也从 (0,1) 扩到 (-0.1,1.1)。这就是“消除网格敏感”：不是取消网格，而是让中心靠近、甚至轻微跨过格界时更好学。当前官方配置的三层分别使用 1.2、1.1、1.05；论文正文只写“乘以大于 1 的因子”，精确回中式来自实现。

## 一个真值可以交给多个 anchor

YOLOv3 默认只让形状 IOU 最高的 anchor 当正样本。YOLOv4 把阈值也纳入分配：最佳 anchor 仍负责；其他 anchor 若与真值形状 IOU 高于阈值，也能一起学习。

沿用 <code>60×120</code> 的行人框，公开配置的 9 个 anchor 里：

~~~text
36×75   → IOU 0.375
76×55   → IOU 0.408
72×146  → IOU 0.685  ← 最佳
142×110 → IOU 0.407
~~~

遗传搜索得到的阈值是 0.213，因此这四个都超过阈值，可能同时成为正样本；其余五个低于阈值。它提高正样本覆盖，但也改变了正负平衡，不能只把阈值调低而不看训练稳定性。详见 [[anchor-truth-assignment]]。

## CIoU · 框损失一次管三件事

[[complete-iou-loss]] 写成：

~~~text
L_CIoU = 1 - IoU + ρ²(b, b_gt) / c² + αv
v = 4/π² × [atan(w_gt/h_gt) - atan(w/h)]²
α = v / (1 - IoU + v)
~~~

每个参数都对应一个肉眼能看见的问题：

- <code>IoU</code>：预测框与真值框的重叠比例；<code>1-IoU</code> 管“盖住多少”。
- <code>b,b_gt</code>：两个框的中心；<code>ρ²</code> 是中心距离平方。
- <code>c²</code>：能同时包住两框的最小外接框对角线平方，用它归一化中心距离。
- <code>w,h,w_gt,h_gt</code>：预测框和真值框宽高；<code>v</code> 管长宽比差异。
- <code>α</code>：自适应权重。重叠已经较好时，长宽比修正才更值得加力。

取真值框中心 <code>(0,0)</code>、宽高 <code>4×2</code>；预测框中心 <code>(1,0)</code>、宽高 <code>2×4</code>：

~~~text
交集 = 2×2 = 4
并集 = 8+8-4 = 12
IoU = 4/12 = 0.3333

中心距离平方 ρ² = (1-0)² = 1
最小外接框是 4×4，所以 c² = 4²+4² = 32
中心项 = 1/32 = 0.03125

v = 4/π² × [atan(2) - atan(0.5)]²
  ≈ 0.16784
α = 0.16784 / (1-0.3333+0.16784)
  ≈ 0.20110
αv ≈ 0.03375

L_CIoU = 0.66667 + 0.03125 + 0.03375
        ≈ 0.73167
~~~

✓ 三笔账都非零：框没盖好、中心偏了、长宽比也反了。单纯 <code>1-IoU</code> 只能看到第一笔 0.66667。

## 训练配方 · 论文、搜索结果和当前配置要分开

论文先在 ImageNet 上筛 backbone 组件：训练 8,000,000 step，总 batch 128、mini-batch 32，初始学习率 0.1，poly 衰减，warm-up 1,000 step，momentum 0.9，weight decay 0.005。BoS 对照沿用这套预算；BoF 对照因为增强更难，额外增加 50% 训练 step。因此表里的 BoF 收益并不是“相同训练时长下的纯组件增益”，读结果时要把额外训练预算算进去。

论文 COCO 实验默认：500,500 step，初始学习率 0.01，在 400k / 450k 各乘 0.1；momentum 0.9，weight decay 0.0005；总 batch 64，单卡 mini-batch 4 或 8，多尺度训练。

遗传搜索另得到一组数：学习率 0.00261、momentum 0.949、正 anchor IOU 阈值 0.213、框损失归一系数 0.07。当前 GitHub <code>master</code> 的 <code>yolov4.cfg</code> 又是学习率 0.0013、subdivisions 8、CIoU、Mosaic，并使用上面的 9 个 anchor。三组数字回答的不是同一个问题，不能揉成一套“论文默认配置”。

还有一个实现差异值得留档：论文最终配方列了 DIoU-NMS，但当前公开 <code>master</code> 配置写的是 <code>nms_kind=greedynms</code>。复现实验必须钉住具体 cfg 与 commit，不能只写“YOLOv4”。

## 实验一 · 分类更准，不保证检测更准

CSPDarknet53 的 ImageNet 结果：

| 分类训练配方 | Top-1 | Top-5 |
|---|---:|---:|
| 基线 | 77.2 | 93.6 |
| CutMix + Mosaic + 标签平滑 | 77.8 | 94.4 |
| 再加 Mish | 78.7 | 94.8 |

但同样的结论不能机械搬到所有骨干。CSPResNeXt50 用 BoF + Mish 做分类预训练后，分类变好，拿去做检测反而从 42.4 AP 变成 42.3；CSPDarknet53 则从 42.4 升到 43.0。论文因此选的是“更适合检测的骨干”，不是“ImageNet 第一名”。

## 实验二 · 消融告诉了什么，也没告诉什么

Table 4 的 CSPResNeXt50-PANet-SPP 基线行使用 MSE，得到 38.0 AP；CIoU 对应的单项设置行是 39.6 AP，高 1.6。这里可以比较两行结果，但仍不应把整张表解读成一套严格正交实验：后半段会同时勾选多个 BoF，组合最高到 42.4 AP，不能把所有行差值逐项相加。

BoS 的结果更能说明“装得多不等于强”：

| 结构 | AP | AP50 | AP75 |
|---|---:|---:|---:|
| PANet + SPP | 42.4 | 64.4 | 45.9 |
| + RFB | 41.8 | 62.7 | 45.1 |
| + SAM | **42.7** | **64.6** | **46.3** |
| + SAM + Gaussian YOLO | 41.6 | 62.7 | 45.0 |
| + ASFF + RFB | 41.1 | 62.6 | 44.4 |

SAM 小幅有效，RFB、Gaussian YOLO、ASFF 的这些组合反而掉点。论文最终清单很长，但并不是“热门模块越多越好”。

mini-batch 实验也要窄读：带 BoF/BoS 的 CSPDarknet53 在 mini-batch 4 与 8 时是 41.6 vs 41.7 AP，差 0.1；不带这些策略的另一套 CSPResNeXt50 是 37.1 vs 38.4，差 1.3。它支持“这套配方在该设置下对小 mini-batch 更稳”，不能外推成 batch size 永远无所谓。

## 最终结果 · AP75 与小目标一起补上来

COCO test-dev：

| 模型 | 输入 | GPU | FPS | AP | AP50 | AP75 | AP-small |
|---|---:|---|---:|---:|---:|---:|---:|
| YOLOv3 | 608 | Maxwell | 20 | 33.0 | 57.9 | 34.4 | 18.3 |
| YOLOv4 | 608 | Maxwell | 23 | 43.5 | 65.7 | 47.3 | 26.7 |
| YOLOv4 | 608 | Volta | 62 | 43.5 | 65.7 | 47.3 | 26.7 |
| EfficientDet-D2 | 768 | Volta | 41.7 | 43.0 | 62.3 | 46.2 | 22.5 |

同为 608 输入、Maxwell 表里，v4 比 v3 增加 10.5 AP、12.9 AP75 和 8.4 small AP，速度还从 20 到 23 FPS。相比 Volta 上 AP 接近的 EfficientDet-D2，v4 是 <code>62/41.7≈1.49×</code> FPS，但两者输入尺寸不同，不能把速度差全归功于某个模块。

YOLOv4 的 V100 速度/精度档位是：416 输入 41.2 AP / 96 FPS，512 是 43.0 / 83，608 是 43.5 / 62。分辨率从 512 拉到 608 只多 0.5 AP，却少 21 FPS；部署时未必总该选最大档。

## 误差边界与局限

- 论文没有按类别或错误类型拆定位、分类、背景误检；只能从 AP50、AP75、small/medium/large AP 看结果，不能补写不存在的错误画像。
- 大量技巧互相作用，消融又跨骨干、输入尺寸和组合，难以给每个组件分一张精确功劳表。
- “普通单卡可训”成立于论文给出的 8–16GB 显存与 Darknet 配方，不代表任何框架、任意数据规模都能原样复现。
- 仍是 anchor-based 密集检测：要手工/搜索 anchor、设正样本阈值，推理还要 [[non-max-suppression|NMS]] 收尾。
- 速度表已按 Maxwell / Pascal / Volta 分开，但不同方法的代码、算子优化与输入尺寸仍不完全一致；读 Pareto 趋势比读绝对名次更稳。
- 论文把许多来自其他工作的技巧装成系统，原创性主要在筛选、修改与组合；Mosaic、遗传超参和网格敏感改法也在致谢中明确感谢 Ultralytics YOLOv3 的思路。

## 关键概念

- [[bag-of-freebies-specials]] · 把训练账单与推理账单分开
- [[cross-stage-partial-network]] · CSPDarknet53 的分流骨架
- [[spp-panet-neck]] · 感受野扩张与双向多尺度融合
- [[mosaic-augmentation]] · 四图拼成一个训练样本
- [[complete-iou-loss]] · 重叠、中心、长宽比合成框损失
- [[anchor-truth-assignment]] · 阈值让多个 anchor 同时负责
- [[multi-scale-detection]] · head 仍沿用 v3 的三尺度预测
- [[multi-scale-training]] · 训练时继续随机切输入尺寸
- [[non-max-suppression]] · 论文配方谈 DIoU-NMS，当前 cfg 使用 greedy NMS
- [[mean-average-precision]] · AP50、AP75 与尺寸分桶共同读结果
- [[one-stage-detection]] · 保留 anchor-based 密集预测范式
- [[iou-intersection-over-union]] · CIoU 与正样本阈值的基础度量
- [[darknet-53]] · CSPDarknet53 从这套残差骨干改造而来
- [[receptive-field]] · 骨干与 SPP 的选型都围绕空间覆盖范围
- [[batchnorm]] · Mosaic 与 CmBN 都在处理小 batch 下的统计问题

## 我的批注

- v4 最值得学的不是组件清单，而是<strong>改模型要按训练成本、推理成本、硬件吞吐分别记账</strong>。BFLOPs 只是其中一栏。
- CSP、SPP、PAN、Mosaic、CIoU 各自来自不同问题；“YOLOv4”更像一份经过赛道测试的装车方案，而不是单一理论突破。
- 论文敢把负结果放进表里：RFB、ASFF、Gaussian YOLO 不是没名气，只是在这套车上没跑赢。
- 从 v3 到 v4，严格定位的 AP75 提升 12.9，比 AP50 的 7.8 还大。CIoU 与更强 neck 至少在整体结果上确实补到了框的精修，但消融不足以把功劳单独判给 CIoU。
- 论文配方与仓库当前 cfg 不完全一致，是复现实战里最该醒目的警告：模型名不是可执行规范，版本化配置才是。

## 跟 wiki 里其他 paper 的关系

- [[yolo]] · 开出一阶段整图检测主线
- [[yolov2-yolo9000]] · 引入 anchor、维度聚类与多尺度训练
- [[yolov3]] · 提供三尺度 head；v4 主要重搭 backbone、neck 与训练配方
- [[resnet]] · CSPDarknet53 仍以残差块为加工支路

## 历史定位

- 2015-06 [[yolo]] · 整图一次前向直接出框
- 2016-12 [[yolov2-yolo9000]] · anchor 与多尺度输入
- 2018-04 [[yolov3]] · Darknet-53 与三尺度检测
- 2020-04 **YOLOv4** · CSPDarknet53 + SPP/PAN + 系统化 BoF/BoS
- 2021-07 YOLOX · anchor-free、解耦 head 与动态标签分配
