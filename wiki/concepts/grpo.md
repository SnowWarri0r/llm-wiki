---
name: grpo
type: concept
sources: [fish-speech-s2-pro, ppo]
updated: 2026-05-31
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

## RM ≠ critic · GRPO 到底砍了哪个

最常见的误解：以为 GRPO 跟 PPO 的区别在 reward model。**不是。** RL 训练里有两个会"给分"的角色，长得像活儿完全不同，GRPO 砍的是 critic，不是 RM：

| | reward model (RM) | critic / value 网络 V(s) |
|---|---|---|
| 干啥 | 看**整篇答案**给总分 | 写到**一半**时预测"最后大概拿多少" |
| 类比 | 终评委 / 阅卷老师 | 过程预测员 / 庄家盘口 |
| 用来 | 提供 reward 信号 | 当 baseline 算 advantage |
| 多大 | 一个独立模型 | **跟 policy 一样大**，且单独训、不稳 |

PPO 算 advantage 靠 `A = reward − V(s)`，所以**必须养 critic**。GRPO 改成"同一题采 G 个回答，拿这组的 mean/std 当 baseline" —— 省掉那个跟 policy 同样大的网络，这才是它在 LLM 上火的实际原因（显存近乎减半），代价是采样开销上去。

<figure style="margin:32px 0; padding:24px; background:#f7f1de; border:1px solid #bfb398; border-radius:4px;">
<svg viewBox="0 0 900 465" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;">

  <!-- 共享顶注: reward 来源不是区别 -->
  <rect x="140" y="10" width="620" height="42" rx="5" fill="#faf4e1" stroke="#bfb398" stroke-width="0.8"/>
  <text x="450" y="29" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#3a3128">reward 从哪来 · RM 学人类偏好 / reasoning 场景规则判对错</text>
  <text x="450" y="44" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#4a6b3a">PPO 和 GRPO 都一样 —— 不是区别</text>

  <line x1="450" y1="66" x2="450" y2="406" stroke="#d8cfb4" stroke-width="1" stroke-dasharray="4 4"/>

  <!-- ===== PPO 半边 ===== -->
  <text x="235" y="86" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="18" font-weight="700" fill="#9b2c2c">PPO</text>

  <rect x="170" y="100" width="130" height="40" rx="5" fill="#d8e6ce" stroke="#4a6b3a" stroke-width="1.5"/>
  <text x="235" y="125" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="12" fill="#3a3128">policy π</text>
  <path d="M 235 140 L 235 165" fill="none" stroke="#3a3128" stroke-width="1.4" marker-end="url(#ga)"/>

  <rect x="115" y="167" width="110" height="34" rx="4" fill="#ffffff" stroke="#bfb398" stroke-width="0.8"/>
  <text x="170" y="189" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#3a3128">1 个回答</text>
  <path d="M 225 184 L 252 184" fill="none" stroke="#3a3128" stroke-width="1.2" marker-end="url(#ga)"/>
  <rect x="254" y="169" width="92" height="30" rx="4" fill="#f0e0a8" stroke="#b8841c" stroke-width="0.8"/>
  <text x="300" y="189" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#3a3128">reward r</text>

  <path d="M 235 201 L 235 228" fill="none" stroke="#3a3128" stroke-width="1.4" marker-end="url(#ga)"/>

  <!-- critic 高亮: 这就是 GRPO 砍的 -->
  <rect x="115" y="230" width="240" height="64" rx="5" fill="#ffffff" stroke="#9b2c2c" stroke-width="2.2"/>
  <text x="235" y="254" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="12" font-weight="700" fill="#9b2c2c">critic V(s)</text>
  <text x="235" y="272" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#7a6f5d">独立网络, ≈ policy 大小, 单独训不稳</text>
  <text x="235" y="287" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#9b2c2c">← GRPO 砍的就是它</text>

  <rect x="115" y="312" width="240" height="38" rx="4" fill="#f7f1de" stroke="#bfb398" stroke-width="0.8"/>
  <text x="235" y="336" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="13" fill="#3a3128">A = r − <tspan fill="#9b2c2c" font-weight="700">V(s)</tspan></text>

  <text x="235" y="374" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" fill="#3a3128">要养一个跟 policy 同样大的 critic</text>

  <!-- ===== GRPO 半边 ===== -->
  <text x="670" y="86" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="18" font-weight="700" fill="#b8841c">GRPO</text>

  <rect x="605" y="100" width="130" height="40" rx="5" fill="#d8e6ce" stroke="#4a6b3a" stroke-width="1.5"/>
  <text x="670" y="125" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="12" fill="#3a3128">policy π</text>
  <path d="M 670 140 L 670 165" fill="none" stroke="#3a3128" stroke-width="1.4" marker-end="url(#ga)"/>

  <rect x="550" y="167" width="120" height="34" rx="4" fill="#ffffff" stroke="#bfb398" stroke-width="0.8"/>
  <text x="610" y="189" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#3a3128">同一题 G 个回答</text>
  <path d="M 670 184 L 697 184" fill="none" stroke="#3a3128" stroke-width="1.2" marker-end="url(#ga)"/>
  <rect x="699" y="169" width="96" height="30" rx="4" fill="#f0e0a8" stroke="#b8841c" stroke-width="0.8"/>
  <text x="747" y="189" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="11" fill="#3a3128">r₁ r₂ … r_G</text>

  <path d="M 670 201 L 670 228" fill="none" stroke="#3a3128" stroke-width="1.4" marker-end="url(#ga)"/>

  <!-- critic 位置留空 + 组统计 -->
  <rect x="550" y="230" width="240" height="64" rx="5" fill="#f0e0a8" stroke="#b8841c" stroke-width="1.5"/>
  <text x="670" y="254" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="12" font-weight="700" fill="#b8841c">组内 mean / std 当 baseline</text>
  <text x="670" y="272" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#7a6f5d">本该放 critic 的位置 → 空着</text>
  <text x="670" y="287" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9.5" fill="#4a6b3a">✓ 不要网络, 纯统计</text>

  <rect x="550" y="312" width="240" height="38" rx="4" fill="#f7f1de" stroke="#bfb398" stroke-width="0.8"/>
  <text x="670" y="336" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="12" fill="#3a3128">A = (rᵢ − <tspan fill="#b8841c" font-weight="700">组均值</tspan>) / 组标准差</text>

  <text x="670" y="374" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" fill="#3a3128">用 G 个回答互相比, 省掉 critic</text>

  <!-- 底部 punchline -->
  <rect x="90" y="398" width="720" height="56" rx="5" fill="#efd6c8" stroke="#9b2c2c" stroke-width="0.8"/>
  <text x="450" y="421" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#181410">真正的区别 = 要不要 critic（那个跟 policy 同样大的过程预测员）</text>
  <text x="450" y="442" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10.5" fill="#3a3128">reward model 是上游, 两边共用, 跟选 PPO 还是 GRPO 无关</text>

  <defs>
    <marker id="ga" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#3a3128"/>
    </marker>
  </defs>
</svg>
</figure>

**你以为**：SFT → reward model → PPO 三步里 RM 那么显眼，GRPO 肯定在 RM 这儿不一样。
**其实**：RM 是 RLHF 这个场景的上游，PPO / GRPO 共用；GRPO 动的是 advantage 怎么算 —— 把"critic 估 baseline"换成"组内互比当 baseline"。而且在 reasoning 场景（数学/代码答案能自动判对错），GRPO 经常连 RM 都不训，reward 直接用规则（对=1 错=0）。

所以 GRPO 严格说是"**省了 critic 的 PPO 变体**"，loss 还是 PPO 那个 `clip(r,1±ε)·A` + KL，几乎一字没改 —— 你觉得"区别不大"在 loss 层面没说错，只是真正省的那块在 critic，不在 RM。

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
