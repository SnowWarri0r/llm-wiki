---
name: autoregressive-vs-bidirectional-video-diffusion
type: concept
sources: [hierarchical-denoising-visual-reasoning, solaris-multiplayer-world-model, interactive-video-world-modeling-survey]
updated: 2026-07-24
---

# 流式 AR vs 双向视频扩散

## 一句话

双向扩散让整段视频在每个去噪 step 互相修改，推理强但代价高；流式 AR 从左到右提交，延迟低但早期错误无法撤回。

## 双向扩散

一开始就建立固定长度的整段 noisy latent。每轮去噪时，任意时间位置都能和其他位置交换信息，所以终点约束能反过来修正开头。代价是每轮都处理整段序列，全局时间注意力约为 `O(KN²)`。

## 流式自回归扩散

按 `p(z₁|c)p(z₂|z₁,c)…p(zN|z<N,c)` 从左到右生成。过去的 K/V 可以缓存，新的 latent 生成后立即输出；但错误的 `z₃` 会成为 `z₄,z₅…` 的固定条件。

KV cache 减少了过去 token 的重复投影，不代表总 attention 变为线性：第 `i` 个 query 仍要读取 `i` 个历史 key，`1+2+…+N` 仍是平方级。

## HDR 的折中

HDR 在输出最终细节点之前，先生成粗时间层。它把“整段可修改”压缩成少量上层节点，再用稀疏父子连接传给下层，目标是保留流式延迟，同时推迟早期决定。

## Solaris 的 teacher → student 路线

Solaris 先训练能整段联合去噪的双向多人 teacher，再把中间 checkpoint 改成只能读取过去的因果 student。student 用 6 个 latent frame 的滚动窗口生成，最后在自己生成的历史上做 Checkpointed Self Forcing。这里“双向质量高、因果可部署”的分工非常直接。

## 链接

- [[hierarchical-denoising-visual-reasoning]] · HDR 完整方案
- [[sparse-hierarchical-attention]] · 稀疏连接
- [[kv-cache]] · 流式复用的基础
- [[solaris-multiplayer-world-model]] · 双向单人→双向多人→因果多人→Self Forcing
- [[interactive-video-world-modeling-survey]] · 交互式世界模型为什么必须做因果 rollout
