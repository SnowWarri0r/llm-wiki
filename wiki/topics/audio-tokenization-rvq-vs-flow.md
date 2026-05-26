---
name: audio-tokenization-rvq-vs-flow
type: topic
sources: [fish-speech-s2-pro, interaction-models-tml]
updated: 2026-05-20
---

# 音频 token 化：RVQ vs Flow Matching

两条**当前主流**路线的对照。fish-speech 走前者，TML 走后者。

## 范式区别

| 维度 | RVQ codec | Flow Matching |
|---|---|---|
| 表征 | 离散 token（多 codebook 残差量化） | 连续向量场 |
| 训练目标 | cross-entropy on token | conditional flow matching loss（学速度场） |
| 推理 | AR 模型吐 token + decoder 重建 waveform | ODE 求解 N 步采样 |
| 端到端联训 | VQ 不可微，需 straight-through estimator | 干净，可微 |
| 表达力 | 受 codebook size 限制（量化误差） | 连续，无量化 |
| 延迟 | 单 step 吐多 codebook token → 取决于 codec 解码 | ODE 多步，每步矩阵乘 |
| 跟 LLM 接口 | 完美：token 序列直接喂 transformer | 需要 flow head 作为输出接口 |
| 推理基建复用 | 直接吃 SGLang / vLLM | 需要定制 sampler |

## 选哪条的判断

**RVQ 适合**：
- 服务化 TTS（fish-speech 场景）—— 想直接复用 LLM 推理栈
- 训练数据量大、想 scale 到多语言
- 工程复杂度低优先

**Flow matching 适合**：
- 实时双向交互（TML 场景）—— 想跟主 transformer 端到端联训
- 模型容量很大、能 carry flow head
- 音质上限优先

## 我的解读
**这是工程取舍而不是理论优劣**。

fish-speech 选 RVQ 是因为它要"做最好的离线 TTS 同时极致流式"。"跟标准 LLM 同构"这条让他们直接吃 SGLang 红利 → 工程 ROI 极高。

TML 选 flow matching 是因为它要"做实时双向对话"。flow head 端到端可微 → 音频生成质量随主模型 scaling 自然涨，不被 codec 拖后腿。

如果哪天 fish-speech 团队也做实时双向（不只是流式 TTS），他们大概率也会切到 flow matching 或类似可微 head。

## 一个延展问题
RVQ codec 本身能不能也"端到端可微" 替代 straight-through？已经有人在做（RQ-VAE-Transformer、FunCodec 系列），但还没看到在 LLM 一体化训练里大规模用起来。值得跟踪。

## 链接
- [[rvq-codec]] · 离散路线
- [[flow-matching]] · 连续路线
- [[dmel]] · TML 输入侧的离散化（不是 codec）
- [[fish-speech-s2-pro]] · RVQ 实例
- [[interaction-models-tml]] · Flow matching 实例
