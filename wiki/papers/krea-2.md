---
name: krea-2
type: paper
source: https://www.krea.ai/blog/krea-2-technical-report
upstream: https://www.krea.ai/blog/krea-2-technical-report
ingested: 2026-06-25
authors: Krea AI · 2026
year: 2026
---

# Krea 2 · 不追一种"标准好看",撑开整个审美空间

Krea 2 是 Krea AI 2026-06-23 放出的文生图模型技术报告(K2 Raw + K2 Turbo 开放权重)。论点跟主流反着来:现在的图像模型技术都很强了,可它们**收敛到了一小撮默认审美**——一看就是"AI 味"那种锐利、油润、讨喜的样子。Krea 的主张是图像生成应该是**探索性的媒介**:既要表达力广(能横跨很多种审美),又要可控(创作者能在里面导航),而不是把所有 prompt 都优化成同一张"精致默认图"。

## 一句话
**主流模型都在卷"单一默认审美"并卷到饱和;Krea 2 反过来——数据上拒绝按美学分过滤、拒绝 AI 合成图,训练上用六段流水线(预训→中训→SFT→偏好优化→多奖励 RL→蒸馏)把审美空间撑宽,还自创 STPO(稳住 DPO 的偏好优化)和 prompt 级 rubric 奖励,目标是"多样且可控",不是"一种好看"。**

## 它要解决的痛点
- **模型审美收敛**:技术指标都满了,但顶尖模型画出来越来越像同一种风格(高饱和、强对比、糖水感)。创作者要的是"能探索很多种审美",不是"一种最讨喜的"。
- **数据过滤反而注入偏见**:业界常用美学打分(aesthetic score)和画质评估(IQA)模型筛数据,Krea 认为这套**隐式地把模型口味锁死**——把"不讨喜但真实"的图全删了,模型就再也学不到那部分分布。
- **AI 合成图污染分布**:很多管线拿 AI 生成图扩充训练集。Krea 发现哪怕掺一点点,模型质量就被**封顶**了——合成图"更好学",模型会偷懒往那边塌。
- **偏好优化会跑偏**:直接用 DPO 做偏好对齐时,模型可能把"赢的样本"和"输的样本"概率**一起压低**(只要差距拉大 loss 就降),结果整体质量下滑。

## 核心贡献
1. **数据策展哲学的反转**:[[generative-data-curation]] —— **不**按美学分过滤,只删重复/打错 caption/有害偏见/过于复杂不适合低分辨率建模的;并**全程 0 AI 合成图**。核心信条:"只要 caption 准确描述了图,哪怕这张图本身不讨喜,也对训练有用"。
2. **六段训练流水线**:预训(256→512→1024 渐进)→ 中训(自上而下按域策展,~500 万维基概念覆盖)→ SFT(小而精的人工审美集 + 模型合并)→ 偏好优化 PO → 多奖励 RL → 时间步蒸馏。每段各司其职,见图。
3. **STPO —— 稳住的偏好优化**:[[direct-preference-optimization]] —— 报告自创的 DPO 变体(报告未给全称),加一个辅助损失 + 改 DPO 公式,专治"win/lose 概率一起掉"的策略发散。PO 分两步:先大规模合成偏好对(类 delta learning,保证多数对里至少有一个 on-policy 样本)初调,再用**纯人工标注**(自家熟悉模型脾性的人)校准。
4. **多奖励 GRPO 式 RL + prompt 级 rubric 奖励**:[[grpo]] —— 四个奖励模型(通用美学 / 提示遵循 / 文字渲染 / 瑕疵与结构)一起推;rubric 奖励借鉴 [[rubric-based-evaluation]],把每个 prompt **拆成可验证的要求逐条判**,而不是让判官给一个笼统总分。整个 RL 阶段**不用 CFG**(保持 rollout 与训练分布一致,推理时再开)。
5. **TDM 时间步蒸馏 + 双发布**:[[trajectory-distribution-matching]] —— 对比了 DMD/DMD2/Decoupled DMD/piFlow/APT,最后选 TDM(好调、超参少)。发布 **K2 Raw**(未蒸馏基座,给做微调/后训练研究的)和 **K2 Turbo**(引导+时间步双蒸馏,少步快出图)。
6. **Prompt Expansion(防多样性塌缩)**:短用户输入扩成富 caption 的前置模型。SFT(从长 caption 反造用户 caption + 合成 thinking trace) + RL(GDPO 多奖励:图级 + prompt 级可验证 + 安全闸)。关键:expander 会塌成一种高奖励 house style,靠 **DINOv3 组内多样性奖励**(全程保活)压住;RL prompt 混硬例,挑"难但不绝望"的。
7. **Style Reference(压内容泄漏)**:文字 + 一/多张参考图导风格,要多风格平滑混合 + 强度连续可调。难题是 style/content 边界模糊导致**内容泄漏**(参考图主体钻进结果)。做法:**新自监督训练** style 模块 + 偏好优化对齐。
8. **罕见地摊开系统工程**:Kueue 调度 + Virtual Kubelet 外溢推理 + Packerman 把 dev 塞坏节点;observability 反直觉结论(InfiniBand fabric 是头号崩溃源 / GPU 利用率会骗人改看张量核 / <128 卡稳翻倍更崩 / 大规模无 run 跑过 24h);Weka 换 Ceph;krablet(PG 分片,208TB 元数据,FOR UPDATE SKIP LOCKED 把 DAG 当 DB 队列)。
9. **未来路线**:MoE / native 2K-4K(稀疏注意力) / NVFP4 预训 / Muon;**MOPD**(多教师 on-policy 蒸馏:各域专家→密集监督蒸进一个学生,各域不打架 + 团队可并行);架构统一(VAE+DiT+文本编码+expander 合一,让研究像 LLM 那样并行)。

## 架构速览
- **主干**:多模态扩散 Transformer [[mmdit]] / [[diffusion-transformer]],用 [[flow-matching]] 训。
- **注意力**:分组查询注意力 GQA + 门控 sigmoid 注意力;[[qk-rmsnorm]](QKNorm)+ 零中心 RMSNorm。
- **MLP**:[[swiglu]] 4× 扩展。
- **文本编码器**:[[qwen3-vl]](Qwen3-VL)多层特征聚合(受 Unifusion 启发)。
- **自编码器**:Qwen-Image VAE + FLUX 2 VAE 做 latent。
- **位置编码**:3D 轴向 [[rotary-position-embedding]](3D axial RoPE)。
- **训练加速**:首个 256px epoch 用 iREPA 加速收敛后撤掉;低/中分辨率 8-bit 训练(提速 15-20%);LR 用 warmup-stable-decay + PMA(参数合并近似,效果接近 [[ema]] 但省显存)。

## 关键概念
- [[generative-data-curation]] · 反美学分过滤 + 0 AI 数据:数据哲学是这报告的灵魂
- [[direct-preference-optimization]] · DPO 与 Krea 的 STPO 变体(治"win/lose 一起掉")
- [[trajectory-distribution-matching]] · TDM 少步蒸馏(K2 Turbo 的来源)
- [[grpo]] · 多奖励 GRPO 式 RL 的底座(四个奖励 + rubric)
- [[rubric-based-evaluation]] · prompt 级 rubric 奖励:把 prompt 拆成可验证项逐条判
- [[mmdit]] / [[diffusion-transformer]] · 主干;[[flow-matching]] 训练目标
- [[progressive-resolution-training]] · 256→512→1024 渐进训练
- [[guidance-distillation]] / [[dmd-distillation]] · 蒸馏家族对照(K2 Turbo 同时做引导+时间步蒸馏)

## 我的批注 / 疑问
- 最值得记的不是某个 trick,而是**整篇的逆向品味**:别人都在"把图变得更讨喜",Krea 在"别把不讨喜的图删掉"。这跟 [[qwen-image-bench]] 是一体两面——一个说"对齐饱和后差异在真实感和创意",一个说"想要多样就别在数据端先把多样性筛没了"。
- **0 AI 数据**这条很硬核也很反潮流。逻辑是合成图"更好学"→ 模型会塌向它 → 给质量封了个顶。这等于说:用模型自己的输出喂模型,是在给后代近亲繁殖。
- STPO 的动机讲得很实在:DPO 只看"赢减输"的差,模型可以**两个都压低、只要差距变大**就降 loss——结果赢的样本概率也掉了,等于"为了拉开差距把好的也练差了"。加辅助损失顶住赢样本的绝对概率,是对症的。
- **RL 不开 CFG** 这点容易被忽略但很关键:rollout(采样生成图)和训练如果一个开 CFG 一个不开,两者分布就错位,RL 信号会脏。代价是推理时再补 CFG。
- 待查:STPO 的辅助损失具体长什么样(报告只说"加了一个");四个奖励之间怎么加权;参数量始终没公开。
- 工程侧有意思的两条:把数仓自己写了个 PostgreSQL 系(krablet,无锁队列每秒数万次竞争 UPSERT);"张量核利用率"是判断训练是否稳的最可靠信号,且 GPU 翻倍带来的不稳定性远超预期(分布式训练的隐性税)。

## 跟 wiki 里其他 paper 的关系
- [[qwen-image-bench]] · 一体两面:它量"创造性",Krea 2 在生产端保住创造性的来源(数据多样)
- [[flux-1]] / [[stable-diffusion-3-5]] / [[qwen-image-2]] / [[ideogram-4]] · 同代文生图;同走 [[mmdit]]+[[flow-matching]],但 Krea 2 的差异化在数据哲学和 PO/RL 后训练
- [[rae-dit]] / [[dit]] · 主干谱系上游
- [[ppo]] / [[grpo]] / [[rlhf]] · RL 后训练的方法族

## 历史定位
- 2023-24 **SD / SDXL / 早期 DiT** · 把文生图做到"能用",卷技术指标
- 2024-25 **FLUX / SD3.5 / Ideogram / Qwen-Image** · MMDiT + flow matching 成主流,画质对齐双双拉满
- 2026 **Krea 2(本篇)** · 在指标饱和后转向"审美多样性 + 可控性",用数据哲学(反过滤、0 合成)+ PO/RL 后训练(STPO + 多奖励 rubric)做差异化;Artificial Analysis 文生图榜前十、独立实验室第二
