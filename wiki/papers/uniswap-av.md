---
name: uniswap-av
type: paper
source: https://arxiv.org/html/2608.11752
upstream: https://uniswap-av.github.io/
ingested: 2026-08-18
authors: Yuxuan Zhang, Haozhong Xiong, Jiayi Song, Jinpeng Yu, Yang Shi, Jiaming Liu, Ruihua Huang, Liwei Wang · CUHK × Qwen Applications Business Group, Alibaba · 2026
year: 2026
---

# UniSwap · 一套模型同时换脸、换声，并按块流式生成

视频换人通常是两条互不相干的流水线：视频模型换外观，声音模型换音色。两边各做各的，嘴型看不到转换后的声音，声音也不知道画面里的人何时张嘴。UniSwap 把参考人物的外观与声音、原视频的动作与台词，一起交给同一个音视频扩散 Transformer；再把离线双向模型分三步改造成可缓存、三步去噪的流式生成器。

## 一句话

**先把普通真人视频伪装成“动作和台词相同、身份不同”的输入，再训练模型恢复原身份；学会联合换脸换声后，用块因果掩码、Self-forcing DMD 与可重定位 RoPE，把它改造成持续流式生成器。**

## 先分清三个公开口径

1. **论文实测**：100 条约 10 秒视频、20 条 1 分钟视频；三步模型在单张 H100 上达到 13.6 生成帧每秒。
2. **项目页宣称**：支持稳定的小时级长视频生成。论文没有给小时级量化表，项目页公开演示也以 10 秒和 1 分钟为主。
3. **代码公开状态**：截至 2026-08-18，官方仓库仍写着 <code>Code coming soon</code>，只有 README 与展示资源；无法从实现核对掩码、缓存和训练循环的所有细节。

## 原文覆盖地图

| 原文章节 | 本页落点 |
|---|---|
| 1 Introduction | 为什么“视频换人 + 变声”级联无法联合修正嘴型与声音 |
| 2 Related Work | 换人、变声、联合音视频生成、少步蒸馏四条前置路线 |
| 3.1 Data synthesis | swap-and-reconstruct 的视觉、音频、参考身份三路构造 |
| 3.2 Stage 1 | 双流输入拼接、位置偏移、联合 flow-matching |
| 3.3 Stage 2 | 三 latent 帧一块、解耦流式掩码、teacher forcing 与 KV cache |
| 3.4 Stage 3 | self-forcing rollout、三角色 LoRA、DMD 方向、三步噪声表 |
| 3.4.2 Feature-RoPE | sink、reference re-anchoring、四槽滚动窗口 |
| 4 Experiments | 数据、训练配方、指标、短视频/长视频/速度与消融 |
| Supplement §6–9 | 定性消融、完整缓存算法、30 人用户研究、更多样例 |
| Supplement §10–11 | 单人场景、遮挡与表情控制局限；冒充与误导风险 |

## 先拼完整系统

```text
普通真人片段 (Vt, At)
  ├─ 去掉人物外观，留下背景 + 姿态骨架 ─→ 源视频 Vs
  ├─ 把原声音转换成随机说话人音色 ─────→ 源音频 As
  ├─ 抽一帧人物照 ────────────────────→ 参考图 Ir
  └─ 抽原音频 30% 的一段 ─────────────→ 参考声音 Ar

Stage 1 · 双向联合换人
  [参考 ; 源 ; 带噪目标] → LTX-2.3 音视频双流 DiT → 恢复原片

Stage 2 · 学会按块向前
  当前块只看：参考 + 对齐的源块 + 已完成历史 + 自己
  → 每完成一块，写入 KV cache

Stage 3 · 适应自己的历史并蒸成 3 步
  Teacher LoRA / Generator LoRA / Critic LoRA
  共用同一套冻结 backbone，轮流启用

推理
  永久参考 cache + 首块 sink + 两块滚动历史 + 当前块
  → 每块 24 像素帧，3 次去噪，持续输出画面与声音
```

## 数据从哪里来：标签是真片，输入是人工退化片

自然界几乎找不到两个人同时说同一句话、做同一套动作、站在同一背景里且逐帧对齐的视频。UniSwap 不去收这种配对，而是从一条真实片段自己造。

设真实目标为视频 (V_t) 和声音 (A_t)：

- 视觉侧用 ViTPose 找全身 2D 关键点，再用关键点提示 SAM 2 分割人物；膨胀并随机扰动人物 mask，挖掉人物得到背景底片，然后把渲染的姿态骨架贴回背景，形成源视频 (V_s)。它保住动作、时间与背景，却尽量拿掉脸、衣服和体型等身份线索。
- 音频侧用现成的 Seed-VC，把 (A_t) 转成随机说话人的音色，得到 (A_s)。台词、语速和韵律尽量不变，只换音色。
- 从原视频抽一帧当参考图 (I_r)，再从原声音随机截取全长 30% 当参考声音 (A_r)。

模型收到 ((V_s,A_s,I_r,A_r))，目标仍是恢复 ((V_t,A_t))。Seed-VC 没有制造训练标签：标签一直是真实录音；它只负责把输入音色改乱，逼模型从 (A_r) 找回原说话人。

## Stage 1：把“照谁长、按谁动、用谁的声音”放进同一上下文

LTX-2.3 有视频流和音频流，两边每层通过双向 cross-attention 交换信息。视频 VAE 每 8 个像素帧压成 1 个 latent 帧；音频是每秒 25 个 latent token。两条流都使用同一条物理时间轴。

两条输入序列分别写成：

\[
x^v=[z_r^v;z_s^v;z_t^v],
\qquad
x^a=[z_r^a;z_s^a;z_t^a].
\]

- 上标 (v/a)：视频或音频模态；
- 下标 (r/s/t)：参考身份、源内容、目标；
- (z)：VAE 或音频编码器得到的 latent token 序列；
- 分号：沿 token 序列拼接，不是加法。

训练只给目标段 (z_t^v,z_t^a) 加噪；参考和源内容保持干净，相当于噪声强度 (sigma=0)。源与目标表达同一时间段，因此共享时间位置；参考图与参考音频使用各自固定偏移 (Delta_r^v,Delta_r^a)，避免输入长度一变，三段的位置关系就跟着乱。

## Flow matching：每个符号和一笔完整手算

干净 latent 是 (z_0)，随机高斯噪声是 (epsilon)，噪声比例是 (0\leq\sigma\leq1)。先把两端线性混合：

\[
z_\sigma=(1-\sigma)z_0+\sigma\epsilon.
\]

当 (sigma=0) 时得到干净数据；当 (sigma=1) 时得到纯噪声。沿这条直线对 (sigma) 求导：

\[
\frac{\mathrm d z_\sigma}{\mathrm d\sigma}
=-z_0+\epsilon
=\epsilon-z_0.
\]

所以网络 (v_\theta) 要预测的不是凭空指定的目标，而正是从干净端走向噪声端的恒定速度：

\[
\mathcal L_{\mathrm{FM}}
=\mathbb E_{z_0,\sigma,\epsilon}
\left[
\left\|v_\theta(z_\sigma,\sigma)-(\epsilon-z_0)\right\|_2^2
\right].
\]

- \(\theta\)：正在训练的 LoRA 参数；
- \(\mathbb E\)：对训练片段、噪声强度和随机噪声取平均；
- \(\lVert q\rVert_2^2\)：向量每个分量平方后相加；
- 视频和音频各算一份，Stage 1 总损失是 \(\mathcal L_{\mathrm{FM}}^v+\mathcal L_{\mathrm{FM}}^a\)。

用标量手算：取 (z_0=2,epsilon=-1,sigma=0.25)。

\[
z_\sigma=0.75\times2+0.25\times(-1)=1.25,
\qquad
v^*=\epsilon-z_0=-3.
\]

若网络预测 (-2.5)，这一项损失就是 ((-2.5-(-3))^2=0.25)。从 (z_0=2) 沿速度 (-3) 走满 1 个 (sigma) 单位，正好到 (-1)，与噪声端对上。

## Stage 2：不是“把双向 attention 改成 causal”一句话就结束

目标视频按 (K=3) 个 video latent 帧切块；因为视频 VAE 压缩 8 倍，一块对应 24 个像素帧，约 0.96 秒。第一块例外，使用 4 个 latent 帧，来自因果 VAE 的时间索引要求。音频也按同一物理时段切块。

记第 (i) 个目标块为 (B_i)，对齐的源块为 (S_i)。训练当前块时，它只准看：

\[
\mathrm{ref},\quad S_i,\quad B_0^{\mathrm{clean}},\ldots,B_{i-1}^{\mathrm{clean}},\quad B_i^{\mathrm{noisy}}.
\]

参考 token 和每个源块独立编码；已完成目标块按块因果读取；当前带噪块不能偷看未来目标。相同的角色掩码同时用在视频 self-attention、音频 self-attention 和音视频 cross-attention 上，模态块长不同，但覆盖的真实时间相同。

Stage 2 仍用 teacher forcing：历史块来自真实目标。损失只算当前带噪块：

\[
\mathcal L_{\mathrm{Stage2}}
=\mathbb E_{i,\sigma}
\left[
\mathcal L_{\mathrm{FM}}
(B_i\mid\mathrm{ref},S_i,B_{<i}^{\mathrm{clean}})
\right].
\]

这一步让训练时的可见范围与 KV-cached 推理对齐，却留下一个缺口：部署时历史是模型自己生成的，错一点就会喂回下一块；Stage 3 专门补这一刀。

## Stage 3：Self-forcing 修历史，DMD 修速度

学生先真正生成整条音视频：每块都把上一块自己的结果当历史，不再只吃真值。每块只走三个噪声点 ([0.999,0.757,0.522])，于是训练时就会碰到部署时的错误历史。

DMD 需要三个角色：

| 角色 | 本文怎么初始化 | 训练时做什么 | 推理时保留吗 |
|---|---|---|---|
| Teacher | 冻结 Stage-1 LoRA | 双向看完整序列，给目标分布方向 | 否 |
| Generator | Stage-2 LoRA 初始化 | 块因果生成，接收梯度更新 | **是** |
| Critic | 随机 LoRA | 追踪学生当前生成分布 | 否 |

三者轮流挂在同一个冻结 LTX-2.3 backbone 上。共享 backbone 省的是参数副本，不是把三次前向合成一次；只有当前角色的 LoRA 被启用。峰值显存从单张 80 GB 卡上直接 OOM 降到 65.34 GB。

## DMD 公式：先算 CFG teacher，再与 critic 相减

对学生生成的整段 (hat z) 随机加噪，噪声强度 (sigma\sim\mathcal U[0.02,0.98])。论文给出的样本方向是：

\[
g_{\hat z}
=D_\phi(\hat z_\sigma,\sigma)
-\left[
T_\psi^+(\hat z_\sigma,\sigma)
+\gamma\bigl(T_\psi^+(\hat z_\sigma,\sigma)-T_\psi^-(\hat z_\sigma,\sigma)\bigr)
\right].
\]

- (hat z)：Generator 生成的音视频 latent；
- (hat z_\sigma)：重新加噪后的学生样本；
- (D_\phi)：Critic 对学生当前分布的预测；
- (T_\psi^+)：Teacher 看条件时的预测；
- (T_\psi^-)：Teacher 不看条件时的预测；
- (gamma)：CFG 强度，视频为 3，音频为 5；
- (g_{\hat z})：先在生成样本空间算出的方向，再通过 (hat z=G_\theta(\cdot)) 的链式法则更新 Generator。

数字例沿视频分支走一遍。若 (T^+=0.8,T^-=0.2,gamma=3,D=3.1)：

\[
T_{\mathrm{CFG}}=0.8+3(0.8-0.2)=2.6,
\qquad
g_{\hat z}=3.1-2.6=0.5.
\]

Critic 认为学生分布在这个方向上的值比 Teacher 目标高 0.5，Generator 的梯度下降会沿相反方向修正。若 Critic 已追到 Teacher，二者同为 2.6，差值变 0，Generator 在这一维不再被推。论文没有公开 critic 的完整训练损失，只说明它在带噪学生样本上训练；不能据此补写一套未披露公式。

## Feature-RoPE Decomposition：缓存内容，位置需要时再贴

普通 KV cache 会把已经做过 RoPE 的 Key 存下来，时间越长，绝对位置越大，最终跑出训练时见过的范围。UniSwap 改存未旋转的 Key：内容特征只算一次，位置相位按它当前所在的 cache 槽重新旋转。

把尚未加入位置的内容 Key 记为 \(k\)，真正缓存的是 \(k\)，attention 使用前才贴上本轮的局部相位：

\[
K_{\mathrm{cache}}=k,
\qquad
K_{\mathrm{attn}}=R(\widetilde p_i)k.
\]

- \(R(\widetilde p_i)\)：局部位置对应的 RoPE 旋转矩阵；
- \(K_{\mathrm{cache}}\)：窗口滚动时仍可复用的内容 Key；
- \(K_{\mathrm{attn}}\)：当前这轮拿去与 Query 做点积的、已重新定位的 Key。

缓存固定为 (W=4) 个局部槽：首块 (B_0) 永久充当 identity sink；两格放最近完成的历史；最后一格放当前块。参考身份永久缓存，但每轮会相对当前槽重新定位。滚动块的本地坐标是：

\[
\widetilde p_i(\tau)=\tau-\tau(h_i).
\]

- \(\tau\)：当前 token 在共同物理时间轴上的时间；
- (h_i)：本轮保留历史里最早的滚动块；
- \(\tau(h_i)\)：这块的起始时间；
- \(\widetilde p_i\)：减去窗口起点后的局部位置。

例如窗口保留的物理块时间是 100、101、102；最早滚动块从 100 开始。三块局部位置是 (0,1,2)。下一轮丢掉 100，保留 101、102 并加入 103，新的起点变 101，局部位置仍是 (0,1,2)，不会长到 10,000。视频和音频都从同一物理时间算局部位置，移动窗口后仍对齐。

## 一块实际怎样走完缓存

1. 参考图与参考音频只 prefill 一次，Key/Value 永久留在参考区。
2. 第 (i) 个源块 (S_i) prefill 到当前槽，只在生成对应 (B_i) 时暂存。
3. (B_i) 走三次去噪，只读参考、sink、两块滚动历史和 (S_i)，不反复写 cache。
4. 去噪完成后，把干净 (B_i) 再前向一次并提交到历史；若是 (B_0) 就进 sink，否则进滚动区。
5. 滚动区满了就踢掉最老一块，保留块换成本地坐标并重新施加 RoPE。
6. 删除临时源块 (S_i) 的 KV，再处理下一块。

参考区、sink 和滚动历史大小固定，所以单块 attention 成本不会随着已生成时长一直增长。

## 训练配方

- 数据：AVSpeech；训练片段 241 帧，25 FPS，约 9.6 秒。
- 分辨率：(512\times512)、(416\times704)、(704\times416) 三档。
- Backbone：冻结 LTX-2.3；bf16；8 张 GPU；FSDP。
- Stage 1：attention projection 上 rank-128 LoRA；AdamW；学习率 (10^{-4})；50k 步。
- Stage 2：音视频 attention、FFN 与 cross-attention 上 rank-128 LoRA；学习率 (10^{-4})；50k 步。
- Stage 3：三套 rank-128 LoRA；Generator/Critic 学习率 (10^{-5})；20k 步；Critic 每次 Generator 更新前先更新 5 次。
- 发布模型：官方项目 README 称 conditioned model 为 22B；论文未给可下载 checkpoint，截至写作时代码和权重尚未公开。

## 实验：它赢在联合同步与长程身份，不是每列都赢

先翻译指标：Sync-C 越高、Sync-D 越低表示嘴型与声音更对齐；DINO-S 比较输出人物和参考图的视觉身份；IQA / ASE 分别估图像技术质量与审美；SIG 属于 DNSMOS 语音质量分，SECS 比较说话人嵌入。它们都是代理指标，不能代替真人观看和听辨。

短视频基准有 100 条约 10 秒片段。视觉 baseline 全部配相同 Seed-VC，才构成“换人 + 换声”级联对手。

- 音画同步：Sync-C 3.633 为最高，Sync-D 10.304 为最低。
- 视觉身份：DINO-S 0.629，和最强 SCAIL-2 的 0.630 只差 0.001；但美学与画质分低于 MoCha / SCAIL-2。
- 声音：SIG 3.486，接近 Seed-VC 的 3.489；但 BAK、OVRL、SECS 和 SSIM 没赢过最强单模态变声器。
- 速度：一块 24 帧用 1.76 秒，即 13.6 FPS，约为 Wan-Animate 1.367 FPS 的 10 倍；但播放速度是 25 FPS，所以它能边生成边吐块，**还不能实时跟上播放**。

长视频基准只有 20 条、每条 1 分钟。UniSwap 的 DINO-S 三段为 0.596、0.590、0.596；SCAIL-2 从 0.566 降到 0.517。UniSwap 的身份更稳，但 SCAIL-2 的 IQA 全程更高。项目页的“小时级稳定”没有同等量化表支撑，应视为额外宣称而非论文已经证明的结论。

## 消融比主表更能说明三阶段各管什么

- Stage 1 的同步、画质和说话人相似度最好；它是离线双向上限。
- Stage 2 换来块因果和缓存，但同步与声音分数下降。
- Stage 3 把 30 步压到 3 步，并让训练看到自生成历史；DINO-S 和多项声音质量比 Stage 2 回升，但同步、ASE、IQA、SSIM 又下降。蒸馏不是白拿十倍速度。
- Stage 2 删除 condition PE offset 后，Sync-C 从 4.620 掉到 1.738，DINO-S 从 0.623 掉到 0.463。
- Feature-RoPE 三件套任删一个，后 20 秒退化都更明显。删 reference re-anchoring 后，末段 IQA 从 3.741 降到 3.208，DINO-S 从 0.595 降到 0.491。

30 人盲测里，每人看 4 条源视频。UniSwap 的外观身份 4.16、嘴型同步 4.11、自然度 3.96 都最高；声音身份 3.87 反而低于四个 Seed-VC 级联对手。联合模型把优势集中在“人、声、嘴能不能对上”，没有在纯声音克隆上击败专用系统。

## 没有公开或没有证明的部分

1. 多人同时说话、严重遮挡、复杂互动仍是明确局限。
2. 表情由音频自动驱动，不能独立指定或编辑表情。
3. 训练数据清洗、AVSpeech 实际样本数、mask 增强分布、随机说话人采样规则未公开。
4. critic 完整目标、DMD 的反向实现、三角色切换调度与缓存 tensor 形状没有公开代码可核。
5. 13.6 FPS 小于 25 FPS，术语“streaming”不能偷换成“实时播放”。
6. 小时级生成只有项目页宣称；论文量化只到 1 分钟。
7. DINO-S、SyncNet、DNSMOS 等代理指标不能代替真人对身份、同步和自然度的全部判断；用户研究也只有 30 人 × 4 条片段。
8. 换脸换声会提高冒充、未经同意生成和虚假信息风险；论文建议采用同意、来源标记、显著披露、访问控制与取证检测。

## 我的批注

- 最有价值的不是“同时换脸换声”这句产品描述，而是三步迁移路线：先学任务，再对齐训练/部署可见范围，最后才让学生吃自己的历史并做少步蒸馏。三个难题没有被一个大 loss 硬塞在一起。
- swap-and-reconstruct 跟旧版 Wan-Animate 的自重建监督同属一条思路：真实片始终当干净标签，人工退化只负责制造条件输入。这里的新点是视觉和音频身份同时被拿掉。
- Feature-RoPE 解决的是缓存“地址过期”，不是重新算内容。把未旋转 Key 与位置相位拆开后，缓存内容可复用，地址可随滚动窗口重贴。
- Multi-LoRA switching 省下三套 22B backbone，却没有免掉 Teacher、Generator、Critic 各自的前向；这是显存优化，不是计算免费。
- 实验很诚实地暴露了速度账：三步模型已经能流式吐块，却只有 13.6 FPS。低延迟接口、实时吞吐、最终画质是三笔不同的账。

## 相关概念

- [[swap-and-reconstruct-supervision]] · 没有跨身份配对时怎样自己造监督。
- [[decoupled-streaming-conditioning-mask]] · 训练时就限制成部署时能看到的上下文。
- [[efficient-multi-lora-switching]] · 三个 DMD 角色共享冻结主干。
- [[feature-rope-decomposition]] · 缓存内容与位置相位分开。
- [[audiovisual-cross-attention]] · 嘴型和转换后声音在同一模型里互相校正。
- [[conditional-flow-matching]] · Stage 1/2 的去噪目标。
- [[dmd-distillation]] · Stage 3 的少步分布匹配。
- [[chunk-wise-self-forcing]] · 为什么训练要接触自己的历史。
- [[kv-cache]] · 参考、源块与目标历史怎样缓存。
- [[lora]] · 三阶段只训练低秩适配器。

## 跟 wiki 里其他论文的关系

- [[ltx-2]] · UniSwap 冻结并改造的音视频双流基础模型。
- [[dmd]] / [[dmd2]] · 三角色分布匹配的上游。
- [[wan-animate-2]] · 同样用人工退化的自重建监督和分块 self-forcing，但目标集中在视觉角色替换。
- Omni-Forcing 路线 · 同属从双向音视频模型蒸成滚动流式模型的思路；UniSwap 额外加入源视频、参考身份和换人任务。
- [[wan-streamer-v03]] · 同样追求持续音视频输出，但 Wan-Streamer 更偏交互角色生成，UniSwap 是源视频驱动的身份替换。
