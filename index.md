# Index · 个人学习 wiki 目录

按类别组织。每条 `[标题](路径) — 一句话钩子`。

## 精读页 · Deep Dives

> 手工打磨的 bespoke 深读页（不只论文）：ML 论文 + 系统 + 金融 + 史。live 站按领域分小标题 + 顶部领域 chip 筛选。

- [FFT · 快速傅里叶变换](wiki/papers/fft.md) — 信号处理/算法基础: 傅里叶=棱镜拆频率, FFT 用偶奇折半+单位根对称(蝴蝶)把 N² 砍成 N·logN; 接卷积定理 + 音频频谱(STFT)
- [CNN · 卷积神经网络](wiki/papers/cnn.md) — 视觉骨架基础: 小核滑遍全图+权重共享, 把局部性/平移不变焊进结构; 卷积滑窗动画 + LeNet→ResNet→ViT 谱系
- [Deep Residual Learning · ResNet](wiki/papers/resnet.md) — 残差连接的起源，把"网络越深越好"做成现实，也给两年后的 Transformer 留好 sublayer 模板
- [LSTM · 长短期记忆](wiki/papers/lstm.md) — Transformer 前的序列霸主: cell state 记忆传送带(加法更新)+三个门(遗忘/输入/输出)治住RNN梯度消失; 加法梯度高速路=ResNet残差同构; 被Attention取代
- [Attention Is All You Need](wiki/papers/attention-is-all-you-need.md) — Transformer 始祖，整个 LLM 时代的奠基
- [BERT](wiki/papers/bert.md) — 只要 Transformer encoder，用 MLM 学双向上下文，立住 pretrain → finetune 范式
- [GPT-1](wiki/papers/gpt-1.md) — 只要 Transformer decoder，causal LM 预训练，用输入格式编码任务结构
- [GPT-2](wiki/papers/gpt-2.md) — 同架构 scale 13× 到 1.5B + WebText，发现 prompt 能 zero-shot 触发任务
- [GPT-3](wiki/papers/gpt-3.md) — 同架构再 scale 100× 到 175B，prompt 里给几个例子模型现学（ICL），ChatGPT 时代由此开始
- [Flow Matching](wiki/papers/flow-matching.md) — 把 diffusion 的 score matching 换成"学速度场 + ODE 积分"，简单 + 少步推理
- [ODE vs SDE · 确定性流与随机流](wiki/papers/ode-sde.md) — 方法底层页: ODE=风场弹珠确定/SDE=醉汉每步随机踹; 桥=同一团云两看法; Euler 真数字演算(同起点ODE永远落5/SDE跑出6.13与3.30); 接 flow-matching + diffusion
- [Generative Modeling via Drifting](wiki/papers/drifting-models.md) — 一步生成新范式(Kaiming He组): 吸引真数据+排斥自己的漂移场, 反对称→q=p场归零; 把迭代从推理时搬进训练时, 推理1步; ImageNet256 FID 1.54; 像无判别器GAN
- [DiffusionOPD · 扩散的 On-Policy 蒸馏](wiki/papers/diffusion-opd.md) — 多奖励对齐扩散: 先各训单任务专家老师, 再沿学生rollout轨迹蒸进一个学生; 扩散=高斯马尔可夫链→同协方差KL塌成均值MSE; 接 ppo+ode-sde+cross-entropy
- [dMel](wiki/papers/dmel.md) — 跳过 neural codec 直接 bin quantize log-mel，简单方案跟 RVQ 一样好
- [Interaction Models · Thinking Machines](wiki/papers/interaction-models-tml.md) — 把交互能力做进权重的 276B MoE 模型
- [Fish Audio S2 Pro](wiki/papers/fish-speech-s2-pro.md) — Dual-AR + RVQ + GRPO 的开源 TTS
- [RoPE · Rotary Position Embedding](wiki/papers/rope.md) — 不加位置向量，旋转 Q/K 让点积天然含相对位置；LLaMA / Mistral / Qwen 全在用
- [Whisper](wiki/papers/whisper.md) — 68 万小时弱监督训 ASR，zero-shot 碾压精标模型；语音领域的 GPT 时刻
- [Qwen3-ASR · 给 LLM 接个耳朵](wiki/papers/qwen3-asr.md) — 不从头训ASR: 预训练Qwen3当解码器+AuT音频编码器(8×下采样12.5Hz+动态窗口流式/离线)+projector; modality-projector生产级; prompt塞热词定制转写; RL用GSPO; 带口音英语完胜Whisper
- [Generative Agents · Smallville](wiki/papers/generative-agents.md) — 给 LLM 加记忆流 + 反思 + 规划，25 个 agent 在虚拟小镇里自主生活
- [MemGPT · LLMs as Operating Systems](wiki/papers/memgpt.md) — context 当 RAM、外部存储当硬盘，LLM 自己 function call 调度记忆
- [Lumine · 从像素玩 3D 开放世界](wiki/papers/lumine.md) — VLM(Qwen2-VL)直接吃画面像素吐键鼠, 端到端打通原神5h主线零样本迁移; 动作即文本token + action chunking(5Hz看30Hz动) + hybrid thinking(该想才想); 2424h人类录像纯模仿零RL + W8A8实时
- [ViT · An Image is Worth 16×16 Words](wiki/papers/vit.md) — 把图切成 16×16 patch 当 token，纯 Transformer 干视觉；CNN 在视觉的护城河被填平
- [CLIP · Learning Transferable Visual Models](wiki/papers/clip.md) — 4 亿图文对对比学习, 图像和文本对齐到同一向量空间; DALL-E / SD / LLaVA 都靠它
- [PPO · Proximal Policy Optimization](wiki/papers/ppo.md) — 一行 clip 干掉 TRPO 的复杂; RLHF 的训练发动机, 撑起 ChatGPT 的对齐
- [Go GC · 从 mark-sweep 到 Green Tea](wiki/papers/go-gc.md) — 系统/runtime 深度页: 三色并发 mark-sweep + write barrier + GOGC/GOMEMLIMIT, 到 Go 1.26 默认的 Green Tea 按页扫优化
- [康波周期 · 经济的四季](wiki/papers/kondratiev-wave.md) — 宏观/有争议框架: 50–60 年长波 + 五次技术浪潮 + 四季资产轮动 + 多周期嵌套 + 周金涛本土化; 当罗盘不当钟表
- [缠论 · 把走势拆成可数的结构](wiki/papers/chan-theory.md) — 技术分析/自洽但主观: 分型→笔→线段→中枢 + 级别自相似 + 背驰 + 三类买卖点; 坐标系不是预言机 ｜ 形态学(主篇)
- [缠论 · 动力学 · 背驰与区间套](wiki/papers/chan-theory-dynamics.md) — 缠论深入②: 背驰精判(MACD面积/趋势vs盘整) + 区间套精确定位 + 背驰↔买卖点定理 + 级别嵌套转化
- [缠论 · 操作 · 走势分解](wiki/papers/chan-theory-operation.md) — 缠论深入③: 走势类型定理(趋势/盘整) + 同级别分解 + 中枢震荡 + 走势多义性 + 只做当下
- [盐铁论 · 两千年前的国营 vs 民营](wiki/papers/discourses-salt-iron.md) — 史/政治经济学: 公元前81年盐铁会议, 桑弘羊财政机器 vs 贤良文学民本, 富国强兵 vs 藏富于民; 两千年回声
- [净利润断层 · 业绩惊喜 + 跳空缺口](wiki/papers/net-profit-gap.md) — 交易/事件驱动: 净利润惊喜 + 断层缺口, 本质捕捉 PEAD(Ball&Brown 1968); 有学术底子但会衰减
- [资金面 · 量能与共识](wiki/papers/capital-flow.md) — 交易/盘口经验派: 量能(量价关系) + 共识(游资分歧转一致/筹码集中/抱团); 经验派语言, 易事后解释
- [爱在冰川 · 低吸待涨的道法术](wiki/papers/aizai-bingchuan.md) — 交易/短线经验派: 道(低吸待涨极简循环)→法(横盘龙头低吸/大智大勇/潜伏)→术(揉搓线/做小T); 从公开复盘合集提炼, 非荐股
- [Stable Diffusion 3.5 · 整流流 + MMDiT](wiki/papers/stable-diffusion-3-5.md) — 开源文生图(基于SD3论文): 把"文字当调料"换成"文字图像坐同一张桌子"(MMDiT双权重单序列) + 整流流直线少步采样 + 三文本编码器(CLIP-L/G+T5-XXL) + QK-Norm稳训; Large 8B/Medium 2.5B(MMDiT-X消费级能跑)
- [FLUX.1 · 先双流后单流 + 两道蒸馏](wiki/papers/flux-1.md) — SD原作者新公司(Black Forest Labs)的12B整流流T2I: 混合架构(前段双流MMDiT对齐+后段单流共享省) + 引导蒸馏(CFG两遍压一遍)做dev + 步数蒸馏4步做schnell(两道正交); pro/dev/schnell三档
- [Ideogram 4.0 · 9.3B 单流 DiT](wiki/papers/ideogram-4.md) — 文生图开源权重: 单流 DiT + Qwen3-VL 文本编码器 + 结构化 JSON caption(bbox/调色板); 9.3B 文本渲染碾压 80B
- [MiniMind-O · 0.1B 端到端 Omni](wiki/papers/minimind-o.md) — 从0实现的听看说 Omni: Thinker–Talker 双路径 + MTP 出8层 Mimi codes + 冻结编码器/projector; fish-speech 的麻雀版
- [ELT · Elastic Looped Transformers](wiki/papers/elt.md) — looped transformer 进视觉生成: N层block循环L圈(深度共享权重) + 一族深度弹性推理 + ILSD; 同算力 4× 参数缩减
- [HiDream-O1-Image · 像素级统一 Transformer](wiki/papers/hidream-o1.md) — 文生图反向操作: 无VAE像素空间扩散 + 文本编码器收进主干(Qwen3-VL) + 混合注意力 + O1推理agent先想后画; 8B 超更大模型
- [Qwen-Image-2.0 · 生成与编辑统一](wiki/papers/qwen-image-2.md) — 20B MMDiT: 生成vs编辑=条件里塞不塞原图latent(Concat), 同backbone, 没点名天然照抄; frozen Qwen3-VL条件编码器 + VAE升16×(f16c64) + MSRoPE + DMD蒸馏4-NFE; 中文文字渲染 + 1K token直出信息图; LMArena中文#1
- [PiD · 像素扩散解码器](wiki/papers/pid-pixel-diffusion.md) — NVIDIA 把 latent→像素的确定性 VAE 解码器换成条件像素扩散: 解码从"忠实还原"升级成"生成式补细节+顺手超分4×/8×"; sigma-aware adapter 吃半成品 latent 让 latent 扩散早停 + DMD2 蒸 4 步 + 通吃 VAE/语义 latent; 512²→2048² 1秒内
- [MRT · Masked Region Transformer](wiki/papers/mrt.md) — 分层图像生成编辑(CVPR2026,Canva): 产出可编辑RGBA图层而非拍平图; masking哪些图层干净/噪声=切文生层/拆图成层/层改层三任务(Qwen-Image-2.0"条件→目标"的分层升级); anonymous region transformer + overflow画布留溢出 + DMD蒸馏50→8步; 比Qwen-Image-Layered快10~100×
- [Qwen3-VL · 视觉语言模型怎么看图](wiki/papers/qwen3-vl-report.md) — VLM三件套(SigLIP-2 ViT眼睛+MLP merger插头+Qwen3 LLM大脑); 图按原生分辨率变长token; 三升级 Interleaved-MRoPE(频谱均衡长视频)/DeepStack(3层ViT注入前3层LLM)/文字时间戳; 四阶段预训练到256K+thinking; OCR32语种/2D3D grounding/GUI agent
- [DINO · 自监督 ViT](wiki/papers/dino.md) — 无标签自蒸馏: student 对齐 EMA teacher + multi-crop 局部猜全局 + centering/sharpening 防坍缩; 涌现物体注意力, DINO loss 的来历
- [LPIPS · 深层特征当感知度量](wiki/papers/lpips.md) — 像素L2跟人眼差很远: 过预训练网络比深层特征 + 人类2AFC校准权重; 感知相似是深度表征的涌现属性, 既度量又当损失

## Books · 书籍精讲

非 ML papers，但跟我自己关心的领域（理财 / 行为 / 决策）相关。每章独立成页，"精讲 + 自己加例子"形态，不做 bespoke HTML。

- [The Psychology of Money · Morgan Housel](wiki/books/psychology-of-money.md) — 财富 = 行为 × 时间，不是数学
  - [Ch01 · No One's Crazy](wiki/books/pom-ch01-no-ones-crazy.md) — 你的金钱观是你经历过的世界
  - [Ch02 · Luck & Risk](wiki/books/pom-ch02-luck-and-risk.md) — 运气和风险，一对从同一台抽奖机出来的双胞胎
  - [Ch03 · Never Enough](wiki/books/pom-ch03-never-enough.md) — 胃口别跟着饭量长；别拿你有且需要的去赌你没有也不需要的
  - [Ch04 · Confounding Compounding](wiki/books/pom-ch04-confounding-compounding.md) — 复利的关键不是收益率，是时间
  - [Ch05 · Getting Wealthy vs Staying Wealthy](wiki/books/pom-ch05-getting-vs-staying-wealthy.md) — 致富靠进攻，守富靠防守；两套完全相反的技能
  - [Ch06 · Tails, You Win](wiki/books/pom-ch06-tails-you-win.md) — 极少数极端事件主导大部分结果；你做对的事可以很少，只要那几下对了
  - [Ch07 · Freedom](wiki/books/pom-ch07-freedom.md) — 钱最高的红利是对时间的控制权，不是物质
  - [Ch08 · Man in the Car Paradox](wiki/books/pom-ch08-man-in-the-car-paradox.md) — 你想用钱买 admiration，但别人在看你的东西，不在看你
  - [Ch09 · Wealth is What You Don't See](wiki/books/pom-ch09-wealth-is-what-you-dont-see.md) — 财富 = 你没花掉的钱；看着有钱的大多数只是在花钱
  - [Ch10 · Save Money](wiki/books/pom-ch10-save-money.md) — 财富 = 收入 − 虚荣心；存钱不需要理由
  - [Ch11 · Reasonable > Rational](wiki/books/pom-ch11-reasonable-gt-rational.md) — 能坚持 30 年的普通方案吊打坚持 3 年就放弃的最优方案
  - [Ch12 · Surprise!](wiki/books/pom-ch12-surprise.md) — 从没发生过的事一直在发生；历史教的是人性，不是具体会发生什么
  - [Ch13 · Room for Error](wiki/books/pom-ch13-room-for-error.md) — 安全边际让预测变得不必要；给计划留"计划不成"的空间
  - [Ch14 · You'll Change](wiki/books/pom-ch14-youll-change.md) — 未来的你跟现在不一样；中庸策略给未来的自己留路
  - [Ch15 · Nothing's Free](wiki/books/pom-ch15-nothings-free.md) — 任何回报都有标价；波动是费用不是罚单
  - [Ch16 · You & Me](wiki/books/pom-ch16-you-and-me.md) — 同一市场里两个人玩的是不同游戏
  - [Ch17 · The Seduction of Pessimism](wiki/books/pom-ch17-seduction-of-pessimism.md) — 悲观听起来聪明，但过去 200 年押乐观的人都赢了
  - [Ch18 · When You'll Believe Anything](wiki/books/pom-ch18-when-youll-believe-anything.md) — 越想要某结果越容易相信通往它的故事；诱人虚构
  - [Ch19 · All Together Now](wiki/books/pom-ch19-all-together-now.md) — 全书 12 条原则速查清单
  - [Ch20 · Confessions](wiki/books/pom-ch20-confessions.md) — Housel 自己的方案：简单到无聊
  - [Postscript · 美国消费者心理简史](wiki/books/pom-postscript-us-consumer-history.md) — 75 年经济史，预期脱节于现实的根源

## Topics · 综合

- [训练 vs 推理 · 同一个模型的两种跑法](wiki/topics/training-vs-inference.md) — 三种架构训练/推理对比（teacher forcing / causal mask / KV cache / MLM 放在一起看）
- [音频 token 化：RVQ vs Flow](wiki/topics/audio-tokenization-rvq-vs-flow.md) — 两种主流路线的工程对照
- [把外挂规则吃进权重](wiki/topics/replace-heuristics-with-weights.md) — 反复出现的范式：VAD、phonemizer、Whisper encoder 都在被收

## Concepts · 概念

### TML interaction models
- [Micro-Turn](wiki/concepts/micro-turn.md) — 200ms 一片，输入输出同时入流
- [Dual-Model Architecture](wiki/concepts/dual-model-architecture.md) — 前台 always-on + 后台异步
- [Early Fusion](wiki/concepts/early-fusion.md) — 各模态早早进同一 transformer
- [hMLP](wiki/concepts/hmlp.md) — TML 的轻量视频预处理，把 patch 压成 token
- [Flow Matching](wiki/concepts/flow-matching.md) — 学速度场积分到目标
- [dMel](wiki/concepts/dmel.md) — 规则离散化 Mel 频谱
- [Bitwise Determinism](wiki/concepts/bitwise-determinism.md) — 训推 bit-for-bit 一致
- [Batch-Invariant Kernel](wiki/concepts/batch-invariant-kernel.md) — batch 怎么切都尽量同结果
- [Split-KV](wiki/concepts/split-kv.md) — attention 沿 KV 序列切分并行
- [Grouped GEMM vs GEMV](wiki/concepts/grouped-gemm-vs-gemv.md) — MoE 小 batch 推理的吞吐/延迟取舍
- [NVLS](wiki/concepts/nvls.md) — NVIDIA 低延迟集合通信
- [MoE](wiki/concepts/moe.md) — 稀疏激活，276B/12B

### fish-speech
- [Dual-AR](wiki/concepts/dual-ar.md) — 慢 AR 4B + 快 AR 400M 主从
- [RVQ Codec](wiki/concepts/rvq-codec.md) — 10 层残差量化 codec
- [GRPO](wiki/concepts/grpo.md) — 无 critic 的组内相对 RL
- [SGLang Inference](wiki/concepts/sglang-inference.md) — fish-speech 借用的 LLM 推理基建
- [Voice Cloning Reference](wiki/concepts/voice-cloning-reference.md) — 参考音频提供说话人条件
- [Inline Emotion Tags](wiki/concepts/inline-emotion-tags.md) — 文本里直接写情绪/风格控制

### Transformer 骨架
- [Self-Attention](wiki/concepts/self-attention.md) — Q·Kᵀ/√dₖ 然后 softmax 加权 V
- [Multi-Head Attention](wiki/concepts/multi-head-attention.md) — 多个 head 学不同关系模式
- [Cross-Attention](wiki/concepts/cross-attention.md) — decoder 用自己的 Q 去查 encoder 的 K/V
- [Positional Encoding](wiki/concepts/positional-encoding.md) — 给无顺序的 attention 加位置
- [Rotary Position Embedding](wiki/concepts/rotary-position-embedding.md) — 旋转 Q/K 让点积天然含相对位置，现代 LLM 事实标准
- [一次前向 · token→下一个token](wiki/concepts/next-token-forward-pass.md) — QKV→注意力softmax→末位向量撞词表→输出softmax→挑token；拆清两个 softmax
- [Cross-Entropy 交叉熵](wiki/concepts/cross-entropy.md) — −log(你押对的概率)；one-hot时是"别答错"，软标签时整条分布去贴；最小化它=最小化KL
- [EMA 指数滑动平均](wiki/concepts/ema.md) — 一行 `新=m·旧+(1−m)·新值`；磨平抖动追"更稳的自己"；DINO/BatchNorm/Adam 全在用
- [Relative Position Encoding](wiki/concepts/relative-position-encoding.md) — 为什么"差几个位置"比"在第几个位置"好
- [Transformer Architecture](wiki/concepts/transformer-architecture.md) — Encoder + Decoder 堆叠
- [LayerNorm](wiki/concepts/layernorm.md) — 每个 token 内部归一化，序列模型比 BN 更顺手
- [归一化家族 Normalization](wiki/concepts/normalization.md) — BN/LN/GN/RMSNorm 只差"对哪根轴求μ/σ"; 同一个2×4矩阵算三遍(按行LN/按列BN/分块GN)真数字例子 + 立方体图
- [Residual + LayerNorm](wiki/concepts/residual-layernorm.md) — 现代 Transformer block 的稳定训练骨架

### CNN 基础
- [Convolution](wiki/concepts/convolution.md) — 小核滑遍全图、逐元素相乘求和；局部连接+权重共享，省参数又平移不变
- [Pooling](wiki/concepts/pooling.md) — 小窗取 max/avg 下采样：降计算、扩感受野、带一点平移鲁棒
- [Receptive Field](wiki/concepts/receptive-field.md) — 一个输出能看到原图多大一片；堆卷积线性长、下采样指数级扩

### ResNet 系
- [Residual Connection](wiki/concepts/residual-connection.md) — `+ x` 快车道，identity 是默认值
- [Degradation Problem](wiki/concepts/degradation-problem.md) — 深网络反而变差的怪现象
- [BatchNorm](wiki/concepts/batchnorm.md) — z-score 归一化 + scale/shift
- [ResNet Architecture](wiki/concepts/resnet-architecture.md) — stage 堆叠：分辨率降、通道升
- [Bottleneck Block](wiki/concepts/bottleneck-block.md) — 1×1 → 3×3 → 1×1 的省算力残差块

### BERT 系
- [Masked Language Model](wiki/concepts/masked-language-model.md) — BERT 的核心预训练任务
- [Next Sentence Prediction](wiki/concepts/next-sentence-prediction.md) — 段间关系 pretrain，后被证伪
- [Encoder-Only Paradigm](wiki/concepts/encoder-only-paradigm.md) — 双向 attention 路线
- [Pretrain-Finetune Paradigm](wiki/concepts/pretrain-finetune-paradigm.md) — NLP 训练范式革命

### GPT 系
- [Causal Language Model](wiki/concepts/causal-language-model.md) — 每位置预测下一词，CLM
- [Input Transformations](wiki/concepts/input-transformations.md) — 用文本格式编码任务结构，prompting 的雏形
- [Decoder-Only Paradigm](wiki/concepts/decoder-only-paradigm.md) — 因果 attention 路线，最终赢的那条
- [Zero-Shot Transfer](wiki/concepts/zero-shot-transfer.md) — GPT-2 用 prompt 触发任务，不 finetune
- [WebText](wiki/concepts/webtext.md) — Reddit karma 筛网页，GPT-2 数据集
- [Language Modeling as Multitask](wiki/concepts/language-modeling-as-multitask.md) — LM 预训练即多任务学习
- [In-Context Learning](wiki/concepts/in-context-learning.md) — GPT-3 的核心，prompt 里给例子模型现学
- [Few-Shot Learning](wiki/concepts/few-shot-learning.md) — ICL 里最常见的 prompt 形态
- [Emergent Abilities](wiki/concepts/emergent-abilities.md) — 小模型 ≈ 0 大模型突然能的 hockey-stick 曲线
- [Sparse Attention](wiki/concepts/sparse-attention.md) — GPT-3 用的省算力 attention 方案
- [Scaling Laws](wiki/concepts/scaling-laws.md) — LM loss 跟参数/数据/算力的 power law

### 生成模型基础
- [Velocity Field](wiki/concepts/velocity-field.md) — flow matching 学的目标，(x, t) → 该往哪走
- [Conditional Flow Matching](wiki/concepts/conditional-flow-matching.md) — 实际可训练的 flow matching loss
- [Probability Path](wiki/concepts/probability-path.md) — 噪声到数据的密度演化路径
- [Optimal Transport](wiki/concepts/optimal-transport.md) — 让噪声到数据尽量走直路的路径选择
- [Continuity Equation](wiki/concepts/continuity-equation.md) — 粒子守恒：密度变化 = 净流入
- [ODE vs SDE](wiki/concepts/ode-vs-sde.md) — flow（确定性）vs diffusion（随机性）
- [Markov Chain](wiki/concepts/markov-chain.md) — 只看现在、不看历史；高斯版=每步一团钟形雾，扩散去噪就是它
- [闭式 KL](wiki/concepts/closed-form-kl.md) — 公式直算 vs 撒豆子估；同协方差高斯 KL 塌成均值差²(MSE)
- [Diffusion Transformer](wiki/concepts/diffusion-transformer.md) — 去噪网络从 U-Net 换成 Transformer；单流 vs 双流 MMDiT
- [MMDiT](wiki/concepts/mmdit.md) — 双流多模态扩散 Transformer: 文字图像同序列共享注意力、各用各的权重; SD3/FLUX/Qwen-Image 主干
- [像素扩散解码器](wiki/concepts/pixel-diffusion-decoder.md) — 把 latent→像素的确定性 VAE 解码器换成条件扩散; "复印机→插画师", 边解码边补细节+超分; latent 与全像素扩散两路线的缝合
- [引导蒸馏](wiki/concepts/guidance-distillation.md) — 把 CFG 的每步两遍前向蒸成一遍(引导强度当输入); FLUX dev 这么训; 与步数蒸馏正交
- [Classifier-Free Guidance](wiki/concepts/classifier-free-guidance.md) — 条件/无条件两支放大差值逼模型听话；Ideogram 的非对称变体
- [结构化 Caption 条件](wiki/concepts/structured-caption-conditioning.md) — 不喂一句话喂 JSON，把位置/颜色/文字显式做进训练
- [KL-VAE](wiki/concepts/kl-vae.md) — 把图压成 latent 的地基；扩散在压缩空间画画省 48 倍计算
- [Video VAE · Wan-VAE](wiki/concepts/video-vae.md) — VAE视频版: 3D因果卷积空间+时间一起压((1+T)→1+T/4)、只看过去帧、特征缓存做无限长1080P; MRT 用它编 region latent
- [Pixel-Space Diffusion](wiki/concepts/pixel-space-diffusion.md) — 不要 VAE，直接在原始像素上扩散；patch embedding 替掉 VAE 压缩、去掉 latent 瓶颈
- [图像质量指标 PSNR/SSIM](wiki/concepts/image-quality-metrics.md) — 重建像不像两把尺子: PSNR逐像素误差(dB)/SSIM局部结构(0-1); PSNR平移即崩→故有LPIPS
- [DMD 蒸馏 / NFE](wiki/concepts/dmd-distillation.md) — 把40步老师蒸成4步学生: 不抄轨迹只让出图分布匹配(teacher_score−fake_score=吸老师斥自己=Drifting同构); NFE=跑几次网络
- [渐进式分辨率训练](wiki/concepts/progressive-resolution-training.md) — 256P→512P→2K: 先小图便宜学构图再升大图抠细节; 类比缩略图→放大
- [Unified Transformer](wiki/concepts/unified-transformer.md) — 像素+文本+条件一条流 + 混合注意力(文本causal/生成full)；LLM 和 DiT 缝成一个
- [Perceptual Loss](wiki/concepts/perceptual-loss.md) — 不逐像素比图，在预训练网络特征空间里比；LPIPS(VGG·纹理) + DINO(自监督ViT·语义)
- [Qwen3-VL](wiki/concepts/qwen3-vl.md) — 当文本编码器用的 VLM；翻译官水平决定画师上限，取 13 个中间层
- [Forced Alignment](wiki/concepts/forced-alignment.md) — 文字已知只求每字时间(卡拉OK逐字对时间); Qwen3-ForcedAligner 填槽+NAR一次并行→不累积误差, RTF≈0.001
- [M-RoPE](wiki/concepts/mrope.md) — 位置从一个数字升级成 (时间,行,列) 三元组；bbox 布局靠它
- [QK-Norm](wiki/concepts/qk-rmsnorm.md) — 给 Q/K 做 RMSNorm 防 attention 塌成 one-hot 炸训练

### Looped / 弹性
- [Looped Transformer](wiki/concepts/looped-transformer.md) — 同一个 block 循环套 L 圈，深度上共享权重；有效深度 N×L、参数只看 N；写 for 循环不复制粘贴
- [Elastic Inference](wiki/concepts/elastic-inference.md) — 一次训练一族深度，推理按算力挑一档；旋钮做在循环圈数上，Matryoshka 同思路

### 音频 tokenization
- [Log-Mel Spectrogram](wiki/concepts/log-mel-spectrogram.md) — 音频特征基础
- [Bin Quantization](wiki/concepts/bin-quantization.md) — dMel 的核心，等距分箱量化
- [dMel](wiki/concepts/dmel.md) — log-mel 直接 bin quantize（避开 codec）

### 语音 / ASR
- [Weak Supervision at Scale](wiki/concepts/weak-supervision-at-scale.md) — 弱标注 + 量大力飞，Whisper 核心策略
- [Multitask Speech](wiki/concepts/multitask-speech.md) — 一个模型多任务，靠特殊 token 切换

### 视觉
- [Patch Embedding](wiki/concepts/patch-embedding.md) — 图切成 16×16 块, 每块拉平投影成 token, ViT 唯一的工程创新
- [Inductive Bias](wiki/concepts/inductive-bias.md) — 模型架构里的"祖传家产", 数据少时是宝大数据时是包袱
- [3D Gaussian Splatting](wiki/concepts/gaussian-splatting.md) — 场景=几百万个高斯椭球, splat投影+α混合实时渲染+任意新视角; vs NeRF快且可编辑; "高斯泼溅"LoRA是2D扩散借名模仿非真3D

### 多模态
- [Contrastive Learning](wiki/concepts/contrastive-learning.md) — 拉近正样本 + 推开负样本, in-batch negatives 白送 N²-N 个负例
- [Zero-Shot Image Classification](wiki/concepts/zero-shot-image-classification.md) — 分类变成"哪句话最配这张图", 类别由文本定义
- [Dual-Tower Architecture](wiki/concepts/dual-tower-architecture.md) — 两个独立 encoder + 末端点积; 推理可缓存, 适合检索

### Omni / 语音交互
- [Thinker–Talker](wiki/concepts/thinker-talker.md) — 想的(语义文本)和说的(渲染音频codes)分两路解耦; Talker 吃 Thinker 中间层条件
- [Multi-Token Prediction](wiki/concepts/multi-token-prediction.md) — 同帧并行预测多层 RVQ codebook, 避免 8 倍序列膨胀; 共享主体+轻量 adapter
- [Modality Projector](wiki/concepts/modality-projector.md) — 两层 MLP 把冻结编码器特征翻译进 LLM 隐空间占位符, 小投影撬动大编码器

### 强化学习 / 对齐
- [RL 直觉打底](wiki/concepts/rl-for-llm-people.md) — 给懂 LLM 不懂 RL 的人: policy/rollout/advantage/KL/loss 走势全翻译成自回归术语 (含 loss 函数走势对照图)
- [Policy Gradient](wiki/concepts/policy-gradient.md) — RL 的基础: 用 reward 当 loss 权重直接 gradient ascent, 步子大就崩
- [Clipped Surrogate Objective](wiki/concepts/clipped-surrogate-objective.md) — PPO 核心的一行 clip, 软性 trust region
- [Advantage Function](wiki/concepts/advantage-function.md) — A = Q - V, "比平均好多少" 比 raw return 信号稳得多
- [Actor-Critic](wiki/concepts/actor-critic.md) — 一个动手(actor)一个打分(critic), clip 只是 actor 那半; critic 共享 CNN 用监督回归估 V
- [GAE](wiki/concepts/gae.md) — 优势的"惊讶值加权和", γλ 相乘衰减, λ 在"稳但偏 ↔ 准但抖"间插值
- [Entropy Regularization](wiki/concepts/entropy-regularization.md) — 完整 loss 第三项, 花钱买探索防过早笃定撞死
- [RLHF](wiki/concepts/rlhf.md) — SFT → reward model → PPO 三步, 把人类排序偏好变成 LLM 训练信号
- [GSPO](wiki/concepts/gspo.md) — GRPO 后继: 重要性比率从 token 级提到序列级(每 token 只采一次→token 级是高方差噪声易崩), 稳住 MoE RL; Qwen3 用

### Agent 记忆
- [Deep Research](wiki/concepts/deep-research.md) — 派会上网的研究员: 拆问题→规划→多轮搜读→核对→带引用报告; 4 根轴(脑子/工具/规划/可信)拆任何深度研究系统
- [ReAct](wiki/concepts/react-loop.md) — 想一步→动一下→看结果, agent 用工具的最小循环; vs Planner-Executor 先规划后执行
- [Memory Stream](wiki/concepts/memory-stream.md) — 所有观察按时间存成一条流，带重要性评分
- [Agent Reflection](wiki/concepts/agent-reflection.md) — 碎片观察 → 高层认知，定期提炼
- [Retrieval Scoring](wiki/concepts/retrieval-scoring.md) — 时近度 × 重要性 × 相关性 三维排序
- [Virtual Context Management](wiki/concepts/virtual-context-management.md) — context 当 RAM，LLM 自己 function call 调度记忆
- [Action Chunking](wiki/concepts/action-chunking.md) — 看一眼预测多步动作; 慢感知喂快控制 + 更连贯少累积误差; 机器人 VLA / Lumine 通用
- [Imitation Learning](wiki/concepts/imitation-learning.md) — 行为克隆抄专家演示, 不试错不要 reward; 对照 RL; 软肋是误差累积(distribution shift)

### 共享基础设施
- [矩阵的秩 · rank](wiki/concepts/matrix-rank.md) — 一个变换"真正有几个独立旋钮"; 低秩=冗余可压(拆成两个瘦矩阵); LoRA/SVD/PCA/注意力瓶颈背后同一件事
- [特征向量 / 特征值](wiki/concepts/eigenvector.md) — 被矩阵作用后"只缩放不转向"的方向 Wv=λv; 怎么手算(特征方程 det(W−λI)=0 全程); 特征分解 W=QΛQ⁻¹; SVD 的地基
- [SVD · 奇异值分解](wiki/concepts/svd.md) — 接特征向量: 看 WᵀW 特征向量推广到任意矩阵; W=UΣVᵀ 入方向/拉伸/出方向(U≠V); σ=√特征值; 截断前r个=最佳低秩近似; PCA/压缩/LoRA 根
- [点积与投影](wiki/concepts/dot-product.md) — a·b=Σaᵢbᵢ=|a||b|cosθ, 衡量"方向多一致+多长"; 注意力分数/检索打分/矩阵乘的最小积木; 投影=影子长度
- [Softmax · 温度](wiki/concepts/softmax.md) — 一组实数压成和为1的概率(exp再归一); 可导的软argmax; 温度T调软硬(小→尖锐接近argmax/大→平); 注意力权重和采样都用
- [LoRA](wiki/concepts/lora.md) — 冻底模只训低秩小增量 ΔW=BA; 几十MB加个技能、可插拔; PEFT, 文生图社区标配
- [AI 服务器内存层级](wiki/concepts/ai-memory-hierarchy.md) — HBM/LPDDR5X-SOCAMM/DDR5/CXL/光互连 的"快但小↔慢但大"阶梯; "NVIDIA 砍内存"砍的是哪层 + 为何走向池化光互连
- [量化 · WxAy](wiki/concepts/quantization.md) — 少比特存数字; W8A8(权重激活都INT8)让矩阵乘跑INT8提速; 激活离群值靠 SmoothQuant 搬给权重
- [KV Cache](wiki/concepts/kv-cache.md) — 流式推理的内存账本
- [Prefill / Decode](wiki/concepts/prefill-decode.md) — LLM 推理两阶段
- [VAD](wiki/concepts/vad.md) — 判断用户是否说完的传统语音启发式
- [Bitter Lesson](wiki/concepts/bitter-lesson.md) — 可 scale 的学习系统长期吃掉手写规则

## Threads · 开放问题

- [Open Questions](wiki/threads/open-questions.md) — 这次 ingest 后还想搞清楚的问题清单
- [Fish Speech GRPO Determinism Question](wiki/threads/fish-speech-grpo-determinism-question.md) — RL 训练和推理 kernel 不一致时怎么处理

## Raw 源 · 已 ingest

- `raw/interaction-models-zh.html` — TML interaction models 中文讲解版
- `raw/fish-speech/` → 软链到本地 clone
