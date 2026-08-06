---
name: physics-of-multimodal-pretraining
type: paper
source: https://arxiv.org/pdf/2608.05000v1
upstream: https://junlinhan.github.io/projects/physics_of_mm_pretrain/
ingested: 2026-08-06
authors: Junlin Han, Shengbang Tong, David Fan, Minghao Chen, Philip Torr, Filippos Kokkinos, Mike Lewis · FAIR / Meta / Oxford · arXiv 2026
year: 2026
---

# 多模态预训练的经验规律 · 文字、看图和画图怎样互相帮忙，又怎样争参数

这篇首先是一张统一图文模型的“训练决策表”：给正在从头训练模型的人回答参数该怎样共享、视觉什么时候接入、三类数据怎样分预算；没有这些规律，只能拿昂贵的预训练反复试错。标题里的 Physics 不是要给神经网络套牛顿定律，而是想找几条在控制变量实验中反复出现的“经验规律”。论文把一个统一模型拆成三项训练能力：纯文字 (L)、视觉理解 (U) 和视觉生成 (G)，再逐项追问谁能帮谁、什么情况下联合训练是净赚、什么时候应该开始一起练。

这页不照原论文的章节顺序压缩。先把模型和实验尺子搭好，再沿“知识流 → 协同与竞争 → 训练时机 → 配方 → 证据边界”走一遍。

## 一句话

**语言普遍帮助视觉、看图明显帮助画图，但画图很少零样本反哺前两者；共享 attention 和 norm 负责交流、拆开的 FFN 负责隔离冲突，从早期联合训练，最后按 70/25/5 分配 L/U/G token，是论文在自身实验范围内找到的最好折中。**

## 论文覆盖地图

| 原文 | 本页怎样处理 |
|---|---|
| §1 Introduction | 先解释 Physics、L/U/G 和四条主张 |
| §2 Experimental Setup | 模型总览、四种视觉 token、训练与全部指标 |
| §3.1 Real-world transfer | 三个固定基座 + 增量数据实验，画成方向图 |
| §3.2 CLEVR | 数据生成、概念剔除、baseline/control、零样本与微调恢复 |
| §4.1 Complexity | 七档视觉、三档语言、ΔPPL 与 Δdiffusion loss |
| §4.2 Parameter sharing | dense、只拆 FFN、再拆 attention/norm、全拆 |
| §4.3 Tokenizers | RAE、Raw Pixels、CLIP+VAE、AR UniTok 的复现 |
| §5.1 Timing | 1T 时间 sweep，以及视觉 token 总量未配平的限制 |
| §5.2 Sequential | 六种 L/U/G 顺序、12.5% replay 与同时联合训练 |
| §5.3 Vision laziness | 200B 配平 continuation、四类内部探针和公式 |
| §6.1 Ratio search | 23 组 L/U/G 比例搜索和 70/25/5 的真实含义 |
| §6.2 Scaling | 13.5B MoE、2T token、balanced/dense/late/full，以及 late 排程不可复算的报告缺口 |
| Related Work / Conclusion | 统一模型谱系、经验规律的定位、实践建议与外推边界 |
| Appendix A–E | 局限、三类 tokenizer 补充、CLEVR 细节、定性生成对照 |

## 1. 先把完整模型拼起来

控制实验使用一个近似 Llama-3 的 decoder-only Transformer：16 层、隐藏维 2048、32 个 Query head、8 个 KV head，文本词表约 128k。语言 token 与图像 token 共用 attention，但默认走各自的 FFN；语言骨干约 1.5B，拆开 FFN 后总参数约 2.3B。

训练框架是 Transfusion：

- (L)：纯文字做 next-token cross-entropy；
- (U)：图像作为输入，caption/VQA 答案作为文字输出，同样做 cross-entropy；
- (G)：文字作为条件，图像 latent 做 rectified flow / flow matching。

默认图像表征是 RAE：冻结 SigLIP-2 ViT-400m/14，把 $224\times224$ 图像变成 $16\times16=256$ 个语义 token；理解直接读这些 token，生成在同一 latent 中做 flow matching，再由 RAE decoder 还原像素。作者还用三种视觉入口重复关键趋势，目的是逐项拆掉可能的解释：

- **Raw Pixels**：用一层 $14\times14$ 卷积直接把 $224\times224$ 图像切成 $16\times16=256$ 个 patch，轻量 MLP 只对齐隐藏维；没有预训练视觉 encoder，也没有 decoder。它检验知识流是否只是 SigLIP 先验带来的。
- **CLIP+VAE**：理解仍用 SigLIP 的 256 个 token；生成改用 SD3 VAE，把 $256\times256$ 图像经 8 倍下采样变成 $32\times32\times16$ latent。它检验理解与生成是否必须共用 latent 才能协同。
- **AR UniTok**：把图像量化成离散码，按空间位置自回归预测；每个位置再由 causal depth head 逐个预测残差量化码本。它连 diffusion 都换掉，用来检查趋势是否依赖 flow matching。

## 2. 生成目标为什么能和 LLM 放在一套主干里

设干净图像 latent 为 $x_0$，与它同形状的高斯噪声为 $\epsilon$，时间 $t\in[0,1]$ 从噪声端走向数据端，$x_t$ 是时刻 $t$ 喂给网络的带噪 latent：

\[
x_t=t x_0+(1-t)\epsilon.
\]

论文让网络预测干净 $x_0$，再换算成 Euler ODE 要用的速度 $v$。当前位置到干净端的位移是 $x_0-x_t$，剩余时间是 $1-t$，所以速度先写成“位移除以时间”：

\[
v=\frac{x_0-x_t}{1-t}.
\]

把 $x_t$ 的定义代进位移，完整中间式是：

\[
x_0-x_t=x_0-[t x_0+(1-t)\epsilon]=(1-t)(x_0-\epsilon).
\]

因此除以 $1-t$ 后，正好得到直线路径的恒定速度 $v=x_0-\epsilon$。例如 $x_0=2,\epsilon=-1,t=.25$，则 $x_t=.25\times2+.75\times(-1)=-.25$，速度 $v=(2-(-.25))/.75=3$，也等于 $2-(-1)=3$。$t=1$ 时已经抵达干净端，不再做这次除法。网络仍是 Transformer；变化的是图像 token 使用双向去噪目标，而文字 token 使用离散 next-token 目标。

记 $r_L,r_U,r_G$ 为三类 token 的抽样比例，三者相加为 1；$\mathcal L_L,\mathcal L_U,\mathcal L_G$ 分别是纯文字、视觉理解和视觉生成的单项损失。只看比例与权重两只旋钮，混合损失可粗略写成：

\[
\mathcal L\approx r_L\mathcal L_L+r_U\mathcal L_U+3r_G\mathcal L_G.
\]

系数 3 是论文把 flow-matching loss 上调 3 倍。它提醒我们：70/25/5 是**数据比例**，不等于生成梯度只占 5%，更不严格等于 GPU 时间只占 5%。

## 3. “A 帮 B”到底怎样测

真实数据实验每次固定目标能力的 50B token，再增加另一能力。记 $A$ 为新增能力的数据量，单位是 B token；$r$ 为这批新增 token 占最终总量的比例。先有 $r=A/(50+A)$，移项后才得到：

\[
A=\frac{50r}{1-r}\;\text{B tokens}.
\]

例如 $r=20\%$，$A=50\times.2/.8=12.5B$；$r=80\%$，$A=50\times.8/.2=200B$。所以论文的 0/20/40/60/80% 对应新增 0/12.5/33/75/200B，不是把固定的 50B 再切开。

语言用 accuracy 与困惑度衡量。设 $N$ 为被评分的 token 数，$y_i$ 为第 $i$ 个真值 token，$y_{<i}$ 为它前面的真值前缀，$p(y_i\mid y_{<i})$ 为模型给真值的概率。困惑度公式是：

\[
\mathrm{PPL}=\exp\left[-\frac1N\sum_{i=1}^{N}\log p(y_i\mid y_{<i})\right].
\]

$N$ 是 token 数，$y_i$ 是第 $i$ 个真值 token，$p(y_i\mid y_{<i})$ 是模型读过前缀后给真值的概率。若四步概率为 $[.5,.25,.5,.25]$，平均负对数为 $1.0397$，PPL 约 $e^{1.0397}=2.83$。越低表示文字越符合模型预期。

视觉理解汇总 16 个 benchmark，分 General、Knowledge、OCR & Chart、Vision-Centric 四组；但分数是在预训练后再用 Cambrian-7M 做一轮 SFT 得到，不是纯零样本读数。生成用 DPG、GenEval、CLIP-Sim 与验证集 diffusion loss。

还有一个容易漏掉的控制变量：六个知识流方向并不全从同一起点开始。L→U、L→G、U→L、G→L 从头初始化；U→G 与 G→U 从已经训练 50B 语言 token 的 checkpoint 起步，让模型先具备基本文字能力。因此结果是在作者各自设定的起点上比较新增数据的作用，不是六次完全同初始化的对称实验。

## 4. 第一张知识流地图：方向明显不对称

真实数据的主结果是：

- $L\rightarrow U$：语言比例 0→80% 时四组 VQA 都升，OCR/知识提升尤其明显；
- $L\rightarrow G$：DPG、GenEval、CLIP-Sim 上升，条件与无条件 diffusion loss 都下降；
- $U\rightarrow G$：增加看图数据明显改善画图，说明判别式视觉特征能给生成提供结构先验；
- $U\rightarrow L$：语言略退化，论文认为与图文数据里的文字分布偏离纯 DCLM 有关；
- $G\rightarrow L/U$：大多只是小幅波动，没有稳定正向趋势，也没有严重冲突。

Raw Pixels、CLIP+VAE、UniTok AR 的附录重复实验得到相同大方向，所以它不只依赖 RAE 或 diffusion。

## 5. 为什么“会看黄色”不等于“会画黄色”

真实网页数据里变量缠在一起，论文又造了约 100 万张 CLEVR 场景。每张图都有场景图、密/稀 caption 和 1–3 个 VQA，概念分颜色、形状、空间关系、大小、数量五类。

要测 $U\rightarrow G$，就在生成数据里彻底删掉 yellow，理解数据仍保留 yellow；测试时要求生成黄色物体。要测 $G\rightarrow U$，就反过来删理解流里的 yellow。每次都与“两个流都见过”的 baseline 和“两个流都没见过”的 control 比，且每个概念用 100 个生成 prompt / VQA 问题评估。

结果分两层：

- 颜色、形状：双向零样本转移几乎失败。看懂 yellow 的语义接口，不足以学会生成黄色像素；画过 yellow，也不会自动学会用文字回答 yellow。
- 关系、大小、数量：理解能部分零样本帮助生成；生成对理解仍很弱，count 有一点例外。

接着作者把缺失概念补回去微调 2000 step、每 200 step 测一次。生成预训练虽然不能零样本回答颜色/形状，却显著加速后续 VQA 学习；它学到的是“可用但尚未接到答案接口”的低层视觉先验。理解对颜色生成几乎不加速，对形状只有小幅帮助。

## 6. 协同与竞争是两股同时存在的力

论文固定 100B token，语言/视觉各 50B，并与 50B 单模态基线比较。记 $\mathrm{PPL}_{joint}$ 为联合训练后的语言困惑度，$\mathrm{PPL}_{language-only}$ 为只用 50B 语言数据训练的基线，差值定义为：

\[
\Delta\mathrm{PPL}=\mathrm{PPL}_{joint}-\mathrm{PPL}_{language-only}.
\]

负数是协同，正数是净干扰。纯色背景带来 ΔPPL=-.211，噪声是 -.183；复杂视频变成 +.052，SSTK 自然图像 +.075。反方向上，简单字母语言给图像生成的 conditional/unconditional diffusion loss 带来 -.0153/-.0168，帮助比完整 DCLM 更大。

不能把它简化成“数据越简单越好”。作者自己说明这只是大致的复杂度阶梯，不是严格单调标尺；七档视觉数据同时改变了语义、结构、任务形式和分布。实验更可靠的结论是：联合训练里确实同时有正向共享和有限容量竞争，任务越吃容量，竞争越可能盖过协同。

## 7. 冲突主要放在 FFN，交流主要留在 attention

论文把 Transformer block 分成 FFN、Attention、FinalNorm 三组：

- dense：三组全共享，ΔPPL=+.272、Δdiffusion loss=+.0537，两边都坏；
- split_ffn：只把 FFN 按模态拆开，ΔPPL=-.211、Δloss=-.0168，两边最好；
- split_ffn_attn：连 attention 也拆，收益缩到 -.045 / -.0064；
- split_ffn_norm：拆 FFN 和 norm，收益也比只拆 FFN 小；
- split_all：全部隔离，接近两个单模态基线，既不冲突也不再协同。

直觉上，attention 是跨 token 交换上下文的“会议室”，norm 维持可交流的数值尺度；FFN 是每个 token 真正消化和变换特征的容量仓。共享前两者、给不同模态自己的 FFN，正好把交流与专用计算拆开。这个趋势在四种视觉 tokenizer 上都复现。

## 8. 早联合的证据要分三层读

第一组 1T 实验把纯语言 warm-up 从 0B 扫到 800B，剩余 token 再按 50/50 做联合训练。语言略好，绝大多数视觉理解与生成指标明显变差。但这里越晚开始，视觉 token 也从 500B 降到 100B，不能把下降全归因于“开始时间”。

第二组顺序实验固定 L/U/G=50/25/25，尝试全部六种顺序。严格顺序训练几乎都输给同时联合；保留 12.5% 旧模态 replay 能缓解遗忘，却仍达不到 joint baseline。它说明问题不只剩 catastrophic forgetting，训练过程里的持续协同也丢了。

第三组是更强的证据：

- vision-laziness 探针从 0/200/400/600/800B 语言 checkpoint 出发，每组都再做相同的 200B 50/50 联合训练；
- 2T 规模 early/late 对照中，作者称两组视觉 token 总量相同，late 到最后 40% 才接入视觉；但论文未公开最后阶段的 L/U/G 比例或逐步 token 口径，读者无法独立复算“同量”。

这两组仍显示越晚接视觉越差，支持“成熟语言主干会抵抗视觉共同塑形”的解释；其中 matched-200B continuation 可直接核对，2T 等量控制只能按作者报告接受，证据强度应分开写。

## 9. Vision laziness 怎样被量出来

模型不是因为模块参数少就被叫“懒”，而是四类读数一起下降：训练时图像 FFN 激活、图像 wrapper token 的 embedding 范数、推理时图像 FFN 的 RMS、注意力落到图像 token 的比例。

设 $h=[h_1,\ldots,h_n]$ 是某一层的输出向量，$h_i$ 是第 $i$ 个元素，$n$ 是元素数。L2 汇总所有元素的能量，逐元素 RMS 再除以 $\sqrt n$，消掉“元素越多，L2 天然越大”的影响：

\[
\lVert h\rVert_2=\sqrt{\sum_{i=1}^{n}h_i^2},\qquad
\mathrm{RMS}(h)=\frac{\lVert h\rVert_2}{\sqrt n}.
\]

若 $h=[3,4,0,0]$，L2=5，RMS=2.5。注意力比例可用下面的等价记号写清；这不是论文新提出的训练损失。$A_{img}$ 表示平均落到图像上的注意力，$Q$ 是被考察的 query 集，$I$ 是图像 key 的位置集合，$a_{qk}$ 是 softmax 后从 query $q$ 到 key $k$ 的权重：

\[
A_{img}=\frac1{|Q|}\sum_{q\in Q}\sum_{k\in I}a_{qk}.
\]

生成时 $Q$ 取图像 query，理解时取文字 query。每行 attention 权重和为 1，所以先把所有图像 key 对应的权重相加，再对 query 取平均，就得到模型平均把多少注意力给了图像。

随着语言起点变晚，这四项都下降，最终生成也更容易漏掉“绿头鸭”“三色意面”这类细粒度约束。它仍是机制线索，不是数学定理；但比只看 benchmark 分数更有解释力。

## 10. 70/25/5 是怎样搜出来的

作者对 1T token 做 23 组比例：先扫 L=10–90%、其余 U/G 平分；再固定 L=50% 扫 U/G；最后固定 L=70% 精扫 U/G。最佳折中落在 L70/U25/G5：General VQA 48.3、Vision-Centric 47.1、VQA Avg 38.5、DPG .450、GenEval .237。

它不是每列都绝对最好：例如最低语言 PPL 出现在 L90/U5/G5，最低 diffusion loss 出现在 L50/U5/G45。70/25/5 是作者按语言、理解、生成综合指标选出的 Pareto 式折中。更准确的表述是“5% 生成 token 已足以得到很强的综合生成指标”，不是“任何模型只用 5% 总算力都能达到峰值画质”。

## 11. 放大到 13.5B MoE / 2T token

大模型共有 13.5B 参数，每个 token 激活约 1.5B。256 个 FFN experts 中每次使用 16 个：2 个固定为语言/视觉专用，14 个动态路由；attention 和 norm 共享。

四组结果：

| 模型 | 配方 / 时机 / 架构 | PPL ↓ | L Acc | U Avg | DPG | GenEval | CLIP-Sim | DiffLoss |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Balanced | 50/25/25，early，MoE | 11.97 | 52.86 | 41.42 | .676 | .467 | .310 | **.261** |
| Dense | 50/25/25，early，3.5B dense | 12.14 | 52.03 | 40.49 | .667 | .459 | .308 | .266 |
| Late | 50/25/25，late，MoE | 12.25 | 51.78 | 40.66 | .672 | .471 | .308 | .269 |
| Full | 70/25/5，early，MoE | **11.67** | **54.31** | **43.08** | **.689** | **.482** | **.312** | .272 |

Full 的 diffusion loss 比 Balanced 略差，但 50k 图像 FID 仍为 5.234，对照是 5.131。少五倍生成 token 并非所有图像指标都更好，而是语言、理解和提示对齐的综合收益更高。MoE 对照也不是总参数完全匹配：13.5B 总参/1.5B active 与 3.5B dense 的总容量不同，比较更接近“相似活跃计算下，稀疏大容量是否更合适”。

## 12. 实验与工程账本

- 控制模型：16 层、hidden size 2048、32 个 Query head / 8 个 KV head；SwiGLU、RoPE $\theta=500k$、pre-RMSNorm、QK-Norm、FlashAttention，FFN expansion=1.5；语言骨干约 1.5B，拆分 FFN 后总计约 2.3B。
- 优化：AdamW，β1=.9、β2=.95、weight decay .1、gradient clip 1.0；8000 step warm-up 后 cosine decay。
- 数值与并行：bf16、FSDP-2、4096 context。
- 生成：logit-normal 采样 t，25-step Euler，CFG=5.0，x-prediction 转 velocity。
- 数据：DCLM 纯文本；约 3.5 亿 SSTK 图文对同时供应理解与条件生成。
- VQA SFT：Cambrian-7M 一轮，峰值学习率 1e-5，global batch 128。
- 复现控制：初始化和 data iterator 都固定 seed=0，评估 temperature=0。
- 语言评测：11 项 accuracy/EM + DCLM/C4 PPL。
- 理解评测：16 项，四组汇总。
- 生成评测：DPG、GenEval、短/中/长 prompt CLIP-Sim、1000 样本 diffusion validation loss，规模实验另报 50k FID。

## 13. 这篇论文真正建立了什么，没建立什么

它最有价值的不是宣称一个新 SOTA，而是把多模态联合训练拆成了可做控制变量的几个问题，并用真实数据、合成因果测试、内部探针和 2T 放大验证串成一条证据链。

但边界也很清楚：控制实验全部固定 seed=0，没有误差条或置信区间；complexity 没有独立量化；CLEVR 每概念只有 100 个样本，生成由 Qwen3-VL-8B 自动判分，没报告人工一致性；主范围仍是文字与静态图像；70/25/5 只在当前模型、数据和指标网格内最优；前沿万亿参数、视频、音频、动作是否沿用同一规律尚未验证。2T late 对照虽被作者描述为视觉 token 等量，但完整排程没有披露，也无法从公开数字独立复算。

另外，“生成不反哺理解”只适用于这里的标准 benchmark 与零样本路径。论文自己的恢复曲线已经说明：生成学到的低层先验可能藏在内部，只是没有接到 VQA 输出接口。把“零样本没涨分”说成“完全没学到”会读错。

## 核心贡献

1. **知识流**：[[multimodal-knowledge-flow]] —— 把 L/U/G 的六个方向拆开，发现强烈不对称且依赖概念层级。
2. **协同结构**：[[modality-synergy-competition]] —— 共享 attention/norm 保留交流，拆 FFN 缓解容量冲突。
3. **训练时机**：[[early-fusion]] / [[vision-laziness]] —— 早期持续联合比晚接和阶段式课程更稳。
4. **数据配方**：[[asymmetric-multimodal-pretraining-recipe]] —— 用 70/25/5 与 MoE 把小规模规律带到 2T。

## 我的批注

- 最漂亮的实验不是 70/25/5 表格，而是 CLEVR 把“概念是否见过”从一条训练流里外科式拿掉；它让“理解帮助生成”从相关性变成可解释的概念级差异。
- 最容易被宣传稿夸大的数字是“5% compute”。更严谨应说 5% generation-token share，且 generation loss 乘了 3。
- 主时间 sweep 有视觉 token 量混杂，若只读摘要会错过；matched-200B 内部探针是可直接核对的硬支撑，2T late 对照则因排程不完整，只能视为作者报告的规模证据。
- split-FFN 的意义不是“视觉和文字最好分家”，而是把需要交流的 attention 留共享，把最吃容量的逐 token 变换分开。
- 生成对理解的帮助更像“预训练地基”而不是“现成答题技能”：先学会像素细节，再用少量 VQA 教它怎样把细节说出来。

## 跟 wiki 里其他 paper 的关系

- Beyond Language Modeling（arXiv:2603.03276）· 同一研究线的前篇：RAE、Transfusion、MoE 与统一世界模型的大方向。
- [[rae-dit]] · 默认视觉 latent 为什么既能用于理解又能用于生成。
- [[interaction-models-tml]] · 更激进的 encoder-free early fusion；本篇证明的是训练时机上的 early unification。
- [[cosmos-3]] · 另一种统一理解/生成的 MoT 方案，拆分范围比本篇 split-FFN 更大。
- [[sensenova-vision]] · Bagel/MoT 如何把统一模型继续扩成检测、深度、分割等视觉输出。

## 历史定位

- 2024-02 Transfusion · 一套 Transformer 同时做文字 next-token 与图像 diffusion。
- 2026-03 Beyond Language Modeling · 从头训练统一模型，提出 RAE、跨模态协同与 MoE scaling。
- 2026-08 **Towards Physics of Multimodal Pretraining** · 用控制实验解释知识流、竞争位置、早联合和数据配方。
