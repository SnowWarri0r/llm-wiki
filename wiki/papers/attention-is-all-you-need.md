---
name: attention-is-all-you-need
type: paper
source: raw/attention-is-all-you-need.txt
upstream: https://arxiv.org/abs/1706.03762
ingested: 2026-05-20
authors: Vaswani et al. (Google Brain / Google Research) · NeurIPS 2017
---

# Attention Is All You Need · Transformer 始祖

整个 LLM 时代的奠基论文。所有现代大模型（GPT / BERT / Claude / Gemini / Qwen / Llama / fish-speech / TML interaction model）都是 transformer 的后代。

## 一句话
**砍掉 RNN 的"必须按时间步串行处理"枷锁**，用 self-attention 让序列里每个位置一次性看到所有其他位置，整个模型可并行训练，长程依赖也变成 O(1) 跳。

## 它要解决的痛点
2017 前的 SOTA 是 RNN/LSTM/GRU + attention（Bahdanau 2014 引入了 cross-attention 但只作为 RNN 的辅助）：

1. **串行瓶颈**：RNN 必须 t=0 算完才能 t=1，无法在 sequence length 维度并行 → 训练慢
2. **长程依赖衰减**：信息要逐步传递 N 步才到达远端，梯度沿路衰减
3. **难 scale**：参数量上去后 RNN 训练不稳定

CNN-based seq2seq（ConvS2S / ByteNet）尝试用空洞卷积并行化，但长程依赖仍是 O(log N) 跳。

## 核心贡献
1. **架构**：[[transformer-architecture]] —— 完全抛弃 recurrence，纯 attention + FFN 堆叠。Encoder 6 层 + Decoder 6 层。
2. **机制**：[[self-attention]] —— 每个 token 用 Q、K、V 三个投影，和序列里所有 token 做相似度加权求和。长程依赖 O(1) 跳。
3. **并行**：[[multi-head-attention]] —— 把 attention 跑 8 次，每个 head 用不同的 Q/K/V 投影，concat 后再线性。
4. **顺序信息**：[[positional-encoding]] —— attention 本身对位置不敏感，用 sinusoidal PE 把位置信息加进 embedding。
5. **稳定训练**：[[residual-layernorm]] —— Pre/Post-LN + residual 让深层 transformer 训得稳。

## 关键概念
- [[self-attention]] · Q·Kᵀ/√dₖ 然后 softmax 加权 V
- [[multi-head-attention]] · 多个 head 并行学不同模式
- [[positional-encoding]] · 给无顺序的 attention 加位置信息
- [[transformer-architecture]] · Encoder + Decoder 堆叠
- [[cross-attention]] · Decoder 看 Encoder 输出
- [[residual-layernorm]] · 让深层网络训得动

## 我的批注
- **最重要的洞察**：自注意力是 O(N²) 但 **N 维度可并行 + 长程 O(1)**，跟 RNN 的 O(N) 但**串行 + 长程 O(N)** 完全相反。算力换 wall-clock + 信息流，划算
- **scaled** 的 √dₖ 不是装饰，是为了 softmax 不进饱和区
- 论文里的 BLEU 是次要的，重要的是它**开辟了完全新的 scaling 路线** —— 现在所有 LLM 都在这条路线的延长线上
- **多头 ≠ 多次跑同一个 attention**：是用**不同的投影矩阵**学不同的关系模式（句法 / 语义 / 共指）
- **Positional encoding 是个工程妥协**：理论上 attention 应该完全置换不变，加 PE 是为了让它"知道顺序"。后来 Rotary PE / ALiBi 都在改进这部分
- 跟现代 LLM 的差异：现在的 GPT / Claude 都是 **decoder-only**（去掉 encoder + cross-attention），用 causal mask 让 decoder 既做"encoder"又做"decoder"

## 跟 wiki 里其他 paper 的关系
- [[fish-speech-s2-pro]] 的 Dual-AR 都是 decoder-only transformer
- [[interaction-models-tml]] 的 interaction model + background model 也都是 transformer 变种
- [[rvq-codec]] 用 transformer 作 encoder（waveform → 连续向量）
- [[flow-matching]] 用 transformer 作 velocity field 估计器
- 任何"X is all you need"标题都是在致敬这篇

## 历史定位
2017 之前：seq2seq 时代（Bahdanau attention 是辅助）  
2017 这篇：attention 上位为核心  
2018 GPT-1 / BERT：decoder-only / encoder-only 分化  
2020 GPT-3：scaling 验证 emergence  
2023+：所有现代大模型
