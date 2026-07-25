---
name: dapo
type: concept
sources: [grpo, ppo]
updated: 2026-07-22
---

# DAPO · Decoupled Clip and Dynamic Sampling Policy Optimization

## 一句话
DAPO 是面向长 CoT 在线 RL 的 GRPO 系统配方：放宽上侧 clip 保探索、动态过滤零梯度题、按有效 token 汇总 loss，并把超长截断的硬惩罚改成平滑信号。

## 四项修改各治一个问题

| 修改 | 看到的问题 | 实际改法 |
|---|---|---|
| Clip-Higher | 低概率探索 token 很难提高，熵过早坍缩 | clip 从对称 `[.8,1.2]` 改为示例中的 `[.8,1.28]` |
| Dynamic Sampling | 一题全对 / 全错时组相对 advantage 全 0 | 过采样并过滤组准确率为 0 或 1 的 prompt |
| Token-Level PG Loss | 每条回答先平均会摊薄长回答 token | batch 内所有有效 token 的 loss 一起求平均 |
| Overlong Reward Shaping | 被截断不等于整段推理都错，硬罚带来 reward 噪声 | 先屏蔽截断样本，再用接近上限时逐渐增强的软惩罚 |

## 为什么 Clip-Higher 只放宽上侧

重要性比率 \(\rho_t=\pi_\theta/\pi_{\mathrm{old}}\)。正 advantage 希望 \(\rho_t\) 变大，普通 PPO 在 1.2 封顶。DAPO 论文实验把上界放到 1.28，让原本概率很低但有价值的探索 token 多一点上升空间；下界仍为 0.8，避免把低概率 token 进一步过度压低、缩死探索空间。

## Dynamic Sampling 不是“丢掉难题”

它过滤的是这一轮采样中 \(G\) 条回答全错或全对的组，因为 \(R_i-\operatorname{mean}(R)=0\)，当前 batch 里没有相对方向。下一轮策略变化后，同一道题仍可能重新出现有效分歧。它的目标是让每个训练 batch 保持足够多非零梯度组，而不是断言这些题永远没价值。

## 跟 Dr.GRPO 的关系

两者都注意到“每条回答先除以自己的长度”会改变 token 权重：[[dr-grpo]] 用固定生成上限作分母；DAPO 用整个 batch 的有效 token 总数作分母。它们方向相近，但缩放和 batch 权重并不完全相同。DAPO 还额外处理探索、零梯度采样和截断奖励。

## 论文结果要按口径读

DAPO 报告 Qwen2.5-32B 在 AIME 2024 上从 naive GRPO 的 30 分逐项提升到 50 分，并使用 16 条 / prompt、16,384 期望最大长度和 4,096 soft-punish cache。它证明这套组合在该系统有效，不等于把其中任一技巧移到任意任务都能复制相同增益。

## 来源与链接

- [DAPO 技术报告](https://arxiv.org/abs/2503.14476)
- [[ppo-grpo-gspo]] · 完整算法地图和公式
- [[grpo]] · DAPO 的基础骨架
- [[dr-grpo]] · 另一种去除长度 / 难度偏置的修正
- [[gspo]] · 把重要性比率和 clip 提到序列级
