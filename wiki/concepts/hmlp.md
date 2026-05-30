---
name: hmlp
type: concept
sources: [interaction-models-tml]
updated: 2026-05-22
---

# hMLP · Hierarchical MLP

## 一句话
TML 用来处理视频 patch 的轻量预处理器：先保留空间局部性，再把图像块压成 transformer 能吃的 token。

## 直觉
它不像 ViT encoder 那样自己做一整套视觉理解，更像一个很薄的"图像打包器"。raw frame 太大，直接喂主 transformer 会把上下文窗口和算力烧光；hMLP 先把 40×40 这类局部 patch 压成紧凑表示，把剩下的理解工作交给主模型。

这正好符合 TML 的 [[early-fusion]] 思路：预处理只做必要的归纳偏置，不把语义理解锁死在一个冻结 encoder 里。

## 怎么做的
- 输入视频帧，切成固定大小的空间 patch
- 每个 patch 过轻量 MLP，把局部像素关系压进一个 embedding
- 多层/多尺度地合并局部信息，避免完全丢掉邻近 patch 的关系
- 输出 token 序列，与文本 token、[[dmel]] 音频 token 一起进主 transformer

## 代码出处
当前只有 TML 文章级描述；没有公开代码可精确指到文件行。

## 链接
- [[early-fusion]] · hMLP 的架构位置
- [[interaction-models-tml]] · 来源
- [[replace-heuristics-with-weights]] · 把重 encoder 收进主模型的范式
