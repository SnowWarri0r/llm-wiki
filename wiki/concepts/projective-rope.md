---
name: projective-rope
type: concept
sources: [minwm]
updated: 2026-07-24
---

# PRoPE · 把相机几何写进注意力

## 一句话

普通 RoPE 告诉 attention“两个 token 在画面里相隔多远”；PRoPE 再把相机内参和位姿写进 Q/K/V 的坐标变换，使两个不同帧的 token 交互时能直接看到相机之间的相对投影关系。

## 为什么二维位置不够

同一张桌子在连续两帧中可能从画面左侧移到右侧。只看二维像素坐标，模型不知道这是桌子移动了，还是相机向左转了。若每一帧都带有：

- `K_i`：相机内参，描述焦距和主点；
- `T_i^{cw}`：从世界坐标变到第 `i` 帧相机坐标的外参；

就可以把“第 1 帧和第 2 帧的相机如何相对移动”显式送进注意力。

PRoPE 先把二者合成 4×4 投影矩阵：

\[
\widetilde P_i=
\begin{bmatrix}
[K_i\;0]T_i^{cw}\\
e_4^\top
\end{bmatrix},
\qquad e_4=(0,0,0,1)^\top.
\]

随后把一部分 attention head 维度留给 `\widetilde P_i`，剩余部分继续使用横向 `x` 与纵向 `y` 的普通 RoPE。两个 token 的 Q/K 做点积时，真正留下的是：

\[
\widetilde P_{i_1}\widetilde P_{i_2}^{-1}.
\]

也就是“从第 2 帧相机坐标换到第 1 帧相机坐标”的相对变换，而不是两份互不相关的绝对位姿。

## 一个只移动 1 米的例子

为简化，令两台相机内参都是单位矩阵。第 1 帧相机不动，第二帧相机沿世界 `x` 轴移动 `+1`，其 world-to-camera 外参含 `-1` 平移。于是：

\[
\widetilde P_1\widetilde P_2^{-1}
=
\begin{bmatrix}
1&0&0&1\\
0&1&0&0\\
0&0&1&0\\
0&0&0&1
\end{bmatrix}.
\]

右上角的 `+1` 正是两台相机之间的相对水平位移。真实模型同时处理旋转、平移、焦距和每个 token 的二维坐标。

## 与“把 pose token 拼进去”有什么不同

拼 pose token 是让网络自己学“这些数字和画面有什么关系”；PRoPE 直接把已知投影几何放进 attention 运算。前者更自由，后者归纳偏置更强。它仍不是 3D 重建：网络没有显式 mesh 或点云，只是更容易根据相对相机关系对齐跨帧内容。

## 链接

- [[minwm]] · PRoPE 怎样进入一条完整的实时世界模型训练流水线
- [[rotary-position-embedding]] · 普通 RoPE 的旋转与相对位置
- [[camera-pose-tokenization]] · 另一类把相机位姿编码成 token 的方案
- [[self-attention]] · Q/K/V 点积的基础
