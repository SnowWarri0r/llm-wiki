---
name: convolution
type: concept
sources: [cnn, elt, fft, resnet, yolo, yolov2-yolo9000, yolov3, yolov4]
updated: 2026-07-14
---

# Convolution · 卷积 · 一把小尺子滑过整张图

## 一句话
拿一个小窗口（卷积核）滑过整张图，每停一处就把窗口盖住的像素跟核**逐元素相乘再求和**得到一个数 —— 滑遍全图得到一张新图（feature map）。

## 直觉 · 为什么不直接全连接

把一张 224×224 的图拉平喂全连接（MLP）：第一层每个神经元要连 ~5 万个输入，几百个神经元就上千万参数，而且**学到的东西不能挪位置**——猫在左上角学的权重，猫挪到右下角就白学。图像的两个先验它都没利用：

1. **局部性**：一个像素最相关的是它周围的像素，不是对角线另一头的。
2. **平移不变**：一只猫是猫，不管它在画面哪。

卷积把这两条先验**焊进结构**（[[inductive-bias]]）：用一个**小核**（只看局部，比如 3×3）**滑遍全图共用同一套权重**（位置无关）。参数从"上千万"降到"几个核 × 9 个数"，而且天生平移不变。

## 怎么做的 · 滑窗点乘求和

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="cv-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1f3a5f"/></marker></defs>
  <!-- 输入 5x5 -->
  <text class="reveal d1" x="130" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f3a5f">输入 5×5</text>
  <g class="reveal d1" font-size="10" fill="#3a3128" text-anchor="middle">
    <rect x="48" y="46" width="164" height="164" fill="none" stroke="#9fb3c8"/>
    <line x1="48" y1="79" x2="212" y2="79" stroke="#cdd9e6"/><line x1="48" y1="112" x2="212" y2="112" stroke="#cdd9e6"/><line x1="48" y1="145" x2="212" y2="145" stroke="#cdd9e6"/><line x1="48" y1="178" x2="212" y2="178" stroke="#cdd9e6"/>
    <line x1="81" y1="46" x2="81" y2="210" stroke="#cdd9e6"/><line x1="114" y1="46" x2="114" y2="210" stroke="#cdd9e6"/><line x1="147" y1="46" x2="147" y2="210" stroke="#cdd9e6"/><line x1="180" y1="46" x2="180" y2="210" stroke="#cdd9e6"/>
  </g>
  <!-- 核覆盖左上 3x3 高亮 -->
  <rect class="reveal d2" x="48" y="46" width="99" height="99" fill="#1f3a5f" opacity="0.14" stroke="#1f3a5f" stroke-width="2"/>
  <text class="reveal d2" x="97" y="160" text-anchor="middle" font-size="9" fill="#1f3a5f">3×3 核盖住这块 patch</text>
  <!-- 运算 -->
  <g class="reveal d3" font-size="11" fill="#3a3128">
    <text x="250" y="96" fill="#1f3a5f" font-weight="700">patch ⊙ 核</text>
    <text x="250" y="118">= 9 个数对应相乘</text>
    <text x="250" y="138" fill="#1f3a5f" font-weight="700">→ Σ 求和</text>
    <text x="250" y="158">= 1 个输出数</text>
    <path d="M250,150 L470,150" fill="none" stroke="#1f3a5f" stroke-width="1.4" marker-end="url(#cv-a)"/>
  </g>
  <!-- 输出 3x3 -->
  <text class="reveal d4" x="560" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f3a5f">输出 feature map 3×3</text>
  <g class="reveal d4" text-anchor="middle">
    <rect x="510" y="80" width="100" height="100" fill="none" stroke="#9fb3c8"/>
    <line x1="510" y1="113" x2="610" y2="113" stroke="#cdd9e6"/><line x1="510" y1="146" x2="610" y2="146" stroke="#cdd9e6"/>
    <line x1="543" y1="80" x2="543" y2="180" stroke="#cdd9e6"/><line x1="576" y1="80" x2="576" y2="180" stroke="#cdd9e6"/>
    <rect x="510" y="80" width="33" height="33" fill="#1f3a5f" opacity="0.6"/>
    <text x="526" y="101" font-size="9" fill="#fff">●</text>
  </g>
  <text class="reveal d4" x="560" y="200" text-anchor="middle" font-size="9" fill="#7a6f5d">左上 patch → 左上这个输出格</text>
  <text class="reveal d5" x="360" y="250" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#3a3128">核往右/往下滑一格，重复 → 填满整张 feature map（核的权重一路不变）</text>
</svg>
</figure>

- **核（kernel/filter）**：一个小权重矩阵，比如 3×3 = 9 个可学的数。
- **滑窗**：核从左上角开始，盖住一块 patch，点乘求和出一个数；右移一格再来；走完一行换下一行。
- **stride（步长）**：一次滑几格，2 就跳着走、输出更小。
- **padding（补边）**：边上补一圈 0，让输出不缩水 / 控制尺寸。
- 输出尺寸 ≈ `(W − K + 2P) / S + 1`。

## 多核 → 多张 feature map

一个核只能抓**一种**局部模式（比如"竖边")。所以一层放**很多核**（比如 64 个），每个学一种模式（横边、斜边、某种颜色块……），输出 64 张 feature map 摞起来 = 这层的输出通道。下一层的核再在这 64 通道上滑，组合出更复杂的模式（角 → 纹理 → 部件 → 物体）。

## 为什么赢过全连接 · 三个先验焊进结构
- **局部连接**：核只看局部 → 参数少、抓的是空间相邻关系
- **权重共享**：同一个核滑遍全图 → 参数再砍一大刀，且**平移不变**（猫在哪都用同一套核认）
- **层级组合**：层层堆叠，感受野（[[receptive-field]]）越来越大，特征从边缘→部件→物体

这三条就是 CNN 的 [[inductive-bias]]：数据少时是宝（自带视觉先验），大数据时代被 [[patch-embedding]] 的 ViT 用纯注意力填平了护城河，但卷积仍是最省、最快的视觉底座。

## 代码出处
- `nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding)` 是所有框架的标准实现
- 源头：LeCun 的 LeNet（1989/1998）；现代视觉骨干（[[resnet]]）全建在卷积上

## 链接
- [[cnn]] · 卷积堆起来的完整网络故事
- [[receptive-field]] · 堆深了一个输出能"看到"多大范围
- [[pooling]] · 卷积之间下采样、扩感受野
- [[inductive-bias]] · 局部性+平移不变是焊进结构的先验
- [[patch-embedding]] · ViT 用它替掉卷积进视觉
- [[resnet]] · 卷积网络做深的关键
- [[fft]] · 卷积定理：时域卷积 = 频域逐点乘，大核可走 FFT 加速
