---
name: gaussian-splatting
type: concept
sources: []
updated: 2026-06-17
---

# 3D Gaussian Splatting · 3DGS · 用一堆高斯椭球表示场景

## 一句话
不用网格/体素,把一个 3D 场景表示成空间里**几百万个带颜色、透明度、形状朝向的小高斯椭球**;渲染时把它们**"泼/拍(splat)"到屏幕上按深度叠起来**——又快(实时)又能从任意新角度看(新视角合成)。

## 直觉 · 场景是一团会发光的"果冻球"

要在电脑里表示一个真实场景、还能从任意角度看它,传统办法是建三角网格 mesh,或用 [[score-function]] 那类隐式表示。3DGS(Kerbl et al. 2023)换了个直白的表示:**把场景拆成一大堆半透明的小椭球**,每个椭球身上记着:
- **位置**(它在 3D 空间哪儿)
- **形状 + 朝向**(协方差矩阵——是圆是扁、朝哪歪)
- **颜色**(还随视角微变,模拟反光)
- **不透明度 α**

一团这样的椭球叠在一起,远看就拼成了整个场景——像用**几百万颗会发光的小果冻**摆出一个房间。

## 怎么做的 · splat + α 混合,可微优化

**渲染(splat)**:把每个 3D 高斯椭球**投影到屏幕**变成一个 2D 的模糊斑点,按**深度从前到后做 α 混合**(前面的半透明斑盖住后面的),叠成最终像素。纯投影 + 混合,没有逐光线积分 → **极快、能实时**。

**怎么得到这堆椭球**:给一组**多视角照片**,从随机椭球开始,**可微地渲染**出图、跟真实照片比、反向传播去调每个椭球的位置/形状/颜色/α,直到渲染图匹配所有照片。优化好之后,**任意新角度**都能渲染出来——这就是**新视角合成(novel view synthesis)**。

<figure style="margin:26px 0; padding:22px; background:#eef2f0; border:1px solid #9fb8aa; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="gs-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#1f4d3a"/></marker></defs>
  <!-- 一堆 3D 高斯椭球 -->
  <text class="reveal d1" x="130" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#1f4d3a">一堆 3D 高斯椭球</text>
  <g class="reveal d1">
    <ellipse cx="90" cy="80" rx="26" ry="14" fill="#9b2c2c" opacity="0.5" transform="rotate(-20 90 80)"/>
    <ellipse cx="140" cy="100" rx="20" ry="12" fill="#b8841c" opacity="0.5" transform="rotate(25 140 100)"/>
    <ellipse cx="110" cy="130" rx="30" ry="16" fill="#1a6a64" opacity="0.5" transform="rotate(10 110 130)"/>
    <ellipse cx="160" cy="150" rx="18" ry="22" fill="#3949ab" opacity="0.5" transform="rotate(-35 160 150)"/>
    <ellipse cx="70" cy="150" rx="22" ry="12" fill="#6a3a8e" opacity="0.5"/>
    <ellipse cx="125" cy="165" rx="16" ry="10" fill="#4a6b3a" opacity="0.55"/>
  </g>
  <text class="reveal d2" x="130" y="200" text-anchor="middle" font-size="8.5" fill="#7a6f5d">每个椭球: 位置·形状朝向·颜色·不透明度α</text>
  <!-- splat 箭头 -->
  <line class="reveal d3" x1="210" y1="120" x2="320" y2="120" stroke="#1f4d3a" stroke-width="1.6" marker-end="url(#gs-h)"/>
  <text class="reveal d3" x="265" y="110" text-anchor="middle" font-size="9" fill="#1f4d3a">splat 投影</text>
  <text class="reveal d3" x="265" y="136" text-anchor="middle" font-size="8" fill="#7a6f5d">按深度 α 混合</text>
  <!-- 屏幕成像 -->
  <text class="reveal d4" x="430" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#1f4d3a">拍到屏幕成图</text>
  <rect class="reveal d4" x="350" y="56" width="160" height="120" rx="3" fill="#faf4e1" stroke="#1f4d3a"/>
  <g class="reveal d4" opacity="0.8">
    <circle cx="400" cy="95" r="10" fill="#9b2c2c"/><circle cx="430" cy="110" r="9" fill="#b8841c"/><circle cx="415" cy="135" r="12" fill="#1a6a64"/><circle cx="450" cy="140" r="8" fill="#3949ab"/>
  </g>
  <text class="reveal d4" x="430" y="194" text-anchor="middle" font-size="8" fill="#7a6f5d">纯投影+混合 → 实时</text>
  <!-- 换视角 -->
  <text class="reveal d5" x="600" y="34" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#b0327a">任意新角度</text>
  <path class="reveal d5" d="M540 120 A 60 60 0 0 1 600 70" fill="none" stroke="#b0327a" stroke-width="1.5" marker-end="url(#gs-h)"/>
  <circle class="reveal d5" cx="600" cy="120" r="6" fill="#b0327a"/>
  <text class="reveal d5" x="600" y="150" text-anchor="middle" font-size="8.5" fill="#b0327a">同一堆椭球</text>
  <text class="reveal d5" x="600" y="164" text-anchor="middle" font-size="8.5" fill="#b0327a">换相机就换视角</text>
  <text class="reveal d5" x="600" y="184" text-anchor="middle" font-size="7.5" fill="#7a6f5d">= 新视角合成</text>
</svg>
</figure>

## vs NeRF(为什么 3DGS 火)
上一代新视角合成是 **NeRF**:用一个 MLP,沿每条光线采很多点、查询颜色密度再积分 → 表示紧凑但**渲染慢**(每像素几百次 MLP 查询),难实时、难编辑。

3DGS 把场景**显式**摊成一堆椭球(像点云):
- **快**:splat 是投影+混合,实时渲染。
- **可编辑**:椭球是显式的,能直接搬动/删改某块场景。
- 代价:**存储大**(几百万椭球),且仍需多视角照片先重建。

## 这跟那个 "高斯泼溅" LoRA 啥关系
HuggingFace 上有个 `Qwen-Image-Edit-2511-Gaussian-Splash` **LoRA**([[lora]]),名字借了"高斯泼溅",但**它不真做 3D 重建**:它是挂在 [[qwen-image-2]] 编辑底模上的 2D 扩散 [[lora]],被训来**模仿** 3DGS 的效果——给两张图,把场景**透视摆正/换视角**,并把换视角后露出的**空白区域 inpaint 补上**。

本质:**几何上该用 3D 算的(透视变换 + 视角合成 + 补遮挡),改交给生成模型"脑补"**——跟 [[pixel-diffusion-decoder]] 那种"算不出的细节让扩散补"是同一种思路。真 3DGS 是几何重建,这个 LoRA 是生成式近似,别混。

## 代码出处 / 来源
- 3D Gaussian Splatting:Kerbl et al. 2023(SIGGRAPH)——实时辐射场渲染
- 例子 LoRA:huggingface.co/dx8152/Qwen-Image-Edit-2511-Gaussian-Splash(2D 扩散模仿,非真 3D)

## 链接
- [[lora]] · 那个"高斯泼溅"是个 LoRA,不是新模型
- [[qwen-image-2]] · LoRA 挂的编辑底模(条件→目标)
- [[pixel-diffusion-decoder]] · 同思路:几何/信息算不出的,交给扩散脑补
- [[score-function]] · NeRF/扩散都跟"场"有关的对照背景
