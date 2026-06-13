---
name: ppo
type: paper
source: https://arxiv.org/abs/1707.06347
upstream: https://arxiv.org/abs/1707.06347
ingested: 2026-05-28
authors: [John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov]
year: 2017
---

# PPO · Proximal Policy Optimization

## 一句话
强化学习里**最关键也最容易翻车**的一件事是更新步子的大小 —— PPO 用一行 `clip` 把"别走太远"这个约束硬塞进 loss 里, **简单到能在 200 行代码内复现, 又稳到撑起了 ChatGPT 的对齐**。

## 它要解决的痛点

强化学习的基本设定: agent 跟环境互动, 每步选一个 action, 拿到 reward, 目标是让长期累计 reward 最大。**策略** π(a|s) 告诉 agent "在状态 s 下选 action a 的概率"。训练就是调 π 的参数 θ, 让好的 action 概率上升、坏的下降。

**策略梯度** (policy gradient) 是最直接的训法: 算梯度 → 走一步 → 算梯度 → 走一步。但它有个致命缺陷 —— **步子大小决定生死**:

- 步子太小 → 训得太慢, 一个游戏要跑几亿帧
- 步子太大 → 一更新 π 就跑偏, 收集的数据立刻不能用, 整个学习崩盘

具体崩在哪? 因为你收集 rollout 时用的是**老的策略 π_old**, 算 gradient 用的是**新的策略 π_new**。如果 π_new 离 π_old 太远, 那些 rollout 描述的"在 π_old 下哪些 action 好"对 π_new 就完全不适用了。**数据失效, 训练崩盘**。

之前的解法是 **TRPO** (Schulman 2015): 加一个 KL 散度约束 `KL(π_new ‖ π_old) ≤ δ`, 强制每步不能跑太远。理论漂亮, 但工程上要做共轭梯度 + 线搜索, 复杂、慢、跟现代深度学习框架不亲。

**PPO 的回答**: 不用 KL 约束, 不用共轭梯度, 就一行 `torch.clamp` —— 把新老策略的概率比值卡在 `[1-ε, 1+ε]` (ε 一般 0.2) 之间。**简单粗暴, 效果跟 TRPO 接近, 且能跑 Adam**.

## 核心贡献

1. **Clipped surrogate objective** —— PPO 的核心。把"新老策略别差太远"这个约束**直接写进 loss**, 不需要拉格朗日乘子, 不需要 KL 约束。
   
   $$L^{CLIP}(\theta) = \mathbb{E}_t \left[ \min(r_t(\theta) A_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t) \right]$$
   
   其中 $r_t = \pi_{new}(a_t|s_t) / \pi_{old}(a_t|s_t)$ 是新老策略概率比, $A_t$ 是优势函数

2. **Sample efficiency 大幅提升**: 同一批 rollout 数据可以**反复跑 K 个 epoch** (论文用 K=3-10), 不像 vanilla 策略梯度只能用一次扔掉。因为 clip 保证了 π_new 不会跑太远, 所以老数据还能用

3. **跟现代深度学习无缝集成**: 用标准 Adam 优化器 + minibatch SGD, 不需要任何特殊数值方法, 一个 PyTorch programmer 一下午就能复现

4. **跨任务的鲁棒性**: 同一套超参数在 MuJoCo 连续控制、Atari 离散控制、Roboschool 多任务上都能跑得动 —— 这是 RL 算法少见的"开箱即用"

## 跟 LLM 的关系

PPO 在 LLM 圈被**疯狂使用**的地方是 [[rlhf]] (Reinforcement Learning from Human Feedback):

- **InstructGPT** (OpenAI 2022): 用 PPO 让 GPT-3 学会跟人类偏好对齐, 直接造就了 ChatGPT
- **GPT-4 alignment**: PPO 是核心
- **Claude / Llama / Qwen / DeepSeek 的 chat 模型**: PPO 或其变种 (DPO / GRPO) 几乎都用

你已经在 [[fish-speech-s2-pro]] 里见过 [[grpo]] —— **GRPO 是 PPO 的简化版本**, DeepSeek 2024 提出, 干掉了 PPO 里的 value network, 用一组样本的相对得分直接当 advantage。本质还是 PPO 那套思想。

## 关键概念 → 概念页链接

- [[policy-gradient]] · 策略梯度, RL 的基础
- [[clipped-surrogate-objective]] · PPO 的核心创新 (一行 clip)
- [[advantage-function]] · 比 raw reward 信号更稳的"超出预期多少"
- [[actor-critic]] · PPO 跑在其上的双网络结构 (clip 只是 actor 那半)
- [[gae]] · 把优势算得又稳又准的 λ 插值法 (工程上比 clip 还关键)
- [[entropy-regularization]] · 完整 loss 的第三项, 防过早笃定
- [[rlhf]] · PPO 在 LLM 端的杀手级应用
- [[grpo]] · PPO 的后继简化版, 你已经熟悉的

## 我的批注 / 疑问

- **PPO 真正的价值不在数学**, 在工程稳定性。同期还有 ACER、A3C、ACKTR 等算法, 论文里说自己"on par" with state-of-the-art, 但**实际工程界几乎都选了 PPO**, 因为它最稳、最少需要调参。这跟 ResNet 在 CNN 里、Transformer 在 NLP 里的地位类似 —— "不是最聪明, 是最能 work"
- **clip 这个 trick 看起来朴素**, 但隐含的设计哲学是: **当你不知道精确解时, 给一个粗暴但够用的近似**。TRPO 是精确解 (KL 约束 + 求精确 step size), PPO 是粗暴近似 (clip)。**结果工程上反而是粗暴的赢了**, 因为它简单到 (1) 没 bug (2) 能跑大数据 (3) 能跟现代优化器组合。一个迷你版的 bitter lesson
- 现在 (2024-2025) PPO 在 LLM 端逐渐被 **DPO** (Direct Preference Optimization) 替代 —— DPO 用对比学习的思路直接 skip 掉 reward model, 训练更稳。但 DPO 跟 PPO 不是冲突, 是接力 —— 大模型 alignment 用 DPO 多, 但需要 online 探索的场景 (比如 GRPO 在 reasoning 训练) 还是 PPO 系
- 一个误解: 很多人以为 "PPO = clipped objective". 实际上 PPO 论文给了两个版本, "clipped" 和 "KL penalty", **clipped 版本简单且效果稍好, 所以工程界几乎都用 clipped**。论文里的 KL penalty 版本基本没人提
- 工程坑: PPO 训练时 "advantage 怎么算" 比 "clip" 本身重要得多。GAE (Generalized Advantage Estimation) 是 PPO 的标配, 但调好 λ 参数 (一般 0.95) 需要经验
- **"PPO = clip" 是只看了一半**: clip 是 actor 那半, 但 PPO 跑在 [[actor-critic]] 结构上 —— 还有个 critic 在用监督回归估 V, [[gae]] 拿它算优势, 完整 loss 是**三项**(clip 策略项 + 价值回归项 + [[entropy-regularization]] 熵项), 不是论文公式里那一个 $L^{CLIP}$。少了 critic 优势没法算, 少了熵项策略容易过早确定化 —— 自己动手训过才会发现, clip 只是冰山一角
- 训练实战体感 (论文不写但一跑就懂): ① RL 的 `loss` 不代表学得好坏 (跟监督学习直觉相反), 要看 reward 走势; ② `explained_variance` 是 critic 的成绩单 (0→1 越准); ③ 奖励数值太大会淹没熵奖励 → 熵秒崩 → 策略躺平, 所以要奖励归一化; ④ on-policy 怕经验单一, 多开并行环境收集去相关的数据; ⑤ 没收敛的策略别用 deterministic (argmax) 评估, 会低估它 —— 该用随机采样
- 疑问: PPO 的 KL 散度约束做不到精确边界 —— `clip(r, 1-ε, 1+ε)` 只保证概率比值有界, 但不保证 KL 有界。**为什么这种"近似 trust region" 反而工程上够用**? 看起来跟梯度下降的"局部线性近似"是一脉相承的: 在小邻域内, 近似就足够准
