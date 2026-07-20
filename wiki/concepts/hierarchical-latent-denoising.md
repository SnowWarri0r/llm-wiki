---
name: hierarchical-latent-denoising
type: concept
sources: [hierarchical-denoising-visual-reasoning]
updated: 2026-07-20
---

# Hierarchical Latent Denoising · 层级 latent 去噪

## 一句话

先用少量粗时间节点决定整段轨迹，再用更多细节点逐层落实；粗层故意不完全去噪，避免太早把一种方案锁死。

## 直觉

流式生成最难修的是早期错误。普通模型生成迷宫第一段路线后，后面只能沿着它继续。层级去噪把“马上输出第一段”改成“先做整段低分辨率规划”：

```text
1 个节点：整段方向
2 个节点：前半 / 后半
4 个节点：四个阶段
8 个节点：具体时间点
```

上层不是文字计划，也不是显式搜索树，而是时间分辨率较低的连续 latent。

## 为什么粗层少去噪

把粗节点完全去噪，会得到非常具体的上层状态，下层只能补细节；少去噪则保留残余噪声，使下层还有修正空间。HDR 用 `[5,8,13,20,32,50]`，从粗到细逐渐增加采样步数。

这不等于“噪声越多推理越好”。粗层需要模糊，最细层仍需充分去噪，三者失衡都会变差。

## 证据边界

HDR 的 All-50 消融从 `60.29/89.56` 降到 `58.38/88.21`，支持保留粗层不确定性；但作者没有直接测量每层熵，也未公开层级干净 token 的完整构造代码。

## 链接

- [[hierarchical-denoising-visual-reasoning]] · HDR 完整论文
- [[sparse-hierarchical-attention]] · 层级节点怎样通信
- [[conditional-flow-matching]] · 每个节点如何训练
