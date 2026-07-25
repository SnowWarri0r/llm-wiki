---
name: gspo
type: concept
sources: [qwen3-asr, grpo, ppo]
updated: 2026-07-21
---

# GSPO · Group Sequence Policy Optimization

## 一句话
GSPO 沿用 GRPO 的组相对 advantage，但让整条回答共用一个长度归一的新旧策略比率，并在序列级做 clip；它修的是更新粒度，不是 reward 的来源。

## GRPO 的 token 级比率并非“算错”，问题是粒度错位

在 outcome RL 中，一条回答通常只拿一个最终 reward，组相对 advantage `A_i` 也属于整条回答。但 GRPO 沿用 PPO，对每个 token 分别计算：

```text
ρ_i,t = π_θ(y_i,t | x,y_i,<t) / π_old(y_i,t | x,y_i,<t)
```

然后每个 `ρ_i,t` 各自 clip。于是同一条好回答里，某些 token 可能按 `1.2` 奖励，另一些按 `0.8` 或未截断值更新。若训练和推理引擎精度不同，或 MoE 路由让局部 log-prob 更敏感，个别 token 的比率波动会改变 clip 决策。

GSPO 的思路是：既然奖惩对象是一条回答，就让更新幅度也属于整条回答。

## 序列比率公式逐项拆开

```text
s_i(θ) = [π_θ(y_i|x) / π_old(y_i|x)]^(1/|y_i|)
       = exp((1/|y_i|) Σ_t log ρ_i,t)
```

- `y_i`：同一 prompt 的第 `i` 条完整回答。
- `π(y_i|x)`：整条回答的似然，即各 token 条件概率连乘。
- `s_i`：这条回答唯一的序列级重要性比率。
- `|y_i|`：回答 token 数。
- `1/|y_i|`：长度归一；把连乘后的总比率拉回“平均每 token”尺度。
- `exp(mean(log ρ))`：与上式完全等价，也是 token 比率的几何平均，数值计算时更稳定。

GSPO 最大化：

```text
L = E[(1/G) Σ_i min(s_i A_i, clip(s_i,1−ε,1+ε) A_i)]
```

`A_i` 仍可按 [[grpo]] 从同题多回答 reward 算出。变化只在 `s_i`：整条回答一起放大、缩小或被 clip。

## 四个 token 的手算

若 token 比率为 `[1.10, 1.05, .90, 1.25]`：

```text
s = (1.10 × 1.05 × .90 × 1.25)^(1/4)
  = 1.299375^(1/4)
  ≈ 1.0677
```

不做 `1/4` 次方时，总比率是 `1.299375`，仅仅因为序列更长就更容易远离 1。长度归一以后，`1.0677` 可解释为平均每个 token 约提高 6.77%。若 `A_i=1`、clip 区间 `[.8,1.2]`，这条回答的目标贡献就是 `1.0677`；不会只因末 token 的 `1.25` 就让局部单独触发上侧 clip。

这不是说异常 token “被证明是噪声”，而是用全序列的几何平均把局部波动合成一个共同更新尺度。好处是稳定，代价是失去逐 token 区分更新幅度的自由度。

## 为什么对 MoE 特别重要

MoE 每个 token 只激活部分专家。训练引擎与 rollout 引擎在精度、batch 划分或路由实现上的细小差异，可能使少数 token 的专家选择和 log-prob 更敏感。token 级 ratio / clip 会把这种局部差异直接变成不同的梯度截断；序列级聚合对此更宽容。Qwen 团队报告 GSPO 稳定了此前不稳定的 MoE RL，并可去掉 Routing Replay 等额外机制。

这是论文和官方技术报告给出的机制解释与实验结果，不应外推为“所有 MoE 训练都必须用 GSPO”。

## 它没有改什么

- 没有改 reward 的来源：仍可用规则或 reward model。
- 没有自动去掉 critic：GSPO 论文沿用 group-relative advantage，但序列级 ratio 本身也可与别的 advantage 估计结合。
- 没有解决全对 / 全错组的零 advantage；那是 [[dapo]] Dynamic Sampling 处理的问题。
- 没有自动去掉 GRPO 的标准差 / 长度偏置；可另行结合 [[dr-grpo]] 式修正。

## 来源与链接

- [GSPO 论文](https://arxiv.org/abs/2507.18071)
- [Qwen 官方中文解读](https://qwenlm.github.io/zh/blog/gspo/)
- [[ppo-grpo-gspo]] · 与 PPO / GRPO / Dr.GRPO / DAPO 放在同一数值例子中比较
- [[grpo]] · 它继承的组相对 advantage
- [[qwen3-asr]] · GSPO 在语音后训练中的使用
