---
name: color-legend-mask
type: concept
sources: [sensenova-vision]
updated: 2026-07-13
---

# Color-Legend Mask · 颜色图例掩码

## 一句话
文字先声明“哪个区域对应哪个 RGB”，生成图再用这些颜色铺满像素；文字负责语义与实例身份，图像负责精细边界。

## 为什么需要两部分
单张彩色 mask 有空间信息，却不知道 `(18,210,90)` 代表道路、行人还是第 7 个杯子；纯文字能命名对象，却不擅长列出几十万个像素。混合输出把两种优势拼起来：

```text
图例：<p>road<color>(20,190,240)</color></p>
      <p>person-1<color>(245,80,120)</color></p>
图像：道路像素涂 (20,190,240)，人物像素涂 (245,80,120)
```

解码器建立 `RGB → label/instance` 字典，再对每个像素查表。黑色保留给背景。

## 200 个颜色怎么拉开
SenseNova-Vision 在 RGB 立方体里用 greedy farthest-point sampling 选 200 个 anchor。设已经选中的颜色集合为 `S`，候选颜色 `c` 到集合的安全距离为：

```text
d(c,S) = min ||c-s||₂,  s∈S
c_next = argmax d(c,S)
```

`||·||₂` 是 RGB 三维欧氏距离；先看候选离最近旧颜色有多远，再挑这个“最近距离”最大的候选。

数字例：已有红 `R=(255,0,0)`、绿 `G=(0,255,0)`，比较蓝 `B=(0,0,255)` 与黄 `Y=(255,255,0)`：

```text
d(B,R)=√(255²+0²+(-255)²)=360.6
d(B,G)=360.6                 → d(B,S)=360.6

d(Y,R)=255
d(Y,G)=255                   → d(Y,S)=255
```

因此先选蓝，不选黄；它离当前调色板的最近成员更远，更不容易混色。

## 最脆弱的链条
多区域输出是自回归链：**先生成实例列表和颜色，再生成 mask**。如果文字多报了一个实例、漏了颜色槽，图像通道会忠实执行错误协议。论文附录里，人工修正实例列表后 mask 明显更聚焦，这说明混合输出具有可编辑性，也暴露了文本错误向图像传播的瓶颈。

## 链接
- [[decodable-vision-representation]] · 可逆协议的总框架
- [[promptable-segmentation]] · 点、框、文字等提示如何指定目标区域
- [[sensenova-vision]] · 该协议用于 panoptic、semantic 与 GCG 分割

