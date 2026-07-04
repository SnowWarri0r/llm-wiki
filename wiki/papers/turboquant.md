---
name: turboquant
type: paper
source: https://arxiv.org/abs/2504.19874
upstream: https://arxiv.org/abs/2504.19874
ingested: 2026-07-01
authors: [Amir Zandieh, Majid Daliri, Majid Hadian, Vahab Mirrokni · Google Research · ICLR 2026]
year: 2026
---

# TurboQuant · 随机旋转把"任意向量"变成"分布已知",在线量化逼近理论最优

## 一句话
在线向量量化(边来边压、看不到数据统计)老做不到最优失真。TurboQuant 一个几何洞察破局:**先随机旋转向量,它的每个坐标就服从一个固定已知的分布(集中的 Beta),而且高维下坐标之间近独立**([[random-rotation-quantization]])——于是可以**离线就设计好一个最优标量量化器、在线只旋转+套用**,不看数据。逼近信息论下界只差 ~2.7×。再补一手两阶段:MSE 量化器会让内积估计有偏,后接 1-bit [[quantized-jl]] 残差纠成无偏([[mse-vs-inner-product-bias]])。用在 [[kv-cache]] 压缩:3.5-bit 质量无损、2.5-bit 微降,≥6× 省内存、H100 上 attention 快 8×。

## 它要解决的痛点
[[kv-cache]] 压缩和向量检索都要**在线/data-oblivious** 量化:KV 向量边生成边存,没法先扫全量数据算统计再定量化格子;检索索引也想"建索引接近零成本"。可现有在线量化器**达不到最优失真率**——要么坐标分布未知只能保守切格子,要么 MSE 最优但内积估计有偏。

## 核心贡献
- **随机旋转 → 分布已知 → data-oblivious 最优标量量化**([[random-rotation-quantization]]):把向量乘一个随机正交矩阵旋一下,单位向量的每个坐标平方就服从 `Beta(1/2, (d-1)/2)`(集中在 `±1/√d` 附近),且高维下不同坐标**近独立**。分布固定且已知 → **离线把每坐标的最优标量量化器([[bin-quantization]] 的最优版)设计好,在线只旋转+套**,完全不看数据。近独立让"各坐标各自最优"复合起来 ≈ 向量最优。
- **两阶段治内积偏差**([[mse-vs-inner-product-bias]]):**MSE 最优量化器会把内积估计压偏**(量化误差与向量相关)。所以第一阶段用 MSE 量化器压主体,第二阶段对**残差** `r=x−x̂` 再做 **1-bit [[quantized-jl]]**(符号随机投影,内积无偏)——合起来是个既低 MSE、内积又无偏的估计器。
- **理论**:给出任意向量量化器的**信息论失真下界**,证明 TurboQuant 在所有 bit 宽/维度下都逼近它,只差一个小常数(≈2.7×)。
- 结果:[[kv-cache]] 量化 **3.5 bit/通道质量无损、2.5 bit 微降**;**≥6× 省 KV 内存、H100 上 attention 快 8×**;向量检索 recall 超过现有 [[faiss-ann-search]] 的 product quantization,且建索引成本近零。

## 关键概念 → 概念页
- [[random-rotation-quantization]] · 核心:旋转让坐标分布已知+近独立 → 离线设计、在线套用
- [[quantized-jl]] · QJL:1-bit 符号随机投影,给内积一个无偏估计
- [[mse-vs-inner-product-bias]] · MSE 最优会让内积有偏,两阶段(MSE + QJL 残差)纠回无偏
- 复用:[[kv-cache]] 落地场景 · [[quantization]] / [[bin-quantization]] 标量量化基底 · [[dot-product]] 内积失真 · [[faiss-ann-search]] 向量检索对照(PQ) · [[flash-attention]] attention 加速语境

## 我的批注 / 疑问
- 一句话记牢:**随机旋转是把"我不知道数据长啥样"变成"我精确知道每个坐标的分布",于是最优量化器能离线预制、在线零成本套用**。这是 data-oblivious 的真正杠杆——不是压得更狠,是把未知变成已知。
- 两阶段那手很干净:MSE 压主体(低失真)+ QJL 1-bit 残差(去偏),各管一件事,跟 [[diffusionnft]]/[[diffusion-opd]] 里"把一个目标拆成两块各自最优"是同一种工程审美。
- 来源:arXiv 2504.19874(ICLR 2026,Google Research)。机制(随机旋转→Beta 坐标分布→近独立→最优标量量化、MSE+QJL 两阶段、≈2.7× 下界、3.5/2.5-bit、6×/8×)已确证。
- 待查:随机旋转矩阵用的是 Hadamard/结构化旋转(省算力)还是稠密正交;QJL 残差那 1-bit 在总 bit 预算里占多少;2.7 这个常数是不是 ≈e。
