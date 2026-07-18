---
name: modality-aware-cfg
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Modality-Aware CFG · 把“听 prompt”和“跟另一模态同步”分开加力

## 一句话

分别测出文本与另一模态改变了预测多少，再用两个 scale 独立放大。

## 直觉

音视频生成有两种不同的“听话”：画面/声音要符合文字，同时声音与画面还要彼此同步。只用一个 CFG scale，会把两种控制绑在一起。Modality-CFG 多算一个去掉另一模态的分支，将两条差值方向拆开。

它不是新的训练损失，而是推理时组合多次模型预测的方法；控制更细，但需要更多前向计算。

## 怎么做的

\[
\widehat M=M(x,c,m)
+s_{text}[M(x,c,m)-M(x,\varnothing,m)]
+s_{cross}[M(x,c,m)-M(x,c,\varnothing)]
\]

- `x`：当前模态的 noisy latent；
- `c`：文本条件；
- `m`：另一模态条件；
- `∅`：有意拿掉对应条件；
- `s_text`：文本 guidance scale；
- `s_cross`：跨模态 guidance scale。

第一条差值只改变文本是否存在，近似抽出“文本造成的预测变化”；第二条只改变另一模态是否存在，近似抽出“音视频互相影响的变化”。这不是严格因果效应，因为神经网络是非线性的，两个条件之间仍可能交互。

## 数字例子

```text
full = M(x,c,m) = 2.0
no_text = M(x,∅,m) = 1.5   → text direction = 0.5
no_cross = M(x,c,∅) = 1.2  → cross direction = 0.8

视频 scale (3,3)：2 + 3×.5 + 3×.8 = 5.9
音频 scale (7,3)：2 + 7×.5 + 3×.8 = 7.9
```

自检：若两个 scale 都为 0，结果退回完整条件预测 `2.0`。若拿掉另一模态不改变输出，即 `full=no_cross`，跨模态项自动为 0。

## 跟标准 CFG 对比

标准 CFG 常写成 `uncond + s(cond-uncond)`，从无条件预测出发；LTX-2 论文公式从完整条件预测出发，再加两条增量。相同 scale 下，两者数值并不相同，不能直接把经验参数照搬。

## 链接

- [[ltx-2]] · 视频用 (3,3)，音频用 (7,3)
- [[classifier-free-guidance]] · 单条件前身
- [[audiovisual-cross-attention]] · `m` 进入当前流的结构通道

