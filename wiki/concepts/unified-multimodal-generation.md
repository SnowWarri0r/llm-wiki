---
name: unified-multimodal-generation
type: concept
sources: [sensenova-vision]
updated: 2026-07-17
---

# Unified Multimodal Generation · 统一多模态生成

## 一句话
不再给检测、分割、深度和 3D 各接一颗专用 head，而是把答案翻译成底座本来就会生成的**文本、图像或文本+图像**，再按确定协议还原成框、mask、深度或 3D 坐标。

## 直觉
传统通用视觉模型常像一排专用插座：检测 head 吐框，分割 head 吐 mask，深度 head 吐连续值。共享 backbone 不等于共享输出接口；新增任务往往还要新增解码器、损失和后处理。

统一多模态生成换了问题：既然统一多模态模型已经能读图、写字、生成图，就把视觉标注变成这两种原生语言。

- 稀疏、符号化答案适合文本：类别、框、点、OCR、关键点、相机参数。
- 每像素都有答案的稠密场适合图像：mask、深度、法线、point map。
- 既要命名又要逐像素定位时用混合输出：文字图例绑定颜色，图像负责铺 mask。

任务本身由 instruction 指定，所以“统一”统一的是**训练与生成接口**，不是说所有任务的评测指标、编码规则都消失了。

## 一个端到端例子
同一张 640×480 街景图可以接三条请求：

```text
请求 A：找出自行车
输出 A：<p>bicycle</p><bbox>[0.100,0.200,0.700,0.800]</bbox>

请求 B：估计深度
输出 B：一张 640×480 灰度深度图

请求 C：给道路和行人分别上色
输出 C：<p>road<color>(20,190,240)</color></p> + 彩色 mask 图
```

三条请求复用同一个 Bagel 模型，但“同一个模型”不等于“所有 token 走完全相同的权重”。A 的文字 token 走 MoT 的理解专家，用 next-token 交叉熵训练；B、C 的图像 latent token 走生成专家，用 flow matching 训练。两路 token 位于同一条多模态序列中，可以互相读取上下文。最终仍要按约定把 A 解回像素框、把 B 解回深度、把 C 的颜色解回类别 mask。

## 它统一了什么，没统一什么

| 统一了 | 没有自动统一 |
|---|---|
| 一个模型与调用入口 | 底座内部的模态专家权重 |
| 文本/图像生成训练通道 | 每种输出的可逆编码约定 |
| instruction 指定任务 | 专家模型的几何先验 |
| 跨任务组合的可能性 | 组合任务一定正确的保证 |

## 链接
- [[sensenova-vision]] · 把该范式扩到结构化视觉、稠密几何、分割和多视图 3D
- [[decodable-vision-representation]] · 标注怎样翻成可生成、又能还原的答案
- [[cross-entropy]] · 文本输出的训练目标
- [[flow-matching]] · 图像 latent 输出的训练目标
- [[mixture-of-transformers]] · 为什么同一模型内部仍有理解与生成两套权重
- [[generalized-causal-attention]] · 文本、输入图和待生成图之间到底谁能看谁

