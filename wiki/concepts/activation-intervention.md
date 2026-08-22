---
name: activation-intervention
type: concept
sources: [global-workspace]
updated: 2026-08-18
---

# Activation intervention · 直接改内部状态，区分“看见相关”与“真的在用”

## 一句话

不是只观察某个概念与答案同时出现，而是改掉那段激活，看答案是否跟着变。

## 直觉

比分牌和球场比分高度相关，但改比分牌不会改变比赛。要证明某个内部方向参与了计算，不能只看它会不会亮；得把“蜘蛛”换成“蚂蚁”，再看“8 条腿”是否跟着变成“6 条腿”。

## 怎么做的

### 写入 / steering

沿目标概念方向 \(v_t\) 给内部状态加一段：

\[
h'=h+\alpha v_t.
\]

\(\alpha>0\) 增强概念；\(\alpha<0\) 压低概念。

### 删除 / ablation

若 \(v\) 已归一化，从 \(h\) 中删掉沿 \(v\) 的投影：

\[
h'=h-(v^\top h)v.
\]

### 互换 / coordinate swap

论文把源概念和目标概念的方向并成 \(V=[v_s\;v_t]\)，先读出两维坐标 \(c=V^\dagger h\)，交换后写回：

\[
h_{\text{swap}}=h+V\bigl(\sigma(c)-c\bigr).
\]

- \(V^\dagger\)：伪逆；方向不正交时也能求最合适的两维坐标。
- \(\sigma(c)\)：把源、目标两个坐标互换。
- 其余与 \(\operatorname{span}\{v_s,v_t\}\) 正交的部分不动。

## 数字例子

为方便手算，设两个概念方向正交：\(v_s=[1,0]\)、\(v_t=[0,1]\)，内部状态 \(h=[3,1]\)。

此时 \(V=I\)、\(V^\dagger=I\)，所以：

\[
c=[3,1],\qquad \sigma(c)=[1,3].
\]

写回差值：

\[
h_{\text{swap}}
=[3,1]+I([1,3]-[3,1])
=[1,3].
\]

源方向强度从 3 变 1，目标方向从 1 变 3；若输出也稳定改成目标对应答案，才有证据说下游计算确实读了这组坐标。

## 三类结论别混

- 只读到概念：相关性证据。
- 改概念后输出改变：因果证据。
- 同一次替换能重定向多种不同任务：共享、可复用表示的证据。

## 链接

- [[global-workspace]] · Soccer→Rugby、spider→ant、France→China 等干预实验。
- [[jacobian-lens]] · 提供论文使用的概念方向。
- [[gradient-backprop]] · 干预实验与“只看梯度相关”有什么区别。
