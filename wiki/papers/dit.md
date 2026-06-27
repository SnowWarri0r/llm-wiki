---
name: dit
type: paper
source: https://arxiv.org/abs/2212.09748
upstream: https://github.com/facebookresearch/DiT
ingested: 2026-06-24
authors: William Peebles (UC Berkeley), Saining Xie (NYU) · ICCV 2023
year: 2023
---

# DiT · 把扩散模型的 U-Net 换成 Transformer

扩散生成的"骨架换芯"里程碑。在它之前，扩散模型的去噪网络几乎都是 U-Net；DiT 证明**纯 Transformer 在 latent patch 上做去噪，不但能用，还更会 scale**——越多算力(更大模型/更小 patch)FID 越低。后来 SD3、FLUX、可灵、Sora 那一代图像/视频生成主干，全是 DiT 的后代。它是 [[diffusion-transformer]] 这个概念的源头论文。

## 一句话
**把扩散去噪的 U-Net 整个换成 ViT（在 VAE latent 的 patch token 上跑），用 adaLN-Zero 把时间步和类别条件注进每层归一化——架构干净、scale 起来 FID 一路降到 2.27。**

## 它要解决的痛点
- **U-Net 是扩散的"祖传家产"，但未必最优**：U-Net 带一堆卷积归纳偏置(局部性、多尺度)，在别的领域(NLP/视觉理解)早被 Transformer 的"大数据 + 可 scale"打败了。扩散为什么还非得用 U-Net？DiT 来验证：换成 Transformer 行不行。
- **怎么把"时间步 t + 类别 c"喂进 Transformer**：去噪网络必须知道"现在去噪到第几步、要生成哪类"。U-Net 有现成的注入位置；Transformer 该怎么接？DiT 系统比了四种，选出 [[adaptive-layernorm]] 的 adaLN-Zero。
- **生成模型缺一条清晰的 scaling law**：DiT 用 Gflops 当横轴，画出"算力越多 FID 越低"的干净曲线，给扩散生成立了 scaling 标尺。

## 核心贡献
1. **U-Net → Transformer**：[[diffusion-transformer]] —— 去噪骨架换成 ViT，在 Stable Diffusion VAE 的 latent(256×256 图 → 32×32×4)上 **patchify** 成 token 序列去噪。patch 越小(p=2)token 越多、算力越大、FID 越低。
2. **adaLN-Zero 条件注入**：[[adaptive-layernorm]] —— 不用固定的 LayerNorm 缩放/平移，而是从 (t+c) 用小 MLP **算出** γ、β 去拧每层归一化；再加一个**零初始化的门控 α**，让每个块开训时是恒等函数(同 [[resnet]] 的 identity 起点)。比 cross-attention / in-context 都好，还最省算力。
3. **干净的 scaling law**：算力(更深/更宽/更小 patch)↑ → FID↓，单调且可预测。DiT-XL/2 在 class-conditional ImageNet 256×256 拿下 **FID 2.27**(cfg=1.5)，SOTA。

## 关键概念
- [[diffusion-transformer]] · 本文开创的架构：Transformer 当扩散去噪骨架
- [[adaptive-layernorm]] · adaLN-Zero：从 t+c 算归一化的 γ/β + 零初始化门控 α
- [[swiglu]] · 现代 DiT 家族(SD3/FLUX)的 FFN 升级；**原版 DiT 其实用的是 GELU**，这条是后话
- [[flow-matching]] · 训练目标的另一种选择；原版 DiT 用 DDPM(预测噪声 ε)，但**架构与目标正交**——同一个 DiT 换成预测速度就是 flow matching
- [[patch-embedding]] · latent 切 patch 成 token，跟 [[vit]] 同一招
- [[classifier-free-guidance]] · 拿 cfg=1.5 把 FID 从 9.62 提到 2.27

## 我的批注
- 最值得记的一句：**DiT 是架构，flow matching / diffusion 是训练目标，两者正交**。你在 DiT 结构图里看不到 flow matching，因为它根本不在架构里——它在"你训这网络去预测什么(噪声 ε vs 速度 v)"和"怎么用输出(采样循环)"。原版 DiT 预测 ε(DDPM)；SD3/FLUX 把同一个 DiT 拿去预测速度 = flow matching。**adaLN 的时间条件是把网络和轨迹接起来的桥**。
- adaLN-Zero 的"零初始化门控"是个被低估的细节：它让 28 层的 DiT 开训即恒等，梯度好走。这跟 ResNet"白送 identity"、Cosmos 3 MoT 两塔从 VLM 初始化是同一个母题——**给深网络一个不破坏信号的起点**。
- 条件注入的账算得很实：adaLN-Zero 只动归一化的几个参数，比 cross-attention 省，FID 还更低(19.47 vs 26.14 @400K)。"便宜又好"很少见。
- 容易踩的误区:别把 SwiGLU、flow matching 当成原版 DiT 的东西——那是 2024 的 SD3 给 DiT 家族做的现代化升级。原版 DiT(2022) = GELU MLP + DDPM ε 预测 + adaLN-Zero。

## 跟 wiki 里其他 paper 的关系
- [[stable-diffusion-3-5]] / [[flux-1]] · DiT 的直系后代：把 DiT 升级成 [[mmdit]] 双流 + flow matching + SwiGLU
- [[rae-dit]] · 在 DiT 主干上换 latent(语义编码器)，主干仍是 DiT
- [[vit]] · DiT = ViT 拿去当扩散去噪器；patchify、Transformer 块同源
- [[cosmos-3]] · MoT 的 generator 塔本质就是个 DiT

## 历史定位
- 2020-22 **DDPM / ADM / LDM** · 扩散去噪一律用 U-Net；LDM 把扩散搬进 VAE latent
- 2022-12 **DiT(本篇)** · U-Net → Transformer，adaLN-Zero，scaling law，FID 2.27
- 2024 **SD3 / MMDiT** · 把 DiT 升级成双流 MMDiT + flow matching + SwiGLU，做文生图
- 2024+ **FLUX / 视频 DiT / Cosmos** · DiT 成为图像/视频/世界模型生成的通用主干
