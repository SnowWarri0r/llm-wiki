---
name: advantage-function
type: concept
sources: [ppo]
updated: 2026-05-28
---

# Advantage Function · 跟基线比,不是看绝对值

## 一句话
"这一步赚了多少"比"这一步总共拿了多少"信号更稳定 —— **优势函数 = 实际回报 − 预期回报**, 让训练不会因 reward 整体偏移就乱掉。

## 直觉 · 为什么 raw return 不够好

策略梯度的原始版本用 **return** R_t (这一步之后的总 reward) 当 loss 的权重:

```
loss = -log π(a_t) × R_t
```

问题: **return 跟 action 没有直接因果关系**. 比如:

- 你在围棋里第一手下了一个不错的位置, R = +10 (最后赢了)
- 你在围棋里第一手下了一个**很烂**的位置, R = +10 (但后面救回来, 最后还是赢了)

这两种情况 R 都是 +10, 但**第一种 action 应该被鼓励, 第二种应该被惩罚**. Raw return 区分不了。

更糟的是: 如果环境 reward 偏移 (比如所有 reward 都加 100), policy gradient 会变得离谱:

- Raw return 偏移后: `loss = -log π(a) × (R + 100)` —— 100 这个偏移把所有 action 都强推, 不管好坏

## Advantage = 这步比平均好多少

定义:

```
A(s, a) = Q(s, a) - V(s)
```

- `Q(s, a)`: 在状态 s 选 action a 之后的预期 return
- `V(s)`: 在状态 s 不管选啥的平均预期 return
- `A`: 这个 action 比"我在这种局面下平均能拿多少" 好多少

**意译**: "在这个局面下, 选了这个 action 是赚了还是亏了?"

举例:
- 围棋开局: V(s) = 0.5 (双方对等)
- 你下了一手坏棋: Q(s, a) = 0.3 → A = -0.2 → 该惩罚
- 你下了一手好棋: Q(s, a) = 0.7 → A = +0.2 → 该鼓励
- 即使最后赢了 (R=+1), 那一手坏棋的 A 仍然是负的

**这就是 advantage 比 raw return 强的本质** —— 它**只看 action 的相对贡献**, 跟最终的 reward 偏移无关。

## 实际怎么估计 advantage

精确的 Q 和 V 我们都不知道, 都要估计。最常用的两种估计:

**TD (1-step Temporal Difference)**:
```
A_t = r_t + γ V(s_{t+1}) - V(s_t)
```
"这一步 reward 加上下一步的预期, 减去当前预期" —— bootstrap 估计

**MC (Monte Carlo, 跑完整 episode)**:
```
A_t = R_t - V(s_t)         # R_t 是这一步开始的实际累计 reward
```

**GAE (Generalized Advantage Estimation)** —— Schulman 2015, 现在 PPO 标配:
```
A_t = δ_t + (γλ) δ_{t+1} + (γλ)² δ_{t+2} + ...
其中 δ_t = r_t + γ V(s_{t+1}) - V(s_t)
```
TD 和 MC 之间插值, 用 λ 控制 bias-variance tradeoff. **λ=0 → TD, λ=1 → MC**. 实际常用 λ=0.95.

## Actor-Critic 架构

要算 advantage, 你需要一个 V(s) 的估计器 —— 这就是 **critic** (评论员).
要选 action, 你需要一个 π(a|s) —— 这就是 **actor** (演员).

两个网络一起训:

```python
# Actor: 输出 action 分布
actor_net: state → action_distribution

# Critic: 输出 state 的 V 估计
critic_net: state → V_estimate

# 训练循环
for rollout in rollouts:
    states, actions, rewards = rollout
    
    V_estimates = critic_net(states)
    advantages = compute_gae(rewards, V_estimates)
    
    # actor loss: 策略梯度 (PPO 的 clipped 版)
    actor_loss = ppo_clip_loss(actor_net, states, actions, advantages)
    
    # critic loss: 监督回归到实际 return
    critic_loss = (V_estimates - returns).pow(2).mean()
    
    # entropy bonus: 鼓励探索, 防过早笃定 (见 entropy-regularization)
    entropy = action_dist.entropy().mean()
    
    loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy   # 完整三项
    loss.backward()
```

**Actor 学怎么选, critic 学评估当前局面好坏**. 互相配合. 注意完整的 PPO loss 是**三项**: clip 策略项 + 价值回归项 + 熵项 —— 少了第三项策略容易过早确定化, 详见 [[entropy-regularization]].

PPO / TRPO / A3C / SAC 全都是 actor-critic 结构。GRPO 是个例外 —— 它**干掉了 critic**, 改用一组采样的相对得分直接当 advantage (省一个网络的开销, 这是 DeepSeek GRPO 的核心简化).

## Reward 偏移不变性 (advantage 的关键性质)

如果环境的 reward 整体加一个常数 C, V 也跟着变 (V_new = V_old + C/(1-γ)). **A 不变**.

意义: 你的训练**对 reward 的绝对值不敏感, 只对 reward 的相对差异敏感**. 这让 hyperparameter 调起来方便很多.

跟监督学习里"输入做 normalize"是同一回事: **去除无关的整体偏移, 只保留有信息的相对值**.

## 链接
- [[rl-for-llm-people]] · RL 术语打底 (state/action/分布/loss 走势)
- [[policy-gradient]] · 它的 loss 权重就是 advantage
- [[actor-critic]] · 提供 V 估计的 critic + actor 的双网络结构
- [[gae]] · 用 λ 插值 TD 和 MC 来估优势的标配方法
- [[entropy-regularization]] · 完整 loss 的第三项
- [[clipped-surrogate-objective]] · PPO 的 clip 作用在 A_t 上
- [[ppo]] · 用 advantage 配合 clip 训练
- [[grpo]] · 不要 critic, 用组内相对得分当 advantage
