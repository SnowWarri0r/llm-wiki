---
name: krea-2
type: paper
source: https://www.krea.ai/blog/krea-2-technical-report
upstream: https://www.krea.ai/blog/krea-2-technical-report
ingested: 2026-06-25
authors: Krea AI · 2026
year: 2026
---

# Krea 2 · 先保住视觉世界，再教模型怎么走

Krea 2 是 Krea AI 发布的 12B 文生图 DiT。它最值得学的不是某个孤立的注意力改造，而是一条贯穿数据、训练和产品接口的主线：**预训练先保住尽可能宽的视觉分布，后训练再教模型沿着用户意图在这个分布里移动。**

## 一句话

Krea 2 把“更好看”拆成三个不同问题：预训练负责铺地图（广覆盖、不过度按美学筛选、预训练不使用 AI 生成图），SFT / PO / RL 负责装方向盘（审美、提示遵循、文字和结构），prompt expander 与 style reference 负责让用户说得清方向，TDM 最后把长去噪路线压成 Turbo 的 8 步推理。

## 先纠正四个容易读错的点

1. **“0 AI 图”只限定预训练图像混合。** 报告随后明确使用合成偏好对、合成用户 caption 和合成 thinking trace；这不矛盾，因为它们属于后训练或 prompt-expander 训练。
2. **Krea 不是完全不用美学过滤。** 高分辨率阶段仍会用画质与美学分删掉极差样本，只是不按分数过采样“更美”的图。
3. **STPO 的完整公式没有公开。** 报告只披露它修改了 DPO 目标并加入辅助损失；可以准确解释 DPO 为什么会让 winner / loser 的似然一起下降，但不能把某个猜测的正则项写成 STPO 原式。
4. **两个 VAE 不是串起来用。** 早期放大实验采用 Qwen Image VAE，较大的模型后来采用 FLUX 2 VAE；报告的汇总表把二者都列为最终实践，不代表一次前向要过两个 VAE。

## 核心主线：铺地图 → 装方向盘 → 压路线

- **铺地图：数据与预训练。** 不用单一审美打分器裁掉分布尾部；OCR + 元数据 + captioner 生成信息密集的长配文；256→512→1024 渐进训练。
- **补地图：中训。** 层级 k-means 保住长尾视觉概念，SigLIP 语义去重，用 Wikipedia PageRank 和全文检索检查约 500 万个可表示实体的覆盖。
- **装方向盘：SFT / PO / RL。** SFT 用小而精的审美数据定调；PO 用合成偏好对初调、纯人工偏好校准；RL 用美学、提示遵循、文字渲染、瑕疵结构四类奖励继续优化。
- **翻译用户意图。** Prompt expander 把短而模糊的用户输入变成长 caption；style-reference 模块让参考图提供风格而尽量不泄漏主体内容。
- **压缩路线。** TDM 不只匹配最终干净图的分布，还在多个时间步做分布匹配；发布 Raw 基座与 8 步 Turbo。

## 架构：12B 单流 DiT，设计重点是稳定、效率、简单

- 单流 Transformer：文字 token 与图像 token 共用注意力和 MLP 权重；混合流略好，但最终为简单性选单流。
- GQA 降低计算与通信成本，gated sigmoid attention 主要改善训练稳定性。
- SwiGLU 4×；zero-centered RMSNorm + QKNorm；3D axial RoPE。
- 时间步调制从每块一套 MLP 简化成轻量 bias。传统调制 MLP 可占总参数 20–30%，这里把容量还给主干。
- Qwen3-VL 作为单一文本编码器；跨层聚合让模型自己挑粗粒度到细粒度文字特征，并加轻量双向层削弱自回归表征偏置。
- DC-AE 压缩率高但重建误差给细节设上限；早期采用 Qwen Image VAE，较大模型后采用 FLUX 2 VAE。

## Rectified flow 到底在学什么

报告说 Krea 2 用标准 rectified-flow loss 和 `v` 参数化。按常见约定：

\[
x_t=(1-t)x_0+t\varepsilon,\qquad v^*=\varepsilon-x_0,
\]

\[
\mathcal L_{\mathrm{RF}}=\mathbb E_{x_0,\varepsilon,t}\left[\lVert v_\theta(x_t,t,c)-v^*\rVert_2^2\right].
\]

`x₀` 是真实图像 latent，`ε` 是噪声，`t∈[0,1]` 是当前位置，`xₜ` 是两者之间的点，`c` 是文字条件，`v*` 是从图指向噪声的恒定速度，`vθ` 是模型预测。训练不是让模型一次画完，而是让它在任意中间位置都知道该往哪里走；推理时从噪声反向积分回图像。

标量例：`x₀=2, ε=-1, t=.25`，则 `xₜ=.75×2+.25×(-1)=1.25`，目标速度 `v*=-3`。若模型预测 `-2.6`，这一样本损失是 `(-2.6+3)²=.16`。梯度会把预测往 `-3` 拉近。

## 训练流水线

1. **预训练**：256→512→1024；第一轮 256px 用 iREPA，256/512 用 8-bit 训练获得 15–20% 加速，1024 起回 bf16。
2. **中训**：在 SFT 前补高分辨率、领域覆盖和文字渲染等能力；报告认为这是最后一个适合增加基础能力的阶段。
3. **SFT**：用少量人工精选的高审美图修正早期 checkpoint 的高饱和与纹理问题；领域模型合并成通用模型。
4. **PO**：先用大规模合成偏好对初调，再用熟悉模型特性的内部人工偏好校准；多数偏好对至少含一个 on-policy 样本。
5. **RL**：多奖励 GRPO-style 方法；最终美学奖励采用高效的 pointwise Bradley–Terry reward model。
6. **可选蒸馏**：同时做 guidance distillation 与 timestep distillation，得到少步 Turbo。

## DPO 为什么会“两个都降”

标准 DPO 只关心策略相对参考模型时，winner 与 loser 的**差距**是否变大：

\[
\mathcal L_{\mathrm{DPO}}=-\log\sigma\!\left(\beta[(\log p_\theta(y_w|c)-\log p_\theta(y_l|c))-(\log p_{\rm ref}(y_w|c)-\log p_{\rm ref}(y_l|c))]\right).
\]

`c` 是 prompt，`y_w/y_l` 是偏好图与落选图，`pθ` 是正在训练的模型，`p_ref` 是冻结参考模型，`β` 控制偏好信号强度。若参考差距为 0，一次“好更新”可让 log-likelihood 从 `(-2,-2)` 变为 `(-1.5,-3)`，差距为 1.5；另一次“偷懒更新”变成 `(-2.5,-4.5)`，虽然 winner 也降了，差距却达到 2。DPO 会更喜欢后者。Krea 观察到这种漂移会在后续阶段表现成高频伪影，于是提出 STPO。**但报告没有给 STPO 全式，因此只能确认其目标是减少这种 divergence，不能确认辅助项具体怎样约束 winner。**

## 多奖励 RL：奖励决定方向，prompt 池决定算力花在哪

- 四个裁判：通用美学、提示遵循、文字渲染、瑕疵与结构。
- 美学 reward model 比过 pointwise Bradley–Terry 与 pairwise VLM judge，最终采用前者；它高效、无候选位置偏差，适合大量 rollout 打分。
- Prompt-specific rubric 把“红衣女孩、两只猫、雨夜”等要求拆开逐项核验，避免一个笼统总分掩盖局部失败。
- Prompt 池优先选择“难但并非无解”且组内分数有方差的样本；太容易、总失败、或同组全一样都没有多少学习信号。
- RL 的 rollout 和训练都不开 CFG，避免分布错位并节省计算；推理时 CFG 仍可作为控制旋钮。

用四张图的总奖励 `R=[.35,.55,.75,.35]` 举例，均值 `.50`，总体标准差约 `.166`，组内标准化 advantage 约为 `[-.90,.30,1.51,-.90]`。第三张得到最强正向更新，第一和第四张被压低。这里的数字只是说明 GRPO-style 的组内相对信号；Krea 没公开四类奖励的权重与完整策略损失。

## Prompt Expansion 与 Style Reference

Prompt expander 解决的是“训练时看长 caption，用户却只写短句”的条件分布错位。SFT 数据由长 caption 反向生成短、口语、故意省细节的用户输入，并配合合成 thinking trace；RL 再直接通过最终出图优化。其最大风险是学成一种安全的 house style，所以 Krea 用 DINOv3 嵌入衡量同组图像多样性，而且实验发现该奖励一旦衰减得太小，模型很快又会塌缩。

Style Reference 解决文字难以说明的视觉意图：支持多参考图、权重混合与连续强度。核心难题是“风格”和“内容”没有天然边界，参考图里的主体很容易泄漏到结果中。报告只披露采用新的自监督训练再接偏好优化，**没有公开自监督任务、模块结构和损失公式**。

## TDM 与两套权重

普通 DMD 让少步学生生成干净图，再加噪并匹配干净图分布；TDM 把这种分布匹配铺到多个时间步，约束整条去噪轨迹，而不只约束终点。Krea 选择它是因为无数据、超参数少、容易调，并支持灵活的多步蒸馏。

- **Krea 2 Raw**：12B、未蒸馏、适合 LoRA / 微调 / 后训练；官方示例用 52 步、CFG 3.5、约 1K。
- **Krea 2 Turbo**：蒸馏 checkpoint；官方推荐 8 步、CFG 0、`mu=1.15`，支持约 1K–2K。LoRA 先在 Raw 上训练，再挂到 Turbo 推理。
- 权重使用 Krea 2 Community License；推理代码仓库是 Apache-2.0。两者不要混成“模型是 Apache-2.0”。

## 报告没有告诉我们的事

- STPO 全称、完整公式、辅助损失和消融数据。
- 四个 RL 奖励的权重、GRPO-style 的完整目标与训练超参数。
- Style Reference 的具体结构、自监督配对方式与损失。
- 数据规模的精确组成、训练 FLOPs、GPU 总量与主结果的完整可复现实验表。
- “审美多样性更宽”的定量指标和系统对照。报告给了产品论点与大量工程经验，但不是一份完整公开实验的学术论文。

## Future Work：下一代要解决的四笔债

1. **继续扩规模。** 引入 MoE、稀疏注意力下的原生 2K–4K、NVFP4 预训练和 Muon；团队也直接承认当前模型仍然 undertrained，更长训练可能继续带来收益。
2. **MOPD。** 不同团队先训领域专家，再用 multi-teacher on-policy dense supervision 把它们蒸进同一个学生，避免某个领域进步导致另一个领域回退。报告称已用内部专家验证 OPD / MOPD 有效，但没有公开方法细节和结果。
3. **架构统一。** 当前生产链由 VAE、DiT、文本编码器、prompt expander，以及可选的 style reference / upscaler 拼成；未来想合成一个统一模型，把研究资源集中在同一主干上。
4. **原生理解多种输入协议。** 用户会写自然语言、tags、JSON、bounding box、指令、视觉规范和 Markdown。Prompt expansion 只能缓解一部分，底座最终应直接理解这些格式；能力方向还包括稳健编辑、图像参考和原生 2K/4K。

## 我的判断

Krea 2 最有价值的地方，是把“多样性”当成需要从数据源头一直保护到产品接口的系统属性：预训练不过早压缩分布，后训练却又不可避免地加入审美偏置，因此 prompt expander 的多样性奖励、STPO 的防漂移和 style reference 的内容隔离，实际上都在偿还“对齐会收窄分布”这笔债。

它的不足也很明确：最关键的 STPO、style reference 和奖励组合都没有给出足够细节，架构与数据部分披露得远比核心后训练机制完整。所以阅读时最好把它当成**一份很有诚意的系统报告与研究路线图**，而不是已经能够逐项复现的论文。

## 相关概念

[[generative-data-curation]] · [[siglip-semantic-dedup]] · [[hierarchical-kmeans-curation]] · [[pagerank-entity-coverage]] · [[progressive-resolution-training]] · [[flow-matching]] · [[mmdit]] · [[direct-preference-optimization]] · [[grpo]] · [[rubric-based-evaluation]] · [[prompt-expansion]] · [[dinov3-diversity-reward]] · [[style-reference]] · [[trajectory-distribution-matching]] · [[guidance-distillation]]

## 官方来源

- 技术报告：https://www.krea.ai/blog/krea-2-technical-report
- 模型权重与 model card：https://huggingface.co/krea/Krea-2-Raw
- 官方推理代码与 Raw / Turbo 参数：https://github.com/krea-ai/krea-2
