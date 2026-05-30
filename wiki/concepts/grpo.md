---
name: grpo
type: concept
sources: [fish-speech-s2-pro, ppo]
updated: 2026-05-28
---

# GRPO · Group Relative Policy Optimization

## 一句话
PPO 的简化版：不用 value network，用**同 prompt 一组采样**之间的相对 reward 当 advantage。

## 直觉
PPO 训 LLM 的痛点：要养一个 value network（critic）单独学每个状态的价值，跟 policy 一样大，训练成本翻倍且不稳定。

GRPO 砍了 critic，做法是：
- 对同一个 prompt 一次性采样 **G 条响应**
- 算每条的 reward
- 用组内 mean / std 标准化 reward → 当 advantage

类比：考试不需要"绝对分数模型"，只要看你在班里的排名相对位置就够了。

## 怎么做的
```
for prompt in batch:
    sample G responses {r_1, ..., r_G}
    rewards = [R(r_i) for r_i in responses]
    advantages = (rewards - mean(rewards)) / std(rewards)
    loss = clipped_pg_loss(advantages) + KL_penalty(policy || ref_policy)
```

- **无 critic** → 只训 policy，省内存省计算
- **组相对** → 自动消除 reward scale 漂移
- **KL 约束** → 限制 policy 偏离参考模型太远，防止跑偏

来源：DeepSeek-Math 的 GRPO 论文（也用在 DeepSeek-R1 训练里）。

## fish-speech S2 怎么用
- 不只一个 reward —— **多维 reward**：语义准确（ASR WER）+ 指令遵循（情感 tag 命中）+ 音色相似（SIM）+ 声学偏好（人评 / proxy 模型）
- **Reward model = 数据清洗 / 标注用的同一套模型** → 解决传统 RLHF 的 distribution mismatch：reward model 训在另一份数据上 vs policy 训在 pre-train 数据上，那条 gap 消失

## 跟 TML 的关系
TML 也提到 RL 训练 → bitwise determinism 是为它服务的。[[bitwise-determinism]] 缺失会让 GRPO / PPO 这类 RL loop 不稳定甚至发散，因为训练时算梯度的 kernel 和推理时采样的 kernel 数值不一致 → 学到的 policy 偏离 sampler 的真实行为分布。

## 链接
- [[rl-for-llm-people]] · 看不懂 RL 术语先读这个打底
- [[fish-speech-s2-pro]] · 这里 RL 对齐
- [[bitwise-determinism]] · RL 训练稳定性前提
- [[dual-ar]] · GRPO 在 Dual-AR 之上做 post-training
