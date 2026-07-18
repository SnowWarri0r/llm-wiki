---
name: meshflow
type: paper
source: https://arxiv.org/abs/2606.04621
upstream: https://github.com/facebookresearch/meshflow
ingested: 2026-07-14
authors: Weiyu Li, Antoine Toisoul, Tom Monnier, Roman Shapovalov, Rakesh Ranjan, Ping Tan, Andrea Vedaldi · Meta AI / HKUST · CVPR 2026 Highlight
---

# MeshFlow · 不再逐 token 拼网格，一次并行长出全部顶点和边

直接生成 3D mesh 一直有个两难：顶点坐标是连续数，边和面却是离散拓扑。自回归方法把它们全切成离散 token，结构好生成了，代价是坐标被量化，而且 mesh 越大，逐 token 解码越慢。MeshFlow 的主意是先把“坐标 + 法线 + 谁和谁相连”压进连续 latent，再让整流流 DiT 一次处理全部 latent token。

## 一句话

**把离散连接关系改写成每个顶点的连续边嵌入，用 MeshVAE 压到约四分之一 token，再用 Rectified Flow DiT 并行生成。**

## 它要解决的痛点

- **隐式表面能出形状，却不一定出好用的 mesh**：SDF 加 Marching Cubes 容易得到过密三角面、磨平锐边，还常要求封闭表面；美术师后续很难编辑。
- **自回归 mesh 生成太慢**：朴素面 token 化一张三角面至少要 9 个坐标 token；模型还得一个接一个往后吐，长 mesh 容易提前停止。
- **坐标量化会伤几何**：主流方法常把每轴压到 128 档，细节会抖，顶点还可能撞到一起，带来重面和塌面。
- **连续坐标不难，离散拓扑才难**：扩散模型擅长连续张量，却不能直接对“顶点 i 是否连顶点 j”这种 0/1 邻接矩阵做平滑去噪。

## 核心贡献

1. **连续 mesh 表示**：[[continuous-mesh-connectivity]] —— 每个顶点携带位置、外法线和边嵌入；边由两顶点的连接分数过阈值恢复，三条边成环便恢复一个三角面。
2. **紧凑 MeshVAE**：[[mesh-token-merge]] —— TokenMerge 把顶点 token 分组塞进通道，再用 cross-attention 回看完整输入；TokenSplit 反向展开。
3. **并行生成**：[[flow-matching]] + [[diffusion-transformer]] —— DiT 在连续 mesh latent 上学直线速度场，发布 pipeline 默认用 28 步 Euler 更新，而不是逐顶点自回归。
4. **形状条件**：[[voxel-rope-conditioning]] —— 把点云落到 32³ 粗体素格，再用 3D RoPE 把空间位置写进注意力。
5. **评测拆账**：[[mesh-quality-metrics]] —— CD/HD 衡量几何距离，却看不全洞、翻面和拓扑是否好编辑。

## 方法主线

### 1. 先把 mesh 改写成连续的顶点表

一张三角 mesh 原本是顶点列表 `V` 加面列表 `F`。MeshFlow 不直接生成面，而是给每个顶点一条连续向量 `(v_i, n_i, h_i)`：`v_i` 是三维坐标，`n_i` 是外法线，`h_i` 是边嵌入。两个顶点的连接分数过阈值，就恢复一条边；三条边组成三环，就恢复一个三角面；三个顶点法线的平均方向决定面朝里还是朝外。

这套表示避开了离散 face token，也不要求输入是 watertight manifold。不过它只覆盖三角面，而且默认假设“三条边构成的三环就是一个面”。

### 2. MeshVAE 把 N 个顶点压成 n 个 latent

编码器给每个顶点拼上 Fourier 编码后的坐标、法线和邻居坐标。TokenMerge 把 `N×D` 重排成更短、更宽的 token，再用 MLP 压回隐藏维。短 token 随后通过 cross-attention 回看全部 `N` 个输入，因此“先缩短”不等于“从此看不见被合并的顶点”。

解码器做反向 TokenSplit，最后分别预测顶点、法线、边嵌入和有效顶点 mask。损失由 mask BCE、顶点 MSE、法线 MSE、边对比损失和 KL 组成；补充材料给出 `τ=0.6`、`λ_neg=0.01`、`λ_KL=10^-3`。

### 3. 从一堆候选边恢复三角面

解码后先删掉 mask 判为无效的顶点，再两两计算边分数。每条边 `(i,j)` 查找共同邻居 `k`，若三条边都存在，就收下三角面 `(i,j,k)`。几何叉乘得到面法线，若它与三个顶点法线的平均方向相反，就交换两个顶点，把朝向翻回来。

论文还描述了短边界环补洞：找到只属于一个面的边，用 DFS 找小环再三角化。但发布代码 `55f56f6` 的 `MeshFlowPipeline.run()` 没有暴露这个开关，`decode_latent(fill_holes=False)` 默认关闭补洞。

### 4. Rectified Flow DiT 并行生成 latent

训练时拿干净 latent `x0` 和高斯噪声 `ε` 连直线：`x(t)=(1-t)x0+tε`。这条线的目标速度始终是 `ε-x0`。DiT 输入带噪 latent、时间 `t` 和点云条件，回归这个速度。推理反过来从噪声出发，沿预测速度往 `t=0` 积分，最后交给 MeshVAE 解码。

“并行”指每一步同时更新整串 latent，不是按顶点逐个生成。发布 README 默认 28 步。它确实砍掉了自回归的串行解码链，但代码每层仍是全量 self-attention，因此注意力计算对 token 数仍是二次量级；论文所谓“随 mesh 大小线性增长”，更稳妥地理解为生成轮数不随输出 token 数增长，而不是总 FLOPs 严格线性。

### 5. 点云怎样给 DiT 指路

论文试过两条路。第一条把 32,768 个点送进预训练 shape encoder，变成 2,048 个条件 token，再做 cross-attention；推理自然，但训练收敛慢。第二条直接把三维坐标写进 RoPE，收敛快，可训练看的是 mesh 顶点，推理看的是表面均匀采样点，两者分布不一样。

最终做法先把点落进 32³ 体素格，只给 RoPE 较粗的位置。粗格子抹掉“顶点采样方式”的细枝末节，缩小训练—推理差距；代价是条件几何变粗。论文只给出“32³ 是合理折中”的定性结论，没有列不同分辨率的消融表。

## 训练配方

- 数据：约 60 万个专业美术师制作的私有 3D 模型；归一化到 `[-1,1]³`，合并重复/离群顶点，不做坐标量化；过滤最大顶点度数超过 50 的 mesh。
- MeshVAE：8 层 encoder + 8 层 decoder，隐藏维 1024，233M 参数；32 张 H100 训练 3 天，每卡 batch 64，AdamW，学习率 `5e-4`。
- DiT：主文写 18 层、隐藏维 1024、427M；补充材料却写 16 层、隐藏维 1536、895M。两组数在同一 v2 PDF 内互相冲突，公开模型配置又需要通过 gated Hugging Face 才能下载，因此不能擅自替作者选一组“正确答案”。
- DiT 训练：补充材料写 64 张 H100、每卡 batch 32、训练 10 天，学习率 `1e-4`；用 BF16、Flash Attention 和 EMA，后期改用 logit-normal 时间采样，推理 timestep shift 为 3.0。

## 实验结果

### MeshVAE 重建

MeshFlow 的压缩比是 `0.014`，TreeMeshGPT 是 `0.22`，EdgeRunner 是 `0.47`；也就是前者只保留约 1.4% 的表示长度。重建 CD×100 为 `1.29`，略逊于 EdgeRunner 的 `1.21`，但好于 TreeMeshGPT 的 `1.63`。所以准确说法不是“重建误差全场最低”，而是“用远短的连续表示做到接近最优的重建”。

### 点云条件生成

Toys4K 上，MeshFlow 的 `CD=2.33`、`HD=4.23`，优于 FastMesh-V1K 的 `4.09 / 10.32`。主表按 batch 均时口径报告 `1.06s` 采样 + `0.47s` 抽 mesh，总计 `1.53s`；FastMesh-V1K 是 `3.41s`，约快 `2.2×`。

论文摘要的 `18×` 来自补充材料的单物体计时：FastMesh-V1K 约 `21s`，MeshFlow 约 `1.2s`，`21/1.2=17.5×`。两种口径都是真实表格，但不能混成同一个数字。

### 消融

- 初始化 cross-attention query：Q-Former / FPS / TokenMerge 的边 F1 分别是 `49.47 / 60.18 / 99.78`。
- 压缩倍率：2× / 4× 的边 F1 是 `92.65 / 88.82`，压得越狠，拓扑恢复越差。
- 最大顶点数：2048 / 4096 / 8192 的边 F1 是 `99.84 / 99.78 / 99.71`，这组重建实验没有随规模明显崩掉。

## 局限与实现差异

- 只生成三角面，不生成美术工作流常见的 quad，也不做 UV 与纹理。
- 约 60 万训练 mesh 是私有数据，外部无法完整复现训练分布。
- CD/HD 对翻面、洞和拓扑可编辑性不敏感；论文也承认现有指标不够。
- 主文式 (2) 写“距离 `d≤τ` 就连边”，但边损失、补充算法 1 和发布代码都让正边满足 `d>τ`。代码里的 `d` 实际是带符号的 spacetime score，不应按普通欧氏距离读。
- 论文说默认修补 `k<5` 的边界环；补充伪代码没有真正使用 `k<5` 条件，发布实现则支持更大环但 pipeline 默认关闭补洞。
- README 加入了可选 DINOv3 图像条件，但项目页 Q&A 同时说发布模型仍期待表面点云，图像不是点云的替代品。

## 我的批注

- 最值钱的不是“又一个 flow DiT”，而是先把 mesh 拆成了扩散模型吃得下的连续对象：位置管几何，边嵌入管连接，法线顺手管朝向。
- TokenMerge 的消融差距大得反常：它不只是省 token，还给 cross-attention 一个带原输入信息的 query 起点；随机 query 和 FPS query 在这套训练里都很难收敛。
- `18×` 速度提升成立，但只成立在单物体口径；主表口径是约 `2.2×`。复述 benchmark 时必须把分母写出来。
- “非自回归 = 对 mesh 大小线性”说得太满。它把串行深度从输出长度降成固定采样步数，但标准 DiT 的全注意力仍是二次计算。
- 论文最诚实的一段是主动不报 Normal Consistency：模型直接预测法线，拿这项高分不一定说明 mesh 更好。可惜拓扑质量又缺少可靠量化指标。
- 公开代码和 PDF 已经出现阈值方向、DiT 规模、补洞默认值三处不一致。复现记录必须同时保存论文版本 `v2`、代码提交 `55f56f6` 和 gated 模型配置。

## 跟 wiki 里其他 paper 的关系

- [[dit]] · MeshFlow 沿用 DiT 骨架，但目标从图像 latent 换成 mesh latent。
- [[flow-matching]] · 同样学速度场；MeshFlow 明确用数据 `x0` 到噪声 `ε` 的直线路径。
- [[stable-diffusion-3-5]] · 复用整流流、logit-normal 时间采样和 timestep shift。
- [[rae-dit]] · 都先重做 latent 再做生成；RAE 换图像表征，MeshFlow 解决连续几何与离散拓扑共存。

## 历史定位

- 2023-11 MeshGPT · 把三角 mesh 当离散序列自回归生成。
- 2024-09 SpaceMesh · 用每顶点连续嵌入表示连接关系。
- 2025-03 MeshCraft · 用 GCN autoencoder + flow DiT 做非自回归 mesh 生成。
- 2025-08 FastMesh · 把顶点自回归与确定性连面拆开，先把速度拉快。
- 2026-06 **MeshFlow** · 连续边表示 + MeshVAE + Rectified Flow DiT，单物体约 1.2 秒。
