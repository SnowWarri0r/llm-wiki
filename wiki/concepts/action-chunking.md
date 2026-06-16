---
name: action-chunking
type: concept
sources: [lumine]
updated: 2026-06-16
---

# Action Chunking · 一次推理预测多步动作

## 一句话
看一眼 → **一口气预测未来好几步动作**，而不是"看一眼只走一步"。让慢的感知/推理频率喂出快的控制频率，还顺带让动作更连贯、少抖、少累积误差。

## 直觉 · 瞄一眼乐谱的一个小节

慢的不是手，是"看 + 想"。Lumine **每 200ms 才看一帧画面(5Hz)**，但游戏要 **30Hz(每 33ms 一个动作)** 才流畅。如果"看一眼只走一步"，那操作频率就被卡在 5Hz，动作一顿一顿。

**action chunking** 的办法:**一次推理预测未来 6 个动作块**(6×33ms≈200ms)，看一眼就把接下来 200ms 的连续操作全规划好，边执行边等下一帧。

类比:熟练乐手**瞄一眼乐谱的一个小节，手指就连续把这小节的音符弹完**，而不是每个音符都回头看一次谱子——眼睛慢、手指快，靠"成块读、成块弹"对上。

## 为什么不只是"提速度"
chunk 不止解决频率，还有两个附带好处:
- **更连贯**:一次性出一串动作，天然平滑(不会每步重新决策导致抖动/反复横跳)。
- **少累积误差**:逐步预测时，每步的小误差会喂回输入、越滚越歪(compounding error);成块预测把"喂回"的次数减少。

代价:chunk 太长 → 来不及对环境突变做反应(规划了 200ms，中途情况变了还在执行旧动作)。所以 chunk 长度是"反应灵敏 ↔ 平滑省算力"的权衡。

## 怎么做的
```
# 慢感知、快控制
obs = see()                      # 200ms 一帧 (5Hz)
chunk = model(obs)               # 一次推理 → [a1, a2, a3, a4, a5, a6]  各 33ms
for a in chunk: execute(a)       # 连续执行 6 步 → 等效 30Hz
# 机器人 VLA(ACT / RT 系 / Diffusion Policy / π0)同款思路
```

## 代码出处 / 来源
- [[lumine]] · 6 块 × 33ms，用 5Hz 感知喂 30Hz 键鼠控制
- 机器人模仿学习里早成标配:ACT(Action Chunking Transformer)、Diffusion Policy、RT/π0 系

## 链接
- [[lumine]] · 游戏 agent 用 chunking 实时操作
- [[imitation-learning]] · chunking 多用在模仿学习的控制策略上
- [[react-loop]] · 对照:ReAct 是"想一步动一步"，chunking 是"想一次动多步"
- [[kv-cache]] · 一次多吐 token 的自回归生成靠它省重算
