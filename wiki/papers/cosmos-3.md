---
name: cosmos-3
type: paper
source: https://research.nvidia.com/labs/cosmos-lab/cosmos3/technical-report.pdf
upstream: https://github.com/nvidia/cosmos
ingested: 2026-06-24
authors: NVIDIA · Cosmos 3 Technical Report 2026
year: 2026
---

# Cosmos 3 · 一个模型同时理解世界、生成世界、在世界里动手

NVIDIA 2026-06 的 Physical AI 旗舰（GTC Taipei 发布）。它把以前要拼好几个模型才能干的事——看懂画面（VLM）、生成视频（视频模型）、模拟世界（world model）、产出动作（VLA/世界-动作模型）——用一个 [[mixture-of-transformers]] 架构**全收进一个模型**，统一处理和生成语言/图像/视频/音频/动作五种模态。是 [[world-foundation-model]] 这条线（给 [[physical-ai]] 当"训练场"）目前的集大成。

## 一句话
**用 MoT 把"自回归推理塔"和"扩散生成塔"装进同一个 transformer——一个模型一口气把理解、生成、动作五模态全干了，不用再拼一串专用模型。**

## 它要解决的痛点
- **以前得拼一串模型**：让家用机器人收拾餐桌，要 VLM 找碗+规划、VLA/WAM 出动作、world model 模拟评估未来——四个割裂模型缝在一起，既笨重又难一致。
- **理解和生成被人为切开**：但这俩本就耦合——"理解"得能推演世界接下来怎么变、动作有什么后果（这是生成）；"生成"得有对世界和行为的紧凑结构化表示（这是理解）。分开训是次优解。
- **AR 和扩散各有所长，硬要二选一**：自回归（AR）擅长语言/推理，扩散擅长高保真生成。以前要么纯 AR、要么纯扩散。Cosmos 3 用 MoT 把两者**塞进同一条序列、同一个模型**。

## 核心贡献
1. **MoT 双塔架构**：[[mixture-of-transformers]] —— 每个 decoder 层带**两套参数**：reasoner 塔处理 AR 子序列（理解/推理，因果注意力，像 VLM），generator 塔处理扩散子序列（生成，双向注意力）。两塔都从预训练 [[qwen3-vl]] 初始化，继承语言+视觉能力再学生成。
2. **dual-stream 联合注意力**：AR token 只**因果**看 AR（保住文本生成能力）；扩散 token 用**全双向**注意力看 [AR; 扩散] 全部（能看到文字 prompt + 所有条件/生成 token）；AR 永不被扩散 token 更新。这是 [[unified-transformer]] 的"混合注意力"再加一层"两塔分权重"。
3. **一个模型多种 I/O 模式**：靠 token 排列切换——纯语言（=VLM）、文生图、文生视频(+音频)、图生视频/视频生视频、视频 transfer（边缘/深度图→RGB）、动作（前向动力学/逆动力学/策略）。一套权重**subsume** 了 VLM + 视频生成 + 世界模拟 + 世界-动作模型。
4. **动作是一等模态**：专设一类 action token，跟图/视频/音频一样先过模态专用 encoder 进统一空间，推理时**靠迭代去噪生成**(只有语言走自回归)；前向动力学/逆动力学/策略只是 token 摆法不同。这是它能当世界模拟器又当机器人策略的根。
5. **三档规模 + SOTA**：Edge 4B(底座 dense 2B，Qwen3-1.7B 式)/ Nano 16B(底座 8B)/ Super 64B(底座 32B)，总参≈2×稠密底座(两塔)，每 token 只过一塔、激活≈单塔。Nano/Super 本次发布、Edge 稍后。后训练版被 Artificial Analysis 评为**最强开源文生图 + 图生视频**、被 RoboArena 评为**最强策略模型**。

## 关键概念
- [[mixture-of-transformers]] · 本文发动机：模态/任务各一套 transformer 权重（塔）+ 联合注意力
- [[world-foundation-model]] · 世界模型范式：学世界怎么演化，给 Physical AI 当训练场/模拟器
- [[physical-ai]] · 目标场景：具身智能体在真实世界感知-推理-行动，理解与生成天生耦合
- [[unified-transformer]] · 最近的亲戚：一条序列混合注意力同时干理解+生成；MoT 在它上面把权重拆成两塔
- [[moe]] · 对照：MoE 是 FFN 级"专家"按 token 路由、共享注意力；MoT 是整条 transformer 通路按模态/任务分、联合注意力
- [[diffusion-transformer]] · generator 塔干的就是这件事（latent token 上去噪）
- [[qwen3-vl]] · 两塔的初始化权重来自它

## 我的批注
- 最关键的一刀：**MoT ≠ MoE**。MoE 省的是算力（多 FFN 专家、每 token 只激活几个、共享注意力）；MoT 解的是**多模态/多任务冲突**（理解要因果、生成要双向，两种工作模式硬塞一套权重会打架，所以干脆给每种工作模式一套完整权重，但共用一次注意力让它们对齐）。一个为效率，一个为统一。别混。
- "总参 64B = 稠密 32B ×2" 这点很实在：两塔各约等于一个完整 VLM，所以总参翻倍，但每个 token 只过它该过的那一塔，激活量≈单塔。
- 把动作当成一种可生成的模态(forward/inverse dynamics + policy)，跟视频/音频平起平坐——这是它能当"世界-动作模型"的根。跟 [[lumine]] 把"动作即 token"是同一个母题，但 Lumine 是纯 AR，Cosmos 3 把生成交给扩散塔。
- 动作 tokenizer 已确认:专门一类 action token、过模态专用 encoder、推理时迭代去噪生成(非自回归)；前向/逆动力学/策略=token 摆法不同。
- 待解的疑问：两塔联合注意力的显存/延迟代价多大(报告未给单流 baseline 对比数);Edge 4B 在端侧机器人上实测延迟;各任务的具体 benchmark 分数(榜单排名有、绝对分散在各 section)。

## 跟 wiki 里其他 paper 的关系
- [[lumine]] · 同是 Physical AI / 具身：Lumine 纯 AR 从像素出键鼠零样本玩游戏；Cosmos 3 用 MoT 把生成+动作+理解统一
- [[qwen3-vl]] · Cosmos 3 的两塔骨架直接 adapt 它
- [[stable-diffusion-3-5]] / [[flux-1]] · generator 塔是 DiT + 扩散一族；Cosmos 3 把它和 AR 推理缝进同一模型
- [[rae-dit]] · 都在"扩散主干 + 高维语义"上做文章，方向不同

## 历史定位
- 2025 **Cosmos（1/2）** · World Foundation Models 分立：Predict（生成）/ Transfer（受控生成）/ Reason（理解）/ Policy（动作）各一个模型
- 2026-06 **Cosmos 3（本篇）** · MoT 把上面四件事合一：omnimodal、单模型、单次前向同时理解+生成+行动
- 趋势 · 朝"一个具身基础模型通吃感知-推理-生成-行动"走，世界模型当通用 backbone
