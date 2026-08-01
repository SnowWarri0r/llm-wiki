---
name: sparse-context-forcing
type: concept
sources: [wonder-video-world-model]
updated: 2026-07-29
---

# Sparse Context Forcing · 先练会“少看历史”，再开稀疏记忆

## 一句话

历史完整保存、摘要负责挑块、完整 KV 负责读取；训练时还随机断掉远端连接，让模型提前适应推理时只能看到少数旧块。

## 直觉

长视频若让新 chunk 看全部历史，attention 会越来越慢。只留最近窗口又会忘记远处看过的房门。Wonder 把两件事分开：

1. **存什么**：每块保存完整 K/V，另存很小的 key 摘要。
2. **本轮算什么**：一定看开头和最近块，再按摘要相似度挑 top-k 旧块；只把这些块的完整 K/V 送进 attention。

但直接在部署时把历史砍稀会翻车，因为训练时模型一直吃满上下文。Sparse Context Forcing 在 ODE 初始化阶段随机丢掉可选历史边，先把这种缺历史的工作方式练熟。

## 怎么做的

活跃块：

\[
\mathcal A_t=\{0\}\cup\mathcal N_r(t)\cup
\operatorname{TopK}_k\{\operatorname{sim}(\bar Q_t,\bar K_c)\mid c\in\mathcal M(t)\}.
\]

- \(\mathcal A_t\)：当前块 \(t\) 真正会读取的历史块。
- \(\{0\}\)：首块，作为身份/场景锚点。
- \(\mathcal N_r(t)\)：最近 \(r\) 块；Wonder 取 \(r=2\)。
- \(\mathcal M(t)\)：除首块和最近块外的中段历史。
- \(\bar Q_t,\bar K_c\)：池化后的 query/key 摘要。
- \(\operatorname{sim}\)：摘要相似度；论文没公开具体形式。
- \(k\)：从中段挑几块；论文没公开取值。

训练掩码：

\[
M^{(\ell)}_{ij}
=\mathbf1[a(i,j)\in\mathcal R]
+b^{(\ell)}_{ij}\mathbf1[a(i,j)\in\mathcal O],
\qquad
b^{(\ell)}_{ij}\sim\operatorname{Bernoulli}(1-p_\ell).
\]

必须边 \(\mathcal R\) 永远开；可选边 \(\mathcal O\) 以 \(1-p_\ell\) 的概率保留。每层、每次前向都重抽。

## 数字例子

历史块是 0–7，当前生成第 8 块。设 \(r=2,k=2\)：

```text
固定首块：{0}
固定最近：{6,7}
中段候选：{1,2,3,4,5}
相似度： [.15,.82,.20,.76,.11]
top-2：   {2,4}
最终 A₈： {0,2,4,6,7}
```

若每块 8 个 token，当前 query 也有 8 个：

```text
全历史 attention：8 × (8块×8 token) = 512 个分数
稀疏 active：      8 × (5块×8 token) = 320 个分数
历史涨到 100 块，只要 active 仍是 5 块，主 attention 仍是 320
```

再看训练掩码。取 \(p_\ell=.6\)，4 条可选边本轮伯努利样本为 `[1,0,0,1]`：

```text
必须边： [1,1]            → 永远保留
可选边： [1,0,0,1]        → 只保留第 1、4 条
最终：   [1,1 | 1,0,0,1]
```

自检：无论随机数怎样，前两条 required 都不会被关掉。

## 边界

固定的是 active attention 大小，不是总内存。完整历史 K/V 存储仍随 rollout 增长，摘要检索也要比较候选。Wonder v1 没公开 top-k、池化、相似度、drop rate 和一分钟后的淘汰策略。

## 链接

- [[wonder-video-world-model]] · 提出并用于实时长时记忆
- [[sparse-attention]] · 更广义的只计算少数 token 对
- [[kv-cache]] · 完整历史 K/V 存储
- [[self-attention]] · 最后仍用被选块的完整 K/V 做标准 attention
