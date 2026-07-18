---
name: mesh-token-merge
type: concept
sources: [meshflow]
updated: 2026-07-14
---

# Mesh TokenMerge / TokenSplit · 把 token 数塞进通道，再反向摊开

## 一句话

先把相邻的 `r` 个顶点 token 拼成一个宽 token，再用线性层压回隐藏维；解码时把通道反向拆回 `r` 个 token。

## 为什么不直接放几个可学习 query

VAE 想把 `N` 个顶点 token 压成更短的 `n` 个 latent。常见做法是放 `n` 个随机初始化 query，让它们 cross-attention 全部输入；也可以用最远点采样挑 `n` 个代表点。

问题是，这两种 query 起步时都没有完整原 token 的内容。MeshFlow 先做一次纯重排，把真实输入塞进 query，再让 query 回看全部顶点。query 不是空白工位，而是已经抱着一捆原料上桌。

## 数字例子 · 8 个 token 压成 2 个

为了能手算，先让每个 token 只有一个通道：

~~~text
X = [1, 2, 3, 4, 5, 6, 7, 8]     shape = 8×1
压缩倍率 r = 4
~~~

TokenMerge 只重排，不丢数：

~~~text
row 1: [1,2,3,4]
row 2: [5,6,7,8]                    shape = 2×4
~~~

接一层学出来的线性映射。假设这层权重刚好是平均 `W=[0.25,0.25,0.25,0.25]`：

~~~text
q1 = 0.25×(1+2+3+4) = 2.5
q2 = 0.25×(5+6+7+8) = 6.5
~~~

于是 8 个 token 先变成 2 个 query。真实模型不是算平均，而是学习 `4D→D` 的矩阵；随后 2 个 query 还会 cross-attention 原始 8 个 token，把被压扁的细节重新捞回来。

TokenSplit 反过来。假设两个 latent 各有 4 个通道：

~~~text
z row 1 = [10,20,30,40]
z row 2 = [50,60,70,80]                shape = 2×4
按通道拆开 → [10,20,30,40,50,60,70,80] shape = 8×1
~~~

再用共享线性层把每个 1 通道小 token 扩到目标隐藏维。✓ 自检：拆前后都是 8 个标量，第一步只是把“token 轴”与“通道轴”互换；真正的信息取舍发生在线性层与后续注意力里。

## 真实代码的形状

编码器把 `[B,N,D]` reshape 成 `[B,N/r,rD]`，再做 `Linear(rD,D)`；解码器把 `[B,n,D]` reshape 成 `[B,N,D/r]`，再做 `Linear(D/r,D)`。这就是它像 PixelShuffle 的地方：不靠池化挑点，而是搬运维度。

## 消融告诉了什么

论文表 3 的边 F1×100：

~~~text
Q-Former query     49.47
FPS query          60.18
TokenMerge query   99.78
~~~

这个差距说明 query 的起点对 MeshVAE 很关键。不过表里没有控制更多训练预算，也没有报告方差；能下的结论是“这套训练设置里 TokenMerge 明显更稳”，不是“所有 mesh VAE 都必须这样压”。

## 代码出处

- `meshflow/models/meshflow_vae.py`：`Encoder._get_init_query()` 与 `Decoder._get_init_query()`。

## 链接

- [[meshflow]] · MeshVAE 的压缩与解压核心。
- [[kl-vae]] · TokenMerge 决定压缩形状，KL 负责让 latent 分布规整。
- [[patch-embedding]] · 都在 token 轴和通道轴之间搬信息，但 patch embedding 面向规则图像网格。
