---
name: spatial-conditioning
type: concept
sources: [controlnet]
updated: 2026-08-24
---

# Spatial Conditioning · 用一张图直接指定“哪里该长什么结构”

## 一句话

文字给语义，空间条件图给每个位置的结构约束。

## 直觉

“一个人站在厨房”只说了画面里有什么；一张骨架图还能说清头、手、膝盖各在哪。边缘图、深度图、分割图和姿态骨架都保留二维坐标，因此模型不用从一句话里猜布局。

## 怎么做的

条件图 \(c_i\in\mathbb{R}^{512\times512\times3}\) 先经过小编码器 \(E\)，得到与 Stable Diffusion latent 空间对齐的特征 \(c_f\)：

\[
c_f=E(c_i),\qquad c_f\in\mathbb{R}^{64\times64\times C}.
\]

这里 \(c_i\) 是输入图片，\(E\) 负责下采样和换通道，\(c_f\) 是送进控制分支的特征。之后控制分支继续在 64、32、16、8 四个尺度提取信息：高分辨率保轮廓细节，低分辨率更容易看整体姿态与布局。

## 数字例子

官方 ControlNet 1.0 实现用了三次 stride-2 下采样。stride 2 可以近似理解成边长减半：

\[
512\times512
\rightarrow256\times256
\rightarrow128\times128
\rightarrow64\times64.
\]

边长缩了 \(512/64=8\) 倍，格子数缩了 \(8^2=64\) 倍；512×512 共 262,144 个位置，64×64 只剩 4,096 个。自检：\(4096\times64=262144\)，尺寸账闭合。

论文正文写“四个 4×4、stride-2 卷积”却又说输出 64×64；若四次都减半，结果应是 32×32。官方代码 commit `ed85cd1` 实际使用三次 stride-2，因此不能把论文这句当成精确实现。

## 跟文字条件的对照

- 文字条件：token 没有固定二维坐标，擅长指定物体、属性和风格。
- 空间条件：每个像素或关键点有明确位置，擅长指定轮廓、姿态、区域和几何。
- 两者一起用：文字决定“画成谁、什么风格”，条件图决定“结构放在哪里”。

## 链接

- [[controlnet]] · 把空间条件接进冻结 Stable Diffusion
- [[semantic-segmentation]] · 用类别颜色图规定每块区域是什么
- [[cross-attention]] · 文字 token 怎样进入图像特征
