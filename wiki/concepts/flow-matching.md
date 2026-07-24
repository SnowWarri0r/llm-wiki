---
name: flow-matching
type: concept
sources: [interaction-models-tml, ideogram-4, stable-diffusion-3-5, krea-2, omnieraser, diffusionnft, sensenova-vision, meshflow, ltx-2, drifting-models, solaris-multiplayer-world-model, senseflow]
updated: 2026-07-24
---

# Flow Matching · 流匹配

## 一句话
不直接一次猜出目标数据，而是学一个**速度场**，从噪声出发沿场积分若干步到图像、视频或音频。

## 直觉
跟 diffusion 是近亲：
- **Diffusion**：学"去噪"，每步把噪声减一点
- **Flow matching**：学"速度场" `v(x, t)`，从 `x₀ = noise` 出发解 ODE `dx/dt = v(x, t)` 到 `x₁ = target`

类比：
- Diffusion 是离散的"一步一步擦掉雾气"
- Flow matching 是连续的"沿河道漂下去"

数学根源是 **Continuous Normalizing Flow (CNF) + Conditional Flow Matching**（Lipman et al. 2022）。

## 不同论文怎样使用它
- **连续值** → 可微，端到端跟主 transformer 联合训练
- **可控步数** → 推理时步数可调，质量/延迟可 trade
- **比 VQ codec 平滑** → 不需要量化误差恢复
- **跟 transformer 接口干净** → flow head 拼在 transformer 输出上

TML 用它生成连续音频特征；Solaris 则在双人视频 latent 上学习 `ε−x`，让动作条件决定两路画面怎样共同变化。

## 跟 RVQ 的对比
| 维度 | RVQ codec | Flow matching |
|---|---|---|
| 输出类型 | 离散 token（多 codebook） | 连续向量（每步细化） |
| 训练目标 | cross-entropy on token | conditional flow matching loss |
| 推理 | AR 吐 token + decoder 重建 | ODE 求解 N 步 |
| 延迟 | 单 step 出 N token | N step ODE，每 step 是矩阵乘 |
| 端到端联训 | 麻烦（VQ 不可微 → straight-through） | 干净 |
| 表达力 | 受 codebook 大小约束 | 连续，无量化误差 |

详见 [[audio-tokenization-rvq-vs-flow]]。

## 开放问题
- ODE 推理需要多步，怎么在 200ms 预算里跑完？步数？
- 跟传统 vocoder（HiFi-GAN）比是不是更好？
- 训练时用什么 prior 路径（OT / VP / VE）？

## 链接
- [[interaction-models-tml]] · 论文
- [[rvq-codec]] · 离散对照
- [[audio-tokenization-rvq-vs-flow]] · 横向对比
- [[early-fusion]] · flow head 接在主 transformer 后
- [[stable-diffusion-3-5]] · 整流流(直线少步)就是 flow-matching 在文生图的落地
- [[sensenova-vision]] · mask、深度、法线与 point map 都作为 VAE latent 用 rectified-flow 目标训练
- [[solaris-multiplayer-world-model]] · 双人视频 latent 上的逐符号公式与数值还原
