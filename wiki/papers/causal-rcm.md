---
name: causal-rcm
type: paper
source: raw/causal-rcm.txt
upstream: https://arxiv.org/abs/2606.25473
ingested: 2026-08-14
authors: Kaiwen Zheng 等（清华大学、UT Austin、NVIDIA）· arXiv v1 2026-06-24
year: 2026
---

# Causal-rCM · 把 rCM 的正反散度互补搬进自回归视频

rCM 的续作（同一作者团队）。rCM 蒸的是双向视频扩散——整段一锤子买卖；Causal-rCM 把同一套「正向散度保覆盖 + 反向散度提质量」哲学搬到因果注意力的自回归视频扩散上，用于流式生成和可操控的交互世界模型。

## 一句话

**teacher-forcing CM 管照着老师学（正向、离线、保多样性），self-forcing DMD 管在自己 rollout 上改（反向、在线、治曝光偏差），三段串行。**

## 它要解决的痛点

- 双向少步模型必须整段生成完才能播，首帧延迟 = 全片时长；流式播放和动作条件的世界模型需要逐 chunk 出帧。
- 因果训练的老毛病：teacher-forcing / diffusion-forcing 有曝光偏差（训练看真历史、推理看自己生成的历史，误差滚雪球）；self-forcing 用 on-policy 训练治好了曝光偏差，但 DMD/GAN 都是反向 KL 一族——对初始化敏感、容易模式坍缩。
- 已有系统各自发明初始化招数（ODE-pair 回归 / DF 因果适配 / 混合 TF-DF），但「初始化 × 因果范式 × 蒸馏损失」的组合从没被系统地摆到一张桌上比过。

## 核心贡献

- **统一视角**：TF↔正向散度（对应 rCM 的 CM 项），SF↔反向散度（对应 DMD 项）；与 DDO / DiffusionNFT / DDRL / rCM 同属一脉的正反互补。
- **TF-sCM 首个实现**：teacher-forcing 版连续时间一致性（sCM/MeanFlow），靠 custom-mask FlashAttention-2 JVP kernel 撑起来；比 TF-dCM 收敛快约 10×（1-2k 迭代超过 dCM 的 10k）。
- **系统的初始化消融**：6 种初始化 × 2 种 chunk 粒度；DF/TF 初始化 VBench 分数最高但画面过平滑失细节——分数会说谎，TF-CM 才是综合最可靠的初始化。
- **开源算法-基建配方**：TF/DF/SF 三范式 + JVP + FSDP2 + Ulysses CP + SAC + KV cache 全兼容（对照 Self-Forcing / FastVideo / FastGen 各缺一角）。
- **SOTA 流式生成**：2 步因果 Wan2.1-1.3B 在 VBench-T2V 到 84.63（超双向 14B 老师的 83.35），frame-wise 15.9 FPS，二块延迟 0.23s；纯合成数据训练。
- **交互世界模型**：把 Cosmos 3 的 GEN 视觉流改成时间因果 supertoken + 动作 token 对齐，自动驾驶场景左/右/直行可控。

## 方法骨架（三段串行，不是 rCM 的联合训练）

1. **TF 因果化**（30k 迭代）：packed forward `[clean 历史, noisy 目标]` + TF mask，把双向 Wan 改造成因果扩散——既当因果老师，又当下一阶段的 student 初始化。
2. **TF-CM 少步化**（dCM 10k 或 sCM 1k 迭代）：沿因果老师轨迹做一致性蒸馏；sCM 的 JVP 方向是 `([0^clean, v_teacher^TF], [0,1])`——干净历史支路切线恒为 0。
3. **SF-DMD 精修**：自己逐 chunk rollout（KV cache），只对每 chunk 最后一步反传（梯度截断）；rollout 步数按迭代循环 `[1,1,…]→[2,2,…]→[3,2,…]→[4,2,…]`，让每个去噪区间都轮到「最后一步」。

不联合训的原因（论文 Limitations）：因果老师与双向老师存在分布差距，联合训练压低 VBench 上限。

## 关键工程事实

- **RF-native sCM 而非 TrigFlow 包装**：附录 A 证明两者一致性零点相同、exact 算术下切线只差 b²=(cos τ+sin τ)⁻² 标量，但（i）切线归一化的 +c 让两个 MSE 目标不再等价（cZ⁴ vs c）；（ii）浮点下系数放进/放出 JVP 方向不逐位相等，归一化会放大差异。双向 rCM 里 TrigFlow 包装有益，因果 TF 里反而画质劣化。
- **custom-mask FA2 JVP kernel**：mask 是离散路由、没有切线（被禁位置 S=−∞ 且 tS=0）；在线 softmax 里加三个 JVP 累加器 A/B/r，尾声 tO=ℓ⁻¹(A+B−diag(r)O)；mask 用「query 组 × 合法 key 区间」矩形清单表示，不 materialize 稠密矩阵。Triton 实现，速度只打平 FA2（落后 FA3/4）。
- **noisy context**：复用最后一步去噪的 KV 当上下文，省掉每 chunk 的干净重编码 pass，N+1→N NFE；残噪还是低通滤波，抑制累积的高频伪影。
- **custom step schedule**：首 chunk 定全局布局最难，2 步模型用 `[4,2,2,…]`。
- **反直觉结果**：frame-wise 下 1/2 步反而比 4 步好（单帧 chunk 无内部时间结构，深 rollout 放大自回归反馈误差 → 相机漂移，4 步只能稳训 ~1k 迭代）；chunk-wise（3 帧）下 4 步最好。noisy context 在 chunk-wise 有利（高维冗余 token 群耐噪）、frame-wise 不利。
- **最好初始化 ≠ 最好终点**：TF-sCM 初始更强，但 frame-wise 下 TF-dCM 在 SF-DMD 期更稳、峰值更高。

## 关键概念 → 概念页链接

- [[causal-consistency-distillation]] — TF-CM 就是它的完整配方版
- [[chunk-wise-self-forcing]] — SF-DMD 的 rollout + 梯度截断
- [[autoregressive-vs-bidirectional-video-diffusion]] — 双向 vs 因果的取舍全景
- [[block-causal-attention]] — TF/DF mask 的底座
- [[continuous-time-consistency]] — sCM 切线目标（rCM 页详推）
- [[flash-attention]] — JVP kernel 在其在线 softmax 上加三个累加器
- [[distributed-training-parallelism]] — Ulysses CP 与 JVP/KV cache 的兼容设计

## 我的批注 / 疑问

- 这是「配方 + 基建」型论文：算法增量集中在 TF-sCM 首个实现和系统的初始化消融；基建贡献（兼容性矩阵、custom-mask JVP kernel）对社区可能比算法更值钱。
- VBench 与观感背离（DF/TF 初始化分数最高但过平滑）是全文最值得记住的方法论教训：榜单分数会说谎，选型要看图。
- 世界模型部分只有定性演示（自动驾驶三方向），无定量指标。
- 「student update freq. = 6」原文未展开（推测是 fake-score 与 student 的更新配比），复现时看代码为准。
