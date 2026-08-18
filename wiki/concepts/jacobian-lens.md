---
name: jacobian-lens
type: concept
sources: [global-workspace]
updated: 2026-08-18
---

# Jacobian lens · 把中间向量翻成“它可能让模型说什么”

## 一句话

J-lens 用平均 Jacobian 近似中间层到输出层的变化，再借模型自己的词表输出层把中间状态翻成候选词。

## 直觉

直接把第 30 层的向量塞进最后一层词表投影，像拿三楼半成品去套一楼出货标签：坐标系还没对齐。J-lens 先估一张“三楼的一个小改动，平均会怎样传到出货口”的转换表，再读词表。

它回答的不是“模型下一词一定说什么”，而是“这段内部活动通常有能力把哪些词推向未来输出”。

## 怎么做的

对第 \(\ell\) 层位置 \(t\) 的 residual stream \(h_{\ell,t}\)，论文把它对当前及未来位置最终状态的 Jacobian 在 1,000 条提示、各位置上取平均：

\[
J_\ell=
\mathbb E_{t,\,t'\ge t,\,\text{prompt}}
\left[
\frac{\partial h_{L,t'}}{\partial h_{\ell,t}}
\right].
\]

- \(J_\ell\)：第 \(\ell\) 层到最终层的平均一阶传递矩阵。
- \(t\)：被检查的源 token 位置。
- \(t'\ge t\)：当前或未来输出位置；因果模型不会让当前位置影响过去。
- \(h_{L,t'}\)：最终层在位置 \(t'\) 的状态。

读一个中间向量时：

\[
\operatorname{lens}(h_\ell)
=\operatorname{softmax}
\left(W_U\operatorname{norm}(J_\ell h_\ell)\right).
\]

先用 \(J_\ell\) 把中间坐标变到最终层附近，再归一化、乘 unembedding \(W_U\)，最后 softmax 得到词表排名。

## 数字例子

假设中间状态 \(h=[2,1]\)，平均传递矩阵与三词输出矩阵为：

\[
J=\begin{bmatrix}1&0.5\\0&2\end{bmatrix},
\qquad
W_U=\begin{bmatrix}1&0\\0&1\\-1&0\end{bmatrix}.
\]

先对齐坐标：

\[
Jh=[2.5,2].
\]

暂时省略 normalization，三个词的 logit 是：

\[
W_UJh=[2.5,2,-2.5].
\]

softmax 后约为 \([0.62,0.38,0.004]\)。第一个词排第一。若直接把 \(h\) 送进 \(W_U\)，logit 会是 \([2,1,-2]\)，说明少了层间坐标修正，排名与差距都可能变。

## 跟 logit lens 的对照

- logit lens 相当于把 \(J_\ell\) 当单位阵，快，但早层坐标错位更严重。
- tuned lens 训练一个线性映射去拟合最终输出，善于猜答案，却可能跳过真正的中间步骤。
- J-lens 来自输出对内部激活的导数，因果联系更直接；但它仍是一阶、跨上下文平均的近似。

## 链接

- [[global-workspace]] · J-lens 的提出与主要实验。
- [[residual-stream]] · 被读取的中间状态是什么。
- [[jacobian-vector-product]] · Jacobian 描述“小改动怎样传到输出”。
- [[activation-intervention]] · 如何沿 J-lens 方向写入、删除或互换概念。

