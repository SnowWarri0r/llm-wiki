---
name: dr-grpo
type: concept
sources: [grpo, ppo]
updated: 2026-07-22
---

# Dr.GRPO · Group Relative Policy Optimization Done Right

## 一句话
Dr.GRPO 保留“同题多回答、减组均值”的无 critic 优势估计，但去掉**除组内标准差**和**除每条回答实际长度**，避免原始 GRPO 暗中重加权题目与回答。

## 它不是另一套 RL 循环

[[grpo]] 的两次除法看似只是归一化：

\[
\begin{aligned}
A_i&=\frac{R_i-\mu_R}{\sigma_R} \\
L_i&=\frac{1}{|y_i|}\sum_t \ell_{i,t}
\end{aligned}
\]

这里 \(\mu_R\) 和 \(\sigma_R\) 是同题这组 reward 的均值与标准差；\(|y_i|\) 是第 \(i\) 条回答的 token 数；\(\ell_{i,t}\) 是它第 \(t\) 个 token 的策略损失。

但分母会改变样本的相对权重：`group_std` 小的题更新更重；长回答的每个 token 更新更轻。Dr.GRPO 改成：

\[
\begin{aligned}
A_i^{\mathrm{Dr}}&=R_i-\mu_R \\
L_i^{\mathrm{Dr}}&=\frac1M\sum_t \ell_{i,t}
\end{aligned}
\]

\(M\) 是所有样本共享的固定常数，例如最大生成 token 数。它只统一缩放整批梯度，不随单条回答长度变化。

## 两个数字立刻看懂

题 A 的 reward 为 `[1,1,0,0]`，正确回答的原 GRPO advantage 是 `(1−.5)/.5=1`。题 B 为 `[1,0,0,0]`，正确回答是 `(1−.25)/.433≈1.732`。除标准差以后，题 B 的这个正确样本天然被放大 73%。Dr.GRPO 分别得到 `.5` 和 `.75`，不再额外乘 `1/std`。

再看长度：若 4-token 和 8-token 回答每个 token 的局部贡献都是 `1`，原始逐回答平均后两条的总目标都等于 `1`，但长回答每个 token 只有短回答一半权重。改用同一个 `M=16` 后，总目标分别是 `4/16=.25` 和 `8/16=.5`；每个 token 都是 `1/16`，不再因为住在长回答里就被摊薄。

## 边界

- 它去除的是 objective 中可分析的偏置，不保证回答一定变短或性能一定提高。
- 它仍需同题多次采样，仍可能遇到全对 / 全错组没有梯度。
- “不除组标准差”也意味着不同 reward 标尺必须在上游设计得可比较。

## 来源与链接

- [原论文](https://arxiv.org/abs/2503.20783)
- [[ppo-grpo-gspo]] · 放回完整算法谱系和统一数值例子
- [[grpo]] · 它修正的原始目标
- [[dapo]] · 另一条处理长 CoT 训练问题的路线
