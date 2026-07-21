---
name: ppo
type: paper
source: https://arxiv.org/abs/1707.06347
upstream: https://arxiv.org/abs/1707.06347
ingested: 2026-05-28
updated: 2026-07-21
authors: [John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov]
year: 2017
---

# PPO · Proximal Policy Optimization

## 一句话
PPO 允许用同一批旧策略 rollout 做多轮小批量更新，同时用新旧动作概率比率的 clip 限制单轮策略变化；它把 TRPO 较复杂的受约束优化，换成了能直接交给 Adam 的代理目标。

## 它要解决什么

策略梯度用已采样轨迹判断哪些动作应该更常出现。但 rollout 来自更新前的 `π_old`，训练时改的是 `π_θ`。如果新策略一步走得太远，旧数据对新策略的代表性快速下降，反复使用这批数据就会产生不稳定的大更新。

TRPO 显式限制新旧策略的 KL 距离，但需要二阶近似、共轭梯度和线搜索。PPO 的 clipped 版本把“别走太远”直接写进目标函数，能用普通 minibatch SGD / Adam 优化。

## 核心公式逐项解释

```text
L_CLIP(θ) = E_t[min(ρ_t(θ) A_t,
                    clip(ρ_t(θ),1−ε,1+ε) A_t)]

ρ_t(θ) = π_θ(a_t|s_t) / π_old(a_t|s_t)
```

- `s_t`：第 `t` 步的状态；LLM 中是 prompt 加已生成前缀。
- `a_t`：这一步实际采到的动作；LLM 中是下一个 token。
- `π_old`：收集 rollout 时冻结的旧策略。
- `π_θ`：当前正在训练的新策略，`θ` 是模型参数。
- `ρ_t`：新旧策略给同一已采动作的概率比。大于 1 表示新策略提高了它的概率。
- `A_t`：advantage，表示这个动作比当前状态的平均预期好多少；正数应提高概率，负数应降低。
- `ε`：clip 宽度，论文常用 `.1` 或 `.2` 一类的小值。
- `E_t`：对采样时间步求平均。

若 `A_t>0` 且 `ρ_t` 已超过 `1+ε`，继续提高这个动作概率不再增加代理目标；若 `A_t<0` 且比率跌破 `1−ε`，继续压低也不再获益。`min` 会在不同 advantage 符号下自动取到更保守的一边。

clip 截断的是**目标函数中的收益**，不是直接把参数、概率或梯度硬裁到某个区间；因此 PPO 仍应监控实际 KL，clip 也不构成严格的 KL 上界。

## PPO 不只是一条 clip

常见 PPO 是 actor-critic 系统：

1. actor `π_θ` 选择动作。
2. critic `V_φ(s_t)` 预测从当前状态继续的未来回报。
3. [[gae]] 用多步 TD 误差估计 `A_t`。
4. actor 优化 clipped policy objective。
5. critic 用 return 回归 value；另加 [[entropy-regularization]] 保持探索。

LLM RLHF 还常加入相对冻结 reference policy 的 KL 惩罚，防止模型为追 reward 远离原有语言分布。critic、reward model、reference model 是三个不同角色。

## 为什么能复用同一批数据

普通 on-policy policy gradient 往往更新一次就丢掉 rollout。PPO 对同一批数据跑多个 minibatch epoch；训练中 `π_θ` 逐渐离开采样时的 `π_old`，`ρ_t` 追踪这段变化，clip 抑制过度利用。它不能让旧数据永久有效：epoch 太多时，大量 token 都进入 clip 区间，继续训练既偏离 on-policy，又得不到有用目标增益。

## 到 LLM：token 就是 action

在自回归生成里：

```text
state  s_t = (prompt, 已生成 token y_<t)
action a_t = 下一个 token y_t
policy π   = LLM 的 next-token 概率分布
episode    = 一条完整回答
```

InstructGPT 明确使用 PPO 做 RLHF，是 PPO 进入大模型后训练的代表案例。后来的模型是否使用哪种算法，应以公开技术报告为准，不能仅凭行业惯例推断。

## GRPO / Dr.GRPO / DAPO / GSPO 跟 PPO 的关系

它们共享“在线采样 + advantage 加权 + 限制策略变化”的骨架，但修改不同部位：

| 算法 | 相对 PPO 的主要变化 |
|---|---|
| [[grpo]] | 去掉 critic，用同题多回答的组内相对 reward 估 advantage；仍保留 token 级 ratio 和 clip |
| [[dr-grpo]] | 去掉 GRPO 的组标准差归一化与逐回答长度归一化，修题目难度和长度偏置 |
| [[dapo]] | 为长 CoT 增加非对称 clip、动态采样、token 级 loss 汇总和超长软惩罚 |
| [[gspo]] | advantage 可继续组内互比，但把 ratio 与 clip 从 token 级提升到序列级 |

完整公式、同一组数字手算和选型见 [[ppo-grpo-gspo]]。

[[direct-preference-optimization]] 则是另一条路线：使用离线偏好对直接优化策略，不进行 PPO 式在线 rollout。它不是“更先进的 PPO”，适用数据和能力边界不同。

## 论文贡献与边界

- PPO 原论文提出 clipped surrogate 和 adaptive KL penalty 两个版本；工程界更常提 clipped 版本。
- 论文在模拟机器人、Atari 等任务上比较了样本复杂度和实现便利性；它不是 LLM 论文。
- PPO 的稳定性来自目标、advantage 估计、value loss、熵、batch、学习率等整套配方，不能把所有效果归因于一行 `clip`。
- LLM 长序列、终局 reward、大模型 critic 成本和训推引擎差异，催生了后续 GRPO 系修改；这些不是原 PPO 论文已经解决的问题。

## 链接

- [[ppo-grpo-gspo]] · PPO 家族完整地图
- [[policy-gradient]] · 从 `∇logπ · reward` 开始
- [[clipped-surrogate-objective]] · clip 的正负 advantage 四种情况
- [[advantage-function]] · baseline 为何降方差
- [[actor-critic]] · policy 与 value 两套职责
- [[gae]] · 多步 advantage 估计
- [[rlhf]] · PPO 在语言模型对齐中的使用
- [[rl-for-llm-people]] · 用 LLM 术语补齐 RL 基础
