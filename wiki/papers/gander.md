---
name: gander
type: paper
source: raw/gander.txt
upstream: https://arxiv.org/abs/2609.08977
ingested: 2026-09-11
authors: Hunyuan Speech Team (Tencent) × 浙大 × 上交 × CUHK × NTU · arXiv 2609.08977v2 (2026-09)
year: 2026
---

# Gander · 会插话的全能助手，闲聊归小脑、长活归大脑

腾讯混元语音团队的 Omni Interaction Agent 技术报告。开源 9B 模型（基座 MiniCPM-o 4.5）+ 代码 + 数据；工业版 Hy-Realtime 另有其模型，论文不含。

## 一句话

**把"毫秒级接话"和"分钟级干活"拆给两个脑子：前小脑是全双工 omni 流式模型（1 秒一个 chunk，把听到/看到/说出全部拍平进同一条自回归 token 流，每个 chunk 先预测 听/说/打断），后大脑是免训练的 Codex/Claude Code，中间的编排 runtime 用 task_start/send/resolve 三个工具把两层缝起来。**

## 它要解决的痛点

- turn-based + VAD 流水线撑不起自然对话：打断、抢话、背景人声、多人在场、"嗯嗯"附和这些行为，靠外挂 VAD 判端点全会误判——交互时机必须是模型内生能力才能随智能一起 scale；
- 单个模型同时要毫秒级响应和长程推理，二者互相打架——闲聊要立刻接话，改代码要几分钟工具循环。

## 核心设计

1. **小脑-大脑协同**：小脑（9B 全双工 omni）管实时听说看和接话时机；大脑（Codex app server，GPT-5.6 驱动，免训练即插即用）管长程任务；小脑经三个结构化工具调用委派——task_start（开任务）/ task_send（追加输入，main 转向主任务 / fork 只读旁问）/ task_resolve（cancel / allow_once / allow_session / deny 四种裁决）。传给大脑的是音频转录文本+相关末帧画面（作者自认是最直白的选法）。
2. **编排 runtime**：lean 模式直通（低延迟高确定性）；coordinator 模式加一个只出声明式控制计划的独立控制面模型（管推理强度/提问策略/权限策略/交付策略，只参与 task_start）。Gateway 五实体：Project / Task / Run / WorkerEvent / Delivery；worker provider 接口声明能力集。工具参数绑定传输层确认的真实用户轮次，防小脑幻觉参数。大脑侧三个 runtime 工具：context_fetch / memory_search / share。
3. **流式 chunk 拍平**：交互切成 1 秒窗，每 chunk = [该秒音视频 token + 1 个控制 token + N 个文本 token]（N 可为 0），串成单条因果序列；控制 token ∈ {listen, speak, interrupt}，在内容之前先出——把"要不要说"和"说什么"解耦。滑窗 128 chunk ≈ 2 分钟。
4. **感知与发声**：SigLIP + any-resolution 切片 + query resampler，16× 压缩（许多 omni 模型是 4×），≤448×448；音频 50 帧/s 经 5× 下采样 → 10 token/s。Talker：backbone 末层隐状态+文本 token → 小 AR 语音 token 解码器（CosyVoice 式单码本语义 token）→ 流式 flow matching 解码器 → 波形；zero-shot 音色来自 system prompt 里的参考音频。
5. **数据 2.7M 四族**：语音交互 37%（InteractionSpeech 260.8K 全双工合成管线：四阶段，竞争性打断的"隐藏续写"只留文本不合成、支持性 backchannel ≤8 汉字/6 英词 + 266中/170英词表 11 意图类）；音视频交互 40.66%（1.1M，响应改写到 8 token/s）；agentic 13.3%（种子驱动轨迹合成 + GUI 轨迹）；鲁棒/负样本 8.5%（无关视频/无指令环境/抗干扰/多人）。

## 关键数字

- Full-Duplex-Bench v3（100 场景）：Take-turn 100%（并列最佳）+ Interrupt 8.0%（全场最佳，GPT-Realtime 13.5%）——两个时机指标必须一起读，一个可以牺牲另一个刷高；任务四指标垫底附近（Pass@1 0.400 vs 最佳 GPT-Realtime 0.600）；**back-brain-only ToolSel 0.934 全场最高**——瓶颈在小脑路由+语音通道，不在执行层。Filler 51.6%：等后台干活时撑场，口径争议而非纯缺陷。
- SpokenQA：全双工组内第一（Llama Q 75.60 / Web Q 59.30），九个系统全场第二；2052 条里大脑 0 次被调——路由有选择性。
- Omni：Daily-Omni 78.53（基座 80.20，−1.67）、WorldSense 49.62（−6.08）——练什么保什么；模态消融 fusion gain = AV−max(V,A) = +5.01 / +19.13。

## 关键概念 → 概念页链接

- [[cerebellum-brain-collaboration]] — 双层 agent 架构本体
- [[streaming-chunk-flattening]] — 1 秒 chunk 拍平 + 控制 token 前置
- [[backchannel-vs-barge-in]] — 附和与抢话的判据（数据构造角度）
- [[thinker-talker]] — 小脑内部的想/说分工
- [[full-duplex-multimodal-interaction]] — 全双工路线全景
- [[full-duplex-bench-metrics]] — Take-turn/Interrupt/Filler 怎么读
- [[vad]] — 被它替代的外挂端点检测

## 我的批注 / 疑问

- 最有信息量的一行是 back-brain-only：同一个 agent 同一套工具，去掉小脑和语音通道后 ToolSel 从 0.759 涨到 0.934、超过 GPT-Realtime——证明"什么时候委派"和"ASR 转录损耗"才是短板，架构本身不背锅。
- 大脑免训练是双刃剑：推理能力白嫖上游升级，但脑↔小脑只靠 ASR 文本+末帧沟通（作者自己列为 future work）。
- 训练超参、Talker 规模、chunk 特殊 token 具体格式均未公开；OPD/RL 后训练明说没做。
- WorldSense −6.08 的解读诚实：视觉塔冻结没动，跌的是"静态属性盘问"这种语料从不奖励的行为——"练什么保什么"。
