---
name: recovery-oriented-rollout-training
type: concept
sources: [avatar-forever]
updated: 2026-08-19
---

# RRT · 等错误滚起来以后，再教模型怎么救回来

## 一句话

Recovery-oriented Rollout Training 先污染最早的历史块，再让模型用自己的输出连续生成 (K) 个块；这些中间块不反传，最后只用标准 flow-matching loss 训练第 (K+1) 块从真实的累积漂移中恢复。

## 为什么不在污染后立刻监督

如果把一张历史图加点噪声，马上要求模型还原下一块，模型学到的是“一次性修图”。线上真正的问题却是：第 1 块的小错被第 2 块当历史，第 2 块的新错又被第 3 块继承，错误的形状会被模型自己的动力学改变。

RRT 因此把训练题目改成：**先让错误沿部署时的路径传播，再考恢复。**论文的消融也支持这点：\(K=0\) 仍会出现斑点和全局色漂，\(K=4\) 最稳。

## 完整数据流

1. 把视频 latent 切成 \(\mathbf c_0,\mathbf c_1,\ldots,\mathbf c_{K+1}\)。
2. 只对最早历史做退化：\(\hat{\mathbf c}_0=\mathcal D(\mathbf c_0)\)。
3. 用模型自己的预测依次生成 \(\hat{\mathbf c}_1,\ldots,\hat{\mathbf c}_K\)，并用 stop-gradient 截断这段轨迹。
4. 给真实目标 \(\mathbf c_{K+1}\) 加噪，令模型在漂移历史 \(\hat{\mathbf c}_K\) 条件下预测 flow velocity。
5. 只更新最后这一步；中间 rollout 的作用是制造真实训练分布，不是当监督目标。

## 一个五块例子

Avatar-Forever 取 \(K=4\)。假设最早历史的肤色偏差只有 \(+2\)，模型连续复用自己的输出后，四块误差变成 \(+2,+3,+5,+7\)。普通退化训练只见过 \(+2\)；RRT 的最终监督直接在 \(+7\) 的历史条件下要求第 5 块回到正确肤色。这个数字只是教学示意，论文没有把误差压成标量。

## stop-gradient 在这里的真正作用

它不是说中间模型被冻结、下一轮才能比较，而是把 rollout 当成“造题器”：只需要它产生部署时会遇到的坏历史，不需要保存四个 chunk、每个 denoising step 的反向图。否则 22B 模型的显存和计算开销会沿 \(K\times T\) 急剧增长。

## 链接

- [[avatar-forever]] · RRT 的原始论文与全部公式
- [[flow-matching]] · 最后一步使用的标准速度回归
- [[chunk-wise-self-forcing]] · 同样让模型在训练时看见自己的历史
- [[stop-gradient]] · rollout 为什么只造数据、不接梯度
