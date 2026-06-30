---
name: policy-gradient
type: concept
sources: [ppo, diffusionnft]
updated: 2026-05-28
---

# Policy Gradient · 策略梯度

## 一句话
跟监督学习"猜对答案给奖、猜错给罚"不同, 强化学习只能拿到一个迟来的 reward 信号 —— 策略梯度把这个 reward **当成 loss 的"梯度乘子"**, 让模型自己悟出"做这个 action 是该多还是该少做"。

## 直觉 · 跟监督学习的根本区别

**监督学习**: 你给一张图, 标签是 "猫"。模型预测 "狗" → loss 高 → 梯度告诉模型 "下次这种图概率往猫挪"。**直接、即时、明确**。

**强化学习**: 你打游戏。当前看到屏幕 (state), 你按了 "↑" (action), 后来你赢了 (reward = +10)。但 reward 是**这一整局**的, 不是这一步的。你怎么知道 "按↑" 是好动作还是 "因为后面瞎按瞎按反正赢了"?

更糟: 没人告诉你 "标准答案" (优秀玩家会按啥)。你只能通过自己玩 → 看结果 → 调整策略。

**策略梯度的核心想法**: 把策略 π(a|s) 直接当成可微分的函数 (神经网络), 然后用 reward 当 "loss 的方向":

- 这局赢了 → 这局选过的所有 action 的概率都"升一点"
- 这局输了 → 这局选过的所有 action 的概率都"降一点"

**奇怪的是这个粗暴方法竟然 work** —— 因为如果某个 action 在赢的局里出现得多, 那它平均被"升"的次数就多于"降"; 反之亦然。**统计上自然区分了好坏 action**。

## 数学表达 (不重要, 看个意思就行)

策略梯度定理:

```
∇ J(θ) = E [ Σ_t ∇ log π(a_t | s_t; θ) · R_t ]
```

读法:
- `J(θ)` 是目标 (期望总 reward)
- `∇ J(θ)` 是参数 θ 该怎么调
- `π(a_t | s_t; θ)` 是策略, 你给状态它给 action 概率分布
- `∇ log π(...)` 是 log 概率的梯度 (跟分类的 cross-entropy 是同一个 trick)
- `R_t` 是这一步之后的总 reward

**意译**: "在状态 s_t 选了 a_t 之后总收益是 R_t, 就把 'log P(选 a_t)' 朝 R_t 的方向推"。R_t 高 → 推大概率, R_t 低 → 推小概率。

## 实现起来就是一行代码

```python
log_probs = policy(states).log_prob(actions)   # (T,)
returns = compute_returns(rewards)              # (T,)
loss = -(log_probs * returns).mean()            # 注意负号 (我们要最大化)
loss.backward()
optimizer.step()
```

跟监督学习的 cross-entropy loss 几乎一模一样, **唯一区别是 label one-hot 换成了 reward 数值**。这就是策略梯度。

## 为啥它脆弱 · 步子大小决定生死

策略梯度的**致命问题**: 步子太大就崩。

具体的崩盘场景:

1. 一局打完, 算 gradient, 走一步 → policy 改了
2. 但你之前收集的数据是用**老 policy** 跑出来的
3. 如果新老 policy 差太多, 那些数据就**不再代表新 policy 的真实行为**
4. 你拿着不准的数据继续算梯度, 越调越偏
5. 几步之后 policy 完全跑飞, 训练崩盘

这是为什么 vanilla policy gradient 在实际任务上几乎**不能用** —— 不是数学错, 是**数据消费速度跟不上策略变化速度**。

后续所有 RL 算法 (TRPO / PPO / GRPO / DPO) 都是在解这个问题:

- TRPO: 加 KL 约束精确限制每步
- PPO: clip 概率比值, 粗暴但够用
- GRPO: PPO 的简化版, 同时干掉 critic

## 跟监督学习的 cross-entropy 类比

如果你已经熟悉 cross-entropy, 策略梯度就是它的"加权版":

| 监督学习 | 策略梯度 |
|---|---|
| `loss = -log p(true_label)` | `loss = -log π(action) × return` |
| label 来自人工标注 | "label"是自己采样的 action, "权重"是 reward |
| 每个样本权重相同 | 每个 (s, a) 样本权重 = 该回合的 return |
| 数据 i.i.d. 随机收集 | 数据是 policy 自己生成的 → 数据分布跟着 policy 变 |

最后一行是最大的差别 —— **数据分布跟 policy 耦合**, 这是 RL 难训的根本原因。

## 链接
- [[rl-for-llm-people]] · 用 LLM 自回归把这套术语翻译成你已会的东西
- [[ppo]] · 在策略梯度基础上加 clip 防崩
- [[clipped-surrogate-objective]] · PPO 解决步子问题的方案
- [[advantage-function]] · 把 raw return 换成"超出基线多少"的稳定信号
- [[grpo]] · PPO 的简化变体
- [[rlhf]] · 策略梯度在 LLM 训练里的杀手级应用
