---
name: identity-specific-audio-gating
type: concept
sources: [klingavatar-2]
updated: 2026-08-06
---

# 身份特定音频门控 · 多人画面里让声音只驱动正确的人

## 一句话

先为每个人预测随时间变化的区域 mask，再用该 mask 限制对应音频特征的注入位置，避免一条声音同时驱动所有人的嘴和身体。

## 直觉

舞台上有 A、B 两位演员，音响台不只要知道“现在有声音”，还要知道“这路麦克风属于谁”。人物 mask 就像每路麦克风的区域推子：A 的声音在 A 区域开大，在 B 区域压到接近零。

## 教学公式

\[
H'=H+\sum_i M_i\odot A_i.
\]

- \(H\)：注入前的视频特征；
- \(i\)：人物编号；
- \(A_i\)：第 \(i\) 条音频产生的特征更新；
- \(M_i\)：人物 \(i\) 的时空软 mask；
- \(\odot\)：逐位置相乘；
- \(H'\)：注入后的特征。

这是机制的通用写法，不一定是具体论文原公式。mask 预测错人、遮挡时丢失、多人区域重叠，都会让音频串到错误人物。

## 链接

- [[klingavatar-2]] · 用深层 DiT 特征与 reference token 回归人物 mask
- [[multi-person-audio-region-binding]] · L-RoPE 与静音轨的另一种人物—声音绑定方法
- [[cross-attention]] · 音频特征怎样被视频 token 查询
