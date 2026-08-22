---
name: residual-stream
type: concept
sources: [global-workspace]
updated: 2026-08-18
---

# Residual stream · Transformer 每层共用的工作底稿

## 一句话

Residual stream 是每个 token 随层数不断改写的一条向量，attention 和 FFN 都从它读、再把新结果加回去。

## 直觉

把一道题写在白板上。第 1 组人标出关键词，第 2 组人补关系，第 3 组人算中间答案；每组都不另起一块白板，而是在同一块白板上添笔。Transformer 里的这块白板就是 residual stream。

它不是 KV cache。KV cache 保存过去 token 在各层算出的 Key / Value，供以后的位置读取；residual stream 是当前层、当前位置正在被加工的主状态。

## 怎么做的

把第 \(\ell\) 层输入记作 \(h_\ell\)，一个典型 Transformer block 可简写成：

\[
u_\ell=h_\ell+\operatorname{Attn}_\ell(h_\ell),
\qquad
h_{\ell+1}=u_\ell+\operatorname{MLP}_\ell(u_\ell).
\]

- \(h_\ell\)：进入第 \(\ell\) 层的 residual-stream 向量。
- \(\operatorname{Attn}_\ell\)：从本位置与其他位置搬来相关信息。
- \(\operatorname{MLP}_\ell\)：在每个位置上做非线性变换。
- 两个加号：新计算不是把旧状态整块覆盖，而是作为修正量写回同一条流。

最后一层的状态经 normalization 和 unembedding 矩阵 \(W_U\) 变成词表分数：

\[
z=W_U\operatorname{norm}(h_L).
\]

## 数字例子

设当前 token 的底稿是 \(h_0=[2,1]\)。attention 找回一条修正 \([0.5,-0.2]\)：

\[
u_0=[2,1]+[0.5,-0.2]=[2.5,0.8].
\]

MLP 再写回 \([-0.1,0.7]\)：

\[
h_1=[2.5,0.8]+[-0.1,0.7]=[2.4,1.5].
\]

旧信息没有消失；两次计算都只在底稿上添改。解释工具读取中间层时，看的就是这些 \(h_\ell\)。

## 链接

- [[global-workspace]] · J-lens 逐层读取 residual stream，并在其中做替换与删除实验。
- [[residual-connection]] · 为什么用加法把旧状态和修正量接起来。
- [[kv-cache]] · 与“保存过去位置的 K / V”区分。

