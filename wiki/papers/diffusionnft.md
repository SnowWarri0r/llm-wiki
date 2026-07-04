---
name: diffusionnft
type: paper
source: https://arxiv.org/abs/2509.16117
upstream: https://arxiv.org/html/2509.16117v1
ingested: 2026-06-30
authors: [清华/NVIDIA 等 · ICLR 2026]
year: 2026
---

# DiffusionNFT · 把扩散的 RL 从"反向采样"搬回"前向加噪"

## 一句话
给扩散模型做在线 RL 的老路是把反向采样切成多步 MDP 再套 GRPO,但继承一身毛病(锁死一阶 SDE solver、前后向不一致、CFG 要两套模型)。DiffusionNFT 换思路:**一条前向加噪过程是唯一的、反向去噪有无数条**,那就把 RL 直接做在前向上——用奖励把样本切成正/负两堆([[negative-aware-finetuning]]),正负速度之差就是隐式的改进方向([[reinforcement-guidance]],本质是把 CFG 当成"离线版的奖励引导")。整个目标退化成一个**监督式 [[flow-matching]] 损失**:免似然、任意 solver、只要干净图不要轨迹,比 FlowGRPO 快 3–25×。

## 它要解决的痛点
- **扩散的似然算不出来**([[diffusion-rl-likelihood-barrier]]):[[policy-gradient]]/[[ppo]]/[[grpo]] 都要模型对样本的概率,LLM 逐 token 现成,扩散只能靠昂贵的 ODE 概率流或 SDE 变分界近似。
- **FlowGRPO 那套绕法有代价**:把反向采样离散成多步马尔可夫过程(每步高斯就可算概率)→ 能套 GRPO,但①训练损失耦死一阶 SDE 采样器,用不了扩散默认的 ODE/高阶 solver;②只盯反向动态,丢掉对前向过程的忠实,模型可能退化成"级联高斯";③扩散重度依赖 [[classifier-free-guidance]],RL 里硬塞 CFG 变成又慢又繁的两模型优化。

## 核心贡献
- **前向过程做 RL**([[negative-aware-finetuning]]):洞察是"前向加噪只有一条,反向去噪有无数条",所以把策略优化放到前向 flow matching 上。给每个样本一个奖励 `r∈[0,1]`,定义正分布 `π⁺∝r·π_old`、负分布 `π⁻∝(1−r)·π_old`——高奖励样本进正堆、低奖励进负堆。
- **隐式改进方向 = 奖励版的 CFG**([[reinforcement-guidance]]):定理给出正负速度之差成比例 `Δ ∝ (v⁺−v_old) ∝ (v_old−v⁻)`,这个 `Δ` 就是该往哪走的强化引导信号,角色等同 CFG 的"条件−无条件",只是这里由奖励切出来。论文一句点睛:**CFG 本身就是一种"离线的"强化引导**;NFT 把它换成在线学出来的。
- **一个模型隐式装正负 + 监督损失**:单个 velocity 网络 `v_θ` 通过参数插值同时表示正负两副动态——`v_θ⁺=(1−β)v_old+β·v_θ`、`v_θ⁻=(1+β)v_old−β·v_θ`(两者对称于 `v_old`,相加=2v_old)。损失 `L=E[ r·‖v_θ⁺−v‖² + (1−r)·‖v_θ⁻−v‖² ]` 是**纯监督 flow matching**(不是 policy gradient),最优解 `v_θ*=v_old+(2/β)·Δ`。RL 信号靠 `r` vs `1−r` 的对比权重 + 隐式参数化自然揉进监督目标。
- **省 + 强**:免似然估计;数据可用**任意黑盒 solver**(ODE/SDE/高阶都行)采;**只存干净图**不用整条采样轨迹;训出一个 **CFG-free 的 omni-model**,反而超过开 CFG 的基线。
- 结果:SD3.5-Medium(2.5B,LoRA r32,512²)上,GenEval 0.24(无 CFG)→0.63(CFG)→FlowGRPO 0.95(5k+ 步)→**DiffusionNFT ~1.7k 步 0.94 / ~1k 步逼 0.98**,且 PickScore/HPSv2.1/Aesthetics/ImageReward 全面更高;**比 FlowGRPO 快 3–25×(墙钟)**;OOD 上超过更大的 SD3.5-Large、[[flux-1]]-dev。

## 关键概念 → 概念页
- [[negative-aware-finetuning]] · 核心:奖励切正负、前向 flow matching 上做 RL、单模型隐式参数化
- [[reinforcement-guidance]] · 正负速度之差 Δ = 改进方向;CFG = 离线版的它
- [[diffusion-rl-likelihood-barrier]] · 为什么扩散 RL 难 + FlowGRPO 离散反向的三个坑
- 复用:[[flow-matching]] 训练目标 · [[classifier-free-guidance]] 被重新诠释 · [[grpo]]/[[policy-gradient]]/[[ppo]] 对照的反向路线 · [[direct-preference-optimization]] 正负对比的近亲 · [[stable-diffusion-3-5]] 基座 · [[lora]] 微调 · [[flux-1]] OOD 对比

## 我的批注 / 疑问
- 一句话记牢:**反向去噪千条路、前向加噪只一条;在那唯一的前向上做 RL,似然问题、solver 限制、CFG 两模型一次性全绕开。正负样本之差就是该走的方向,RL 退化成一个加权的监督 flow-matching 损失。**
- 跟 [[direct-preference-optimization]] 是表亲:都靠"正负对比"出方向、都把 RL 折成类监督损失;但 DPO 在 LLM 的对数似然上做,NFT 在扩散的速度场上做,且正负是按连续奖励 `r` 软切不是成对偏好。
- "CFG = 离线强化引导"这个视角很值:解释了为什么 NFT 能用一个模型替掉 CFG 的两模型——CFG 的 cond−uncond 本就是一种固定的引导方向,NFT 把它换成随奖励在线更新的 Δ。
- 来源:arXiv 2509.16117 v1 HTML 全文(ICLR 2026);机制(前向 flow matching RL、π⁺/π⁻ 定义、隐式参数化 v_θ±、监督损失、SD3.5-M/LoRA r32、GenEval 曲线、3–25× 效率)已确证。
- 待查:多奖励设置下 β=0.1 + η_max=0.95 的软更新具体调度;omni-model 在更大基座(FLUX 级)上重训的成本;β 取值对"引导强度 vs 稳定性"的实测敏感度。
