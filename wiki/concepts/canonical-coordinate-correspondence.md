---
name: canonical-coordinate-correspondence
type: concept
sources: [lyra-2]
updated: 2026-08-17
---

# Canonical Coordinate Correspondence · 把旧像素地址 warp 过去，而不是把旧 RGB 硬贴过去

## 一句话

先给每张旧帧的每个像素贴上 `(横坐标, 纵坐标, 帧槽号)`，再用深度和相机把这些地址投到新视角；目标位置由此知道该去哪张旧图的哪里取信息。

## 三个通道在说什么

第 `j` 张空间记忆帧的规范坐标图为：

\[
C_j(u,v)=\left(u,v,\frac{2j}{N_s}-1\right),
\]

- \(u,v\in[-1,1]\)：旧帧内归一化横纵坐标；
- `j`：这张旧帧占第几个记忆槽；
- \(N_s\)：空间槽总数，Lyra 2.0 为 5；
- 第三通道把槽编号均匀映射到 `[-1,1]`，让同一个 `(u,v)` 也能区分来自哪张图。

系统再用旧帧深度、旧相机和目标相机做 forward warp，并把 warp 后深度作为第四通道。得到的是目标位置到旧图的稠密“地址表”。

## 为什么不 warp RGB

新视角会露出旧图没见过的区域，RGB warp 必然有空洞；深度边缘还有拉伸和前后景串色。把这张坏图作为强条件，生成器容易照抄伪影。坐标只告诉 attention“该参考谁”，最终像素仍由预训练视频先验合成，允许它补洞和消解冲突。

Lyra 把坐标 embedding 加到 Query / Key，不改 Value：地址影响检索关系，旧帧内容本身仍走原有 Value 通道。

## 链接

- [[lyra-2]] · 稠密对应如何进入每个 DiT block
- [[cross-attention]] · Query / Key 决定读谁，Value 决定读回什么
