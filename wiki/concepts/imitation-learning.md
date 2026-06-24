---
name: imitation-learning
type: concept
sources: [lumine, cosmos-3]
updated: 2026-06-16
---

# 模仿学习 · 行为克隆 · 抄人类作业

## 一句话
不靠试错 + reward，而是**看专家(人类)怎么做，学着复现**——把"看到的状态 → 专家的动作"当成监督学习的输入输出对训练。最简单的形态叫**行为克隆(Behavior Cloning)**。

## 直觉 · 抄作业 vs 自己试错

[[rl-for-llm-people]] / [[policy-gradient]] 那套强化学习是**自己试错**:做动作 → 拿 reward → 强化得分高的行为。问题是**reward 稀疏**时几乎没法学——比如打通一局 5 小时的游戏才"得一次分",中间全程没人给信号,纯试错撞不出来。

模仿学习换思路:**别试错了,直接抄人类录像**。把人类玩游戏的`(画面, 按了什么键)`收集成一大堆样本,当成监督学习——输入画面、预测人会按什么键。这就是 [[lumine]] 的全部训练范式(2424h 人类原神录像,**零 RL**)。

类比:学开车,RL 是"自己瞎开,撞了扣分,慢慢摸";模仿学习是"坐副驾看老司机开几千小时,学他每个路况怎么操作"。开放世界这种 reward 极稀疏的场景,抄作业比试错现实得多。

## 它的软肋:误差累积(distribution shift)

行为克隆最有名的坑:**训练时只见过"专家走过的状态"**。一旦推理时犯个小错、飘到一个**专家从没到过的状态**,模型不知道怎么办 → 错上加错、越飘越远(compounding error / distribution shift)。

缓解办法:海量多样数据(覆盖更多状态)、[[action-chunking]](减少逐步喂回的次数)、或 DAgger(让专家在模型飘到的新状态上补标动作)。Lumine 靠的就是 2424h 大数据 + chunking + 阶段化课程。

## 怎么做的
```
# 行为克隆：纯监督
收集 D = {(状态 s_i, 专家动作 a_i)}        # 人类演示
训练 π：minimize  Σ loss(π(s_i), a_i)      # 预测专家会做什么
# 对照 RL：没有 reward、没有环境交互、不探索
```

## 代码出处 / 来源
- [[lumine]] · 三阶段纯模仿(预训练行为克隆 → 指令跟随 → 推理),零 RL
- 经典:Behavior Cloning、DAgger(Ross et al. 2011)

## 链接
- [[lumine]] · 用模仿学习替代 RL 玩开放世界
- [[rl-for-llm-people]] · 对照范式:试错 + reward
- [[policy-gradient]] · RL 的核心,模仿学习不用它
- [[action-chunking]] · 缓解模仿的误差累积
- [[rlhf]] · 先 SFT(本质是模仿)再 RL,两者常组合
