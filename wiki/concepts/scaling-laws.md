---
name: scaling-laws
type: concept
sources: [gpt-3, vit, clip]
updated: 2026-05-28
---

# Scaling Laws · 模型 size 跟 loss 的经验公式

## 一句话
Kaplan et al. 2020 (OpenAI) 通过大量训练实验拟合出：**LM 的 loss 跟参数量 / 数据量 / 算力满足 power law**（幂律），给出可外推的预测公式。

## 直觉
"模型大效果好" 是直觉。Scaling laws 把它<strong>定量</strong>下来：
- 模型参数翻 10×，loss 大约下降固定多少
- 训练数据翻 10×，loss 下降另一个固定值
- 算力翻 10×（同时增加模型 + 数据），loss 又下降另一个固定值

具体公式（粗略）：
```
loss = a / (params)^α + b / (tokens)^β + c
```

α / β 这些指数都比 1 小（约 0.05-0.1），所以收益是 sub-linear 但<strong>始终在涨</strong>。没有看到 plateau。

## 为什么这事重要
**它把"训多大模型"从猜变成了预算决策**。OpenAI 在 GPT-3 之前用 scaling laws 推算：
- 想要 loss X
- 算力预算 Y
- 公式告诉你 → 训 N 层 / M 参数 / K token = 最佳配置

GPT-3 175B 这个数字不是拍脑袋拍的，是 scaling laws 算出来的：在那个时间点的算力预算下，175B 是最划算的 model size。

## Chinchilla 修正（2022）
Hoffmann et al. (DeepMind) 重新跑实验，发现 OpenAI 原版 scaling laws<strong>低估了数据需求</strong>：
- 原版 GPT-3 175B 用了 300B token，按 OpenAI 公式接近最优
- Chinchilla 实验：同样算力下，用 70B 参数 + 1.4T token 训练，结果比 GPT-3 还好

新结论："compute-optimal" 配比是 **每 1 参数配 ~20 token**。Chinchilla 70B/1.4T = 1/20 比例。GPT-3 175B/300B = 1/1.7 比例 —— 数据严重不足。

→ 2022 之后所有大模型（Llama / Claude / GPT-4）都按 Chinchilla 配比训：先确定参数量，再配 20× 的 token。

## 实践意义
1. **不再凭直觉烧钱**：训新模型前先用 scaling laws 算最优配置
2. **预测下一代能力**：知道当前 size 上 loss 是 X，可以外推到 10× 算力时 loss 是 Y，再外推 capability
3. **看准拐点**：emergence 通常出现在某些"能力 vs scale"曲线的拐点附近

## 它的局限
- 公式是<strong>语言建模 loss</strong>，不是<strong>下游任务 accuracy</strong>。loss 平滑下降不等于 task 平滑提升（参考 [[emergent-abilities]] 的非线性 jumps）
- 数据质量没建模：1T 高质量 token ≠ 1T 网页爬下来的垃圾
- 不外推到极端 scale：不知道 10T 参数会发生什么，公式可能在某个 size 上失效
- 不外推到 reasoning / tool use 这种复合能力

## 跟 emergent abilities 的关系
Scaling laws 描述<strong>底层 LM loss</strong>的平滑下降。Emergent abilities 描述<strong>具体下游任务</strong>的非平滑跳跃。两者不矛盾 —— 底层信号在涨，但 metric 上看像突变。详见 [[emergent-abilities]]。

## 链接
- [[gpt-3]] · 第一个被 scaling laws 指导设计的大模型
- [[gpt-2]] · 提供了 scaling laws 的早期数据
- [[emergent-abilities]] · 跟 scaling laws 互补
