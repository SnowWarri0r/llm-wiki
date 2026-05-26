---
name: rotary-position-embedding
type: concept
sources: [rope]
updated: 2026-05-25
---

# Rotary Position Embedding · RoPE · 旋转位置编码

## 一句话
不给 embedding 加位置向量，而是**按位置旋转 Q 和 K** —— 让 attention 点积天然包含相对位置信息。

## 直觉 · 时钟指针

想象你手里有两根指针，一根代表 token A（位置 m），一根代表 token B（位置 n）。

RoPE 做的事：**把 A 的指针转 m 圈，把 B 的指针转 n 圈**。

现在你量两根指针之间的角度差 = m − n 圈 = **相对位置**。

你不需要查表、不需要额外参数、不需要知道 m 和 n 各自是多少 —— **只要看两根针的夹角**就知道它们差几个位置。而且不管绝对位置怎么变（m=5, n=8 跟 m=105, n=108），差 3 个位置的指针夹角永远一样。

这就是"旋转编码相对位置"的全部直觉。

## 跟 sinusoidal PE 对比 · 为什么旋转比加法好

| | Sinusoidal PE (原版) | RoPE |
|---|---|---|
| 位置信息怎么进模型 | **加**在 embedding 上（input 层一次性注入） | **旋转** Q/K 向量（每层 attention 都重新注入） |
| 什么时候生效 | 只在第 0 层，往后逐层稀释 | 每一层 attention 都有，不稀释 |
| 编码的是 | 绝对位置（模型自己去学相对位置） | **直接就是相对位置**（点积里天然出来） |
| 外推到更长序列 | 理论能 sin/cos 外推，实际效果差 | 配合频率缩放（NTK/YaRN）可以外推到 128K+ |
| 额外参数 | 0 | 0 |
| 跟 KV cache 兼容 | 可以 | 完美兼容（旋转只作用于 Q/K，cache 里存的是旋转后的 K） |

## 怎么做的 · 伪代码版

d 维向量不是整体旋转（那没意义）。实际做法：**把 d 维拆成 d/2 对 2D 子空间，每对用不同的频率旋转**。

```python
# d_model = 64 → 32 对 2D 子空间
# 每对 i 用频率 θ_i = 10000^(-2i/d)

def rope(x, position):
    """x: [seq_len, d_model], position: int"""
    d = x.shape[-1]
    half = d // 2
    
    # 32 个不同频率
    freqs = 1.0 / (10000 ** (torch.arange(0, d, 2) / d))
    
    # position × 每个频率 = 每对子空间的旋转角度
    angles = position * freqs  # [half]
    
    cos_a = torch.cos(angles)
    sin_a = torch.sin(angles)
    
    # 把 x 拆成偶数维和奇数维（每对的两个分量）
    x_even = x[..., 0::2]  # 第 0, 2, 4, ... 维
    x_odd  = x[..., 1::2]  # 第 1, 3, 5, ... 维
    
    # 2D 旋转公式
    out_even = x_even * cos_a - x_odd * sin_a
    out_odd  = x_even * sin_a + x_odd * cos_a
    
    # 交错合并回去
    return interleave(out_even, out_odd)
```

关键点：
- 这段代码对 Q 和 K 各做一次（用各自的 position）
- 然后正常做 Q·K^T —— 点积结果里就自动包含了相对位置
- **V 不旋转** —— 位置信息只在 attention score 里起作用，不影响 value 的内容

## 多频率 · 跟音乐的类比

d/2 对子空间，每对频率不同：

- 低频对（i 小）→ 旋转慢 → 对**长距离**位置差异敏感
- 高频对（i 大）→ 旋转快 → 对**短距离**位置差异敏感

就像：
- 低音鼓 → 标记大拍（每小节）
- 高音钹 → 标记小拍（每拍内部）

合在一起就是一个**多尺度的位置指纹** —— 每个位置在不同频率上有唯一的组合，跟 sinusoidal PE 的多频率思路一脉相承。

## 为什么点积能捕获相对位置

数学上一句话：**2D 旋转是正交变换 —— 保持向量长度不变、只改变方向**。

所以 Rotate(Q, m) · Rotate(K, n) 里面：
- Q 和 K 原始的语义相似度（夹角）完好保留
- 多出一项 cos((m−n)×θ) —— 这就是**相对位置的贡献**

不需要加偏置、不需要改 attention 公式、不需要额外参数。**旋转本身就把相对位置塞进了点积**。

## 距离衰减 · 远的词影响自然变小

RoPE 还有一个好性质：**当两个 token 距离越远，位置对 attention score 的贡献越弱**。

直觉用拔河想：32 个频率 = 32 根绳子。距离近时所有绳子朝同一方向拉（cos 都接近 +1），合力大 → 位置信号强。距离远时每根绳子正负各异（有的 +0.3 有的 -0.7），互相抵消，合力趋近于零 → 位置信号弱。**距离越远，绳子方向越"各说各话"，加起来越接近零**。

这意味着 RoPE **自带一个软窗口效应** —— 不需要显式 mask 长距离，模型天然更关注近处。

## 代码出处
- 原论文：Su et al. 2021, arXiv 2104.09864
- HuggingFace transformers 里 LlamaRotaryEmbedding 是最标准的参考实现
- 几乎所有 LLaMA / Mistral / Qwen 代码库都有

## 链接
- [[positional-encoding]] · PE 家族全景
- [[relative-position-encoding]] · 为什么相对位置好
- [[self-attention]] · RoPE 作用的位置（Q·K^T 之前）
- [[kv-cache]] · 缓存旋转后的 K，推理时不重复计算
