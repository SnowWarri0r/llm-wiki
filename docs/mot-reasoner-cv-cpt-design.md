# 对 MoT reasoner 做 CV 理解 CPT 能否增强泛化、并让 generator 训练更好

> 研究设计草案（2026-07-23）。产出=机理分析 + 可执行消融方案，供决策是否投入真实训练。未跑训练。

## 0. 一句话问题

在 **Mixture-of-Transformers（MoT，模态解耦、共享全局注意力）** 里，先用**传统 CV 图像理解任务**对 reasoner（文本/理解模态 path）做 CPT，(1) 能否提升 reasoner 的泛化，(2) 从这个 checkpoint 起点再训 generator（图像生成模态 path），生成效果是否更好。

## 1. 把问题拆成两个**可分离**子假设

- **H1（理解侧）**：CV 理解 CPT → reasoner 在**held-out + OOD 理解任务**上更强。
- **H2（迁移到生成侧）**：从 CV-CPT 过的 checkpoint 起训 generator，比从 base 起训的 generator 在**指令遵循/组合泛化**上更好，**且不损失低层保真**。

**H1 成立不蕴含 H2 成立**：理解增益可能不迁移到生成，甚至反噬保真。必须分别测。这是本研究的核心——不要用 H1 的结论替 H2 背书。

## 2. MoT 机理：为什么可能成立 / 可能反噬

MoT 关键性质：**非嵌入参数按模态解耦**（FFN、注意力投影、LN 各模态一套 experts），但**全局自注意力跨模态共享**；若沿用 Chameleon/Emu3 式的**图像 VQ token 共享词表**，则图像 experts 在"理解（图→文，图像作输入编码）"和"生成（文→图，图像作输出预测）"之间**是共享的**。

**支持迁移（H2 可能成立）**：
- 生成质量的瓶颈恰恰是**组合/语义 grounding**——我们判官研究实测的生成弱点全在这：计数、空间关系、主体身份、属性绑定、文字/OCR、删除残留。CV 理解任务正是逼模型学"画面里有什么对象/属性/关系/数量/在哪"。
- 若共享注意力 + 图像 experts 的视觉表征被理解 CPT 拉得更判别、更语义 grounded，generator 继承这份表征 → 组合指令遵循更强、OOD 更稳。
- 文献同向：MetaMorph（理解与生成联合互相促进）、Emu3/Chameleon（联合建模）、"加理解数据改善生成"的经验；表征学习视角=更好的视觉 world-model 同时利于"读"和"写"。study wiki 可引：clip/dino（判别式视觉表征）、rae-dit（表征对齐 DiT）、hierarchical-denoising-visual-reasoning、hid_ream-o1（推理增强生成）。

**反噬风险（H2 可能失败/为负）**：
- **理解 vs 生成的表征张力**：理解要**语义/抽象**特征，生成要**低层/可重建细节**特征。**Janus/Janus-Pro 正是为此把理解与生成的视觉编码器解耦**。MoT 图像 experts 共享时，CV 理解 CPT 可能把图像 experts 偏向语义-判别特征，**牺牲生成需要的重建/细节** → 指令遵循涨但保真跌。
- **表征漂移/灾难遗忘**：CPT 过重会漂移 base 能力。
- **净效应先验**：指令遵循/组合泛化上**净正的概率较大**，低层保真上**不确定、有为负可能**。值得做消融；结果强依赖于 (a) 共享范围（仅注意力 vs +图像 experts vs +文本 experts）、(b) CPT 任务配比与规模、(c) full-CPT vs LoRA vs 冻结图像 experts。

## 3. 关键设计洞察：用**生成弱点**反向选 CV 理解任务

不要泛泛上一堆 CV 任务。用我们 v6c 判官研究实测出的 generator 弱点清单来**定向**选理解任务，这样能**直接检验"理解某能力 → 生成该能力变强"的因果迁移**，而不是笼统 CPT：

| generator 已知弱点（判官研究实证） | 对应 CV 理解 CPT 任务 | 对应生成侧评测轴 |
|---|---|---|
| 数量不符 | 计数 VQA（CountBench/TallyQA/FSC-147） | GenEval-counting |
| 空间/左右/方位错 | 空间 VQA、referring grounding（RefCOCO/g） | T2I-CompBench spatial |
| 主体身份/属性不一致 | 属性 VQA、细粒度分类、attribute binding | T2I-CompBench attribute/color |
| 文字多字/错字 | OCR（TextVQA/ST-VQA） | 文字渲染 eval |
| 删除残留/误删 | 指代分割/检测（referring segmentation） | 编辑类 keep 判官 |
| 局部畸形（这类是模型感知天花板） | —（判官研究已证 Kimi 看不出，未必靠 CPT 修） | anatomy 硬检 |

**这张表本身就是实验假设矩阵**：定向 CPT 单一能力，看对应生成轴是否移动。若"计数 CPT → GenEval-counting 涨"，机理为真，可放大；若不动，说明该模态解耦下不迁移。

## 4. 实验 / 消融设计

**变量与臂**：
- **A0 baseline**：base MoT → 训 generator（我们的 i2i keep 集 290万 + video）。
- **A1**：base MoT → CV 理解 CPT（reasoner path）→ 训 generator。
- **CPT 范围消融**：(a) 仅共享注意力 (b) 注意力+图像 experts (c) +文本 experts。
- **CPT 任务配比消融**：定向单能力（计数/grounding/OCR…）vs 混合大盘。
- **CPT 方法消融**：full vs LoRA vs 冻结图像 experts（正面回应 Janus 的解耦教训）。
- **CPT 规模**：token 量 scaling。

**必须的控制臂（否则结论不可信）**：
- **compute-matched baseline**：A0' = 把 A1 花在 CPT 上的算力**改花在更多 generation 训练**上。用来隔离"CV 理解本身"vs"只是多算力/多数据"。**没有这个臂，H2 的任何正结果都可能只是算力效应。**
- **数据泄漏控制**：CPT 图像集与生成评测 prompt/图像不重叠。

**指标**：
- **H1（reasoner 泛化）**：通用 MMBench/MME/SEED + 定向（CountBench、RefCOCO/g、spatial-VQA、TextVQA），**分 in-domain / OOD 两档**。
- **H2（generator）**：GenEval / DPG-Bench / T2I-CompBench（**分轴**：counting/spatial/attribute/color）+ 我们的 v6c 判官（MOS + keep 率，分任务类型）+ OOD prompt 人评。**关键=按第 3 节的轴对应看**（定向 CPT 的轴是否专门涨）。
- **保真控制（抓反噬）**：FID/画质 + 判官的崩坏/anatomy 检查。**CV-CPT 若让保真跌，即使指令遵循涨也要标红**（Janus 风险）。

**决策规则**：H2 判胜 = 在**compute-matched**下，generator-from-CPT 在组合/OOD 生成轴上**显著优于** A0'，**且**保真不回归。否则判"理解 CPT 对生成无净增益"或"需解耦"。

## 5. 最小起步实验（先花小钱 derisk）

选**单一弱点=计数**（最可数、最好评）：
1. 小规模 CV-CPT：只喂计数 VQA（CountBench/TallyQA），小 token 量。
2. 小 generator 训练（子集）。
3. 只看 **GenEval-counting** 这一轴动没动 + FID 没崩。

若定向轴移动 → 机理为真，值得按第 4 节全量消融放大；若不动 → 该 MoT 配置下理解不迁移生成，止损。**这个信号最便宜，先做。**

## 6. 数据来源

- **CV 理解 CPT 数据**：公开集（ImageNet 分类、COCO caption/detect、Visual Genome、RefCOCO/g、TextVQA、CountBench、TallyQA、depth 转文本等），图→文形态。
- **可复用我们已有资产**：v6c 判官对 315万图打的 MOS + 我们能让判官吐的逐条分析（对象/属性/达成核查）本身就是一批"图像→结构化理解"信号；canda 轨迹里 grounded_search/retrieve_skills 的图文对也是弱监督理解语料。
- **generator 训练数据**：i2i keep@≥3 的 290万（或 ≥4 的 239万）+ canda video 60k。

## 7. 风险与失败模式

- 理解 CPT 偏语义 → 生成保真跌（Janus 张力）。缓解：冻结/LoRA 图像 experts、控 CPT 规模、加保真门槛。
- compute 效应冒充 CV 效应 → 必须 compute-matched 控制臂。
- "感知天花板"类弱点（局部畸形）大概率 CPT 修不了（判官研究已证模型看不出）→ 别把它算进预期收益。
- MoT 图像 experts 到底在理解/生成间共享到什么程度，决定迁移强弱——**开工前须先确认这个 checkpoint 的实际共享设计**。

## 8. 待决策（等对齐）

1. 产出范围：本分析 + 消融方案（本文）vs 直接搭训练跑（需 MoT checkpoint/代码 + H20 算力确认）。
2. 是否先跑第 5 节最小计数实验 derisk。
3. MoT checkpoint 的图像 experts 共享设计（共享词表？理解/生成是否同一套图像 experts？）——这决定机理强弱，需你或团队给准。
