---
name: lpips
type: paper
source: https://arxiv.org/abs/1801.03924
ingested: 2026-06-10
authors: [Richard Zhang, Phillip Isola, Alexei A. Efros, Eli Shechtman, Oliver Wang]
year: 2018
---

# LPIPS · 深层特征当感知度量

## 一句话
逐像素比图（L2/PSNR）跟人眼差得离谱。LPIPS 把两图过一个预训练网络、比深层特征的距离——再用人类判断校准的权重加权。深度特征作为"像不像"的尺子好得不讲道理。

## 它要解决的痛点
L2/PSNR 假设"像素值近=看着像"，但平移 1 像素 L2 暴增却看着没变、糊图 L2 反而小。需要一个跟人类感知对得上的"图像相似度"。

## 核心贡献
- **特征空间度量**：两图过 frozen CNN（VGG/AlexNet），取多层特征、通道单位归一化、乘学出来的线性权重、L2、空间平均 + 各层求和 = LPIPS。
- **人类 2AFC 校准**：建 BAPPS 数据集，给人看"参考 + 两失真版，哪个更像"，用人票调那组线性权重。
- **unreasonable effectiveness**：几乎任何预训练网络（甚至自监督/随机）的深层特征当感知度量都远胜 L2/SSIM → 感知相似是深度表征的涌现属性。
- **既度量又损失**：评图像质量更准；也当训练 loss 逼输出在感知上像（生成模型常用）。

## 关键概念 → 概念页
- [[perceptual-loss]] · LPIPS 是它最经典的实例
- [[dino]] · 另一种特征来源（DINO loss）
- [[flow-matching]] · 生成训练里 LPIPS 当附加监督

## 我的批注 / 疑问
- 核心思想跟 perceptual-loss 一回事：把"像不像"从像素空间挪到懂图网络的特征空间。LPIPS 是这思想 2018 年的奠基实例。
- "几乎任何网络的特征都行"很有意思——说明这是深度表征的普遍性质，不是某网络特例。
- HiDream-O1 拿 LPIPS + DINO 一起当 perceptual loss，对照看正好：LPIPS 偏纹理/结构、DINO 偏语义。
