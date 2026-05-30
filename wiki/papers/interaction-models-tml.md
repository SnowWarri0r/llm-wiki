---
name: interaction-models-tml
type: paper
source: raw/interaction-models-zh.html
upstream: https://thinkingmachines.ai/blog/interaction-models/
ingested: 2026-05-20
---

# Interaction Models · Thinking Machines Lab

伴随 **TML-Interaction-Small** 模型发布的研究预览（276B MoE / 12B 激活）。中文讲解版同时是这次 ingest 的源文件。

## 一句话
当前 chat 模型是"轮次制"（你说一段我说一段）；TML 主张把交互能力做进模型本体，做成 **200ms 微回合 + 时间对齐**的并发流。

## 它要解决的痛点
- 整个行业押在"自主性"（agent 跑多久、调多少工具），人参与协作的那一面被牺牲
- 现在的 chat 接口装不下"人"：生成时模型对外部失聪，用户输入时模型干等
- 用户被迫退化成"丢 prompt 让 agent 自己跑"，因为接口架构卡死了真正的协作

## 核心贡献
1. **诊断**：协作需要 共在 / 共时 / 同时 三件事 —— 轮次制全卡死
2. **架构**：[[dual-model-architecture]] —— 前台 always-on 低延迟 interaction model + 后台异步深推理 background model，共享 context
3. **核心 trick**：[[micro-turn]] —— 把时间切成 200ms 一个 chunk，输入输出在同一个 transformer 里看到**单一交错 token 流**
4. **端到端融合**：[[early-fusion]] —— 没有 Whisper 那种独立大编码器，[[dmel]] / [[hmlp]] / 文本 tokenize 后早早进同一个 transformer，[[flow-matching]] 头做音频输出
5. **训推一致**：[[bitwise-determinism]] —— 训练和推理用同一套 [[batch-invariant-kernel]]，<5% 性能代价
6. **新基准**：TimeSpeak / CueSpeak / RepCount-A / Charades —— 在"实时主动交互"维度上比 GPT Realtime-2.0 minimal 档高一个数量级

## 关键概念
- [[micro-turn]] · 200ms 切片单一交错 token 流
- [[dual-model-architecture]] · 前台 + 后台双模型
- [[early-fusion]] · 各模态早早进同一个 transformer
- [[flow-matching]] · 连续值音频生成范式
- [[dmel]] · 离散 Mel 频谱
- [[hmlp]] · 分层 MLP 视频 patch 编码器
- [[bitwise-determinism]] · 训练 = 推理 bit-for-bit
- [[batch-invariant-kernel]] · 让结果只依赖样本本身
- [[kv-cache]] · 流式会话的 GPU 内存账本
- [[prefill-decode]] · LLM 推理两阶段
- [[split-kv]] · attention 并行算法
- [[grouped-gemm-vs-gemv]] · MoE 推理的 batch 取舍
- [[nvls]] · NVLink 网内归约
- [[moe]] · 276B / 12B 激活的稀疏激活

## 我的批注
- benchmark 部分要警觉：GPT 是 `minimal` 档，没对 Gemini Live / Sesame；新基准是自造的天然往强项靠。**但**他们能造出竞品几乎拿零分的题，说明这个维度确实没人在做 —— 开辟新评估子域 ≠ 刷榜
- "把外挂规则吃进权重"是反复出现的范式：Whisper → 端到端语音 LLM；OCR → VLM；VAD → micro-turn；fish-speech 把 phonemizer 也吃了。详见 [[replace-heuristics-with-weights]]
- 双模型分工跟我熟的"前台 socket + 后台 worker"异步架构是同一形状，只是边界画在权重里而不是服务边界 —— 这条值得做成长 thread

## 开放问题
- 200ms 是听觉感知阈值 + GPU prefill 开销的妥协点。换成 100ms / 400ms 手感差异有量化数据吗？
- flow matching 推理需要 ODE 求解多步，怎么在 200ms 预算内做到？步数？
- 见 [[open-questions]]
