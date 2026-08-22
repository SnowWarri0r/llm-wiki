---
name: stop-gradient
type: concept
sources: [dmd, chunk-wise-self-forcing, avatar-forever]
updated: 2026-08-19
---

# Stop-gradient · 数值继续往前，梯度到此为止

## 一句话

(operatorname{sg}(x)) 的前向值仍等于 (x)，但反向导数被规定为 0：后面的计算可以使用它，优化器却不会沿这条支路回去修改产生 (x) 的过程。

## 最小例子

设 (y=w^2)，损失为：


\[
L=(w-operatorname{sg}(y))^2.
\]

当 (w=2) 时，前向仍得到 (y=4,L=(2-4)^2=4)。反向时右侧的 (y) 被当成常数，所以：


\[
\frac{dL}{dw}=2(w-y)=2(2-4)=-4.
\]

如果没有 stop-gradient，(y=w^2) 也参与求导，还要乘上 (dy/dw=2w)，得到完全不同的梯度。

## 它不是什么

- 不是永久冻结整套模型；下一批数据仍可正常更新同一组参数。
- 不是丢弃前向结果；结果照样能作为下一 chunk 的历史。
- 不是让两次模型变成不同权重；它只切断当前计算图的一条反向路径。

## 在 Avatar-Forever 里

RRT 让 22B 模型连续滚出 4 个中间 chunk，每个 chunk 又含 30 个去噪步。中间结果要继续向前传播，才能形成部署时真实的坏历史；但如果保留整个反向图，显存和计算会沿 \(K\times T\) 急剧增加。因此中间 rollout 使用 stop-gradient，只让最后的恢复 chunk 反传。

## 链接

- [[gradient-backprop]] · 反向传播基础
- [[recovery-oriented-rollout-training]] · 无梯度 rollout 的完整用途
- [[chunk-wise-self-forcing]] · 分块自回归里相同的截断思想
- [[dmd-distillation]] · 伪损失怎样用 stop-gradient 注入指定梯度
