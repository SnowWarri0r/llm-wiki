---
name: sparse-reference-attention
type: concept
sources: [wan-animate-2]
updated: 2026-08-12
---

# Sparse Reference Attention · 每帧只查对应时刻的参考帧

## 一句话

目标视频内部仍可全局互看，但目标第 <code>t</code> 帧只读取参考第 <code>t</code> 帧。

## 直觉

如果在学“第 2 秒抬手”，没有必要让目标第 2 秒同时查询参考视频第 0、1、2、3 秒的全部像素。先用时间对齐把正确参考帧找出来，再只在这一帧里挑细节。

## 怎么做的

设每段有 <code>T</code> 帧，目标每帧 <code>S_t</code> 个 token，参考每帧 <code>S_r</code> 个 token：

\[
\text{全量跨分支连边}=T^2S_tS_r
\]

\[
\text{按时间对齐连边}=TS_tS_r
\]

注意：被裁掉的是“目标查询参考”的跨分支连边；目标分支的自注意力仍保持完整。

## 数字例子

取 <code>T=3</code>、<code>S_t=4</code>、<code>S_r=2</code>：

- 全量比较：目标共有 <code>3×4=12</code> 个 query，参考共有 <code>3×2=6</code> 个 K/V，连边数为 <code>12×6=72</code>。
- 时间对齐：每个时刻只有 <code>4×2=8</code> 条跨分支连边，三个时刻共 <code>3×8=24</code>。
- 这组小例子把跨分支比较量从 72 降到 24，正好减少 3 倍；一般会减少约 <code>T</code> 倍。

论文把复杂度写成从 <code>O(N_rN_l)</code> 降到 <code>O(N_l)</code>，隐含前提是每帧参考 token 数视作固定常数。若把 <code>S_r</code> 也展开，更完整的写法是上面的 <code>O(TS_tS_r)</code>。

## 链接

- [[wan-animate-2]] · 提出并用于直接视频驱动
- [[time-align-rope]] · 先给同一时刻一致的时间地址
- [[cross-attention]] · 一路 query 怎样读取另一路 K/V
