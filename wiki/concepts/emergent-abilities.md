---
name: emergent-abilities
type: concept
sources: [gpt-3]
updated: 2026-05-21
---

# Emergent Abilities · 涌现能力 · 小模型 ≈ 0 大模型突然能

## 一句话
某些任务上小模型的表现接近随机，到了某个模型 size 阈值后<strong>突然</strong>跳到接近完美。这种"相变"叫 emergence。

## 直觉
正常 scaling 期望是：模型大一倍 → 性能涨一点。线性预测。

Emergence 描述的是另一种情况：从 125M 到 13B 都接近 0 分 → 到 175B 突然跳到 80 分。中间没有平滑过渡。

类比：水温从 99°C 升到 100°C，只升 1 度但<strong>相变</strong> —— 液态变气态。模型从某 size 升到下一档，能力可能也<strong>相变</strong> —— 从"做不到"变成"能做"。

## GPT-3 论文里看到的例子
- **3 位数加法**：125M / 350M / 760M / 1.3B / 2.7B 都接近 0%；6.7B 跳到 ~10%；175B 跳到 80%+
- **3 位数减法**：类似曲线
- **2 词 cycle 模式识别**：到 13B 才浮现
- **复杂三段论推理**：175B 才达到可用
- **In-context learning 本身**：1.5B (GPT-2) 几乎不 work；6.7B 开始稳定；175B 才形成强能力

GPT-3 论文 Fig 1.3 用一组任务展示这种"hockey stick"曲线 —— 多数任务在 13B-175B 之间突然抬头。

## 为什么会有 emergence
开放问题。几个假设：
1. **门槛效应**：某个能力需要 N 层 attention 才能在内部 routing 出来。N 不够时为 0，达到后变完美
2. **数据效率**：大模型记住了更多 prompt 模式样本，触发率从随机变成稳定
3. **测量假象**（Anthropic 2023 提出）：用错了 metric（如 exact-match）让平滑曲线看着像突变。改用 log-scale + 部分正确分数后，"涌现"变成连续上升

不论哪种解释，<strong>实践上确实存在"小于这个 size 跑不动"的工程现象</strong>。LLM 路线图很大程度上是"凑齐 size 解锁能力"。

## 跟 scaling laws 的关系
[[scaling-laws]]（Kaplan et al. 2020）说 LM loss 跟参数 / 数据 / 算力满足 power law —— 一条平滑曲线。emergence 是 scaling laws 在<strong>具体任务 metric</strong>上的非平滑表现：底层 LM loss 在平滑下降，但下游任务 accuracy 表现为阈值跳跃。

两者不冲突：底层平滑改善 + metric 的离散性 = 表观上的相变。

## 工程含义
- **不能从小模型外推**：13B 跑不通的任务不一定 175B 也跑不通。要试更大尺寸
- **能力解锁靠 size**：reasoning / tool use / 长上下文记忆等能力需要相应阈值。这是为什么 Anthropic / OpenAI / Google 在不停烧钱做更大模型
- **小模型时代的方法可能失效**：BERT 时代的 finetune 在 GPT-3 这种 size 下被 ICL 替代 —— scale 让方法本身换代

## 后续争议
2023 Anthropic 写 "Are Emergent Abilities of Large Language Models a Mirage?" 论文质疑 emergence 是不是 metric artifact。结论：很多<strong>看似的 emergence 是 metric 选择问题</strong>（如 0/1 exact-match），换 token-level metric 后变平滑。

但 reasoning / tool-use / long-context 这类<strong>真正的复杂能力</strong>仍表现出非线性涌现，不只是 metric 问题。

## 链接
- [[gpt-3]] · 首次系统记录
- [[scaling-laws]] · 底层平滑曲线
- [[in-context-learning]] · ICL 本身是一种 emergent ability
