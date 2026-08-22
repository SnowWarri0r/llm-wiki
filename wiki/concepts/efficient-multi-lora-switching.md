---
name: efficient-multi-lora-switching
type: concept
sources: [uniswap-av]
updated: 2026-08-18
---

# Efficient Multi-LoRA Switching · 一套冻结主干，轮流扮演三个 DMD 角色

## 一句话

Teacher、Generator、Critic 不各存一套巨型模型，只各带一份 LoRA，需要谁就临时挂谁。

## 直觉

三位检验员都使用同一台昂贵仪器，只是各自有一块不同的校准片。没必要买三台仪器；轮到谁工作，就换上谁的校准片。

省下的是三套 backbone 参数常驻显存，不是三位角色的计算。Teacher、Generator、Critic 仍要分别前向。

## 怎么做的

令冻结主干权重为 \(W_0\)，第 \(r\) 个角色的 LoRA 更新为 \(B_rA_r\)：

\[
W_r=W_0+B_rA_r,
\qquad
r\in\{T,G,D\}.
\]

- \(W_0\)：共享且不更新的 LTX-2.3 权重；
- \(A_r,B_r\)：第 \(r\) 个角色的小型低秩矩阵；
- \(T/G/D\)：Teacher、Generator、Critic；
- 一次前向只启用对应角色的 \(A_r,B_r\)。

UniSwap 中，Teacher 用冻结 Stage-1 LoRA，Generator 从 Stage-2 LoRA 初始化，Critic LoRA 随机初始化。最终只保留 Generator LoRA。

## 数字例子

把一层 \(4096\times4096\) 的矩阵当作主干：

\[
4096\times4096=16{,}777{,}216
\]

个参数。三份完整副本要 \(50{,}331{,}648\) 个参数。

若 LoRA rank 为 128，每个角色只需两块矩阵：

\[
4096\times128+128\times4096=1{,}048{,}576.
\]

一份主干加三套 LoRA共有：

\[
16{,}777{,}216+3\times1{,}048{,}576
=19{,}922{,}944.
\]

相比三份完整矩阵，参数常驻量约减少 60.4%。这只是单层教学账，真实模型还要算多层、优化器状态和激活；论文实测峰值显存从 80 GB 卡上 OOM 降到 65.34 GB。

## 边界

- 顺序切换角色会省显存，但训练总前向次数没有消失。
- 三个角色必须共享同一 backbone 结构；完全不同架构无法靠换 LoRA 扮演。
- 若同时需要三套角色的梯度或激活，峰值显存仍可能由激活而非参数主导。

## 链接

- [[uniswap-av]] · 三阶段蒸馏里的具体用法。
- [[lora]] · 低秩增量怎样挂到冻结权重上。
- [[dmd-distillation]] · 为什么要 Teacher、Generator 与 Critic 三种角色。
