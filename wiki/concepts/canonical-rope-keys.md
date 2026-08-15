---
name: canonical-rope-keys
type: concept
sources: [worldtrace]
updated: 2026-08-11
---

# Canonical RoPE Keys · 去掉位置旋转的 Key

## 一句话

Canonical Key 是把 RoPE 已写入 Key 的旧位置相位反向旋掉后，留下的内容坐标；要合并不同时间的 Key 或给它们换虚拟位置，应先回到这个共同坐标系。

## 为什么不能直接平均

两帧内容都简化为 `[1,0]`，但时间相位分别为 0° 与 180°：

\[
R(0^\circ)[1,0]=[1,0],\qquad
R(180^\circ)[1,0]=[-1,0].
\]

直接平均得到 `[0,0]`。这不是内容不同，而是两个“地址箭头”方向相反，把内容信号抵消了。

反向旋转后：

\[
R(0^\circ)[1,0]=[1,0],\qquad
R(-180^\circ)[-1,0]=[1,0].
\]

此时平均仍为 `[1,0]`。若要把摘要放到 90° 的虚拟位置，再做一次 `R(90°)`，得到 `[0,1]`。

## 操作顺序

```text
各自带旧时间相位的 Key
  → unrotate：去掉旧地址
  → merge / freeze：只处理内容
  → rerotate：写入新虚拟地址
```

Value 不需要这套处理，因为 RoPE 只旋转 Q/K，位置影响“读谁”，不直接旋转“读回什么”。

## 能保证什么，不能保证什么

Canonical 平均借助点积线性，能保住来源 Key 在共同虚拟位置上的**平均 pre-softmax logit**。它不保证 softmax 后权重或最终 attention 输出完全一样，因为合并后 token 数变了，分母中的其他 Key 也会影响每个权重。

## 链接

- [[worldtrace]] · Field 平均与 Landmark 冻结的完整公式
- [[rotary-position-embedding]] · 旋转矩阵来自哪里
- [[dot-product]] · 为什么平均 Key 的点积等于点积的平均
- [[softmax]] · 为什么 pre-softmax 相等不等于最终权重相等
