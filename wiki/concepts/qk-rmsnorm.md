---
name: qk-rmsnorm
type: concept
sources: [ideogram-4, stable-diffusion-3-5, qwen-image-2, krea-2, drifting-models]
updated: 2026-07-22
---

# QK-Norm · 给 Q/K 做归一化稳住训练

## 一句话
在算 attention 分数之前，先对 Query 和 Key 各做一次 RMSNorm —— **防止点积越训越大、attention 塌成 one-hot 而炸训练**。

## 直觉 · 麦克风别开到爆音

attention 的核心是 `softmax(Q·K^T / √d)`。点积 Q·K 越大，softmax 出来的分布越尖。

深层大模型训着训着会出一个毛病：**Q 和 K 的数值幅度悄悄涨上去**（logit drift）。点积是两个大向量相乘，结果更大。一旦某个 logit 远超其它，softmax 几乎把全部权重压到一个 token 上 → attention 变成**near one-hot**：每个位置只盯死一个邻居，别的全看不见。

后果有两层：
- **表达力没了**：attention 本来该是"软地分配注意力到多个 token"，塌成 one-hot 等于退化成硬选择。
- **梯度炸了**：softmax 在尖锐区的梯度极不稳，loss 开始发散。ViT-22B 不加 QK-Norm 直接训不动。

类比：麦克风增益开太大，稍微有点声音就爆音削顶，细节全糊。**QK-Norm = 在进 softmax 这个"放大器"之前先把音量拉回标准档**。

## 怎么做的 · 一行 RMSNorm

```python
# 普通 attention
q = q_proj(x)
k = k_proj(x)
attn = softmax(q @ k.transpose() / sqrt(d))

# 加了 QK-Norm
q = q_proj(x)
k = k_proj(x)
q = rms_norm(q)          # ← 多这两行
k = rms_norm(k)          #   把 Q/K 的模长归一化
attn = softmax(q @ k.transpose() / sqrt(d))
```

RMSNorm 做的事：把向量除以它自己的均方根，**模长被拉到一个固定尺度**，只保留方向。这样不管训练把 Q/K 的幅度推到多大，进点积前都被压回标准档，logit 不会无限制膨胀。

为什么用 RMSNorm 不用 LayerNorm：RMSNorm 少算一个减均值，更省、更快，效果在这里没差别——现代模型（LLaMA 系、Qwen 系）默认都用它。

## 一个易错点 · 在 RoPE 之前

顺序是 **proj → QK-Norm → RoPE → 点积**。先归一化稳住幅度，再做 [[rotary-position-embedding]] 的旋转（旋转是正交变换、不改模长，所以放归一化后面不会破坏它）。反过来先 RoPE 再 norm 也有人做，但主流实现是 norm 在前。

## 为什么算"免费的午餐"

它几乎零成本：每层多两次 RMSNorm（相对整个 attention 的开销可忽略），换来的是**能开更高学习率、训练不发散、深层不塌缩**。所以从 ViT-22B 之后，大模型、现代扩散模型（含单流 [[diffusion-transformer]]）几乎都标配 QK-Norm —— [[ideogram-4]] 的 9.3B 单流 DiT 也用它来稳住深层 attention。

## 代码出处
- 提出：Scaling ViT to 22B Parameters, arXiv 2302.05442（QK-Norm 是其能稳训的关键之一）
- 现代实现：几乎所有新 LLM / DiT 的 attention 模块里都有 `q_norm` / `k_norm`

## 链接
- [[layernorm]] · 归一化家族，RMSNorm 是它的简化版
- [[self-attention]] · QK-Norm 作用在 Q·K^T 之前
- [[rotary-position-embedding]] · 顺序上 QK-Norm 在 RoPE 之前
- [[diffusion-transformer]] · 单流 DiT 也靠它稳深层训练
- [[ideogram-4]] · 9.3B DiT 的 attention 用到
- [[mmdit]] · 联合注意力里防 logit 爆炸；[[stable-diffusion-3-5]] 相比 SD3 的关键稳定性补丁
