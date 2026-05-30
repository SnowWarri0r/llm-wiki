---
name: clipped-surrogate-objective
type: concept
sources: [ppo]
updated: 2026-05-28
---

# Clipped Surrogate Objective · PPO 的核心一行 clip

## 一句话
不让新策略的概率比"老策略大太多 / 小太多" —— PPO 把这个约束**写进 loss 函数本身**, 一行 `torch.clamp` 干掉了 TRPO 那套复杂的 KL 约束 + 共轭梯度。

## 直觉 · 概率比值是策略距离的代理

要"限制新老策略别差太远", 有两种思路:

**TRPO 思路**: 算精确的 KL 散度 `KL(π_new ‖ π_old)`, 限制它 ≤ δ。理论漂亮但工程上要做共轭梯度 + 线搜索, 慢、复杂

**PPO 思路**: 直接看每个 action 的概率比值 `r = π_new(a|s) / π_old(a|s)`

- r = 1: 新老完全一样
- r = 1.5: 新策略把这个 action 的概率提了 50%
- r = 0.5: 新策略把这个 action 的概率降了 50%

**只要每个 action 的 r 都在 `[1-ε, 1+ε]` 范围内, 新老策略整体就不会差太远**. 这是一个对 KL 的粗暴但有效近似。

## 公式

```
r_t(θ) = π_new(a_t | s_t) / π_old(a_t | s_t)

L_CLIP = E_t [ min( r_t · A_t,  clip(r_t, 1-ε, 1+ε) · A_t ) ]
```

其中 `A_t` 是 [[advantage-function]] (这个 action 比 baseline 好多少)。`ε` 通常 0.2.

读这个公式的两个关键点:

### 当 A_t > 0 (这个 action 是好的)

- 我们想增加 P(这个 action), 也就是想让 r 变大
- 但 `clip(r, 1-ε, 1+ε)` 在 r > 1+ε 时变成常数 (1+ε)
- 所以 loss 在 r > 1+ε 之后变成常数 → **梯度为 0**
- **效果**: 想增加这个 action 概率 → OK, 但增加到比老策略大 20% 就停, 不让你贪
- 防止"看到一个好 action 就一次性 push 它的概率到天上"

### 当 A_t < 0 (这个 action 是坏的)

- 我们想减小 P(这个 action), 也就是想让 r 变小
- `clip(r, 1-ε, 1+ε)` 在 r < 1-ε 时变成常数 (1-ε)
- 所以 loss 在 r < 1-ε 之后变成常数 → **梯度为 0**
- **效果**: 想减小这个 action 概率 → OK, 但减小到比老策略小 20% 就停
- 防止"看到一个坏 action 就一次性 push 它的概率到 0"

### min 函数干啥的

`min(r · A, clip(r) · A)`: 取**更不利于增加 loss** 的那个。

- 当我们的更新是"善意"的方向 (好 action 增、坏 action 减): clip 起作用, 防止贪心
- 当 r 跑过了 clip 范围的"另一侧" (比如 r > 1+ε 但 A < 0): 让原 r·A 起作用, 还能修正
- 这个 `min` 设计让 clip 只在"该停的方向"停, 不阻碍"该修正的方向"

## 一张图就能看懂

x 轴: r_t (新老概率比)
y 轴: 单个 token 的 loss 贡献 L

**A > 0 的情况** (这个 action 是好的):
```
L
↑
|  - - - - - -  (clip 之后变常数, 梯度=0)
|       /
|      /
|     /
|    /
|   /
|  /
| /
+----·----·--------→ r
    1-ε  1+ε
```

**A < 0 的情况** (这个 action 是坏的):
```
L
↑
|  \
|   \
|    \
|     \
|      \
|       \  
| - - - -   - - - - - - -  (clip 之后变常数)
+----·----·--------→ r
    1-ε  1+ε
```

`clip` 在两边都"切平"loss, 让梯度在那一侧消失。**梯度消失就意味着 optimizer 不再继续推这个方向**, 等价于"软性的 trust region".

## Sample efficiency 暴涨的副作用

因为 clip 保证了 π_new 不会跑离 π_old 太远, **老数据没失效那么快**. 所以 PPO 可以**同一批 rollout 跑 K 个 epoch** (K=3~10):

```python
rollouts = collect_rollouts(π_old, env, n_steps=2048)

for epoch in range(K):                      # K=4 是常用值
    for batch in minibatches(rollouts):
        loss = ppo_clip_loss(π_new, batch)  # 用 π_new 算 loss
        loss.backward()
        optimizer.step()

π_old = π_new   # 这一轮收集结束, 更新老策略
```

Vanilla 策略梯度: 每批数据扔掉, K=1. PPO: K=4-10. **样本效率 4-10×**.

## 为什么这套粗暴的 clip 实际工程上够用

理论上 clip 只保证概率比有界, 不保证 KL 散度有界。但实际工程上:

1. **梯度被 clip 切平后, optimizer 自动停在边界附近** —— 即使 r 跑到 1.3 (ε=0.2 的边界外), 由于梯度=0, 下一步 r 不会继续涨
2. **多 epoch 训练里, 几个 epoch 之后所有 action 的 r 都自然分布在 [0.8, 1.2] 附近** —— 因为 loss 已经"鼓励"留在范围内
3. **跟现代深度学习的 Adam / minibatch SGD 完美匹配** —— 不需要任何特殊数值方法

**Bitter lesson 的迷你版**: 当你不知道精确解时, 粗暴近似+大算力反而赢精确解+小算力。

## 链接
- [[ppo]] · 这个 trick 的发源
- [[policy-gradient]] · 不加约束的原始版本, 步子大就崩
- [[advantage-function]] · A_t 是这个 trick 里的关键输入
- [[grpo]] · PPO 的简化变体, 沿用 clipped objective 但去掉 critic
