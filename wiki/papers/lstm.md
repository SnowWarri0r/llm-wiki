---
name: lstm
type: paper
source: https://www.bioinf.jku.at/publications/older/2604.pdf
ingested: 2026-06-15
authors: [Sepp Hochreiter, Jürgen Schmidhuber]
year: 1997
---

# LSTM · 长短期记忆

## 一句话
给 RNN 加一条单独的"记忆传送带"(cell state)，更新主要靠加法、信息能原样带很远；再配三个门(遗忘/输入/输出)决定擦掉什么、写入什么、读出什么。治住 RNN 的梯度消失，是 Transformer 之前的序列霸主。

## 它要解决的痛点
普通 RNN 反向传播穿过多步、连乘同批权重×导数 → <1 越乘越小(梯度消失，学不到长程依赖)、>1 爆炸。实际只记得住几步。

## 核心贡献
- **cell state 记忆传送带**：单独一条从头通到尾的记忆通路，更新是加法 `C_t = f·C_{t-1} + i·g` → 信息和梯度都能带很远。
- **三个门(0~1 阀门)**：遗忘门 f(老记忆留多少) + 输入门 i·候选 g(写什么新的) + 输出门 o(读出 `h_t = o·tanh(C_t)`)。
- **加法梯度高速路**：梯度沿 C 每步 ≈ 乘遗忘门(≈1) 不缩水 → 不消失。与 [[resnet]] 残差 x+F(x) 同构(LSTM 在时间方向、ResNet 在深度方向)。
- GRU = 2 门简化版；LSTM 撑起 seq2seq + 最早的 attention，后被 [[attention-is-all-you-need]] 取代。

## 关键概念 → 概念页
- [[resnet]] · 加法梯度高速路同构(残差 x+F(x))
- [[attention-is-all-you-need]] · 用"任意位置直接互看 + 可并行"取代循环

## 我的批注 / 疑问
- 一句话记牢：**RNN 记不住远处；LSTM 修一条加法传送带 + 三个阀门，让记忆和梯度都能流很远**。"加法路径 = 梯度高速路"是反复出现的母题(LSTM 时间方向 / ResNet 深度方向)。
- pre-cutoff 经典(1997)，凭已有知识写；门控+加法记忆通路的思想留到今天。
- 待查：peephole connections / 各变体差异；GRU 的更新门重置门具体怎么省。
