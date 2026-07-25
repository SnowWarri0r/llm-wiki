---
name: gspo
type: concept
sources: [qwen3-asr, grpo, ppo]
updated: 2026-07-22
---

# GSPO · Group Sequence Policy Optimization

## 一句话
GSPO 沿用 GRPO 的组相对 advantage，但让整条回答共用一个长度归一的新旧策略比率，并在序列级做 clip；它修的是更新粒度，不是 reward 的来源。

## GRPO 的 token 级比率并非“算错”，问题是粒度错位

在 outcome RL 中，一条回答通常只拿一个最终 reward，组相对 advantage `A_i` 也属于整条回答。但 GRPO 沿用 PPO，对每个 token 分别计算：

\[
\rho_{i,t}=\frac{\pi_\theta(y_{i,t}\mid x,y_{i,<t})}
{\pi_{\mathrm{old}}(y_{i,t}\mid x,y_{i,<t})}
\]

- \(x\)：输入的 prompt。
- \(y_{i,t}\)：第 \(i\) 条回答的第 \(t\) 个 token；\(y_{i,<t}\) 是它前面的 token。
- \(\pi_{\mathrm{old}}\)：采样这条回答时的旧策略；\(\pi_\theta\) 是参数为 \(\theta\) 的待更新策略。
- \(\rho_{i,t}\)：新概率除以旧概率。它等于 1 表示没变，1.1 表示新模型把该 token 的概率提高了 10%。

然后每个 `ρ_i,t` 各自 clip。于是同一条好回答里，某些 token 可能按 `1.2` 奖励，另一些按 `0.8` 或未截断值更新。若训练和推理引擎精度不同，或 MoE 路由让局部 log-prob 更敏感，个别 token 的比率波动会改变 clip 决策。

GSPO 的思路是：既然奖惩对象是一条回答，就让更新幅度也属于整条回答。

## 序列比率公式逐项拆开

\[
\begin{aligned}
s_i(\theta)
&=\left(\frac{\pi_\theta(y_i\mid x)}
{\pi_{\mathrm{old}}(y_i\mid x)}\right)^{1/|y_i|} \\
&=\exp\!\left(\frac{1}{|y_i|}\sum_t\log\rho_{i,t}\right)
\end{aligned}
\]

- `y_i`：同一 prompt 的第 `i` 条完整回答。
- `π(y_i|x)`：整条回答的似然，即各 token 条件概率连乘。
- `s_i`：这条回答唯一的序列级重要性比率。
- `|y_i|`：回答 token 数。
- `1/|y_i|`：长度归一；把连乘后的总比率拉回“平均每 token”尺度。
- `exp(mean(log ρ))`：与上式完全等价，也是 token 比率的几何平均，数值计算时更稳定。

GSPO 最大化：

\[
L=\mathbb E\!\left[
\frac1G\sum_i
\min\!\left(
s_iA_i,\operatorname{clip}(s_i,1-\varepsilon,1+\varepsilon)A_i
\right)
\right]
\]

- \(L\)：要最大化的训练目标；值越大，表示这次策略更新越符合 reward 给出的方向。
- \(\mathbb E\)：对训练中采样到的 prompt 和回答求平均。
- \(G\)：同一道题采样的回答数；\(\frac1G\sum_i\) 就是先把这 \(G\) 条回答的贡献平均。
- \(A_i\)：第 \(i\) 条回答的 advantage，仍可按 [[grpo]] 从同题多回答的 reward 算出。
- \(\varepsilon\)：clip 宽度；若 \(\varepsilon=0.2\)，允许区间就是 \([0.8,1.2]\)。
- \(\min\)：在未截断与截断后的两项里取更保守的一项。

真正变化只在 \(s_i\)：整条回答一起放大、缩小或被 clip。

## 四个 token 的手算

若 token 比率为 `[1.10, 1.05, .90, 1.25]`：

\[
\begin{aligned}
s&=(1.10\times1.05\times0.90\times1.25)^{1/4} \\
 &=1.299375^{1/4} \\
 &\approx1.0677
\end{aligned}
\]

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
- [[logarithms]] · `exp(mean(log ratio))` 的对数运算逐步解释
- [[qwen3-asr]] · GSPO 在语音后训练中的使用
