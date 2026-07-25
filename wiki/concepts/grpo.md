---
name: grpo
type: concept
sources: [fish-speech-s2-pro, ppo, krea-2, diffusionnft]
updated: 2026-07-21
---

# GRPO · Group Relative Policy Optimization

## 一句话
GRPO 保留 PPO 的“新旧概率比率 + clip”，但不再训练 critic；它对同一道题采样一组回答，用各回答相对组均值的得分作为 advantage。

## 它真正替换的是哪一块

PPO 通常用 critic `V(s)` 估计“写到这里，最终大概得多少分”，再从实际回报中减掉这个预期。GRPO 把这位过程预测员换成同题组内统计：

```text
PPO:  A_t ≈ return_t − V(s_t)          # V 是要训练的 critic
GRPO: A_i = (R_i − mean(R_1...R_G)) / std(R_1...R_G)
```

- `G`：同一个 prompt 采样的回答数。
- `R_i`：第 `i` 条完整回答的 reward。
- `mean` / `std`：这组 reward 的均值和标准差。
- `A_i`：第 `i` 条回答的组相对 advantage。结果奖励场景下，这条回答的所有 token 共用它。

固定例子：四条回答 reward 为 `[1,1,0,0]`，均值 `.5`、总体标准差 `.5`，所以 `A=[1,1,−1,−1]`。前两条的 token 概率整体往上推，后两条往下压。若四条全是 `1` 或全是 `0`，中心化后全为 `0`，这组没有策略梯度。

## reward model 和 critic 不是一回事

| 角色 | 什么时候打分 | 回答什么问题 | GRPO 是否必然去掉 |
|---|---|---|---|
| reward model / 规则验证器 | 回答完成后 | “这份成品好不好？” | 否 |
| critic / value model | 回答生成途中 | “从当前前缀继续，预计最后得几分？” | **是** |

数学和代码有可验证答案时，reward 可直接来自规则，所以常常既没有 reward model，也没有 critic；主观审美、帮助性等任务仍可能需要 reward model。是否需要 reward model 由任务的打分方式决定，不是由 GRPO 这个名字决定。

## 完整目标没有消失

原始 outcome GRPO 的策略项仍是逐 token 的 PPO-Clip：

```text
ρ_i,t = π_θ(y_i,t | x,y_i,<t) / π_old(y_i,t | x,y_i,<t)

L_i = (1/|y_i|) Σ_t min(
        ρ_i,t A_i,
        clip(ρ_i,t,1−ε,1+ε) A_i
      )
```

`ρ_i,t` 表示新模型相对采样时的旧模型，把这个 token 的概率改了多少；`ε` 限制一次更新的有效幅度；`|y_i|` 是回答 token 数。DeepSeekMath 原始版本还直接在目标里加入相对 reference policy 的逐 token KL 惩罚。

所以 GRPO 不是“只按 reward 做监督学习”，也不是把 PPO 整套推翻：**它主要替换 advantage 的估计方式，并保留 policy ratio、clip 和可选 KL 约束。**

## 为什么省资源，但不是“白省”

省掉与 policy 规模相近的 critic，可减少模型参数、优化器状态和前后向计算。但代价是每个 prompt 要采 `G` 条回答；生成很长时，rollout 本身可能成为主要成本。实际节省多少取决于并行、模型共享、序列长度和训练框架，不能笼统写成“显存减半”。

## 原始 GRPO 的两个后续问题

1. 除以每题自己的 `std` 会改变题目权重；每条回答先除以自身长度会改变长短回答的 token 权重。[[dr-grpo]] 针对这两点去偏。
2. 全对 / 全错组无梯度、长 CoT 截断噪声和探索不足仍需系统处理。[[dapo]] 给出一套组合方案。
3. reward 是序列级，却逐 token 计算 ratio 和 clip，训练 / 推理数值差异会让局部比率波动。[[gspo]] 把它提升到序列级。

## 在这个 wiki 里怎么用

- [[fish-speech-s2-pro]]：多维 reward 做 TTS 对齐。
- [[krea-2]]：文生图用多奖励组相对 RL。
- [[diffusionnft]]：解释扩散模型为什么难直接照搬语言模型的似然比目标。

## 来源与链接

- [DeepSeekMath：GRPO 原论文](https://arxiv.org/abs/2402.03300)
- [[ppo-grpo-gspo]] · PPO、GRPO、Dr.GRPO、DAPO、GSPO 的统一公式与手算
- [[ppo]] · ratio 和 clip 的来源
- [[advantage-function]] · baseline 为什么能降方差
- [[rl-for-llm-people]] · RL 基础术语
