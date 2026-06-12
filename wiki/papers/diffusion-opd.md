---
name: diffusion-opd
type: paper
source: https://arxiv.org/abs/2605.15055
ingested: 2026-06-12
authors: [ali-vilab]
year: 2026
---

# DiffusionOPD · 扩散的 On-Policy 蒸馏

## 一句话
给扩散做多奖励对齐时，多奖励一起 RL 会打架、级联训会遗忘。DiffusionOPD 先各训单任务专家老师，再沿学生自己 rollout 的轨迹把老师蒸进一个学生；扩散去噪是高斯马尔可夫链，每步 KL 有闭式解、塌成均值的 MSE。

## 它要解决的痛点
RL 对齐扩散（美学/文字 OCR/指令遵循）单奖励还行，多奖励就难：联合 RL 任务互相打架（cross-task interference）+ 难易不均；级联 RL 灾难性遗忘 + 调度繁琐。

## 核心贡献
- **On-Policy Distillation（OPD）**：学生自己 rollout 生成轨迹，在**学生实际走到的状态**上匹配老师的下一步。每步稠密监督（对比 off-policy 照抄固定数据、对比 RL 稀疏终局奖励）。
- **两阶段解耦**：Stage 1 各任务用 RL 训专家老师（探索解耦）；Stage 2 沿学生轨迹把 M 个老师蒸进一个统一学生（整合不打架、不遗忘）。
- **把 OPD 从离散 token 推广到连续扩散**：扩散去噪 = 高斯马尔可夫链（来自反向 SDE），协方差只由 noise schedule 定、与策略无关 → 同协方差高斯 KL 有闭式解：`KL = ‖μ_s−μ_t‖²/(2σ²)`，每步 KL 蒸馏塌成学生 vs 老师去噪均值的 MSE。`L_OPD = E[Σⱼ ‖μ_s−μ_t‖²/(2σⱼ²)]`（ODE 版去掉 1/σ）。
- 结果：平均归一化 0.929 vs 级联 0.851 / 多任务 RL 0.763；美学/OCR/GenEval 全 SOTA，训练更快更省。

## 关键概念 → 概念页
- [[ppo]] · RL 对齐基底；OPD 用蒸馏绕开多任务 RL 的打架与遗忘
- [[ode-sde]] · 扩散去噪 = 反向 SDE 的高斯马尔可夫链（闭式 KL 的前提）
- [[cross-entropy]] · 同协方差高斯的 KL 退化成均值差的 MSE

## 我的批注 / 疑问
- 一句话记牢：**探索交给各任务专家老师，整合用"沿学生自己轨迹、贴老师去噪均值"的一个干净 MSE**。把 RL/PPO 对齐 + on-policy 蒸馏 + 扩散=高斯马尔可夫链 + 高斯 KL=MSE 拧到一起。
- 待查：老师本身的 RL（GRPO-Guard / NFT）细节；Stage 2 跨任务梯度累加 G=M 的均衡怎么保证不再 imbalance；on-policy rollout 的算力开销 vs 收益。
