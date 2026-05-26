---
name: dual-ar
type: concept
sources: [fish-speech-s2-pro]
updated: 2026-05-20
---

# Dual-AR · 双自回归

## 一句话
慢 AR 写主旋律（语义骨架），快 AR 写配器（声学细节），主从串成两层 AR。

## 直觉
TTS 的根本矛盾：要质量高就得在高采样率的 token 流上跑 AR，但每秒上千 token × 大模型 = 推不动。

S2 把任务摊到两层：
- **慢 AR (4B)** —— 沿时间轴每帧吐 **1 个** 主语义 codebook，决定这一帧"说什么"
- **快 AR (400M)** —— 同一帧上再吐 **9 个**残差 codebook，把音色 / 咬字 / 气声补齐

慢 AR 算少次但算重，快 AR 算多次但便宜。乘下来推理 budget 守得住。

## 怎么做的
- [[rvq-codec]] 把 waveform 编成 10 个 codebook、~21 Hz 帧率（约 50ms 一帧）
- 慢 AR = decoder-only transformer，自回归吐主 codebook 序列
- 每个时间步把慢 AR 的隐状态喂给快 AR
- 快 AR 在这一帧上**顺序生成** 9 个残差 codebook
- 整体跟标准 LLM 同构 → SGLang 的 paged KV cache / continuous batching / CUDA graph / RadixAttention 全直接复用

## 为什么不一层搞定
单一大 AR：rate × params = 推不动。
多层 codec 但单 AR：codec 信息瓶颈 OK 但要 AR 每步吐 10 个 token，要么自回归长度 ×10，要么"并行吐" → 牺牲精度。

Dual-AR 是用一个小的"局部 AR" 把 codec 内部依赖打掉，让外层 AR 看到的序列长度跟传统 LLM 一样。

## 跟 TML interaction model 的对照
TML 也是双层结构，但**边界不一样**：
- fish-speech：两层都在生成路径上，主/从（["怎么发"]委托给["发什么"]）
- TML：[[dual-model-architecture]] 是前台 always-on + 后台异步深推理，分工是"谁负责说话 / 谁负责想"

## 代码出处
- 本地 clone 软链至 `raw/fish-speech/fish_speech/models/`（具体文件待查 ingest）
- 技术报告：https://arxiv.org/abs/2603.08823

## 链接
- [[rvq-codec]] · 这是 Dual-AR 操纵的离散 token 来源
- [[grpo]] · 后训练阶段做 RL 对齐
- [[sglang-inference]] · 推理基建复用前提
- [[fish-speech-s2-pro]] · 论文
- [[dual-model-architecture]] · 不同维度的"两层"思路
