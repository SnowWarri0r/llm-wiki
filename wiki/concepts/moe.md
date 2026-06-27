---
name: moe
type: concept
sources: [interaction-models-tml, unlimited-ocr]
updated: 2026-05-20
---

# MoE · Mixture of Experts

## 一句话
模型养着许多"专家"子网，每次推理一个 token 只激活其中少数几个 —— 总参大但计算路径小。

## 直觉
直觉的反面：通常 N 倍参数 = N 倍 FLOP。MoE 打破这条 —— 用路由器（router）决定每个 token 走哪几个专家，只激活那几个的参数。

TML-Interaction-Small：**276B 总参 / 12B 激活** → 每个 token 只过 12B 参数的计算路径，但模型容量是 276B。

## 怎么做的
- Transformer FFN 层换成 N 个并列 FFN（"专家"）
- 每层有个 router（小线性层 + softmax）给每个 token 输出"该走哪 k 个专家"的分布
- top-k 路由：取分数最高的 k 个专家激活
- 各专家算完结果加权求和

## 推理的工程坑
- 不同 token 路由到不同专家 → 计算图不规整
- 大 batch 下用 [[grouped-gemm-vs-gemv]] 凑批
- 小 batch（如 [[micro-turn]] 一个 chunk）凑不起批 → 直接 gather + gemv

## 链接
- [[interaction-models-tml]] · 论文用了 276B MoE
- [[grouped-gemm-vs-gemv]] · MoE 推理的关键取舍
- [[dual-model-architecture]] · 前台 interaction model 用 MoE
