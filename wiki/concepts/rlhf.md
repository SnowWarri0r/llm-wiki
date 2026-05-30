---
name: rlhf
type: concept
sources: [ppo]
updated: 2026-05-28
---

# RLHF · Reinforcement Learning from Human Feedback

## 一句话
**人类用排序代替评分**: 把"哪个回答更好"这种廉价标注转成 reward model, 再用 PPO 把 LLM 训成"按人类偏好回答"的样子 —— 这是 ChatGPT 从"会预测下一个 token 的模型"变成"会聊天的助手"的关键一步。

## 直觉 · 预训练 + SFT 还不够, 为什么

GPT-3 训完后会生成"网上文本风格"的回答, 但**网上的文本不是"好对话"**. 你问它"怎么做番茄炒蛋", 它可能开始随机模仿网上某个帖子, 越扯越远。

第一道补丁: **SFT** (Supervised Fine-Tuning). 雇一批人写"问答对", LLM 学着模仿。这一步把 GPT-3 变成 InstructGPT 的雏形, 但还不够好 —— 因为:

1. **写"完美答案"很贵很慢**. 几万对 SFT 数据已经是天文数字, 但远不够覆盖所有问题
2. **"什么是好答案"很模糊**. 一个问题往往有多个合理回答, 写一个"标准答案"反而把模型框死

更便宜也更准的标注方式: **让人在 LLM 生成的两个回答里选哪个更好**.

- 给一个 prompt → LLM 采样 2 个回答 A 和 B
- 人来评: "A 比 B 好" or "B 比 A 好"
- **这种标注每条只要几秒, 不需要写答案, 不需要专业知识**

但选哪个更好 ≠ 直接可用的 loss. 怎么把"排序标注"转成 LLM 训练信号?

**RLHF 的核心 trick**: 训一个 reward model 学排序, 再用 PPO 让 LLM 最大化 reward.

## 三步流程

### Step 1: SFT (监督微调)

雇一小批专业标注员写高质量问答对 (~10K 量级). 直接 cross-entropy fine-tune 让 GPT-3 学会"对话风格".

```
input: "How do I bake a cake?"
output: "To bake a cake, you'll need..." (人工写)

loss: 标准 next-token cross entropy
```

这一步产物: **SFT 模型** (能聊但偏好不对齐).

### Step 2: 训 reward model

让 SFT 模型对同一个 prompt 采样多个回答 (一般 4-9 个), 让标注员两两比较, 标"这个比那个好".

```
prompt: "解释一下黑洞"
response_A: <较好的回答>
response_B: <较差的回答>
label: A > B
```

把这种 (prompt, response_A, response_B, "A 好") 标注数据**几十万条**收齐, 训一个独立的 reward model RM:

```python
RM: (prompt, response) → scalar reward
loss = -log σ( RM(prompt, A) - RM(prompt, B) )   # Bradley-Terry 模型
```

意译: "希望 RM 给 A 的分比 B 高". 训完后 RM 能给任意 (prompt, response) 打一个"人类觉得好不好"的分数.

这一步产物: **reward model** (能预测人类偏好).

### Step 3: PPO 用 RM 当 reward 训 LLM

现在好了 —— 我们有了一个 "判官" (RM), 可以给任何回答打分. 用 [[ppo]] 把 LLM 训成"会拿高分的样子":

```python
for batch in range(many_batches):
    prompts = sample_prompts()
    
    # LLM 自己生成回答 (rollout)
    responses = LLM.generate(prompts)
    
    # 用 reward model 算 reward
    rewards = RM(prompts, responses)
    
    # 关键修正: 加一项 KL penalty, 让 LLM 别离 SFT 模型太远
    kl = compute_kl(LLM, SFT_frozen)
    final_rewards = rewards - β * kl
    
    # PPO 更新
    advantages = compute_gae(final_rewards, value_net(states))
    ppo_loss = clipped_surrogate(LLM, prompts, responses, advantages)
    ppo_loss.backward()
```

这一步产物: **最终 chat 模型** (跟人偏好对齐).

## KL penalty: 防止 reward hacking

第 3 步如果只是"maximize RM 得分", LLM 会**过拟合 reward model 的 bug**:

- RM 喜欢长回答 → LLM 学到"啰嗦点能拿高分" → 输出越来越冗长
- RM 给 "Certainly!" 高分 → LLM 每个回答都以 "Certainly!" 开头
- RM 给 markdown 加分 → LLM 强行把所有回答都加列表和粗体

工程上发现的最有效缓解: **加一个 KL 散度 penalty, 让 LLM 不要偏离 SFT 模型太远**:

```
reward = RM(prompt, response) - β × KL(LLM ‖ SFT_frozen)
```

β 一般 0.01~0.1. 直觉: SFT 模型是"健康的语言模型基线", 偏离太远说明 LLM 在为了高分变形.

## 历史定位 · ChatGPT 的关键一步

- **InstructGPT** (OpenAI 2022 Jan): 第一次用 RLHF 训 GPT-3 → 跟 GPT-3 base 比对话能力质变. 这是 RLHF 在 LLM 端的首次大规模应用
- **ChatGPT** (2022 Nov): InstructGPT 的对话版, 用了同一套 RLHF pipeline. 上线 5 天用户破百万, 引爆了 LLM 应用浪潮
- **GPT-4 / Claude / Gemini / Llama-chat**: 全部用 RLHF 或它的变种
- **DPO** (2023): 跳过 reward model, 直接用对比学习训 LLM, 工程更稳, 现在很多开源模型选 DPO
- **GRPO** (DeepSeek 2024): PPO 的简化版, 去掉 value network 用相对得分当 advantage, 配合 reasoning 训练 (R1 系列)

## 跟传统 RL 的区别

| 维度 | 传统 RL (玩游戏) | RLHF (训 LLM) |
|---|---|---|
| Reward 来源 | 环境硬编码 (得分 / 输赢) | Reward model 学出来的 |
| Episode 长度 | 几百到几千步 | 几十 token, 一句话就完 |
| Action 空间 | 离散少 (上下左右) 或连续低维 | 词表大小 (~50K) |
| 探索 | 关键 (要尝试新策略) | 弱 (LLM 已经预训练得够好, 只是对齐) |
| KL 约束 | 通常没有 | 必有, 防止偏离 SFT |
| 训练成本 | 几百万 episode | 几百万 GPU 小时 |

## 链接
- [[ppo]] · RLHF 的训练算法主力
- [[grpo]] · PPO 的 LLM 友好简化版本
- [[policy-gradient]] · RLHF 的数学基础
- [[advantage-function]] · PPO 里的关键信号
- [[gpt-3]] · RLHF 的训练对象
