---
name: ppo-grpo-gspo
type: topic
sources: [ppo, grpo, dr-grpo, dapo, gspo]
updated: 2026-07-22
---

# PPO → GRPO → Dr.GRPO / DAPO → GSPO · LLM 强化学习算法地图

<style>
@media (max-width: 640px) {
  .concept-body table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>

## 一句话
这几种算法并不是五套互不相干的训练方法：它们都在做“采样回答 → 打分 → 提高好回答概率、降低坏回答概率”，主要分歧只有三处——**用什么估计 advantage、按回答还是按 token 汇总 loss、用 token 级还是序列级的重要性比率做 clip**。

## 先把共同的训练循环拼起来

以数学题 `17 × 6 = ?` 为例，一轮在线 RL 是：

1. 用当前策略的快照 `π_old` 对同一道题采样若干回答。
2. 验证器或 reward model 给每条完整回答打分。
3. 把 reward 变成 advantage：正数表示“应提高这条回答的概率”，负数表示“应降低”。
4. 用 `π_old` 采到的 token 训练新策略 `π_θ`。因为数据来自旧策略，要用新旧概率之比校正；clip 再限制单轮更新别走太远。
5. 更新后重新采样，进入下一轮。

`π` 读作 policy（策略），在 LLM 里就是“给定题目和已生成前缀，下一个 token 的概率分布”。下标 `old` 表示采样数据时冻结的旧快照；`θ` 表示正在训练的模型参数。

## 一张表先看清它们各改了什么

| 算法 | advantage 从哪来 | 是否训练 critic | loss 怎样汇总 | 新旧策略比率在哪一级 | 它主要解决什么 |
|---|---|---:|---|---|---|
| **PPO** | critic 预测的价值 + GAE | 是 | 经典公式按时间步求和；LLM 实现各异 | token | 限制策略更新幅度，稳定复用 rollout |
| **GRPO** | 同题 `G` 条回答的组内标准化 reward | 否 | 每条回答先按 token 取平均，再对回答取平均 | token | 用同题互比替代 critic，降低训练资源 |
| **Dr.GRPO** | `reward − 组均值`，不除组标准差 | 否 | token 和改成除以固定常数 | token | 去掉题目难度偏置和回答长度偏置 |
| **DAPO** | 沿用组相对 advantage | 否 | 全 batch 的有效 token 一起平均 | token，且上下 clip 不对称 | 让长 CoT 训练更有效、更稳定 |
| **GSPO** | 沿用组相对 advantage | 否 | 每条回答一个目标 | **sequence** | 让比率、clip、reward 处在同一序列粒度，尤其稳定 MoE RL |

注意：这张表说的是论文中的典型定义，不代表所有开源框架都逐字照搬。`PPO` 是通用 RL 算法；后四种主要围绕 LLM 在线 RL / 可验证奖励场景展开。

## 先吃透 PPO 的一项核心公式

PPO-Clip 最大化：

\[
L_{\mathrm{PPO}}=\mathbb E_t\!\left[
\min\!\left(
\rho_tA_t,
\operatorname{clip}(\rho_t,1-\varepsilon,1+\varepsilon)A_t
\right)
\right]
\]

\[
\rho_t=\frac{\pi_\theta(y_t\mid x,y_{<t})}
{\pi_{\mathrm{old}}(y_t\mid x,y_{<t})}
\]

每个符号：

- `x`：prompt，例如题目 `17 × 6`。
- `y_t`：回答的第 `t` 个 token；`y_<t` 是它前面的 token。
- `π_old(...)`：旧策略生成这个 token 时给它的概率。
- `π_θ(...)`：正在更新的新策略现在给同一个 token 的概率。
- `ρ_t`：重要性比率。`ρ_t = 1.1` 表示新模型把这个 token 的概率提高了 10%；`0.9` 表示降低了 10%。
- `A_t`：advantage，表示这个 token 所在的动作比基线预期好多少。
- `ε`：clip 宽度，常见示意值是 `0.2`，对应区间 `[0.8, 1.2]`。
- `min`：在“原始更新收益”和“截断后的收益”里取更保守的一项。
- `E_t`：对采样到的时间步 / token 求平均。

为什么需要 `ρ_t`？回答由 `π_old` 采样，但梯度更新的是 `π_θ`。新旧模型已经不完全一样，`ρ_t` 用来修正这点差异。为什么再 clip？同一批回答会训练多个 epoch；如果某个 token 概率已经从 `0.1` 涨到 `0.3`，比率是 `3`，继续按三倍力度奖励它很容易把策略推坏。clip 让超出边界后的额外变化不再带来收益。

### PPO 的 advantage 为什么需要 critic

最简单地看：

\[
A_t\approx \mathrm{return}_t-V_\phi(s_t)
\]

`s_t = (x, y_<t)` 是写到第 `t` 个 token 前的状态；`V_φ(s_t)` 是 critic 对“从这里继续写，预计最终能拿多少 reward”的预测，`φ` 是 critic 的参数。实际工程通常用 [[gae]] 把多步 TD 误差平滑起来，而不是只做一次相减。

如果某条正确回答 reward 是 `1`，critic 在开头预测 `0.4`，那么简化 advantage 是 `1 − 0.4 = 0.6`。关键不是“答对得 1 分”，而是它比当前模型原本预期多了 `0.6`。

critic 不是 reward model：reward model / 规则验证器负责给已完成的回答判分；critic 负责预测尚未写完时的未来得分。GRPO 砍掉的是后者。

## GRPO：不用 critic，同一道题内部互比

对一个 prompt 采样 `G` 条回答，reward 为 `R_1 ... R_G`。原始 GRPO 的 outcome advantage 是：

\[
A_i=\frac{R_i-\operatorname{mean}(R_1,\ldots,R_G)}
{\operatorname{std}(R_1,\ldots,R_G)}
\]

- `i`：组内第 `i` 条回答。
- `G`：同一道题采样的回答数。
- `R_i`：第 `i` 条完整回答的 reward。
- `mean`：这组回答的平均分，充当 baseline。
- `std`：组内 reward 的标准差，把不同题的 advantage 缩到相近尺度。
- `A_i`：整条回答的组相对 advantage；在 outcome supervision 下，同一回答的所有 token 共用它。

固定例子：四条回答 reward 是 `[1, 1, 0, 0]`。组均值是 `0.5`，总体标准差是 `0.5`，所以 advantage 是：

\[
\begin{aligned}
A&=\left[\frac{1-0.5}{0.5},\frac{1-0.5}{0.5},
\frac{0-0.5}{0.5},\frac{0-0.5}{0.5}\right] \\
&=[1,1,-1,-1]
\end{aligned}
\]

这就替代了 critic：答对的两条相对组均值更好，所有 token 一起增大概率；答错的两条反过来。若四条全对或全错，reward 完全相同，中心化后 advantage 全为 `0`，这组数据不会产生策略梯度。

原始 GRPO 仍使用 PPO 的 token 级比率和 clip。省掉 critic 不等于省掉 reward：数学、代码等任务可以用规则验证器；主观偏好任务仍可能需要 reward model。

## 同一条回答，PPO / GRPO / GSPO 到底怎么算

取上面第一条正确回答，假设它有 4 个 token。旧、新策略给已采 token 的概率如下：

| token | `π_old` | `π_θ` | `ρ_t = π_θ / π_old` |
|---|---:|---:|---:|
| 1 | 0.50 | 0.55 | 1.10 |
| 2 | 0.40 | 0.42 | 1.05 |
| 3 | 0.60 | 0.54 | 0.90 |
| 4 | 0.40 | 0.50 | 1.25 |

设 `ε = 0.2`，clip 区间为 `[0.8, 1.2]`。

**PPO：**假设 critic 算出的 `A_t` 都简化为 `0.6`。前 3 个 token 的比率没越界；第 4 个 token 的 `1.25` 超过上界。对正 advantage，四项贡献是：

\[
\begin{aligned}
&[1.10\times0.6,\;1.05\times0.6,\;0.90\times0.6,\;
\min(1.25\times0.6,1.20\times0.6)] \\
&=[0.66,0.63,0.54,0.72]
\end{aligned}
\]

最后一项没有继续用 `0.75`，而被限制成 `0.72`。这就是 clip 真正在做的事。

**GRPO：**这条回答的组相对 advantage 是 `A_i = 1`，于是四项变成 `[1.10, 1.05, 0.90, 1.20]`。算法骨架没换，只是 advantage 不再来自 critic。

**GSPO：**不再让四个 token 各拿一个比率，先求整条回答的长度归一似然比：

\[
\begin{aligned}
s_i&=\exp\!\left(\frac14[\log1.10+\log1.05+\log0.90+\log1.25]\right) \\
&=(1.10\times1.05\times0.90\times1.25)^{1/4} \\
&\approx1.0677
\end{aligned}
\]

它就是四个 token 比率的几何平均。`1.0677` 没越过 `[0.8, 1.2]`，所以整条回答的目标贡献约为 `1.0677 × 1 = 1.0677`。

这里不是说 token 级比率“算错了”。PPO 的重要性采样在理论上是逐动作定义的；GSPO 的主张是：LLM 常拿到整条回答的奖励，若训练时又因推理/训练数值差异让个别 token 比率波动，逐 token clip 会让一条回答内部出现不一致的截断。把比率和 clip 提到序列级，更贴合序列级 reward，也更能容忍局部概率波动。

## Dr.GRPO：原始 GRPO 暗中给谁加了权

Dr.GRPO 指出原始 GRPO 的两个归一化操作并不只是“让数值好看”，它们会改变样本权重。

### 1. 除以组内标准差，会形成题目难度偏置

比较两道题，每题采 4 条：

```text
题 A rewards = [1, 1, 0, 0]  → mean=.50, std=.50
题 B rewards = [1, 0, 0, 0]  → mean=.25, std≈.433
```

题 A 的正确回答 advantage 是 `1`；题 B 的正确回答是 `(1−.25)/.433 ≈ 1.732`。因为题 B 的组内标准差更小，同样一个正确样本会收到更大的更新权重。极易或极难的问题常出现 reward 几乎全相同，标准差很小；除以它会把少量差异放大。

Dr.GRPO 改成：

\[
A_i^{\mathrm{Dr}}=R_i-\operatorname{mean}(R_1,\ldots,R_G)
\]

仍然减组均值，所以 baseline 还在、critic 仍不需要；只是取消除以组内标准差，避免每道题因自己的 `std` 被重新加权。

### 2. 每条回答先除以自身长度，会形成长度偏置

原始 GRPO 常写成：

\[
L_i=\frac1{|y_i|}\sum_t\ell_{i,t}
\]

`|y_i|` 是第 `i` 条回答的 token 数。4-token 回答里每个 token 占整条目标的 `1/4`；8-token 回答里每个 token 只占 `1/8`。因此好长回答中的推理 token 被摊薄；坏长回答中的错误 token 也被摊薄。论文观察到后者会让错误回答越写越长。

Dr.GRPO 把分母换成训练期间固定的生成上限 `M`：

\[
L_i^{\mathrm{Dr}}=\frac1M\sum_t\ell_{i,t}
\]

`M` 对所有回答相同，只改变整体梯度尺度，不再按每条回答的实际长度重新加权。这里不是奖励“越长越好”，而是让每个有效 token 的单位权重不随其所在回答长度改变。

## DAPO：不是只改一条公式，而是修长 CoT 的整条流水线

DAPO 沿用组相对 advantage 和 token 级 PPO 目标，组合四项工程修改：

### 1. Clip-Higher：给低概率探索 token 多一点上升空间

普通 PPO 对比率使用对称 `[1−ε, 1+ε]`。DAPO 拆成 `[1−ε_low, 1+ε_high]`，论文实验取 `ε_low=0.2`、`ε_high=0.28`。

若旧概率是 `0.01`，上界 `1.2` 最多把它推到 `0.012`；上界 `1.28` 可推到 `0.0128`。绝对差仍小，但相对允许的增长从 20% 放宽到 28%。它针对的是低概率探索 token 很难被抬起来、策略熵过早坍缩的问题。下界没有同步放宽，因为过度压低这些 token 会进一步缩小探索空间。

### 2. Dynamic Sampling：别让全对 / 全错组占训练 batch

如果某题的 16 条回答全对或全错，中心化 advantage 全为 0。这些回答花了生成成本，却不给策略梯度。DAPO 过采样 prompt，过滤组准确率为 `0` 或 `1` 的题，直到凑够固定数量的“组内有分歧”样本。

它提升的是有效 batch 比例，不是凭空让全错题产生正确方向；代价是要生成更多候选，也会改变实际训练题分布。

### 3. Token-Level Policy Gradient Loss：按所有有效 token 汇总

原始 GRPO 是“每条回答先平均，再平均回答”，每条回答权重相同；DAPO 把 batch 内所有有效 token 的 loss 加起来，再除以有效 token 总数。于是每个 token 的单位权重相同，长回答会因 token 多而对总梯度贡献更多。它与 Dr.GRPO 的“除固定生成上限”都在消除逐回答长度归一化，但整体缩放方式不同。

### 4. Overlong Reward Shaping：截断不等于推理全错

达到最大生成长度的回答会被截断。如果一律给硬惩罚，一条本来合理、只是晚了一点写出答案的推理也会突然变成负样本，reward 噪声很大。DAPO 先验证过直接屏蔽截断样本，再采用软惩罚区间：接近长度上限时惩罚逐渐加重，而不是到边界突然跳变。

DAPO 论文在 Qwen2.5-32B / AIME 2024 上报告从 naive GRPO 的 30 分逐项加到 50 分；这是特定模型、数据和训练系统上的组合消融，不能把每项增益直接外推到别的任务。

## GSPO：把“更新幅度”从 token 级统一到回答级

GSPO 的序列级比率为：

\[
\begin{aligned}
s_i(\theta)
&=\left(\frac{\pi_\theta(y_i\mid x)}{\pi_{\mathrm{old}}(y_i\mid x)}\right)^{1/|y_i|} \\
&=\exp\!\left[
\frac1{|y_i|}\sum_t
\log\frac{\pi_\theta(y_{i,t}\mid x,y_{i,<t})}
{\pi_{\mathrm{old}}(y_{i,t}\mid x,y_{i,<t})}
\right]
\end{aligned}
\]

- `s_i`：第 `i` 条回答唯一的序列级重要性比率。
- `π(y_i|x)`：整条回答的似然，等于各 token 条件概率连乘。
- `|y_i|`：回答长度。
- `1/|y_i|` 次方：把连乘比率变成平均每 token 的尺度；否则序列越长，乘积越容易指数级趋近 0 或无穷大。

GSPO 目标为：

\[
L_{\mathrm{GSPO}}=\mathbb E_{x,\{y_i\}}\!\left[
\frac1G\sum_i
\min\!\left(
s_iA_i,
\operatorname{clip}(s_i,1-\varepsilon,1+\varepsilon)A_i
\right)
\right]
\]

`A_i` 仍可使用 GRPO 的组相对 advantage。真正改变的是：一条回答只算一个 `s_i`，整条一起 clip、一起放大或缩小。Qwen 团队报告它比 GRPO 更稳定，尤其能稳定 MoE 模型 RL；其解释包括序列 reward 与 token clip 的粒度错位，以及训练、推理引擎或 MoE 路由造成的 token 概率差异。

## 这些算法不是一条“越来越先进”的排行榜

- 有成熟 critic、奖励沿轨迹分布、任务不是纯文本生成：**PPO** 仍是最通用的起点。
- 同一道题能采多条，reward 可比，critic 太贵：看 **GRPO**。
- 在意原始 GRPO 的长度 / 题目权重偏置：看 **Dr.GRPO**。
- 真正训练超长 CoT，遇到熵坍缩、零梯度组、截断噪声：看 **DAPO** 的系统配方。
- token 级比率波动大，尤其训练 MoE 或训推引擎数值不一致：看 **GSPO**。

它们还可以组合，不能只看名字互斥地选。例如 GSPO 改的是 ratio / clip 粒度，并不强制保留原始 GRPO 的标准差归一化；实际系统可以同时采用去偏的 advantage 或动态采样。组合后应明确写出最终 objective，不能只报一个算法名。

## 最容易混淆的五件事

1. **reward 不等于 advantage。** reward 是结果得分；advantage 是减过 baseline 后的训练方向和强度。
2. **reward model 不等于 critic。** 前者给完成品打分，后者预测中间状态的未来回报。
3. **GRPO 不等于“不需要 reward model”。** 是否能用规则奖励取决于任务，不取决于优化器名字。
4. **clip 不会把模型参数限制在某个区间。** 它截断的是目标函数里的新旧概率比率收益。
5. **GSPO 不是把 reward 从 token 改成序列。** 在 outcome GRPO 里 reward 本来就是序列级；GSPO 改的是重要性比率、clip 和更新权重的粒度。

## 来源

- [PPO 原论文](https://arxiv.org/abs/1707.06347)
- [DeepSeekMath：GRPO 原始定义](https://arxiv.org/abs/2402.03300)
- [Understanding R1-Zero-Like Training：Dr.GRPO](https://arxiv.org/abs/2503.20783)
- [DAPO 技术报告](https://arxiv.org/abs/2503.14476)
- [GSPO 论文](https://arxiv.org/abs/2507.18071) · [Qwen 官方中文解读](https://qwenlm.github.io/zh/blog/gspo/)

## 链接

- [[ppo]] · PPO 原论文深读
- [[grpo]] · 组相对 advantage
- [[dr-grpo]] · 两种归一化偏置
- [[dapo]] · 长 CoT 训练的四项系统修改
- [[gspo]] · 序列级重要性比率
- [[logarithms]] · 外加内乘、外减内除、换底公式，以及 GSPO 的 log 求和
- [[rl-for-llm-people]] · 先补 policy / reward / rollout / on-policy 基础
- [[clipped-surrogate-objective]] · 单独理解 PPO clip
- [[advantage-function]] · 为什么要减 baseline
