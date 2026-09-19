---
name: lynnreal-omni
type: paper
source: raw/lynnreal-omni.txt
upstream: https://arxiv.org/abs/2609.15863
ingested: 2026-09-17
authors: LynnReal Lab × 上海创智学院 × 上交 × 复旦 · arXiv 2609.15863 (2026-09)
year: 2026
---

# LynnReal-Omni · agent 搭台，扩散唱戏：一个模型接所有视觉控制

面向 agentic 视觉工作流的原生多模态视频生成系统报告。32B 标准版(基于 MiniMax-H3 骨干)+ 27B Flash 实时版 + 轻量 VAE 解码器 + MSAVP 评测基准,权重/代码开源。

## 一句话

**agent 造控制(参考图、可编辑 3D 场景、可执行游戏),一个共享 DiT 吃所有控制:T2V/图像条件/参考引导/结构控制/编辑/修复/长视频统一在同一模型里,任务=不同的打包布局;少步蒸馏后瓶颈移到 VAE 解码,于是把 36 块解码器蒸成 26 块——warm 状态 540p 22 帧,标准版 DiT+解码 843ms、Flash 377ms(单 H100)。**

## 它要解决的痛点

- 扩散生成随机、难控:精确内容靠反复抽卡,长视频漂移;agentic 创作(3D 场景/游戏)控制显式但保真度不够——两者互补;
- 四个缺口:任务碎片化(agent 得拼一堆模型)、长程不一致、评测协议不全(多镜头/动作绑定/物理/音频没在一个协议里)、**少步蒸馏后 VAE 解码成为推理大头**。

## 核心设计

1. **原生任务表示**:每任务打包模态标签、行索引、3D RoPE、逐行噪声时刻;帧对齐控制与目标满足 τ_target−τ_control=Δ>0 的固定正偏移(把控制和生成分域;绝对坐标相等会改变条件语义)。两种图像接口:统一参考布局(语义)vs 原生关键帧布局(首末帧编进目标分区)。
2. **训练目标**:clean-time 约定 z_t=tz+(1−t)ε、v*=z−ε;视频噪声 shifted logistic-normal(u=σ(g), s_v=3u/(1+2u);g=0 时 s_v=0.75 偏噪);音频对齐钟 s_b=s_v/(12−11s_v)、s_a=3s_b/(1+2s_b)——同一随机数两模态各自的时刻;L=MSE_v+0.1·I·MSE_a(缺音频≠监督静音);**guidance-aware fitting**:ṽ=(v_c+(w−1)sg(v_∅))/w、w=3,把 CFG 蒸进条件分支,推理不再跑无条件前向,最优时 v_c≈3v*−2v_∅。
3. **少步蒸馏**:标准版 low-rank TDM 4 步(冻结教师+全深 fake critic,critic 用裁剪 SNR 加权的重要性回归,学生用归一化 pseudo-Huber ρ_c(e)=√(e²+c²)−c);Reward Forcing 动态奖励只加权视频项。四步双钟:视频 clean-time (0,.0270,.0769,.2000) ↔ 音频 (0,.10,.25,.50)——后者恰是前者经映射的精确像(已验算)。
4. **Flash 27B**:留 42/50 块、3 步;三明治结构:前 2 块全序列、中 26 块空间 stride-2 token 压缩(≈1/4,保边界行列,文本/音频不压,保原 RoPE),H_out=H+U(F_mid(PH)−PH) 最近邻回填残差,末 14 块全分辨率;W4A8(INT4 权重+FP8 激活)+算子融合。
5. **长视频**:每 chunk 17 新帧、4 次求值;上一 chunk 末帧当共享边界(latent 冻结,与 5 个未来 latent 联合解码后去重);紧凑时间上下文=最早帧全分辨率+近 2 帧 stride2+更早 ≤8 帧 stride4,总 token ≤2 个全分辨率帧,注意力成本与视频长度无关;有界存储(留头留尾丢中间)。
6. **轻量解码器蒸馏**:36 块教师→26 块学生(隐维 2048 不变、latent 接口不变、可直接替换);训练分布 0.6 数据编码 latent + 0.4 模型生成 latent(+0.25 概率扰动);损失=L1+5·MSE 重建 + 15 项空间/时间正则(tile 边界权重 1.50 最大)+ 末 3 块特征蒸馏 + DINOv2 感知 + **cycle 一致性**(师生重建经冻结编码器重编码,逐坐标高斯 KL 过 log(1+max(k,0)) 压制大偏差)。受控对照:同条件 36→26 块解码 469→340ms。
7. **agent 3D/游戏控制**:参考图→场景构建→渲染对比精修位姿相机→接触校正→显式状态更新的游戏逻辑;录制脚本按固定输出间隔推进仿真,录制耗时与播放速度解耦。

## MSAVP 基准(自建)

100 prompt(54 单镜头+46 多镜头,22 条要音乐)× 20 指标 × 6 能力族等权(1/6);流程五步:冻结清单(GPT-6 Astra 只看 prompt 出条件,评审不得增删改)→专家证据(TransNetV2/Qwen3-Omni 音频/CLIP-LAION/MUSIQ/VMBench MSS/InsightFace)→盲评审(只看视频评跨切动作)→主评审(逐条件 1/½/0)→机械聚合。**自家基准自家不是第一**:T2V Seedance 79.39 > H3-FL2V 79.27 > Lynn 77.76;I2V H3 80.65 > Lynn 79.20。Lynn 强项:I2V Prompt Fidelity 86.55(第一)、Entity Fidelity 97.06、Imaging Quality 71.42、World-state 81.65。LTX-2.5/Cosmos3 多镜头族崩(它们本就不做多镜头)。

## 关键数字

- 延迟(warm,单 H100,540p 22帧):标准 4 步 DiT+解码 843ms/墙钟 959ms;Flash 3 步 377/479ms。768p 15s:标准 122.9s vs Flash 40.4s(3.05×)。累积消融:算子融合砍墙钟 43.6%/31.6%;**W8A8 不融合反而变慢**(2682→3627ms);token 压缩关掉 DiT 263→453ms。
- 数据:公开视频→高质量多镜头,产率 0.6%(按存储);场景分组 48 shot 窗/12 重叠;每 clip ≤6 个可复用主体;裁剪上限 25%。

## 关键概念 → 概念页链接

- [[agentic-visual-creation]] — agent 造控制信号这半边(新)
- [[mid-stack-token-compression]] — Flash 的三明治压缩(新)
- [[lightweight-decoder-distillation]] — 解码器蒸馏+cycle 一致性(新)
- [[trajectory-distribution-matching]] — 少步蒸馏主力
- [[dmd-distillation]] — TDM 的母体
- [[guidance-distillation]] — eq6 的 guidance-aware fitting 是它的变体
- [[video-vae]] — 被蒸的对象
- [[chunk-wise-self-forcing]] — 长视频 chunk 化的近亲路线

## 我的批注 / 疑问

- 立意最值钱:「少步蒸馏后瓶颈在 VAE 解码」这个观察 + 把解码器当一等公民蒸馏,是很多少步论文忽略的半截账;延迟消融的纪律也好(逐组件、双 GPU、区分数值精确与近似)。
- 自家 bench 自家非第一是加分的诚实;但 judge 全链路(Astra/Codex/提示)是自家选型,Seedance I2V 因 API 审核缺席,横比要留一分。
- 口径打架自曝三处:摘要 843/377ms vs 引言 909/591ms(后者全文无出处)vs 打包版 857/383;摘要说 20 指标、贡献列表说 25、表 5 实为 20。
- 训练数据规模、算力、步数全部未披露;编辑数据集(§3.7)只有一句话;MSAVP 与人评的一致性明说还没做。
- 基座是 MiniMax-H3(related work 明说 builds directly on),32B 标准版即 H3 骨干的多任务扩展——和 H3-FL2V 同台比时读者应知道这层亲缘。
