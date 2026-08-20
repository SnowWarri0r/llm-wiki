---
name: waveforcing
type: paper
source: https://sjtu-deng-lab.github.io/WaveForcing/
upstream: https://github.com/SJTU-DENG-Lab/WaveForcing
ingested: 2026-08-19
authors: DENG Lab MLSys Team · Shanghai Jiao Tong University · 项目博客（arXiv 未出）
year: 2026
---

# Wave Forcing · 砍一条边，换一条流水线

流式视频生成的算法-系统共设计。**尚无论文**——信源是项目页（博客版论文）与开源的推理 runtime；训练代码与 4-step 正主 checkpoint 未放出，arXiv 出来后本页对照修订。

## 一句话

**造成逐层全组同步的不是 Rolling Forcing 的混合噪声窗口，而是「噪块影响净块」这条反向注意力边；砍掉它，执行图从环变成 DAG，去噪阶段才有条件错步流水。**

## 它要解决的痛点

- 块优先流式（CausVid/Self-Forcing 系）：chunk 内所有去噪步串行，多卡吃不满；
- Rolling Forcing：活的混合噪声窗，但窗内注意力双向 → 每层 Transformer 全窗同步（Ulysses/Ring 也逃不掉逐层协调）;
- Live Avatar：一卡一阶段硬件流水,但各阶段历史 KV 冻结在固定噪声态,不被更净表示刷新。

## 核心设计

1. **算法只改一件事**:跨 chunk 注意力改块因果(噪看净、净不回头),混合噪声日程与活上下文保留;配 rollout-aligned 蒸馏(训练=推理的有向前沿)。
2. **Wave Parallelism**：4 个去噪 rank 与 1 个 store rank 各有完整 DiT 副本；3 个 VAE rank 各自只保存解码器的一段。chunk 每 tick 挪到下一阶段，在 GPU×时间矩阵里走对角线。逐层 KV 改成单向发布，不再逐层全组 all-gather；但当前代码在 tick 边界搬 latent 仍有 world `all_gather`，初始化 clean anchor 也有 broadcast。
3. **负载不均 = overlap 预算**:最噪 rank 上下文最长(≈8 块)算得最慢,较净 rank(≈5 块)快——快者先发 KV,通信藏进关键 rank 计算窗(14B 实测 r0 646ms/层 vs 其余 575–581,~70ms 顺风差)。
4. **KV 传输三税**:FP8 KV 减字节(79→40ms,配 Sage 反噬、实验性);copy engine 单边写免 NCCL 配对(0 SM、343GB/s);paged 直写免 torch.cat(18.49→4.08ms)。推荐 causal+paged。
5. **VAE 按实测时间切**:高分辨率上采样块 memory-bound、同 FLOPs 壁钟差 6×;FLOPs 均分 →146ms 瓶颈段,实测均分 →95/99/96ms 跟上 DiT ~95ms tick。连续 DP min–max 划分,bit-exact。切得动的前提:decoder 是纯前馈单元列(无注意力、无跨块交互),段边界点对点递一次激活;因果 VAE 的时间缓存跟单元驻卡,流水错位恰好满足"块 c 用块 c−1 的缓存"。

## 先分清三个版本

- 公开的 1.3B Preview 是 **5-step、5+2**，README 时间表为 `[1000,800,600,400,200]`，可复跑到 84.2 E2E FPS。
- 最佳 117.7 E2E FPS 来自 **4-step、4+3**，代码默认时间表为 `[1000,750,500,250]`，正式 4-step 权重尚未公开。
- 14B 的 28.1 FPS 使用随机初始化、形状对齐的权重，只测系统扩展，不代表生成质量。

## 关键数字（8×H200 · 1596 输出帧）

- 最佳 E2E:117.7 FPS(13.56 秒出 100 秒视频),单卡 7.9×;最快稳态 tick 126.5 FPS(94.9ms)。
- 5+2 拓扑结构性天花板 ~85 FPS(两段 VAE 藏不住解码尾巴)。
- VBench-Long 100 秒:与 Rolling Forcing 打平,Quality Drift 0.030 vs 0.618;**RF 旧权重硬套块因果推理 → Drift 2.825**——必须配套重蒸馏,算法系统绑定交付。

## 边界

- 无论文;训练代码未开源,蒸馏细节只有"rollout-aligned"一词;14B 行是随机权重系统刻度;4-step 质量是 5-step 权重强推 4 步的口径。
- runtime 最多保留第一个 clean anchor 加最近 7 个 clean page，工作注意力窗还会进一步截断；“无限生成”不等于每一步都回看完整历史。

## 关键概念 → 概念页链接

- [[autoregressive-vs-bidirectional-video-diffusion]] — 流式路线全景
- [[block-causal-attention]] — 砍反向边后的注意力形态
- [[chunk-wise-self-forcing]] — "训练=推理"蒸馏哲学的近亲
- [[distributed-training-parallelism]] — "计算盖通信"一脉;此处时间差来自因果上下文天然不等长

## 我的批注

- 全文最有信息量的对照是"RF on WaveRT"那行:光改推理 mask 漂移恶化 4.6×,重蒸馏后反而比原版稳 20×——证明这是算法-系统共设计,不是纯 runtime 工作。
- "慢 rank 当 overlap 窗口"是共设计的点睛:负载不均不是 bug 是预算,而且由块因果的上下文长度差**天然**产生。
- bespoke 页首次引入 anime.js(CDN+SRI)做波前/甘特动画——"东西随时间流动"的图用时间线库,静态示意继续内嵌 SVG。
