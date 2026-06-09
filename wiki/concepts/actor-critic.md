---
name: actor-critic
type: concept
sources: [ppo]
updated: 2026-06-09
---

# Actor-Critic · 一个动手, 一个打分

## 一句话
一个网络管"做什么"(actor), 一个管"这局面值多少"(critic), critic 算出的"实际比预期好多少"反过来教 actor —— PPO 就跑在这套结构上。

## 直觉 · 为什么光有 actor 不行

只有 actor (纯 [[policy-gradient]]) 的训法是: 做完一整局, 看总分, 总分高就把这局所有动作都调得更可能。问题是**总分里全是噪声** —— 你可能开局走了一步臭棋, 但后面运气好救回来赢了, 这步臭棋也跟着被表扬。

critic 就是来当这个"基线"的。它专门估一个数: **"以我现在的水平, 站在这个局面, 接下来大概能拿多少分?"** 有了这个"预期", 就能算 actor 每一步到底是**超出预期还是低于预期**(这就是 [[advantage-function]]):

```
优势 = 实际拿到的  −  critic 预期的
```

超出预期 → 这动作调得更可能; 低于预期 → 压低。**critic 不碰手柄, 只在旁边点评"这一波比我想的强/弱", actor 照着点评改打法。** 像球员(actor)和教练(critic): 教练不上场, 但球员靠他的反馈进步。

## 怎么做的

**结构**: 现代实现里 actor 和 critic 常**共用一套特征提取器**(比如同一个 CNN 把画面看懂, 压成一串特征), 然后**分两个头**:

```
画面 → [共享 CNN] → 512 个特征 ┬→ actor 头:  → 各动作的概率
                               └→ critic 头: → 一个估值数字
```

有意思的是: 整个网络几乎所有参数都在那个"看懂画面"的 CNN 里, **两个头各自只是一层薄薄的线性映射**(几千个参数)。难的是感知, 决策反而简单。

**critic 怎么越训越准**: 它干的其实就是**监督回归**, 跟普通 fine-tune 一个套路 —— 预测一个数, 跟实际发生的结果比, 用平方误差往回改:

```python
critic_loss = (critic预测的V − 实际拿到的return)² 
```

唯一不同: 标准答案不是人标的, 是 **agent 自己玩出来的真实回报**。还有个巧妙之处叫 bootstrapping —— 它常拿"自己对下一步的估计"当部分答案来训自己, 像揪着鞋带往上提; 但每步都掺了一点真实 reward 当硬锚, 所以会慢慢被现实拽准。它准到什么程度, 用 `explained_variance` 这个指标看 (0=瞎猜, 1=神准)。

**关键区分 · 模型 vs 算法**: actor-critic 是**网络**(被训练的权重), [[ppo]] 是**训练它的算法**(怎么改这些权重的规程, 本身几乎没有参数)。同一个 actor-critic 网络, 你换 A3C / SAC / PPO 来训都行。训练完拿去用的时候, **算法功成身退, 只剩网络在跑**。

## 代码出处

stable-baselines3 `ActorCriticPolicy` —— `policy.pi_features_extractor` 与 `vf_features_extractor` 默认 `share_features_extractor=True` (同一个对象), 上面接 `action_net` (→ 动作) 和 `value_net` (→ 估值)。critic 的回归 loss 见 `ppo.py` 里 `value_loss = F.mse_loss(returns, values)`。

## 链接
- [[advantage-function]] · critic 提供"预期", 实际减预期 = 优势
- [[gae]] · 把"实际 − 预期"算得又稳又准的具体方法
- [[entropy-regularization]] · actor 的 loss 里还会加一项熵, 防它过早笃定
- [[policy-gradient]] · 只有 actor 的原始版, 噪声大
- [[ppo]] · 训练这个 actor-critic 的算法
- [[grpo]] · 反过来, 干掉 critic, 用一组样本相对得分代替
