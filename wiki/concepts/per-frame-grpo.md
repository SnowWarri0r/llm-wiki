---
name: per-frame-grpo
type: concept
sources: [longcat-video-avatar-1-5]
updated: 2026-08-05
---

# Per-Frame GRPO · 让哪一秒出错，哪一秒承担梯度

## 一句话

普通视频级 GRPO 给整段视频一个 advantage；Per-Frame GRPO 把 reward 和 advantage 保留到时间分区，让短暂的坏手、不同步或动作异常不再被其余好帧平均掉。

## 公式

\[
\hat A^i_{k,j}=\frac{r^i_{k,j}-\mu_{k,j}}{\sigma^{\max}_{k,j}},
\qquad
\hat A^i_{\mathrm{total},j}=\sum_k w_k\hat A^i_{k,j}.
\]

(i) 是同一条件下第几条采样视频，(j) 是第几个时间分区，(k) 是奖励维度；(r) 是当前分数，(\mu) 是同组同时间的均值，(\sigma^{max}) 是稳定化标准差分母，(w_k) 是各奖励权重。LongCat 报告没有写全 max 的轴和数值稳定项，因此不能擅自补成某个标准 GRPO 实现。

## 直觉例子

四条视频在某一秒的手部 reward 为 `[.2,.8,.5,.5]`，均值 .5。若课堂示例分母取 .25，advantage 是 `[-1.2,1.2,0,0]`：第二条这一秒应强化，第一条这一秒应压低，而不是把这个判断扩散到整段视频。

## 它和普通 GRPO 的关系

它没有推翻组相对标准化，只是把“一条回答一个分数”扩成“一条视频每个时间区间都有一组分数”。策略更新和去噪 transition 怎样结合仍属于具体算法实现。

## 链接

- [[grpo]] · 组相对 advantage 的基础
- [[longcat-video-avatar-1-5]] · 手部首帧检查、五段 rollout 与多奖励合并
