---
name: teacher-forced-anyflow
type: concept
sources: [solarwm]
updated: 2026-09-14
---

# TF-AnyFlow · 教师强制 + 任意噪声对流映射，一步到位的少步 AR 初始化

## 一句话

把双向视频模型改成因果注意力后，用 AnyFlow 损失直接学"任意两个噪声位之间的流映射"，配 teacher forcing 的干净真历史——产出的初始化天生就是少步自回归，省掉 Causal ODE / Causal CD 两个专门阶段。

## 直觉

把双向视频模型改造成少步因果生成器，主流路线要过两道桥：先做因果化蒸馏（Causal ODE 或 Causal Consistency Distillation）拿到一个多步因果模型，再蒸成少步。TF-AnyFlow 的观察是：双向模型里外观和运动已经学好了，因果化只是"激活"一种预测方式，不是重学表示——那就别绕路，直接用一个**本身就以少步采样为目标**的损失做因果化。AnyFlow 监督的是任意噪声对 (t, r) 之间的映射（flow map），少步采样用到的那些大跨度噪声转移在训练时就被直接练到。

## 怎么做的

- latent 序列切成有序块；预测第 k 块时只能看当前噪声态和**干净的真值历史**（teacher forcing），未来块被遮住。
- 采样一对噪声位 (t, r)，损失 \(\mathcal{L}_{\mathrm{TF\text{-}AF}}=\mathbb{E}\left[\sum_k \ell_{\mathrm{AF}}(f_\phi;\mathbf{z}^k_t,t,r,\mathbf{z}^{<k}_0,\mathbf{c})\right]\)——\(\ell_{\mathrm{AF}}\) 监督从噪声位 t 到 r 的流映射。
- 从双向 checkpoint 初始化,这一步是短暂的因果适配;产出直接交给 DMD 做最后的分布对齐(解决 TF 只见真历史的 exposure bias)。

## 链接

- [[solarwm]] — 三阶段配方的第二阶段
- [[teacher-forcing-video-diffusion]] — TF 端与它留下的 exposure bias
- [[causal-consistency-distillation]] — 被它替代的初始化路线之一
- [[dmd-distillation]] — 接在它后面的第三阶段
