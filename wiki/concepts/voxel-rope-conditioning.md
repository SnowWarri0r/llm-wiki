---
name: voxel-rope-conditioning
type: concept
sources: [meshflow]
updated: 2026-07-14
---

# Voxel + 3D RoPE 条件 · 先把点云位置磨粗，再写进注意力

## 一句话

把点云坐标落进粗体素格，同格点共用一个三维位置编号，再用 3D RoPE 旋转 Q/K。

## 它在修什么差距

训练时有真值 mesh 顶点，推理时只有从表面均匀采样的点云。两者都描述同一形状，点的分布却不同：美术师会在锐边和复杂部位多放顶点；均匀采样只按表面积撒点。直接把精确 XYZ 写进 RoPE，模型可能记住“顶点怎么排”，到推理就换了口音。

体素化先把坐标磨粗。只要落进同一个小方格，就给同一位置编号。模型更难追究采样细节，只能抓住大致空间结构。

## 数字例子 · 一个点落到哪个格子

真实模型用 `[-1,1]³` 和 `32³` 网格。为了手算，先用每轴 4 格：

~~~text
点 p = (0.2, -0.7, 0.9)
resolution = 4

索引 = floor((p+1)/2 × 4)
x: floor(1.2/2×4) = floor(2.4) = 2
y: floor(0.3/2×4) = floor(0.6) = 0
z: floor(1.9/2×4) = floor(3.8) = 3

voxel index = (2,0,3)
~~~

每格宽 `2/4=0.5`，格子中心为：

~~~text
center = -1 + (index+0.5)×0.5
       = (0.25, -0.75, 0.75)
~~~

✓ 自检：原点与中心三轴差值是 `0.05,0.05,0.15`，都没超过半格宽 `0.25`。

换成真实 32 格后，每格宽 `2/32=0.0625`。分辨率太低会把不同局部揉在一起；太高又重新暴露训练顶点与推理采样点的分布差。论文选择每轴 32 格，但没有公开分辨率消融数字。

## 3D RoPE 怎样用这三个数

普通 RoPE 用一维 token 位置旋转 Q/K。发布代码把每个 attention head 的维度分成三份，分别由 x、y、z 的体素索引控制旋转。同一格里的点拿到同一组三轴旋转；相邻格子的相对位移会反映到注意力点积里。

它不是把点云编码成另一串条件 token，而是直接改变 noisy mesh token 在 self-attention 里的位置关系。因此不用额外 2,048 个 shape token 做 cross-attention，收敛也更快。

## 代码出处

- `meshflow/models/meshflow_dit.py`：`voxelize_pc()` 与 `RotaryPositionalEmbeddings(ndim=3)`。
- `meshflow/pipelines/meshflow_pipeline.py`：`sample_surface_points()` → `get_rope_cond()`。

## 链接

- [[meshflow]] · 点云条件进入 DiT 的最终方案。
- [[rotary-position-embedding]] · 一维 RoPE 的基础直觉。
- [[diffusion-transformer]] · 3D RoPE 实际调制的去噪骨架。
