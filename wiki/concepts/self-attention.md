---
name: self-attention
type: concept
sources: [attention-is-all-you-need, vit]
updated: 2026-05-28
---

# Self-Attention · 自注意力

## 一句话
对序列里每个位置，用 Q·Kᵀ/√dₖ 算它跟所有位置的相似度，softmax 当权重，加权求和 V → 输出。

## 直觉
"自注意力"的"自"是因为 Q、K、V 都从**同一个序列**生成（cross-attention 是 Q 从一个序列、K/V 从另一个）。

类比：你读一句话"猫坐在垫子上"，理解"坐"这个字时，你的脑子会**同时看**周围的"猫"和"垫子"判断这是什么场景。自注意力就是把这个"同时看周围"做成显式计算 —— 而且每个 token 都这么干，互相看。

## 怎么做的
对每个 token x：
```
Q = x · W_Q     # 这个 token 在"问什么"
K = x · W_K     # 这个 token 提供"什么 key"
V = x · W_V     # 这个 token 提供"什么 value"
```

然后整个序列：
```
scores  = Q · Kᵀ / √dₖ        # N×N 相似度矩阵
weights = softmax(scores)      # 行内归一化, 每行 sum=1
output  = weights · V          # N×dᵥ 加权求和
```

**复杂度**：O(N² · d)。N 维度可并行（GPU 友好）。

**√dₖ 缩放**：dₖ 大时 dot product 数值容易爆 → softmax 进饱和区梯度消失。除 √dₖ 把方差控回 1 量级。

## 跟 RNN attention 的区别
- Bahdanau 2014 的 attention：作为 RNN 的辅助，给 decoder 看 encoder 输出
- 这里：**attention 本身就是层**，没有 RNN

## 重要变种
- **Causal self-attention**：mask 掉未来位置（decoder-only LLM 用这个）
- **Cross-attention**：Q 从 decoder，K/V 从 encoder
- **Multi-head** ([[multi-head-attention]])：跑 N 次自注意力，每次用不同投影

## 链接
- [[dot-product]] · Q·Kᵀ 注意力分数就是点积
- [[softmax]] · 分数→权重(和为1)；√d 防它太尖
- [[attention-is-all-you-need]] · 论文
- [[multi-head-attention]] · 上层扩展
- [[positional-encoding]] · 解决 attention 无序问题
- [[transformer-architecture]] · 整体架构
