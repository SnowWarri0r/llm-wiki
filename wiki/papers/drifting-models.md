---
name: drifting-models
type: paper
source: https://arxiv.org/abs/2602.04770
ingested: 2026-06-12
authors: [Mingyang Deng, He Li, Tianhong Li, Yilun Du, Kaiming He]
year: 2026
---

# Generative Modeling via Drifting · 训练时漂移、一步生成

## 一句话
扩散把"噪声→数据"的迭代放在推理时（多步慢）；Drifting 用"吸引真数据+排斥自己"的漂移场，把迭代搬到训练时，推理只剩一步。ImageNet 256 一步 FID 1.54。

## 它要解决的痛点
扩散/flow 把复杂映射拆成推理时的几十~几百步（NFE 高），又慢又贵；各种少步采样都是事后压缩这条链。Drifting 问：能不能压根不在推理时迭代，把迭代整个搬到训练时？

## 核心贡献
- **漂移场 V_{p,q} = V⁺(吸向真数据 p) − V⁻(斥离自生成 q)**：像粒子间的力，推动生成样本。
- **反对称 → 平衡**：`V_{p,q}=−V_{q,p}`，所以 `q=p` 时场处处归零——生成分布骗过真实分布那刻自动收敛，不用判别器。
- **stopgrad 不动点训练**：`L = ‖f(ε) − stopgrad(f(ε)+V)‖² = ‖V‖²`。训练迭代 `xᵢ₊₁=xᵢ+V` 就是分布演化（优化器的迭代替代了 ODE solver 的迭代）。
- **核漂移场**：`k(x,y)=exp(−‖x−y‖/τ)`，在预训练特征空间（latent-MAE）里算，吸近处真样本、斥近处自生成。
- 结果：ImageNet 256 一步 **FID 1.54**（latent）/ 1.61（pixel），SOTA 单步；机器人 Diffusion Policy 一步版追平 100-NFE。

## 关键概念 → 概念页
- [[ode-sde]] · 走相反方向：扩散迭代在推理时，Drifting 迭代在训练时
- [[flow-matching]] · 同属"噪声→数据"映射，但 FM 仍多步推理、Drifting 一步

## 我的批注 / 疑问
- 一句话记牢：**别在生成时反复爬，训练时就把生成器调到"一步到位"**。机制像无判别器的 GAN（吸真斥假）+ 反对称平衡 + stopgrad 不动点三件套；排斥自己那项天然防 mode collapse。
- 待查：反对称 V=0 ⟹ q=p 的可辨识性（论文 Appendix C.1 的启发式）；核函数 τ 怎么调、为什么在 latent-MAE 特征空间而非像素空间。
