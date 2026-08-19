---
name: forever-cache
type: concept
sources: [avatar-forever]
updated: 2026-08-19
---

# ForeverCache · 同一个 chunk 的四次去噪，历史只算第一遍

## 一句话

生成当前 chunk 时，历史 chunk 是固定的，只有当前噪声 latent 在变化；ForeverCache 在第一个去噪步完整计算一次历史特征，后续步骤只算当前 token，并从每层缓存读取历史条件。

## 和普通 KV cache 的差别

LLM 的 KV cache 通常跨“下一个 token”持续追加。ForeverCache 的生命周期更短：它服务于**同一个视频 chunk 内的多个去噪步**；切到下一个 chunk 时，历史窗口变了，缓存立即重建，内存因此有界。

## 四步生成的算账

假设可见窗口包含 2 份历史 token 和 1 份当前 token，粗略把每份算力记为 1：

- 不缓存：4 个去噪步都算 \(2+1\)，总成本约 \(4\times3=12\) 份；
- ForeverCache：第 1 步算 3 份，后 3 步各算 1 份，总成本约 \(3+3\times1=6\) 份。

真实 attention 不是线性成本，而且缓存还要读写，所以不会真的恰好快 2 倍。论文报告 5 秒视频吞吐提升 23.6%，30 秒视频提升 45.5%。

## 缓存里是什么

论文不是只缓存最终一组 K/V，而是在 \(L\) 个 Transformer block 各存一份历史上下文特征 \(\mathcal C_k^\ell\)。后续 current token 在视频 self-attention、音频 self-attention 和音视频 cross-attention 中都能读取对应层的历史。

## 质量为什么可能略降

第一个去噪步看到的是最吵的当前 chunk；缓存下来的历史特征此后不再随着当前 chunk 变干净而共同刷新。这换走了冗余计算，也近似了原模型“每步重新联合编码历史与当前”的行为。论文结果里缓存版速度更快，但整体质量略低于不缓存版。

## 链接

- [[avatar-forever]] · 公式 (7)–(9) 与实验
- [[kv-cache]] · Transformer 缓存的基础概念
- [[prefill-decode]] · “先完整算一次、之后只算新增部分”的共同结构
