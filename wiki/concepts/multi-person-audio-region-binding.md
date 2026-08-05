---
name: multi-person-audio-region-binding
type: concept
sources: [longcat-video-avatar-1-5]
updated: 2026-08-05
---

# Multi-Person Audio–Region Binding · 把每条声音送到对应人物区域

## 一句话

多人数字人不能只知道“画面里有两个人、音频里有两条声音”，还要知道谁对应谁。L-RoPE 给人物区域和对应音频相同或相近的 Label，让 attention 更容易把正确声音送到正确嘴部；背景人物再配静音轨，明确告诉模型此人不说话。

## L 不是 Location

L-RoPE 的 L 是 Label。沿 MultiTalk 的示意：人物 A 的视觉区域标签为 0–4，A 的音频标签取 2；人物 B 的区域为 20–24，B 的音频取 22；背景取 12。旋转位置编码让标签接近的 Query 和 Key 更容易互相匹配。

这不是拿标签做普通分类，也不是把人物框坐标直接塞进注意力分数。框先确定哪些视频 token 属于哪个人物，Label RoPE 再把这种归属编码进 Q/K 的旋转相位。

## 为什么还要静音轨

标签负责“分流”：A 的声音别送给 B。静音轨负责“明确无声”：背景人物此刻没有要驱动嘴形的音频。只有分流标签，没有背景静音条件，模型仍可能让非目标人物跟着动嘴。

## 链接

- [[longcat-video-avatar-1-5]] · v1.5 的人物框与背景静音扩展
- [[rope]] · 旋转位置编码基础；本页的标签构造来自 MultiTalk 论文
- [[cross-attention]] · 视频 Query 怎样读取音频 Key/Value
