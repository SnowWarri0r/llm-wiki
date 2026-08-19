---
name: avatar-forever
type: paper
source: https://arxiv.org/abs/2608.12107
upstream: https://github.com/leeruibin/avatarforever
ingested: 2026-08-19
authors: Ruibin Li · Tao Yang · Zhiyuan Ma · Fangzhou Ai · Shilei Wen · Lei Zhang
year: 2026
---

# Avatar-Forever · 把“跑得快”和“跑得久”拆开学

## 一句话

从同一个 22B LTX-2.3 基座并行训练两条支路：DMD 全参数蒸馏负责把生成压到 4 步，RRT LoRA 负责在错误已经滚过 4 个 chunk 后学会恢复；部署时合并两份更新，再用 ForeverCache 避免每个去噪步重算固定历史。

## 先看完整拼图

1. **效率支路**：(	heta_0\to\Delta\theta_{\mathrm{DMD}})，只学 4-step 短片质量，不做 autoregressive rollout。
2. **稳健支路**：(	heta_0\to\Delta\theta_{\mathrm{RRT}})，只训练 rank-128 video LoRA 和首帧 gated condition；故意退化最早历史，stop-gradient 自滚 (K=4) 块，监督下一块恢复。
3. **部署合并**：(	heta^\star=\theta_0+\Delta\theta_{\mathrm{DMD}}+\Delta\theta_{\mathrm{RRT}})。
4. **流式推理**：历史窗只留首块与最近块；每个新 chunk 第一个 denoising step 建每层缓存，剩余 3 步只计算当前 token。

## RRT 不是“给坏图做一次修复”

局部 corrupted-history training 在退化后立即监督，只见到人工造出的单步损坏。RRT 先让这点损坏经过模型自己的四次自回归反馈，形成部署时真正会遇到的色漂、身份漂移和运动错误，最后才用普通 flow-matching loss监督第 5 块。中间 rollout 不直接监督，也不反传；它只负责制造训练题目。

公式按执行顺序是：

1. (hat{\mathbf c}_0=\mathcal D(\mathbf c_0))：只污染最早历史；
2. (hat{\mathbf c}_{k,t}=\operatorname{sg}(G_\theta(\hat{\mathbf c}_{k,t+1};\hat{\mathbf c}_{k-1,0},\mathbf r,\mathbf a_k,y)))：滚出四块坏历史；
3. (mathbf c_{K+1,\sigma}=(1-\sigma)\mathbf c_{K+1}+\sigma\epsilon)：只给真实目标块加噪；
4. (v_\theta) 回归 (epsilon-\mathbf c_{K+1})：在坏历史条件下学会把目标块拉回数据方向。

## ForeverCache 到底缓存什么

对当前 chunk (k)，可见历史 (mathcal H_k={\mathbf c_0,\mathbf c_{k-1}})：第一块提供稳定身份锚点，最近一块提供连续动作。普通实现的 4 个去噪步每次都重算 ([mathcal H_k,\mathbf c_{k,t}])。ForeverCache 只在最初噪声步计算完整窗口并保存每个 Transformer block 的历史特征，后面只推当前 token。换下一个 chunk 时缓存清空重建，因此“无限生成”不是无限显存。

## 数据不是抓来的真人长视频

作者从公开 MDD 对话语料取文本，用 GPT 筛掉不连贯或缺少视觉信息的对话，再改写成包含人物、场景、机位、表情、身体动作和台词的 LTX prompt。LTX 多步模型合成长视频；ImageBind、CLAP、统一奖励模型查语义，Gemini 查视觉退化，相邻帧分析再剔除静止视频和只靠镜头平移/缩放制造“运动”的样本。论文没有披露最终数据量。

## 训练配方

- 基座：22B LTX-2.3；上下文 4 latent 帧，目标 4 latent 帧；
- DMD：全参数、4-step、5000 steps；混合 T2V / 首帧条件 I2V；
- RRT：video-side LoRA rank=alpha=128，(K=4)，rollout 仍用 30-step、无 CFG，训练 3000 steps；
- 退化概率 0.5：噪声、模糊、饱和度和 latent masking；
- 两支路均 AdamW、学习率 (10^{-5})、global batch 256。

## 关键实验

- 768×512、单 H100、DiT+VAE 端到端 27.2 FPS；
- EMTD 5 秒：ForeverCache 5.24→4.24s，吞吐 +23.6%；30 秒：38.85→26.71s，吞吐 +45.5%；
- 消融：DMD-only 的 LLM Overall 3.962，DMD+RRT 4.105；FVD 1080.23→901.81；FM-only 只有 2.308，说明抗漂移不能代替少步画质基座；
- (K=0) 只会局部修复，(K=4) 长片最稳；
- 20 人双盲 EMTD 长片评分：完整模型 76.00，缓存版 74.83，最强基线 SoulX-FlashTalk 60.23；
- 展示了一段连续 11 分钟结果，但标准量化集只测 5 秒和 30 秒。

## 边界

- 仓库仍是 research preview：推理代码、模型和交互 demo 均未发布；
- “effectively unbounded”来自有界历史窗与逐块推进，不表示实验证明任意长；
- 只报告单 H100，且论文明确尚未优化到消费级硬件；
- DMD real/fake score 网络的训练细节沿用 DMD 文献，本文没有完整展开；
- 合并公式没有报告缩放系数消融，也没有分析两份更新的参数冲突。

## 关键概念

- [[recovery-oriented-rollout-training]] — 为什么等错误滚起来后才监督
- [[forever-cache]] — 四步去噪如何只算一次历史
- [[decoupled-parallel-adaptation]] — 两份能力怎样从同一基座合并
- [[dmd-distillation]] · [[score-function]] — 效率支路的前置知识
- [[flow-matching]] · [[stop-gradient]] — RRT 最后一步与无梯度 rollout
- [[lora]] · [[kv-cache]] — 参数增量与缓存机制

## 我的批注

- 最强的实验不是 27.2 FPS，而是 DMD-only / FM-only / DMD+RRT 三角消融：跑得快和跑得久确实不是同一门课。
- RRT 的洞察很实用：人工退化只负责推第一下，真正的错误形状交给模型自己滚出来。
- ForeverCache 与普通 LLM KV cache 不完全相同；它按 chunk 重建、只跨同一 chunk 的 denoising steps 复用。
- 论文标题写 infinite，证据最远是 11 分钟定性演示；这是“机制允许继续”，不是数学上的无限稳定保证。
