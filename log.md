# Wiki Log

按时间倒序最新在下。每条 `## [YYYY-MM-DD] <op> | <subject>`。

## [2026-05-20] init | wiki 骨架建立

照 Karpathy LLM Wiki 模式起步。schema 写在 [CLAUDE.md](./CLAUDE.md)。第一批 ingest 目标：interaction-models-zh.html + fish-speech repo。

## [2026-05-20] ingest | Thinking Machines · Interaction Models

源：`raw/interaction-models-zh.html`（中文讲解版）。写了 1 个 paper 页 + 8 个 concept 页（micro-turn / dual-model-architecture / early-fusion / flow-matching / dmel / bitwise-determinism / moe / kv-cache）+ 跨源 topic 页 [[audio-tokenization-rvq-vs-flow]] [[replace-heuristics-with-weights]]。bespoke HTML 已就位：`html/papers/interaction-models-tml.html`（直接复用 ingest 源本身的 HTML）。

## [2026-05-20] ingest | fish-speech S2 Pro

源：本地 clone 的 `README.md`（软链到 `raw/fish-speech`）。写了 1 个 paper 页 + 3 个 concept 页（dual-ar / rvq-codec / grpo）+ 1 个 prefill-decode 共享概念页。bespoke HTML **待做**。

## [2026-05-20] decision | 渲染策略定型

人面向的内容**全部 bespoke HTML**（每个主题独立静态 HTML，带自己的动画/图表）。md 只做内部 ER + scaffold。**只有 index.html 由 render.py 自动渲染**（扫 wiki/*.md frontmatter 生成目录页）。

## [2026-05-20] fix | interaction-models-tml bespoke HTML 动画修复

- `IntersectionObserver` 选择器 `'#compare figure'` / `'#micro figure'` 都返回 null（h2 不是 figure 的父节点），首句 `o.observe(null)` 抛错把后续两个 obs 也带挂 → 三张图全失去自动播放。改用 `getElementById('tb-u')?.closest('figure')` 反查容器修复
- §02 Figure 1 B 段：从两条满格 bar 改为 5 in chunk 满铺 + 4 out chunk 右移一拍。物理上对：第一拍 model 在听，从 in_1/out_0 起 user 与 model 真正并发，输出滞后一拍是 streaming 推理的自然结果
- 14 个正文 sup 引用全部从 `<span class="jr">` 改成 `<a class="jr" href="#g-NN">`，12 个 glossary item 加 id，加 `scroll-behavior: smooth` 和 `:target` 高亮 pulse 动画

## [2026-05-20] ingest | Attention Is All You Need · Transformer 始祖

Wiki 的"祖宗"paper：
- md: papers/attention-is-all-you-need.md
- 4 concept md: self-attention / multi-head-attention / positional-encoding / transformer-architecture
- bespoke HTML: docs/papers/attention-is-all-you-need.html, 1567 行
- 5 张交互图:
  - Fig 01 · RNN 串行 vs Transformer 并行 (token 一格格亮 vs 全亮 + wall-clock 对比)
  - Fig 02 · Self-attention 一步步算 (KEY 图, 4 步展开 Q→K→softmax→V)
  - Fig 03 · 4 个 head 各学不同 attention 模式 (SVG 连线)
  - Fig 04 · Positional encoding 频率指纹热力图 (20 pos × 64 dim sin/cos)
  - Fig 05 · Encoder 6 层 × Decoder 6 层 + cross-attention 连线
- 12 个 glossary 条目, 全部正文 sup 引用可跳转

## [2026-05-20] refactor | wiki nav strip 改由 render.py 注入

- 用户反馈：TML 页面没有"回 wiki"导航；fish-speech 有但是写死的 → 导航是 chrome 不是 content，该由系统层做
- render.py 新增 `inject_nav_strip()`，扫所有 bespoke 页，在 `<body>` 后注入带 `<!-- wiki-nav:start --><!-- wiki-nav:end -->` 标记的 dark 顶栏
- 幂等：strip 旧版（含 `\n*` 尾随消除）→ 注入新版（标准化单换行）。验证 3 次连跑 SHA 一致
- fish-speech 旧的硬编码 wiki-nav HTML + CSS 都删了，统一靠注入
- TML 现在也有"← 个人 wiki / index"了

## [2026-05-20] fix | TML bespoke §06.1 加 flow matching 图

用户反馈："flow matching 跟 diffusion 类似？有图更好理解"。在 §06.1 (Encoder-Free Early Fusion) 之后插入新的 §06.1·：
- Fig 04 · 5 个时间快照展示 x_t 从 noise (t=0) → target audio (t=1) 沿 ODE 解的过程
- 实际渲染了 5 条 SVG 波形, 每条用 `(1-t)·noise + t·target` 线性插值 + 固定随机种子让形状一致
- 动画顺序: t=0 显形 → arrow → t=0.25 → arrow → t=0.50 → arrow → t=0.75 → arrow → t=1.00 (绿色, target)
- 加 ODE 公式 `x_{t+Δt} = x_t + v(x_t, t)·Δt` 在底部
- 配 note.moss 解释为什么 TML 不用 RVQ —— flow matching 连续可微，端到端联训干净；RVQ 量化不可微，要走 straight-through

Bench Fig 04 → 05 顺移。

## [2026-05-20] fix | fish-speech bespoke §03 重做

- 旧 Fig 02 只画了"层数越多格子越细"，没画清残差递推机制 → 用户反馈"看不太懂"
- 重做 §03 为两个子节：
  - §03.1 **Neural Codec 全貌**（新 Fig 02）· encoder + codebook + decoder 三件套，左右两列动画演示 encode → token → decode 闭环，中间共享 codebook 高亮"最近邻"
  - §03.2 **RVQ 残差量化机制**（原 Fig 02 → 新 Fig 03）· 显式画 3 层 (input → q₁ + r₁ → q₂ + r₂ → q₃ + r₃)，每层 codebook 显式画 8 格、高亮被挑中那格、q/r 条形比例真实反映残差衰减
- 其他 figure 编号顺移：GRPO Fig 03 → 04，Bench Fig 04 → 05

## [2026-05-21] ingest | dMel · 简单 bin quantize 跟 codec 一样好

承接 TML interaction model 的输入侧。Apple 2024-07 paper。

- md: papers/dmel.md
- 2 新 concept md: bin-quantization / log-mel-spectrogram
- 旧 concept md dmel.md 升级 sources 包含本 paper
- bespoke HTML: docs/papers/dmel.html · 主色 ochre (简单战胜复杂的对比叙事)
- 4 张交互图:
  - Fig 01 · 波形 → STFT → Mel scale → log-mel 4 步 pipeline 加 1D/2D 视觉化
  - Fig 02 · KEY · Bin quantization · 6 mel channel 演示 · 连续值条形 → 16 bin 切片 → 6 个 token
  - Fig 03 · dMel vs RVQ codec · "查表" vs "训练模型" 两栏对比 · 配 6 维度 meta
  - Fig 04 · "主模型变强 · 预处理塌缩"范式 · 6 个领域早期复杂 vs 晚期简化对照表
- 12 个 glossary, skill audit 第一次跑出 6 个孤儿 (g-07~12), 已补
- Thesis: 主模型够强后预处理可以塌缩 · "baseline-first" 工程哲学 · 实证 dMel ≈ RVQ codec

## [2026-05-21] ingest | Flow Matching · 把 diffusion 简化成回归

承接 TML interaction model 的输出侧。Meta AI ICLR 2023 paper。

- md: papers/flow-matching.md
- 3 concept md: velocity-field / probability-path / ode-vs-sde
- bespoke HTML: docs/papers/flow-matching.html · 主色 deep (数学基础 / generative primer)
- 4 张交互图:
  - Fig 01 · Flow vs Diffusion · 同样 noise→data 不同路径 (ODE 直线 vs SDE 折线) · 配 panel 两栏特性对照
  - Fig 02 · KEY · 2D velocity field · 4×5 网格箭头 + 红色粒子轨迹从 noise 到 data
  - Fig 03 · OT 直线 vs 弯路 · 4-20 步 vs 50-1000 步 step marker 对比
  - Fig 04 · Flow vs Diffusion 训练步骤 · 4 步对比 (sample/interpolate/forward/loss vs sample/add-noise/forward/loss)
- 12 个 glossary, skill audit 拦截 7 个孤儿 (g-06~12) 已补
- Thesis: 把不直观的训练目标换成直观的 · TML 选 flow matching 而非 RVQ 的工程动机

## [2026-05-21] ingest | GPT-3 · 175B · ICL 浮现 · ChatGPT 时代奠基

GPT 系列收官，完成 trajectory 视角的闭环：finetune → zero-shot → few-shot ICL → product。

- md: papers/gpt-3.md
- 4 concept md: in-context-learning / emergent-abilities / sparse-attention / scaling-laws
- bespoke HTML: docs/papers/gpt-3.html · 主色 brick (GPT 系延续) + deep 强调 (历史拐点)
- 4 张交互图:
  - Fig 01 · 8 size 系列 (125M → 175B) · 175B 用 deep 色突出 · 加 GPT-1/GPT-2/BERT 历史 anchor
  - Fig 02 · KEY · ICL zero/one/few-shot · 同样英→法翻译 prompt · BLEU 22/28/32 演化
  - Fig 03 · KEY · Emergence hockey-stick · 4 个任务在 log-scale x 轴上的非线性跳跃 + 13B 拐点 band
  - Fig 04 · Chinchilla 修正 · GPT-3 1:1.7 vs Chinchilla 1:20 compute-optimal 配比
- 12 个 glossary, skill audit 第一次跑出 7 个孤儿（g-06~12），全部补好
- 重点 thesis: trajectory 视角 vs snapshot · "够好+极快"赢"最好+极慢" · GPT-3 立的 ICL 范式至今没被打破

## [2026-05-21] ingest | GPT-2 · scale 13× + WebText + zero-shot 浮现

Transformer 前向接续 3 / 3，GPT 系第二代。第一次按 study-paper-ingest
skill 走 7 步流程：

- md: papers/gpt-2.md
- 3 concept md: zero-shot-transfer / webtext / language-modeling-as-multitask
- bespoke HTML: docs/papers/gpt-2.html · 主色 brick (GPT 系延续) + ochre 强调 (hero em / TL;DR / scaling)
- 4 张交互图:
  - Fig 01 · 4 size 系列 (124M/355M/774M/1.5B) · 层数 stack + perplexity 单调下降
  - Fig 02 · KEY · Zero-shot · 4 个 prompt 实例（TL;DR / 翻译 / Q-A / Sentiment）
  - Fig 03 · WebText 4 步 pipeline · Reddit ∞ → karma≥3 45M → dedup 8M → 40GB · 配 5 个数据集 size 对比
  - Fig 04 · GPT-1 → GPT-2 演化对照表 · 绿同款 / 黄升级
- 12 个 glossary 条目, 全部正文 sup 引用入口
- 重点 thesis: "Language Models are Unsupervised Multitask Learners" + staged release 先例
- skill checklist 走完：render entries 39 / fig audit 4 / glossary audit (12/12 wired)

## [2026-05-21] ingest | GPT-1 · decoder-only · causal LM 路线起点

Transformer 前向接续 2 / 3，decoder-only 经典：
- md: papers/gpt-1.md
- 3 concept md: causal-language-model / input-transformations / decoder-only-paradigm
- bespoke HTML: docs/papers/gpt-1.html, 主色 brick (跟 BERT moss 形成两极对照)
- 4 张交互图:
  - Fig 01 · CLM 训练 · "the cat sat on the mat" 每个位置预测下一词 · 6 个 prediction 延时显形
  - Fig 02 · KEY · Causal mask · 6×6 attention matrix 对照 GPT 三角 vs BERT 全亮
  - Fig 03 · KEY · Input Transformations · 4 种任务（分类/蕴含/相似度/多选 QA）扇出
  - Fig 04 · GPT-1 vs BERT 12 维度对照表 · brick-win/moss-win 染色, 配 2026 现状结论
- 12 个 glossary 条目, sup 引用可跳转
- 强调 prompting 从 input-transformations → GPT-2 zero-shot → GPT-3 ICL → ChatGPT 一条线
- 更新 index.md 加 GPT-1 入口 + GPT 系 3 个概念分组

## [2026-05-21] revamp | ResNet · §02-05 全面重写

用户反馈"有点烂，图也有缺陷"。整体重做：

- §02 closing 加"白送 36 层 identity 思想实验"，把 degradation 是问题这点讲透
- §03 重写为"F 学的是什么"：先解释 F = H − x、为什么叫残差、配"提亮 1.05x"具体例子
- Fig 02 推倒重做：左侧 block 结构 SVG（移除原 4 步 stepper 的反向梯度叠加），右侧"梯度通过 5 个 block"双 bar 对比（plain 0.5^k 衰减 vs residual 恒为 1）
- §04 重写为"+x 两个独立的好处"：明确角度 1（梯度高速路）和角度 2（identity 免费起点）。Highway Network 只抓到一半的对照
- Fig 03 推倒重做：随机初始化下输出长什么样。Plain 输出 = 噪声 / Residual 输出 ≈ 输入。SGD 起点对比
- §05.2 bottleneck 加真实算力 math：256ch 直接 1.18M ops vs bottleneck 69K ops · 1/17 的对比
- 加 1×1 conv 廉价 + 数据库索引类比

## [2026-05-21] ingest | BERT · encoder-only · pretrain+finetune 范式

Transformer 前向接续 1 / 3，encoder-only 经典：
- md: papers/bert.md
- 4 concept md: masked-language-model / next-sentence-prediction / encoder-only-paradigm / pretrain-finetune-paradigm
- bespoke HTML: docs/papers/bert.html, 主色 moss 区别于 attention 的 brick / resnet 的 deep
- 5 张交互图:
  - Fig 01 · GPT causal 只看左 vs BERT 双向 (实例: 河岸/银行歧义)
  - Fig 02 · KEY · MLM 三步 stepper · 80/10/10 策略可视化, 真实 token "mat→[MASK], a→banana, cat→keep"
  - Fig 03 · NSP 输入构造 + segment embedding · 配 ⚠ RoBERTa 证伪 callout
  - Fig 04 · Transformer / BERT / GPT 同 block 不同砍法对比 (encoder 24 layer / decoder 12 layer / 两边都有)
  - Fig 05 · Pretrain → BERT → 4 task heads (Sentiment/NER/QA/NLI) 扇出动画
- 12 个 glossary 条目, sup 引用可跳转
- 更新 index.md 加 BERT 入口 + BERT 系 4 个概念分组

## [2026-05-21] ingest | ResNet · 残差连接起源 + Transformer sublayer 模板

Wiki 后向追溯到 Transformer 的前身：
- md: papers/resnet.md
- 3 concept md: residual-connection / degradation-problem / batchnorm
- bespoke HTML: docs/papers/resnet.html
- 6 张交互图:
  - Fig 01 · Plain net 越深越差 vs ResNet 越深越好 (CIFAR-10 训练曲线复刻)
  - Fig 02 · KEY · 残差 block 4 步分解 + 反向梯度 identity 不衰减
  - Fig 03 · Identity-as-default · Plain 学恒等 vs ResNet 学 F=0 对比
  - Fig 04 · VGG-19 / GoogLeNet / ResNet-34/50/152 五栏 stack 高度对比
  - Fig 05 · Basic block vs Bottleneck block (1×1 → 3×3 → 1×1) 参数 ~一致
  - Fig 06 · ResNet block 跟 Transformer sublayer 并排，揭示同款结构
- 12 个 glossary 条目, sup 引用可跳转
- 更新 index.md 增加 Attention/ResNet 入口和 transformer/resnet 概念分组

## [2026-05-20] deploy | GitHub Pages 接入

- `html/` 重命名 `docs/`（GH Pages 标准 source path）
- render.py 更新 HTML_OUT
- `.gitignore` 排除 `raw/fish-speech` 软链
- 仓库 `SnowWarri0r/llm-wiki` (public)
- URL: https://snowwarri0r.github.io/llm-wiki/

## [2026-05-22] lint | Claude Code 协作补强

- README / CLAUDE / render.py 顶部说明同步到当前渲染现实：papers bespoke，concept/topic/thread 自动 HTML 兜底，render.py 同时刷新 nav + wikilink
- CLAUDE.md 增加 agent guardrails：先读当前约定、补高频缺失 wikilink、改 md 后必跑 render、维护后补 log
- 补 18 个缺失概念页：hmlp / batch-invariant-kernel / split-kv / grouped-gemm-vs-gemv / nvls / sglang-inference / cross-attention / layernorm / residual-layernorm / conditional-flow-matching / optimal-transport / vad / bitter-lesson / resnet-architecture / bottleneck-block / few-shot-learning / voice-cloning-reference / inline-emotion-tags
- 补 1 个 thread 页：fish-speech-grpo-determinism-question；并把旧 slug `threads-open-questions` 改回现有的 `open-questions`

## [2026-05-22] lint | render.py 加 missing-slug gate

- CLAUDE.md "Claude Code 补强规则" 从 6 条精简到 3 条，砍掉跟工作流重复的部分（raw 只读 / 改 renderer 看 diff / 补 log）
- render.py 新增 `scan_missing_slugs()`：渲染完整 walk 所有 wiki md，发现 `[[slug]]` 没对应页面就列清单 + `sys.exit(1)`
- 把"agent 自觉补 wikilink"从规则物化成工具：下次 ingest 漏页时 render 直接拒绝通过

## [2026-05-22] ingest | 加 books/ 类别 + Psychology of Money 起步

- render.py CATEGORIES 加 books，CSS 给 books 用 brick accent；index 多一栏 §02 Books
- 下载 The Psychology of Money (Morgan Housel) PDF 到 raw/books/
- wiki/books/psychology-of-money.md：书概览 + 20 章 ToC + 整本书三条主线（经历>教育, 行为>智商, 时间>收益率）
- wiki/books/pom-ch01-no-ones-crazy.md：Ch01 pilot · ~2500 字精讲 · 加了中国版对照（房产/A股/加密）+ 套到自己 stock-trading-assistant 项目的启示
- Pilot 是为了拿格式给用户拍板；用户 OK 后继续 ch02-20

## [2026-05-24] ingest | Psychology of Money ch01 润色 + ch02 接力

ch01 润色:
- 删掉所有 stock-trading-assistant 项目 tie-in (强关联不需要), 书概览
  里同名段落也删
- 中国版反直觉例子从 3 条扩到 6 条更具代表性: 终身分红险 / e租宝-善林
  金融 / 大爷抢蛋 / 95后看花火 / 鹤岗买房 / 拼多多砍一刀
- 通篇改译文味, 多用中文口语 (上头/翻车/挂牌价/顶流爆雷/斩钉截铁)

ch02 Luck & Risk:
- 主线: Bill Gates Lakeside 一百万分之一好运 + Kent Evans 同样起点
  另一张彩票输了的对称
- Vanderbilt / Rockefeller: 运气好叫天才, 运气差叫罪犯
- 4 个不能学的极端案例: 雷军 / Tesla / 巴菲特 / 张一鸣 (用 self-serving
  bias 解释为什么"成功者方法论"复制率低)
- 6 条中国语境反直觉对照表
- 4 个自检问题 + 实操原则 "少崇拜个体, 多研究模式"

## [2026-05-25] ingest | Ch02 二轮润色 + Ch03 接力

ch02 二轮润色:
- 用户反馈"还行但不够 native", 全文再过一遍语序和措辞
- 去掉残留英文术语 (distribution/mean/mode), 改纯中文 (分布/规律/噪声)
- "一在一百万分之一"→"百万分之一"; "登山事故, 死了"→"事故, 没回来"
  等典型译文味改口语
- 节奏和断句更顺, 减"对 X 的 Y"句式

ch03 Never Enough:
- 主线: Joseph Heller "I have enough" + Rajat Gupta 已经 1 亿身家还要
  冲十亿做内幕 + Bernie Madoff 合法做市商已经很赚还搞庞氏 + LTCM 把已有
  且需要的赌掉去抢不需要的
- 4 条 lesson: 让球门停下来 / 社会比较无天花板 / "够"不是少是认清反面
  / 有些东西不论收益都不值得赌
- 7 条中国语境对照表 (大厂P9/公募加杠杆/县城首富扩张/宝能举牌万科/顶流
  主播跨界/35岁财务自由/爬藤鸡娃) 模板: 已站台阶 → 还想冲的下一阶 → 通常结局
- 5 个自检 + Vegas 庄家"进门那刻就走"类比

## [2026-05-25] ingest | Ch03 三轮润色 + Ch04 接力 + skill 加 native 规则

ch03 三轮润色:
- "让球门停下来"全部替换成"胃口别跟着饭量长 / 知道在哪喊停 / 满足线"
- 通篇再过一遍, 修掉"得到更多带来的快感"、"净满足感始终在原地"
  这种典型译文味
- "刻骨头里" → "刻进骨子里" (typo + 改 native), "什么都行" → "都一样"
- "被你想被爱的人爱着" → "被你在乎的人爱着" 等

ch04 Confounding Compounding:
- 主线: 冰川 (温和夏天累积而非寒冬) → 复利物理形态; 8+vs 8× 线性 vs
  指数思维; IBM 硬盘 70 年从 3.5MB 涨到 100TB; 巴菲特 99% 财富在 50 岁
  以后挣; Jim Simons 66% 年化但起步晚一半窗口少 75% 财富
- "Shut Up And Wait" 那本最重要但没人写的书
- 8 条中国语境复利对照: 招行茅台 / 银行存款 / 写作代码人脉健康认知
- 工龄 < 5 年的人最大 alpha 是剩下能复利的时间
- 4 个反直觉对照 + 4 个自检

## [2026-05-25] revise(ch04) + ingest(ch05) | Psychology of Money

ch04 修订:
- 用户反馈"读得像在骂我", 4 反直觉对照表过于二元 (X vs Y)
- 加第三选项 C "能让能力升级 + 速度可持续", 把表改为 A/B/C 三档,
  明确 B (位置 stable 但能力天花板低) 是看着像复利其实是 trap
- "工龄 < 5 年 alpha" 清单加第一条 "跳出舒服但能力不动的位置"

ch05 Getting Wealthy vs Staying Wealthy:
- 主线: Jesse Livermore 1929 一天赚 30 亿 / 4 年后破产自杀 + Abraham
  Germansky 同一周破产失踪 + Sequoia Moritz "我们一直害怕破产" +
  巴菲特 6 个"没做" (没加杠杆/没惊慌/没违信誉/没绑死单一策略/没用
  随时撤的钱/没卷崩)
- 致富靠进攻 vs 守富靠防守 - 两套反向技能
- 数字: 上市公司 40% 最终归零 / 福布斯 400 每 10 年换 20%
- 10 条中国语境对照 (薛蛮子 ICO / 王健林扩张 / 暴风冯鑫 / 锤子罗永浩 /
  07&15 牛市散户 / 21 年顶流基金 / 拼多多字节早期员工 all-in / 中产
  加杠杆冲二三套房 / 35 岁程序员消费升级)
- 拷到能力 / 关系 / 健康 / 事业方向, 不只是钱
- 4 自检 + "保命第一" 心法 5 条

## [2026-05-25] ingest | Ch06 Tails You Win + ch05 buffer 梯度图加进章节

ch05 微调:
- 把 chat 里给用户的 buffer 梯度图 (0/3/6/12/18/24 个月对应的自由度)
  加进 self-check #3, 后续读者直接能看到
- 顺手把 "buffer 不是死钱" (货币基金 / 期权价值) 也补进去

ch06 Tails, You Win:
- 主线: Heinz Berggruen 99% 收藏没用但 1% 是 Picasso 撑起 10 亿 + Disney
  400 部赔钱卡通后白雪公主 83 分钟救公司 + VC 21000 笔投资 0.5% 撑大部分
  回报 + Russell 3000 自 1980 涨 73 倍但 40% 成分股归零 + Sue 风雨无阻
  投赢 Jim/Tom 多 67% (1428 月里 300 月衰退期决定 67% 结果)
- 关键洞察: 顶级 dealer 玩法 = 像指数基金那样什么都买等 winners 自己出来;
  Soros 对错率不重要; 巴菲特 400-500 只票财富主要来自 10 只;
  Bezos / Hastings 主动追求更高失败率; Chris Rock 在新泽西小俱乐部磨段子
  vs Netflix 上的精修版
- 10 条中国语境 tail driven 对照 (A 股 / 公募 / VC / 影视 / 短视频 /
  网文 / 创业 / 个人职业 / 婚恋)
- 4 反直觉推论 + 4 自检 + "多上场 + 不破产 + 等" 实操心法

## [2026-05-25] ingest | Ch07 · Freedom

ch07 Freedom (整本书最直接的一章):
- 核心: 钱最高的红利不是物质, 是"我今天想干嘛干嘛"的控制感
- Angus Campbell 1981 研究: 幸福最强预测变量是"对自己生活的控制感",
  比收入/地理/教育都强
- 控制力梯度: 一点点存款→生病能请假; 几月生活费→裁员能等好 offer;
  6 月→不再害怕老板; 1-2 年→选低薪灵活工作; 真正足够→何时退休你选
- Housel 自己投行实习: 4 个月只撑 1 个月; "做爱的事但按别人节奏 =
  做你讨厌的事"
- Reactance 心理学: 哪怕原本愿意, 被推着做也会反抗
- Derek Sivers: 22 岁纽约 $12000 决定了一辈子, 卖公司没改变什么
- 1950→2019 美国家庭收入翻 2 倍, 房子大 2.5 倍, 但 2019 Gallup 45%
  美国人很焦虑 / 55% 很压力, 钱换的是物质不是时间
- Rockefeller 沉默的怪人: 思考型工作的本质; 1870 体力工→今天知识工
  的诅咒, 24/7 在脑子里上班
- Karl Pillemer 1000 个老人: 没有一个人说该按未来收入潜力选工作 /
  该跟身边人比有钱; 都说质量友谊+比自己大的事+跟孩子的非结构化时间
- 9 条中国语境 paradox (大厂 P9 / 体制内副处 / 一线婚房 / 创业 A 轮 /
  顶流直播 / 投行新人 / 大厂程序员 / 内卷家长 / 不愿辞职中年高管)
- 钱该买什么的优先级排序 (buffer > 工作节奏 > 通勤住所 > 健康 >
  家人时间 >> 物质消费)
- 4 自检 + "拒绝单变量优化"心法
- 顺手把用户自己的轨迹套到 ch07 frame (跳出舒服 + 跟 LD 不对付就跳 +
  对"够"清晰认知 + 6 月 buffer 已攒到), 用户其实已经走在这条线上

## [2026-05-25] ingest | Ch08 · Man in the Car Paradox

整本书最短最狠的一章, 篇幅匹配:
- 核心: 你以为豪车 / 名表 / 名牌包 / 大平层能让你被 admire, 真实情况
  是没人在看你这个人, 别人只在看东西然后想象自己拥有它
- Housel valet 经历: 他自己开过 Ferrari / Lambo / RR 但从不记得车主长
  什么样; 顿悟 paradox - "你看豪车不会想'开车那人真牛', 你想的是'我有
  那车多牛'"
- 推论扩展: 大平层 / 名表 / 奢侈品 / 婚礼 / 学区房, 全是同一个 paradox
- 8 条中国语境炫耀消费对照 (朋友圈晒包 / Model X / 茅台局 / 婚礼 50w /
  学区房 / 抖音晒车 / 高定西装 / 体制内"低调" 派反向)
- 反面: 想要 admiration 该靠的是谦逊 / 善意 / 共情 / 注意力, 不是钱
- 3 自检 + 跟 ch07/ch09 的连接 (ch07 钱能买什么, ch08 不能买什么, ch09
  富的人反而看不见)

skill 更新:
- study-paper-ingest 加入"中文 native 表达"硬规则, 避免每次靠用户提醒

## [2026-05-25] ingest | RoPE · Rotary Position Embedding

- wiki/papers/rope.md: paper md (Su et al. 2021, arXiv 2104.09864)
- wiki/concepts/rotary-position-embedding.md: 核心概念 (时钟指针直觉 + 多频率 + 伪代码 + 距离衰减)
- wiki/concepts/relative-position-encoding.md: 为什么相对位置 > 绝对位置 + 4 种做法对比
- wiki/concepts/positional-encoding.md: 更新 sources + 展开 RoPE bullet + 加链接
- docs/papers/rope.html: bespoke HTML, ochre accent, 5 figures:
  - Fig 01 · PE 三代 (加法→偏置→旋转 3 card grid)
  - Fig 02 · 时钟指针 (两个 SVG 钟面 + 角度差 = 相对位置)
  - Fig 03 · 多频率频谱 (低频→高频 bar + 低音鼓/高音钹类比)
  - Fig 04 · PE 方法对比 (6 方法 × 5 维度 table, RoPE highlight)
  - Fig 05 · 谁在用 RoPE (16 个 model chip grid)
  - glossary 12 条全有正文跳转 (审计通过)
  - sym-hint: 频率公式拆解 + 点积结果拆解

## [2026-05-25] ingest | Whisper · Robust Speech Recognition

- wiki/papers/whisper.md: paper md (Radford et al. 2022, arXiv 2212.04356)
- wiki/concepts/weak-supervision-at-scale.md: 弱监督核心策略 (米其林 vs 民间厨师类比)
- wiki/concepts/multitask-speech.md: 一个模型多任务, 靠 token 切换
- wiki/concepts/log-mel-spectrogram.md: 更新 sources 加 whisper
- docs/papers/whisper.html: bespoke HTML, moss accent, 4 figures:
  - Fig 01 · 数据规模对比 (960h LibriSpeech vs 680Kh Whisper, 700×)
  - Fig 02 · 架构 (音频→log-mel→encoder→decoder→文本 flow)
  - Fig 03 · 多任务 (4 task cards: 转录/翻译/语言识别/时间戳)
  - Fig 04 · 模型尺寸 (Tiny 39M → Large 1550M table)
  - glossary 12 条全有跳转
- 历史定位: 语音领域的 GPT 时刻 + Whisper encoder 成为语音 foundation model

## [2026-05-28] ingest | ViT · An Image is Worth 16×16 Words

- wiki/papers/vit.md: paper md (Dosovitskiy et al. 2021, arXiv 2010.11929)
- wiki/concepts/patch-embedding.md: 把图切成 token 的核心操作 (NLP token embedding 完全同构)
- wiki/concepts/inductive-bias.md: CNN 的祖传家产 vs ViT 的"无知"; 老员工 vs 新员工类比
- wiki/concepts/self-attention.md / positional-encoding.md / scaling-laws.md / bitter-lesson.md: 更新 sources 加 vit
- docs/papers/vit.html: bespoke HTML, moss accent, 5 figures:
  - Fig 01 · 完整 pipeline (image → 7×7 patch grid → 196 tokens + cls → Transformer → 分类头), 动画 stagger 50 patch cells
  - Fig 02 · 单个 patch 怎么变 token (slice → flatten → linear projection 三步), 切线动画 + patch 浮起 + 投影箭头
  - Fig 03 · CNN 归纳偏置 vs ViT (3×3 表格: 局部性/平移不变/层次结构)
  - Fig 04 · 数据量决定胜负 (ResNet vs ViT 曲线交叉于 ImageNet-21k, JFT-300M ViT 反超), 曲线 stroke-dasharray 动画
  - Fig 05 · 注意力的自然层次 (浅层 Layer1 局部 / 中层 6 混合 / 深层 12 全局), 3 个 SVG attention dot pattern
  - glossary 11 条全有正文跳转 (审计通过)
- 历史定位: ViT 真正的影响力不在分类准确率, 而在 (1) 跨模态架构统一 (CLIP/DALL-E/GPT-4V 全靠它) (2) CNN 时代结束 (3) 视觉吃 scaling law

## [2026-05-28] ingest | CLIP · Learning Transferable Visual Models

- wiki/papers/clip.md: paper md (Radford et al. 2021, arXiv 2103.00020, OpenAI)
- wiki/concepts/contrastive-learning.md: 拉近正样本推开负样本, in-batch negatives, batch 越大学得越细
- wiki/concepts/zero-shot-image-classification.md: 分类变图文匹配, prompt engineering 来到视觉
- wiki/concepts/dual-tower-architecture.md: 双塔末端对齐 + 推理可缓存, vs single-tower 表达力对比
- wiki/concepts/patch-embedding.md / scaling-laws.md / bitter-lesson.md: 更新 sources 加 clip
- docs/papers/clip.html: bespoke HTML, ochre accent, 5 figures:
  - Fig 01 · Dual-tower 架构 (image encoder + text encoder + 末端点积), 6 阶段错峰浮现
  - Fig 02 · 对比学习矩阵 (5×5 batch + 对角线高亮 +1 / 其余 -1), brick stroke 对角线 highlight
  - Fig 03 · 数据规模 ImageNet 1.3M vs WIT 400M (300× 倍数), scaleX 动画
  - Fig 04 · Zero-shot 分类 (1 个图 + 5 候选 caption, bar 显示相似度 0.95/0.20/0.08/0.15/0.12, 最高 winner 加 brick 边框)
  - Fig 05 · CLIP 下游 (中心 CLIP + 7 个应用扇出: DALL-E / SD / LLaVA / Open-vocab 检测 / 数据筛选 / 图文搜索 / 视频机器人), 箭头 stroke-dash + 节点 scale 弹出
  - glossary 12 条全有正文跳转 (审计通过)
- 历史定位: 视觉的 GPT-3 时刻; GPT-3 跟 CLIP 共享 OpenAI "弱监督 + 大数据 + 大模型 = 通用表征" 哲学

## [2026-05-28] ingest | PPO · Proximal Policy Optimization

- wiki/papers/ppo.md: paper md (Schulman et al. 2017, arXiv 1707.06347, OpenAI)
- wiki/concepts/policy-gradient.md: RL 基础, 用 reward 当 loss 权重 gradient ascent; 步子大就崩
- wiki/concepts/clipped-surrogate-objective.md: PPO 核心 clip(r, 1-ε, 1+ε); A>0 和 A<0 两种情况都切平梯度
- wiki/concepts/advantage-function.md: A = Q-V, 跟基线比不看绝对值; reward 偏移不变性; actor-critic + GAE
- wiki/concepts/rlhf.md: SFT → reward model → PPO 三步; KL penalty 防 reward hacking
- wiki/concepts/grpo.md: 更新 sources 加 ppo
- docs/papers/ppo.html: bespoke HTML, brick accent, 5 figures:
  - Fig 01 · agent ↔ environment 循环 (内含 policy/value 子盒, 抽象游戏场景, 顶部 action 箭头 / 底部 state+reward 箭头)
  - Fig 02 · 步子大就崩 (左 panel 小步 OK / 右 panel 大步 π_new 跑飞, 同 π_old 曲线对比)
  - Fig 03 · PPO 的 clipped objective (左 A>0 右 A<0 两 panel; 显示 unclipped dashed + clipped 实线 + clip region 高亮)
  - Fig 04 · PPO 训练循环 (collect → compute advantage → K-epoch update + dashed loopback 显示数据重用)
  - Fig 05 · RLHF 三步流程 (SFT box → Reward Model box → PPO box; 每个 box 详细标 input/loss/output)
  - glossary 12 条全有正文跳转 (审计通过)
- 历史定位: PPO 自身是 2017 RL breakthrough, 但最大遗产是 2022 RLHF (InstructGPT/ChatGPT); 跟 GRPO/DPO 是接力, 不是冲突
- 工程哲学: clip 是 "粗暴近似打败精确解" 的标杆案例, mirror Adam/SGD 跟 Bayesian DL/MC dropout 的同类规律

## [2026-05-29] query | RL 直觉打底 (用户反馈 PPO 页太进阶)

- 触发: 用户看 PPO 页云里雾里 —— rollout↔分布耦合、指标图怎么增加 reward、KL(LLM‖SFT)、cross-entropy/各 loss 走势都没概念
- 根因: PPO/RLHF 页默认已有 RL 脑回路, 缺一块打底
- wiki/concepts/rl-for-llm-people.md (新): 用 LLM 自回归把 RL 术语全翻译 —— §0 LLM 就是 policy (state/action/π 对号入座表) / §1 rollout 与数据过期 / §2 advantage→clip→海量样本平均才"涨 reward" / §3 KL=拴 SFT 的橡皮筋 / §4 loss 走势内联静态三联 SVG (cross-entropy / -logπ·R 加权 / KL 两分布重合 vs 分叉)
- SVG 自包含 (hex 色 + inline 属性, 无 class 无动画), 验证 python-markdown 块级 HTML 原样透传 → concept 页也能带图
- docs/papers/ppo.html: TL;DR 下加 "先打底" note 链到该页
- 回链: policy-gradient / advantage-function / clipped-surrogate-objective / rlhf / grpo 链接段都加 [[rl-for-llm-people]]
- index.md: 强化学习/对齐 段置顶该页

## [2026-05-31] query | RM ≠ critic (用户问 GRPO 是不是也要训 RM)

- 触发: 用户问"GRPO 不也得训奖励模型吗, 跟 PPO 区别不大吧" —— 把 reward model 和 critic 搞混
- 澄清: GRPO 砍的是 critic (value 网络 V(s), 跟 policy 同样大), 不是 RM; RM 是 RLHF 上游, PPO/GRPO 共用, 不是区分点
- wiki/concepts/grpo.md: 加 "RM ≠ critic" 段 —— RM/critic 对照表 + 静态对比图 (PPO 半边 critic 高亮"GRPO 砍的就是它" vs GRPO 半边组内 mean/std 占位) + "你以为/其实" 澄清; advantage 算法对比 A=r−V(s) vs A=(rᵢ−均值)/std
- 关键点: GRPO = 省了 critic 的 PPO 变体, loss 还是 clip+KL 几乎没变; reasoning 场景 GRPO 常用规则 reward 连 RM 都不训
- updated 28→31

## [2026-06-01] ingest | Go GC · 从 mark-sweep 到 Green Tea (首个非 ML / systems 页)

- 触发: 用户聊到 Go 1.26 的 Green Tea GC, 让做成 HTML; 选定"完整 Go GC 故事 + bespoke 精装页"
- 先 WebFetch 核实: 官方 go.dev/blog/greenteagc + go1.26 notes —— 1.26 默认开 (1.25 实验), GC overhead 降 10–40%, Ice Lake/Zen 4+ 用 AVX-512 GFNI(VGF2P8AFFINEQB)再 ~10%, 关闭 GOEXPERIMENT=nogreenteagc; mark ≥35% 时间 stall 等内存; 工作单元 page(8KiB) 非 object; seen/scanned bitmap; FIFO 非 LIFO
- wiki/papers/go-gc.md: scaffold (非 ML, source=greenteagc blog)
- docs/papers/go-gc.html: bespoke, **deep 蓝 accent** (基础设施色), 5 figures:
  - Fig 01 · 三色标记 (白/灰/黑图例 + roots 推进的灰色前线 + 不可达白簇被回收 + 三色不变式)
  - Fig 02 · write barrier (左没 barrier: B.ptr=W 制造黑→白 + 删 G→W → W 漏标误删 ✗ / 右有 barrier: 写时染灰 W → 存活 ✓)
  - Fig 03 · GC pacing 锯齿 (live 基线 / GOGC=100 触发线 2× / GOMEMLIMIT 天花板 → 逼近时锯齿变密)
  - Fig 04 · graph flood vs Green Tea (左跨页乱跳红线"≥35% stall" / 右逐页 L→R 顺序扫; 城市街道 vs 高速类比) ← 主图
  - Fig 05 · 一页怎么扫 (8KiB page + seen/scanned bitmap + FIFO 攒批 + AVX-512 整页 2 寄存器)
  - glossary 12 条全闭环 (审计通过)
- 工程落点: 纯 locality 优化不改代码, GC CPU% 掉; JSON 重/小对象 churn 大的服务值得量前后; 反直觉"扫一页 2% 就比 graph flood 快" → locality 本身才是赢点
- 形态决策: 非 ML 系统页也走 docs/papers/ bespoke; 暂不抽 concept 页 (island, 避免孤儿), 术语全收 glossary

## [2026-06-03] ingest | 康波周期 · 经济的四季 (理财/决策线, 有争议框架)

- 触发: 用户要做康波周期 + 缠论两页; 先做康波
- 先 WebSearch/WebFetch 核实: Kondratiev 1920s 长波, Schumpeter 技术革命归因; 五次浪潮 Perez 定年 1771/1829/1875/1908/1971; A相扩张/B相收缩; 主流(新古典)多不认, "概念硬套统计数据", 定年成因无共识; 周金涛"人生发财靠康波"本土化
- wiki/papers/kondratiev-wave.md + docs/papers/kondratiev-wave.html: bespoke, **ochre 金 accent**, 5 figures:
  - Fig 01 · 长波与四季 (正弦曲线 stroke draw 动画 + 四季底色带 + 繁荣顶/萧条底 + A/B相)
  - Fig 02 · 五次技术浪潮 (timeline 5 humps + 年份技术 + 第六波 AI 虚线)
  - Fig 03 · 四季资产轮动 (十字四象限钟: 回升→股/繁荣→商品/衰退→债/萧条→现金黄金 + 顺时针箭头)
  - Fig 04 · 多周期嵌套 (基钦3-4y/朱格拉7-11y/库兹涅茨15-25y/康波50-60y 四条 + 叠加=实际)
  - Fig 05 · 一生 vs 一个康波 (康波曲线 + A顺风/B逆风 两人黄金期落不同段)
  - glossary 12 闭环
- 诚实标争议: 顶部 warn 块 + §06 整节讲"罗盘不是钟表"; 跟 Psychology of Money "behavior>择时" 对照, 链到 psychology-of-money.html
- 隐私: 全程只讲理论, 无个人持仓/工作语境; commit 前隐私 grep 干净 (吸取 go-gc 教训)

## [2026-06-03] ingest | 缠论 · 把走势拆成可数的结构 (技术分析, brick accent)

- 接康波之后第二页; 先 WebSearch 核准定义: 形态学(分型/笔/线段/中枢)+动力学(背驰/级别); 中枢=连续三个次级别走势重叠区间[ZD,ZG]; 三类买卖点(1买跌破中枢后背驰/2买回调不破前低/3买突破中枢回测不进); 走势终完美; 李彪《教你炒股票108课》2006-2008
- wiki/papers/chan-theory.md + docs/papers/chan-theory.html: bespoke, **brick 红 accent**, 5 figures:
  - Fig 01 · 分型 (顶分型/底分型 各 3 根 K线, 中间最高/最低 + 包含处理)
  - Fig 02 · 笔→线段 (折线分型点 底/顶 + 5 笔 + 线段 bracket ≥3笔)
  - Fig 03 · 中枢 (三段次级别走势 + ZG上沿/ZD下沿重叠带 box)
  - Fig 04 · 级别嵌套 (30分→5分→1分 自相似放大, 小级别一整段=大级别一笔)
  - Fig 05 · 三类买卖点 (价格路径 + 中枢 box + 1买背驰底/2买回调不破/3买突破回测不进)
  - glossary 12 闭环
- 诚实标争议: 顶部 warn + §07 整节 "自洽≠有效, 事后总对, 划分主观, 无实证超额收益"; 两个 note 串康波(坐标系不是预言机) + psychology-of-money(behavior>预测)
- 隐私 grep 干净 (内部服务名/个人持仓/做T 全无)

## [2026-06-03] ingest | 盐铁论 + 净利润断层 (史 + 交易, 一批两页)

- 盐铁论 (deep 蓝): 前81年盐铁会议 WebSearch 核准(霍光召集/桑弘羊vs贤良文学60余/盐铁均输平准酒榷/历时5月/仅罢酒榷+关内铁官/桓宽辑). 5 figs: 会议两方对坐 / 桑弘羊财政机器四件套→国库→边防 / 富国强兵vs藏富于民两栏 / 均输平准国家做总批发商 / 两千年回声timeline(盐铁论→王安石→计划经济→国进民退). 呈现两边各有理, trade-off 非对错.
- 净利润断层 (moss 绿): WebSearch 核准(两要素=净利润惊喜+断层跳空; 本质 PEAD/Ball&Brown 1968; SUE; 缺口回补证伪; 业绩预告抢跑衰减). 5 figs: 跳空缺口K线 / 惊喜 AND 断层 / PEAD漂移曲线 / 缺口守住vs回补 / 有效vs衰减两栏. 顶部 warn: 有学术底子但会拥挤失效, 非必胜.
- 两页 glossary 各 12 闭环; 串到 kondratiev/chan/psychology-of-money(框架管纪律不保证必胜)
- 隐私 grep 干净 (这次每页 commit 前都跑)

## [2026-06-03] feature | index 加领域分类 + 搜索

- 触发: 内容多了(126 条目), papers 里 ML/系统/金融/史 混一起, 需要分类+搜索
- render.py:
  - 支持 frontmatter `tags: [系统/金融/史/...]` 领域标签; 无 tags 时按 category 推断(books→理财, 其余→ML)
  - entry_search_text(): 抽 标题+hook+slug+领域 + 从渲染后 HTML 抽 h2/h3 章节标题 + glossary 术语(class="term") → data-s 索引
  - 每卡片加 data-domains + data-s; 每段包 cat-block 便于整段隐藏; 领域 pill
  - index 顶部: 搜索框 + 领域 chip(全部/ML/系统/金融/史/理财, 带计数) + 无结果提示
  - 纯前端 JS: 输入实时 substring 过滤 + chip 领域过滤, 组合生效, 空段自动隐藏
- 5 个非 ML 页加 tags: go-gc[系统] / kondratiev-wave·chan-theory·net-profit-gap[金融] / discourses-salt-iron[史]
- 验证: 搜"均输"→盐铁论、"multi-head"→attention(只在glossary的词也能命中); 领域分布 ML99/理财22/金融3/系统1/史1=126

## [2026-06-04] ingest | 资金面 · 量能与共识 (资金量能+资金共识合一页)

- 用户先前分开提"资金量能"+"资金共识", 经确认合成一页(一体两面: 量能=燃料, 共识=方向)
- WebSearch 核准游资框架: 分歧转一致(分歧日爆量/一致日缩量封板, 仅龙头+板块逻辑)、筹码集中度、抱团、量价关系(放量/缩量×涨/跌)、量在价先
- wiki/papers/capital-flow.md + docs/papers/capital-flow.html: bespoke, **deep 蓝 accent**, tags:[金融], 5 figures:
  - Fig 01 · 量价四象限 (放量涨/放量跌/缩量涨/缩量跌 各含义)
  - Fig 02 · 量价配合 vs 顶背离 (价量齐升 / 价新高量萎缩; 量柱递增vs递减)
  - Fig 03 · 分歧转一致 (分歧日爆量震荡K线 → 一致日缩量封板)
  - Fig 04 · 筹码集中 vs 分散 (资金扎堆龙头 vs 撒胡椒面)
  - Fig 05 · 量能×共识 二维四象限 (主升浪/缩量推升/分歧博弈/无人问津)
  - 修了 Fig 05 defs 在 svg 外的 bug
- 顶部 warn + §07: 经验派、高度主观、易事后解释、无学术实证、生态随量化监管变
- 串点: 量价背离=缠论背驰=净利润断层缺口回补, 三套语言同一问题"价格还有没有资金跟"; 链 kondratiev/chan/net-profit-gap/psychology-of-money
- glossary 12 闭环; 隐私 grep 干净

## [2026-06-04] ingest | Ideogram 4.0 · 9.3B 单流 DiT (文生图开源权重)

- 用户要做 Ideogram 4.0 (2026-06-03 开源). WebFetch 博客 403(Cloudflare 挡数据中心 IP), 改用 Claude-in-Chrome 开 ideogram.ai/blog/ideogram-4.0 读全文 + gh 拉 github README 核准架构
- 核准: 9.3B 单流 DiT 34层(文本+图像 token 一序列共享投影, vs SD3/FLUX 双流 MMDiT); 文本编码器 Qwen3-VL-8B 取13中间层 concat; flow matching + 非对称 CFG(无条件支整 drop 文本); frozen KL-VAE 8×; 只用结构化 JSON caption 训练(color_palette 16色/bbox 0-1000归一/文字元素); 2K 原生; emb4608/18头/SwiGLU12288/MRoPE; 文本渲染碾压 Qwen20B/FLUX32B/Hunyuan80B, 设计ELO #2全开源#1
- wiki/papers/ideogram-4.md + docs/papers/ideogram-4.html: bespoke, **brick accent**, ML 领域, 5 figures:
  - Fig 01 · pipeline (Qwen3-VL frozen → 单流DiT trained → Euler flow+非对称CFG → KL-VAE frozen) + spec 表
  - Fig 02 · 单流 vs 双流 (共享投影一序列 vs MMDiT 两套投影)
  - Fig 03 · VLM 文本编码器 (Qwen3-VL 取13层 concat, 对比单层/无)
  - Fig 04 · 结构化 JSON caption (JSON→画布 bbox+调色板+文字)
  - Fig 05 · 参数效率散点 (9.3B 文本渲染占左上, 打赢 20/32/80B)
  - glossary 12 闭环
- 3 新 concept: diffusion-transformer / classifier-free-guidance / structured-caption-conditioning; flow-matching concept sources 加 ideogram-4
- 主线呼应: 9.3B>80B 印证 dMel/Whisper/fish-speech "监督形态>堆参数"; JSON caption = 把结构做进训练
- 隐私 grep 干净

## [2026-06-04] ingest | 爱在冰川 · 低吸待涨的道法术 (从复盘合集提炼)

- 用户下了 ~3000 PDF (2017-2026 公开论坛/公众号复盘+战法) 在 Downloads; 确认是公开发布、可写; 放公开 wiki
- 通读策略: 3000 篇没法逐篇, 抽 29 篇成体系系列帖(道/术/法/潜伏/低吸/短线客) pypdf 抽文本精读, 砍评论区噪声; 每日复盘原则会在系列里重复
- wiki/papers/aizai-bingchuan.md + docs/papers/aizai-bingchuan.html: bespoke, **ochre accent**(交易子簇里未被纯交易页用过的色), tags:[金融], 5 figures:
  - Fig 01 · 道法术金字塔 (模式心法→战法→技术)
  - Fig 02 · 低吸待涨循环 (复盘找逻辑→开盘买→次日了结/持/割, 复利循环)
  - Fig 03 · 低吸 vs 追高 vs 打板 (分时+均价线, 打板跟最激进的人一起反而安全)
  - Fig 04 · 横盘龙头低吸 (一字断档→分歧震荡→空转多→二波; 一致→分歧→再一致)
  - Fig 05 · 情绪周期(沸点续沸/冰点续冰) + 涨停板复盘四看
  - glossary 12 闭环
- 版权处理: 用自己的话复述, **原文/PDF 不入库** (确认无 pdf 进 git); warn + §07 标经验派/散户难复制/幸存者偏差/时代变, 反复带"非荐股"
- 串点: 一致→分歧→再一致 = 资金面分歧转一致 = 缠论中枢震荡; "模式越做越简单/用规则替盘感" 呼应 psychology-of-money behavior>预测
- 隐私 grep 干净(不与用户个人持仓/做T 混淆)

## [2026-06-04] ingest | 缠论深入两篇 · 动力学 + 操作 (主篇只够入门地图)

- 用户觉得缠论一篇不够; 确认补两篇(动力学+操作). WebSearch 核准: 标准背驰 a+A+b+B+c(c段MACD面积<a段)、区间套(c段内套次级别背驰精确定位)、背驰-买卖点定理、走势类型定理(趋势≥2中枢/盘整1中枢)、同级别分解
- chan-theory-dynamics.html (brick, 金融): 背驰结构a+A+b+B+c / MACD面积比较 / 趋势vs盘整背驰 / 区间套 / 背驰↔买卖点定理+三类买卖点级别嵌套. glossary 12 闭环
- chan-theory-operation.html (brick, 金融): 走势类型定理 / 同级别分解 / 中枢震荡操作 / 走势多义性(同图两解相反操作) / 只做当下闭环. glossary 11 闭环
- 主篇 chan-theory.html 加"缠论三篇"串联 note; 三篇 md 互链; seriesnav 在两深入页 hero
- 诚实: 两篇都带 note/争议(MACD面积主观/背驰钝化/级别选择主观/走势终完美不可证伪)
- 串点: 背驰=资金面量价背离; 只做当下=爱在冰川"按规则不预测"
- 隐私 grep 干净

## [2026-06-05] ingest | ideogram-4 前置概念补全
- 新增 4 概念页：kl-vae / qwen3-vl / mrope / qk-rmsnorm（Ideogram 4 读不懂的前置零件）
- 修 ideogram-4.md `[[rope]]` 死链 → 拆成 [[mrope]]（实际 rope 页是 rotary-position-embedding）
- 关键概念段补 4 链接 + 正文 Qwen3-VL/MRoPE 加 wikilink

## [2026-06-05] ingest | next-token-forward-pass 概念页
- 端到端走一遍前向：token→embedding→QKV→注意力softmax→堆N层→末位向量→LM head(撞词表)→输出softmax→挑token
- 核心拆"两个softmax不是一回事"(位置 vs 词表)；"匹配token"=向量相似度点积；weight tying
- 从 training-vs-inference topic 链入；顺手修该 topic 的 [[rope]] 死链

## [2026-06-05] lint/expand | transformer-architecture 加"深度 vs 多头"节
- 补"两个容易混的层数"：堆N层(竖/顺序接力) vs 多头(横/一层内并行concat) + 对比配图
- next-token-forward-pass ④ 处加引流注解

## [2026-06-05] expand | cross-attention 动画图 (动画试点)
- 加自带动画 SVG (SMIL, 不依赖页面 JS): Q decoder→比对K→猫命中→V抄回→解出cat 循环
- 概念页动画方案确立: SMIL <animate>/<animateTransform> 内联, render.py 原样放行

## [2026-06-05] infra | 概念页动画 harness (对齐 bespoke 质感)
- render.py: CSS 加 .reveal/.draw/.pulse + figPulse + prefers-reduced-motion; CONCEPT_PAGE_TEMPLATE 注入 IntersectionObserver(滚动进视口加.play, 播一次)
- cross-attention 重做: 循环SMIL → 滚动触发/描线/分阶段揭示 (Q比对K描线→猫pulse→V弧线抄回→=cat)
- 后续静态图可按需用同 class 升级

## [2026-06-05] expand | kl-vae + 前向链路 升级动画
- kl-vae 死区图: 孤岛reveal→游走线draw→死区reveal; 右N(0,1)reveal→点云reveal→有效线draw
- 前向链路图: 6盒子分阶段揭示组(d1-d6); LM head匹配图: 概率条 grow-x 从左生长错峰
- render.py 加 .grow-x (transform-box:fill-box 横向生长) + reduced-motion 兜底

## [2026-06-08] expand | ideogram-4 加 §05 训练/推理(非自回归)
- bespoke 页插 §05"为什么不是自回归" + Fig 04 AR-vs-扩散对比图(ig-rev 动画, fig-paradigm 入 observer)
- JSON→§06/Fig05, 结果→§07/Fig06 顺延; md scaffold 补"非自回归"bullet
- 核心: AR循环在位置(causal/串行) vs 扩散循环在去噪步(并行/无mask); 训练 flow-matching MSE 非 cross-entropy

## [2026-06-08] ingest | minimind-o (bespoke 精装页)
- 源: github.com/jingyaogong/minimind-o (~0.1B 端到端 Omni, arXiv 2605.03937)
- bespoke 页 docs/papers/minimind-o.html: moss accent, hero+§01-06+5张 mo-rev 动画图(IO总览/Thinker-Talker bridge/projector/MTP 8层codes/训练管线) + jr术语表12条
- 新概念: thinker-talker / multi-token-prediction / modality-projector; 复用 rvq-codec/vad/voice-cloning-reference/early-fusion/moe
- 主线: fish-speech 麻雀版; 瓶颈在多码本输出端 + 条件取中间层

## [2026-06-08] fix/expand | MTP 页纠正"并行=丢依赖" + 加阶梯图
- 用户(fish-speech背景)指出 fish 帧内串行 vs MTP 并行的矛盾 → MTP 实为 delay pattern 阶梯并行
- MTP 页加 delay pattern 阶梯 SVG(对角线=帧f0残差链, 列=不同帧并行) + 三档对比表(裸并行/阶梯/fish串行)
- 纠正口径: 依赖非丢, 沿对角线保住; minimind-o §04 + g-06 同步

## [2026-06-08] expand | MTP 页补"共享主体+adapter=每层LoRA"(读真源码)
- 从 model_omni.py:57-76 读 TalkerHead/TalkerEmbedding: base全尺寸 + 每层 rank=256 低秩adapter, 输出 base+adapter, 输入 8层均值
- 补 LoRA 类比(用户做过LoRA) + 省参表 + bridge融合(model_omni.py:301 可学scale)

## [2026-06-09] ingest | cnn (bespoke 精装页)
- bespoke 页 docs/papers/cnn.html: deep accent, hero+§01-05+5图 + jr术语表10条
- §01 卷积滑窗用 CSS keyframe(cnSlide) 滚动触发一次性滑遍9位置, 输入核+输出格同步高亮
- 新概念: convolution / pooling / receptive-field; 链 inductive-bias/patch-embedding/resnet/vit/self-attention
- 主线: CNN(先验) vs Transformer(通用); 感受野靠深度撑 vs 注意力一层即全局

## [2026-06-09] expand | ppo 补"另一半" + 3 新概念页
- ppo.html 加 4 节 4 图(§05-08): actor-critic 双头+优势回路 / GAE γλ 衰减柱+λ谱 / 完整三项 loss 合流 / 训练翻车vs健康双曲线; 原 RLHF/遗产/改变重编号 §09-11; glossary 补 g-13~g-18
- 新概念: actor-critic / gae / entropy-regularization; 修 advantage-function 的 loss 补熵第三项
- 动机: 原文偏科"PPO=clip", 补回 critic 怎么训(回归)/GAE 深度直觉/熵正则/三项 loss/训练实战体感(loss不代表进度·explained_variance·奖励归一化·并行env·det vs stochastic)

## [2026-06-10] ingest | elt (bespoke 精装页)
- 源: arXiv 2604.09168 ELT Elastic Looped Transformers for Visual Generation (Goyal/Kusupati 等)
- bespoke 页 docs/papers/elt.html: ochre accent, hero+§01-04+4图(循环展开/elastic Pareto/ILSD/谱系) + jr术语表9条
- 新概念: looped-transformer / elastic-inference; 链 convolution(权重共享)/diffusion-transformer/kl-vae/ideogram-4
- 核心: 循环=深度共享权重(N层×L圈, 有效深度N×L 参数看N), 一族深度弹性, ILSD; 4× 参数缩减 FID2.0/FVD72.8

## [2026-06-10] expand | looped-transformer 直觉三层 + ILSD 详写
- looped-transformer 直觉: "for循环类比"展开成3层(省参数不省算力/逼权重共享=偏置/圈数可调=弹性根)
- elastic-inference ILSD: 从bullet改成一步训练详流程(随机L_int + teacher/student + 三loss表 + stop-grad为何) + 单调精修器收口
- elt §03 prose 同步补三loss说明

## [2026-06-10] ingest | hidream-o1 (bespoke 精装页)
- 源: arXiv 2605.11061 HiDream-O1-Image Pixel-level Unified Transformer (HiDream.ai)
- bespoke 页 docs/papers/hidream-o1.html: plum 新配色, hero+§01-05+4图(UiT总览/像素vs latent/混合注意力mask矩阵/推理agent) + jr术语表8条
- 新概念: pixel-space-diffusion / unified-transformer; 链 kl-vae(反着用)/qwen3-vl/flow-matching/grpo/ideogram-4
- 核心: 无VAE像素扩散(patch embed替VAE) + 文本编码器收进主干(Qwen3-VL backbone) + 混合注意力(文本causal/生成full) + O1推理agent

## [2026-06-10] fix/expand | hidream perceptual 理由纠错 + 建 perceptual-loss 页
- 用户指出 perceptual 没介绍 + 我把"为什么用"写错(写成防L2糊, 论文原话是补长程语义连贯)
- 核实原文(grep arxiv html): "flow matching loss + perceptual supervision (LPIPS + perceptual DINO loss)" 确在; 理由是 pixel扩散细节够但语义连贯弱
- 改正 pixel-space-diffusion + hidream §02/§05/g-05 的理由; 新建 perceptual-loss 概念页(LPIPS=VGG纹理/DINO=自监督ViT语义)

## [2026-06-10] ingest | dino + lpips (两个 bespoke 精装页)
- 应用户"这两个可以各做一章"，把 perceptual-loss 里 LPIPS/DINO 拆成各自 bespoke 页
- dino.html (deep): 自蒸馏+EMA teacher / multi-crop / centering-sharpening 防坍缩 / 涌现; 3图; 链 elt ILSD 自蒸馏
- lpips.html (moss): 像素L2烂 / 多层特征+学权重 / 2AFC人类校准 / unreasonable effectiveness; 3图
- perceptual-loss 退成总览, LPIPS/DINO 子节改成指针; 新 paper md scaffold ×2

## [2026-06-11] add/fix | cross-entropy 概念页 + DINO 箭头/§04 公式
- 新建 cross-entropy 概念页(−log曲线图 + 两分布/one-hot vs软标签 + 交叉熵=熵+KL); index + dino backlink
- 修 DINO Fig02 multi-crop: 局部/全局→student 箭头原落在框上方空白(y=135 vs 框y=150), 改成扎进框
- DINO §04 加 centering/sharpening 具体公式: softmax((g−c)/τ_t), c=EMA滑动均值, sharpen=小温度

## [2026-06-11] add | ema 概念页 + adam bespoke 精装页 + fix lpips 2AFC 遮挡
- ema 概念页(一行更新 + 指数衰减 + 抖动信号vs平滑EMA图); 被 dino/batchnorm/adam 引用
- adam bespoke(brick): SGD窄沟抖→动量(一阶EMA)→RMSprop(二阶EMA除√v)→Adam合体+bias correction; 4图; arXiv 1412.6980
- 主线: Adam=EMA两连击(滚梯度/滚梯度平方); 接 dino/batchnorm 同款EMA
- fix lpips Fig03: 绿箭头压住"哪个更像参考?"文字 → 改单箭头穿过、问题文字浮上方

## [2026-06-12] add | fft bespoke 精装页（新 teal accent）
- fft bespoke(teal #1a6a64): 棱镜拆频率→绕线机测频率→偶奇分治树 N²→NlogN→蝴蝶+twiddle→卷积定理; 5 图全本地 headless 验证; Cooley-Tukey 1965
- 主线: 分治(折半再合,同卷积/归并) + 单位根对称(转半圈反号→一次乘喂两输出); 接 convolution(卷积定理) + log-mel-spectrogram(STFT)
- 回链: convolution / log-mel-spectrogram 加 fft source + 链接; index papers 段置顶(基础算法)

## [2026-06-12] add | ode-sde bespoke 精装页（新 iris 靛紫 accent）
- ode-sde bespoke(iris #4a3f9e): 风场弹珠(ODE确定)→醉汉多路(SDE随机)→桥(SDE个体 vs ODE密度水流,Song2021同分布)→Euler 真数字演算→一句话收口; 4 图全本地 headless 验证
- 数值节按用户要求重举例: f(x)=−x/dt=0.5/g=2/起点10, ODE永远10→5; SDE跑A=6.13 跑B=3.30; √dt 解释随机游走按√时间扩散
- 与已有 concept ode-vs-sde 分工: bespoke=底层+数值, concept=FM-vs-diffusion 工程取舍; 互链
- 回链: ode-vs-sde / score-function 加 ode-sde source + 链接; index 接 flow-matching 后

## [2026-06-12] fix | fft §04 实现细节去抽象化（N=8 真例子）
- 用户反馈"两个实现小坑"三条全是结论太抽象; 改成"三个实现细节·拿 N=8 砸实"
- ① radix-2: 8→4→2→1 vs 6 折到 3 卡住; zero-pad/mixed-radix/Bluestein 三出路
- ② bit-reversal: 列 0-7 位翻转表(1=001→100=4...), 读出 0 4 2 6 1 5 3 7 跟 Fig03 叶子一字不差
- ③ IFFT: 最小例 [1,1,1,1]→[4,0,0,0]→同蝴蝶+除N→变回, twiddle 取共轭

## [2026-06-12] add | fft §05 真数字演算（用户再要举例）
- 用户反馈"没举例怎么算太抽象"; 新增 §05"拿 x=[1,2,3,4] 真算一遍", 原 ML 节顺延 §06
- 转子表 w⁰=1/w¹=−i/w²=−1/w³=+i(×−i=转90°); Step1 拆偶奇; Step2 两个2点DFT表(E=[4,−2]/O=[6,−2]); Step3 拼+twiddle 表(X=[10,−2+2i,−2,−2−2i])
- Fig05 真值流图: [1,3,2,4]→中间→输出, 蓝偶/红奇交叉+twiddle 标签; 朴素 N² 硬算对答案一致
- note: X₀=10=直流总和; 省了多少 朴素16 vs FFT 2个2点DFT+2twiddle, N翻倍朴素×4/FFT×2

## [2026-06-12] add | drifting-models + diffusion-opd 两个 bespoke 精装页（用户给的两篇 2026 新论文）
- 用户问 "diffusionOPD" + "drifting model"; AskUserQuestion 确认是两篇具体论文, WebSearch+WebFetch 精读 arxiv 原文（知识截止没覆盖）
- drifting-models bespoke(rust #bf5a1e): Kaiming He 组 2602.04770; 吸引-排斥漂移场→反对称q=p场归零→stopgrad不动点训练即演化→迭代搬家(推理→训练)1步; 3图; 像无判别器GAN; ImageNet256 FID1.54
- diffusion-opd bespoke(garnet #9a2f5e): ali-vilab 2605.15055; 多奖励对齐扩散打架/遗忘→On-Policy Distillation(学生自己走老师纠正)→两阶段(各训专家老师→沿学生轨迹蒸一个学生)→扩散=高斯马尔可夫链同协方差KL塌成均值MSE; 3图; 0.929 vs 级联0.851/多任务RL0.763
- 接线: drifting↔ode-sde/flow-matching(反方向); opd↔ppo+ode-sde+cross-entropy(高斯KL=MSE)
- 回链: cross-entropy 加 diffusion-opd source+链接; index 接 ode-sde 后; 6图全本地 headless 验证

## [2026-06-12] add | markov-chain + closed-form-kl 两个前置 concept 页
- 用户反馈 diffusion-opd g-03 的"高斯马尔可夫链/闭式KL"看不懂(前置没补); 拆成两个 concept
- markov-chain: 无记忆(跳格子/天气)+高斯转移(钟形雾,雾心μ模型猜/雾胖瘦σ由schedule定)+扩散去噪=反向SDE离散化; 链图
- closed-form-kl: 闭式(πr² vs 撒豆子估)+同协方差高斯KL塌成均值差²(MSE); 同宽钟形图
- 回链: diffusion-opd 术语表 g-03/g-04 改成链到这俩新页+"不懂先点进去"; index 生成模型基础段加两条

## [2026-06-14] add | qwen3-asr bespoke 精装页 + gspo concept（用户给 Qwen3-ASR，顺带 GSPO）
- WebSearch+WebFetch 精读 arxiv 2601.21337(Qwen3-ASR) + 2507.18071(GSPO)，知识截止没覆盖
- qwen3-asr bespoke(steel #3d5a6c, 第10色): 不从头训ASR→预训练Qwen3当解码器+AuT耳朵+projector插头(=modality-projector模式); AuT 8×下采样12.5Hz+动态窗口1s~8s流式/离线; 训练四段; context biasing(prompt热词)+52语言+整首歌BGM+ForcedAligner填槽NAR时间戳; 3图; 带口音英语16.07完胜Whisper21.30
- gspo concept: GRPO的token级重要性比率→序列级(每token只采一次=高方差噪声易崩, 奖励本就序列级); 稳MoE RL; token级vs序列级对照图
- 接线: qwen3-asr↔modality-projector/whisper/log-mel-spectrogram/gspo; gspo↔grpo/ppo
- 回链: modality-projector/log-mel-spectrogram 加 qwen3-asr source; grpo 加 gspo 后继链接; index 加两条; 4图全本地验证

## [2026-06-14] add | gspo 数字例子 + log-mel/Fbank 五步流水线
- gspo: 用户嫌 r_seq 公式抽象, 加4token演算(π_old/π_new→r_t 1.2/0.5/1.17/1.1, 序列连乘0.06→0.0462, r_seq=0.77^.25≈0.94=几何平均); 柱状图(0.5探出clip带 vs r_seq稳线); 释 1/|y| 防连乘指数爆塌
- log-mel-spectrogram: 用户问 Fbank 怎么做没补; 正名(Fbank=本页/MFCC=Fbank+DCT) + 从波形到Fbank五步(分帧/加窗防泄漏/每帧FFT=STFT/Mel三角滤波器组=Fbank名字由来/log) + 六格流水线图; 接 fft 页

## [2026-06-14] add | forced-alignment 概念页（用户问 Qwen3-ForcedAligner）
- 强制对齐=文字已知只求每字时间(卡拉OK逐字对时间); 经典做法帧级DP/AR会累积漂移
- Qwen3-ForcedAligner-0.6B: 每字插 [time] token 填槽 + 非自回归一次并行预测全部时间戳→断开误差累积; RTF≈0.001, 比WhisperX/NFA累计偏移降67~77%
- AR级联漂移 vs NAR一次填槽对照图; 接 qwen3-asr/multi-token-prediction(同"串行→并行"思路)/next-token-forward-pass
- 回链: qwen3-asr g-06 链到本页; 注意 render 不支持 [[a|b]] 别名(已避开)

## [2026-06-15] add | qwen-image-2 bespoke 精装页（用户要 Qwen Image Edit 最新论文）
- arxiv 2605.10730 全文 HTML/PDF 拉不到(404/超限), 走 ar5iv 全文镜像 + abstract + GitHub 拼齐, 机制已确证
- qwen-image-2 bespoke(grape #6a3a8e, 第11色): 生成+编辑统一成"条件→目标"; 编辑=条件拼原图VAE latent Concat(ℰ_x,h_y)进同一MMDiT, 没点名天然照抄; frozen Qwen3-VL条件编码器 + MMDiT(QK-Norm/纯乘性调制/SwiGLU/MSRoPE) + VAE f16c64(16×,1.0是8×) + 六段训练+Data Flywheel + DMD蒸馏40步→4-NFE; LMArena ELO1168中文#1; 3图(统一/架构流/编辑一致性)
- 接线: diffusion-transformer(MMDiT)/qwen3-vl(条件编码器)/kl-vae(latent)/mrope(MSRoPE)/qk-rmsnorm + flow-matching(DMD)/drifting-models/diffusion-opd(少步化线)
- 回链: diffusion-transformer/qwen3-vl/kl-vae 加 qwen-image-2 source; index 接 hidream-o1 后

## [2026-06-15] add | mrt bespoke 精装页（用户给 mrt-cvpr.github.io）
- ar5iv 全文 + 项目页核实 arxiv 2605.27235 (Canva, CVPR2026)
- mrt bespoke(cobalt #2f6db0, 第12色): 分层图像生成编辑; 核心=selective token masking 哪些图层干净(给定)/噪声(生成)=切3任务(text/image/layers→layers); anonymous region transformer(WAN-VAE region token+full attention,匿名靠位置内容推角色可重摆); overflow画布留溢出; DMD蒸馏50→8步108.5×; 建在Qwen-Image 20B全参微调; 3图(分层vs拍平/masking网格/overflow)
- 关键: 是 qwen-image-2 "条件→目标、编辑塞原图" 推广成 "任意子集图层当干净条件"
- 接线: qwen-image-2(同底座+思路升级+同DMD)/diffusion-transformer/kl-vae/closed-form-kl(DMD KL)/drifting-models/diffusion-opd
- 回链: kl-vae/diffusion-transformer/closed-form-kl 加 mrt source; qwen-image-2 加 mrt 交叉链接; index 接 qwen-image-2 后

## [2026-06-15] add | 三个前置 concept: image-quality-metrics + dmd-distillation + progressive-resolution-training
- 用户问 qwen-image-2/mrt 里 PSNR/SSIM、256P→512P、DMD·4-NFE 都是啥; 拆成三页
- image-quality-metrics: PSNR(逐像素MSE→dB,平移即崩)/SSIM(局部亮度对比结构0-1); 双标尺图标VAE 33.42/0.9225; 接 lpips(感知短板)
- dmd-distillation: NFE=跑几次网络; DMD=不抄轨迹只让出图分布匹配, update∝teacher_score(吸真)−fake_score(斥自己)=Drifting同构; NFE对比+分布匹配图; 接 ode-sde/drifting/diffusion-opd/closed-form-kl
- progressive-resolution-training: 256P→512P→2K 先小图便宜学构图再升大图抠细节; 阶梯图; 接 qwen-image-2六段/mrt 512→1024
- 回链: qwen-image-2 g-04/g-05/g-06 + mrt g-05 链到三新页; index 生成模型基础段加三条

## [2026-06-15] add | qwen3-vl-report bespoke 精装页 + fix dmd 文案重合
- 用户要 Qwen-VL; arxiv HTML/ar5iv 转换失败, 直接读原始 PDF(pypdf 抽全文 42 页, 4.2MB)一手核实
- 注意 slug 冲突: concept 已占 qwen3-vl, paper 用 qwen3-vl-report; 文件 docs/papers/qwen3-vl-report.html
- qwen3-vl-report bespoke(umber #6b4a2e, 第13色): VLM三件套(SigLIP-2 ViT + MLP merger 2×2压 + Qwen3 LLM); 三升级 Interleaved-MRoPE(t/h/w交错铺频谱均衡)/DeepStack(3层ViT经各自merger残差注入LLM前3层)/文字时间戳<3.0s>代T-RoPE; 预训练四阶段S0只训merger→S1/2/3全参 8K→32K→256K + 后训练长CoT SFT→强师蒸馏→RL; OCR32语种/2D3D grounding/GUI agent/256K→1M; 3图
- DeepStack ↔ ideogram-4"取13中间层" 同思想(多层特征>最后一层)
- 与现有 qwen3-vl concept(当文本编码器)互补互链
- fix: dmd-distillation 图 teacher_score−fake_score 文案压在橙箭头上, 文案上移到184/箭头下移到210
- 回链: index 接 mrt 后; modality-projector 等已有链接覆盖

## [2026-06-15] add | lstm bespoke 精装页 + fix mrt 分层图标签遮挡
- lstm bespoke(pine #2f6e4a, 第14色): RNN梯度消失→cell state记忆传送带(加法更新C_t=f·C_{t-1}+i·g)+三门(遗忘f/输入i·g/输出o); 加法梯度高速路=ResNet残差x+F(x)同构(时间方向vs深度方向); GRU简化; seq2seq+最早attention→被Transformer取代; 3图(cell单元/三阀门擦写读/梯度高速路); Hochreiter&Schmidhuber 1997 pre-cutoff凭知识写
- 接线: resnet(加法高速路同构)/attention-is-all-you-need(取代它); index 接 attention 前
- fix(mrt): Fig01 分层图标签贴右边缘被上层错位盖住→挪到各层露出的左下角(画布/背景/前景logo/前景文字)

## [2026-06-15] add | mrope 页加 T-RoPE→文字时间戳 一节（用户问背景）
- 用户问 qwen3-vl-report "T-RoPE 长视频 id 又大又稀/密集采fps" 背景
- mrope 加节: RoPE→M-RoPE→T-RoPE(t绑绝对时间)两毛病(id大+稀; 要密集采各种fps训)→Qwen3-VL 文字时间戳<3.0s>把时间从位置挪到内容; T-RoPE稀疏大id vs 文字时间戳小密id 对照图
- 回链: qwen3-vl-report §02③ 链到 mrope; mrope sources 加 qwen3-vl-report/qwen-image-2

## [2026-06-15] add | video-vae 概念页（用户问 WAN-2.1-VAE 怎么做）
- 查 Wan2.1 论文 arxiv 2503.20314 核实
- video-vae: VAE视频版 vs 图像版(kl-vae); 三件事=3D卷积时间也压((1+T)×H×W→[1+T/4,H/8,W/8]×16,空间64×+时间4×)/因果只看过去帧(1+T关键帧→T=0退化成图,图视频通吃)/特征缓存+RMSNorm→无限长1080P; 图像VAE vs 视频VAE 对照图
- 回链: mrt 两处 WAN-2.1-VAE 链接从 kl-vae 改指 video-vae; kl-vae 加 video-vae 链接; index 接 KL-VAE 后

## [2026-06-15] add | normalization 家族页（用户问 layernorm/groupnorm，嫌抽象→给真数字）
- 已有 layernorm/batchnorm/qk-rmsnorm 分页; 缺统一家族页(对哪根轴) → 建 normalization
- 核心: 都是拉回μ0σ1+γβ, 区别只在对哪组数求统计; 成绩表类比(BN按列/LN按行/GN分组)
- 真数字例子: 2样本×4通道矩阵[1,2,3,4]/[10,20,30,40] 算三遍 — LN按行(两行都→[-1.34,-.45,.45,1.34],抹scale)/BN按列(每列[-1,1],要全batch)/GN行内分2组([-1,1,-1,1]); 三面板高亮图(行/列/块)
- RMSNorm + 为啥 video-vae 换掉 GroupNorm(因果/流式)
- 回链: layernorm/batchnorm/video-vae 加 normalization 链接; index 接 LayerNorm 后

## [2026-06-15] ingest | deep-research + react-loop (survey 2506.12594)

## [2026-06-16] ingest | ai-memory-hierarchy (PhotonCap SOCAMM selloff)

## [2026-06-16] ingest | stable-diffusion-3-5 + mmdit (SD3 arXiv 2403.03206)

## [2026-06-16] ingest | lumine + action-chunking + imitation-learning + quantization (arXiv 2511.08892)

## [2026-06-17] ingest | pid-pixel-diffusion + pixel-diffusion-decoder (arXiv 2605.23902, nv-tlabs/PiD)

## [2026-06-17] ingest | flux-1 + guidance-distillation (Black Forest Labs FLUX.1)

## [2026-06-17] query | gaussian-splatting + lora + matrix-rank (Qwen-Image-Edit Gaussian-Splash LoRA)

## [2026-06-18] query | svd + dot-product + softmax (数学地基补强)

## [2026-06-18] query | eigenvector + svd 重写(首尾串讲, 含特征方程手算)

## [2026-06-18] query | covariance-gaussian + entropy-kl + gradient-backprop (数学地基 round 2)

## [2026-06-18] query | tokenization + sampling-decoding (LLM 输入输出两端)

## [2026-06-18] query | norm-regularization + bayes-probability (数学地基收尾)

## [2026-06-18] query | flash-attention (IO-aware 精确注意力)

## [2026-06-18] ingest | rae-dit + representation-autoencoder (arXiv 2601.16208)

## [2026-06-22] ingest | x-vector + speaker-embedding + statistics-pooling + time-delay-neural-network (Kaldi 声纹, Snyder ICASSP 2018)

## [2026-06-22] query | TDNN 补"跳着取为何不丢帧"(底层密集+窗口重叠铺满, gridding 坑)

## [2026-06-22] ingest | mfcc (梅尔频率倒谱系数, log-mel+DCT; 串起 fft/log-mel/x-vector)

## [2026-06-22] lint | 清"假设读者已学过其它页"口头禅(你学的/你已经懂/放进你学的), 12 页; skill 3.7 grep 扩充

## [2026-06-22] update | mfcc 数字例子补"代 n 造波→跟 x 点积"两步桥接, 挂 dot-product

## [2026-06-22] ingest | unlimited-ocr + reference-sliding-window-attention + optical-context-compression (Baidu, R-SWA 恒定 KV cache)

## [2026-06-23] update | optical-context-compression 补"SAM/CLIP 各发挥什么"(窗口看清+全局理解+顺序逻辑); 修 unlimited-ocr 误指 vit 的链接

## [2026-06-23] ingest | sam (Segment Anything) + promptable-segmentation + sam-data-engine (闭合 optical-context-compression → SAM 回链)

## [2026-06-23] update | optical-context-compression 补"16× 怎么做"(两次stride-2卷积,边长64→32→16); 修 sam FIG01 两箭头方向
## [2026-06-23] fix | sam FIG03 文字溢出框/FIG04 400×被柱遮挡/去掉"你从OCR点回来"导航预设; skill grep 加导航预设

## [2026-06-24] ingest | cosmos-3 + mixture-of-transformers + world-foundation-model + physical-ai (NVIDIA omnimodal world model, MoT 双塔)

## [2026-06-24] topic | joint-attention-lineage (cross-attn→MMDiT/Unified/MoT 2×2 网格: 权重×注意力两旋钮)

## [2026-06-24] ingest | dit (bespoke, Peebles&Xie) + adaptive-layernorm + swiglu (DiT 升格论文页, 讲透 adaLN-Zero/架构⊥目标/scaling)

## [2026-06-24] update | adaptive-layernorm 重写 怎么做的+数字例子(先讲LN三步, 一条 x=[1,5] 端到端: LN→γ/β调制(两个t对比)→α门控)

## [2026-06-24] update | swiglu 加 Swish/sigmoid 函数图(按方程算点: S曲线+负区小坑+ReLU虚线对照)

## [2026-06-24] feature | render.py inject_glossary_popover: 点 .jr 右侧浮卡(不跳页), 自动注入所有有 glossary 的 bespoke 页; 底部 ol 保留兜底

## [2026-06-25] ingest | qwen-image-bench + rubric-based-evaluation + llm-as-judge (Qwen 文生图评测, 5→23→56 细则 + Q-Judger ρ=0.92)

## [2026-06-25] update | llm-as-judge 补"判官是SFT不是RL"(reward侧监督训, RL在下游用判官当奖励调生成模型); 修 pointwise 措辞

## [2026-06-25] update | qwen-image-bench 补全评测标准: 5 支柱→23 子能力整表 + 打分聚合 (0/1/2/N-A 归一化 0/60/100, N-A 剔除, 三级无权重平均, 每 prompt 激活 3-5 支柱) + 端到端手算总分例子

## [2026-06-25] ingest | krea-2 (Krea 2 技术报告: 反美学分过滤+0 AI数据的数据哲学 / 六段流水线 / STPO治DPO策略发散 / 多奖励GRPO+rubric / TDM蒸馏K2 Turbo) + 3 concept (direct-preference-optimization, generative-data-curation, trajectory-distribution-matching)

## [2026-06-26] query→concepts | krea-2 机制深挖: 新增 6 concept (siglip-semantic-dedup, hierarchical-kmeans-curation, pagerank-entity-coverage, dinov3-diversity-reward, prompt-expansion, style-reference) + DPO 页补 DPOP 式 STPO 修法(数字例); GDPO/自监督风格按报告披露程度标注"框架已知/细节未公开"

## [2026-06-26] concept | faiss-ann-search (IVF倒排分桶+PQ乘积量化, 近似最近邻怎么在十亿向量上做到毫秒级); 从 siglip-dedup/hierarchical-kmeans 链入

## [2026-06-28] expand | mrt 精装页大幅扩充(用户嫌当时太简略): 5节→11节; 新增 §04 RoPE坐标复制=重摆位机制(解旧待查,+fig-repos) / §06训练配方表 / §07 DMD蒸馏真实表(50/16/8步 FID16.02/16.21/18.58) / §08评测表(vs Qwen-Image-Layered PSNR按层数27.34/25.91/25.72,层越多越赢+用户胜率79.5/68.9/82.6) / §09消融表(FLUX13B→Qwen20B 17.79→16.15等) / §10局限; +2 concept (selective-token-masking, layered-image-generation); colophon加↗项目页出站链

## [2026-06-28] ingest | relat (ReLAT: 给潜在推理闭环, 测试时重建保真) bespoke(indigo) 4图: 开环vs闭环/可微期望嵌入/ReLAT测试时循环/token效率; 4 concept (latent-reasoning, reconstruction-as-fidelity, differentiable-thought-representation, test-time-training); 核心=能从潜在重建回问题Q=没丢信息(必要非充分)+softmax期望嵌入可微+测试时临时LoRA N=16步答完复位; Qwen3-8B AIME24 50→73.3省84%token

## [2026-06-29] ingest | grape (The Best Instruction-Tuning Data are Those That Fit, NeurIPS25 spotlight) bespoke(clay) 3图+结果表: 合身vs最强分布/困惑度选择机制/自蒸馏塌缩; 2 concept (perplexity, distribution-aligned-sft); 核心=数据好坏相对模型说, 选目标模型困惑度最低的候选回答(只前向)超405B老师+13.8%/超3×数据/省算力; 跟ReLAT姊妹(都问目标模型自己)

## [2026-06-29] concept | on-policy-vs-off-policy (用户问) — 学自己刚做的(准但贵) vs 学别人/旧的(省但分布错位); 重要性采样π/μ纠偏数字例(裸5.5→2.8), 差远比率爆→PPO clip; 从 grape/distribution-aligned-sft 链入

## [2026-06-29] ingest | omnieraser (OmniEraser: Remove Objects and Their Effects with Paired Video-Frame Data, arXiv 2501.07397, PRIS-CV) bespoke(slate) 5图: 目标=连影子一起删/视频帧白送ground-truth/数据流水线三步/双条件vs只给背景/双消融FID柱; 4 concept (object-effect-removal, video-frame-paired-supervision, object-background-guidance, background-subtraction); 核心=对象消除胜负手在数据: 视频里物体自己会走→有它的帧当输入物体离开后的帧当目标(影子在后帧真没了=免费GT)+mask故意不圈影子逼模型学因果; Video4Removal 13.4万对(MOG>0.15+MSE配帧+GroundingDINO/SAM2); object-background双条件治瞎补; FLUX.1-dev+LoRA r32, "There is nothing here"; RemovalBench FID 39.52(SOTA 55.49), 两组消融各→39.52

## [2026-06-29] expand | flux-1 精装页扩充(用户嫌太粗): 2图→4图/4词条→12词条/4节→6节; 新增 §02整体解剖(fig-anatomy: T5-XXL+CLIP双文本编码/19双流+38单流块/hidden3072·24头×128/RoPE/16通道VAE f8, +VAE压缩数字例12×) / §03补单流块attn+MLP并行 / §04引导蒸馏补CFG外推数字例([1,0]→[1,1.5]外推非插值)+guidance当embedding走AdaLN / §05招三步数蒸馏(fig-dmd: 老师50步vs学生4步,不抄轨迹只匹配出图分布); 架构数全部公开源(DeepWiki flux)确证, md待查清掉双单块数; 修 rope 误指concepts→papers

## [2026-06-29] concept | parallel-transformer-block (用户问 FLUX 单流块 attention/MLP 并行怎么做到) — 改三点: 共享一次LN/MLP读y不读注意力输出(无依赖)/两路加回同一主干; 真省在两路第一个矩阵乘输入都是y→拼成一个大GEMM(FLUX 3072→9216+12288=21504一次算,linear2 15360→3072), 比串行4个中等GEMM+2LN快~15%; 代价=MLP对同层注意力瞎但摞深不亏(GPT-J/PaLM/ViT-22B验证); 从 flux-1 §03 链入

## [2026-06-29] expand | cosmos-3 细化(用户): 补硬规则缺的数字例子+变体表+动作模态; 拉技术报告(139页PDF)取实料: §02新增"两塔的账"数字例(Super每塔32B×2=64B总参,每token只过一塔激活≈单塔,对照64B dense; MoT vs MoE分法)+pre.eq/table.spec样式; §04补动作=一等模态(action token过模态encoder进统一空间,迭代去噪生成非自回归,前向/逆动力学/策略=token摆法); §05加变体表(Edge4B/底座2B 28层2048 16头8KV Qwen3-1.7B式去QKnorm ReLU²/Nano16B-8B/Super64B-32B, Nano/Super本次发Edge稍后)+g-11词条; md待解清掉动作tokenizer与激活账

## [2026-06-30] ingest | diffusionnft (DiffusionNFT: Online Diffusion Reinforcement with Forward Process, arXiv 2509.16117, ICLR2026) bespoke(aubergine) 5图+对照表+数字例: 似然墙逼出FlowGRPO绕反向的三坑/前向唯一反向无数/奖励切正负Δ=改进方向(≈CFG)/单模型隐式装正负+监督损失/GenEval收敛曲线; 3 concept (negative-aware-finetuning, reinforcement-guidance, diffusion-rl-likelihood-barrier); 核心=前向加噪唯一→把RL搬到前向flow matching,π⁺∝r·π_old/π⁻∝(1−r)π_old,v±=(1∓β)v_old±βv_θ对称,L=E[r‖v⁺−v‖²+(1−r)‖v⁻−v‖²]监督非policy gradient,最优v*=v_old+(2/β)Δ; CFG=离线强化引导; SD3.5-M LoRA r32, GenEval~1k步0.98比FlowGRPO快3–25×CFG-free超CFG

## [2026-07-01] expand | diffusion-opd 细化: §04 补"为什么高斯KL塌成MSE"通用三项消项推导(形状tr(I)-d=0/体积ln1=0/只剩位置=均值差)+数字例(μ_s=[1,5]μ_t=[1,4]σ=0.5→KL=2,短式=全式核对); glossary 6→12(补off-policy蒸馏/稠密vs稀疏/专家老师-统一学生/协方差由schedule定/SDE-ODE损失/通用高斯KL三项)并补齐g-05 g-06孤儿+全部jr入口; md核心贡献加三项消项来历

## [2026-07-01] ingest | turboquant (TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate, arXiv 2504.19874, ICLR2026, Google) bespoke(denim) 4图+对照表+2数字例: 在线盲切格子/随机旋转把分布变已知(±1/√d薄壳)/高维近独立各坐标最优≈向量最优(≈2.7×下界)/MSE有偏QJL残差纠无偏; 3 concept (random-rotation-quantization, quantized-jl, mse-vs-inner-product-bias); 核心=随机旋转把"不知道数据长啥样"变"精确知道每坐标分布"→最优量化器离线预制在线零成本套(data-oblivious); 两阶段MSE+QJL 1-bit残差; KV 3.5bit无损/≥6×省内存/H100 attention快8×; 数字例(±1/√d shell + bias0.90 vs unbias1.00)

## [2026-07-01] expand | turboquant 补主线+QJL机制: 开头加 fig-throughline(难题→招1随机旋转→招2 QJL残差→结果 4段路线图,回答"这几块零件咋合起来解量化难题"); §04 深化 QJL "怎么做的"——只存 sign(⟨r,x⟩) 1bit + query 投同方向 ⟨r,q⟩ ×缩放常数取平均=无偏内积(同方向分量累加/垂直分量相消), 加 fig-qjl(单方向符号项乱跳→running平均收敛到0.80)+数字例(±1符号项(2.1,−0.5,1.3,0.3)/4=0.80); 加 .draw stroke 动画

## [2026-07-01] expand | turboquant §02 补"为什么是 Beta / 均值为什么 1/d": Beta=描述0~1占比的分布,均值a/(a+b),a小b大挤向0; 随机旋转=球面均匀撒点=高斯归一化→x_i²=g_i²/Σg²=能量占比(落0~1→天然Beta),参数1/2=这一坐标/(d−1)/2=其余; 均值1/d的对称论证(平方和恒=1,d份平分); 数字例 g=[2,1,0,1]/√6→占比[.667,.167,0,.167]Σ=1→多次平均→1/4→幅度1/√4; 加 fig-beta(左:一次抽样能量占比stacked bar; 右:Beta密度cliff+均值1/d虚线); 下游图 FIG03/04/05→04/05/06 顺延

## [2026-07-01] fix | turboquant fig-beta 密度曲线画错: 原路径在均值处就砸到基线还探到轴线下方(y165<baseline)+拖平尾巴,看着像"均值右边没质量"违背均值=质量平衡点; 改按 d=4 真实 Beta(0.5,1.5) 形状(0处尖峰→单调下降→占比=1才归零),均值线落在曲线下方有质量处; 注解标明画的是 d=4(均值0.25),d 越大越往0挤

## [2026-07-01] fix | turboquant fig-qjl 文案遮挡: "running 平均→收敛到0.80" 原压在绿线+右侧红点上; 挪到右上空白, 加绿虚线 leader 引到终点绿点

## [2026-07-01] expand | turboquant §02 补"参数为什么是 ½"(半个每维): Beta 第一参数 a 管 0 附近形状 x^(a−1),a=½→1/√x 尖峰; 尖峰来自平方换元——等宽 g 段平方后落到的 y 段越靠 0 越窄(宽∝√y),同概率挤进越窄区间→密度∝1/√y→指数−½=形状½; 独立平方高斯 shape 相加→1坐标½/其余(d−1)/2/全体d/2, ½约掉留 1/d; 数字例(g[.1,.2]/[.5,.6]/[1,1.1]→宽.03/.11/.21); 加 fig-half(左:三色等宽g段→不等宽y段+平方箭头; 右:1/√y尖峰; 底:加法规则→均值1/d); 下游 FIG04/05/06→05/06/07 顺延

## [2026-07-02] ingest | viitorvoice (ViiTorVoice / viitor-voice-nar, 开源 LLM-based 流式 TTS 引擎, 无独立论文, 思路源自 DualCodec+OmniVoice) bespoke(petrol) 4图: 三段管线(文本→LLM语义码→NAR声学码→DualCodec波形)/DualCodec双流(RVQ-1语义w2v-BERT蒸馏码本16384 + RVQ2-8声学残差, 24000/1920=12.5帧秒)/AR逐帧200步 vs NAR掩码并行~8步/首块流式60ms; 3 concept (dualcodec, semantic-vs-acoustic-tokens, nar-masked-speech-generation) + 复用 rvq-codec/voice-cloning-reference/classifier-free-guidance 补 source; 硬数字来自组件论文 DualCodec arXiv2505.13000(Interspeech25) + OmniVoice arXiv2604.00688(k2-fsa); 60ms首帧/12.5帧秒/N=8码本/~0.75-0.93kbps/中英日韩粤TODO; HF ZzWater/ViiTorVoice-NAR

## [2026-07-03] fix | viitorvoice fig-stream 误导: 原"首块流式"行比"等整段"行短→像流式整体更快完成; 实际总时长一样只是首声更早出. 对齐两行右边缘到同一 finish 线(x590)+加"两者约同时生成完"共享虚线; caption 改"总时长一样,差别在第一声何时出来"

## [2026-07-03] expand | viitorvoice 加机制细节(嫌讲太粗): §02 加"RVQ 残差递推"——每码本咬上层残差,数字例 x=[.9,.4] 三层码字逼近到 0,8码本=1语义+7声学; §03 加"迭代到底怎么迭代"——置信度(softmax最高档)+余弦式定稿,4步25/50/75/100%示意,定稿按把握非从左到右+随机掩码训练/LLM初始化; §04 加"CFG外推公式"out=uncond+s·(cond−uncond)数字例(0.2+3·0.3=1.1)+两路s(情绪/nvv), 加克隆(prompt前缀条件,内容来自文本音色来自prompt)与流式(block切分,首块=60ms,低帧率帮忙)细节; glossary 12→15(g13残差递推/g14置信度余弦定稿/g15 CFG外推)

## [2026-07-06] fix+expand | vits 图修 + 概念补: ①fig-cvae KL 虚线原悬空 y=150 → 接到底部先验 z; ②MAS 图/正文/glossary/concept "右下↘"与图(a底c顶自下而上)不符 → 全改"右上↗"; ③代码块内 wikilink 渲染成裸<a>标签(stochastic-duration-predictor 的 [[normalizing-flow]] + object-effect-removal 两处)→ 纯文本; ④normalizing-flow 概念加二维 det=单位方块被抻成的面积手算(J=[[2,0],[0,3]]→面积6→密度÷6, shear det=1)

## [2026-07-06] add | concept reading-2x2-matrices (读懂2×2矩阵): 一把钥匙=矩阵两列就是x/y基向量变换后落点(乘基向量=挑那列); 单位方块→两列张成平行四边形, det=面积=ad−bc; 三面板图(缩放对角[[2,0],[0,3]]面积×6 / 旋转45°列正交等长det=1 / 错切[[1,1],[0,1]]det=1歪不改面积)红=x列绿=y列虚线=原方块; 代入基向量手算(缩放/旋转90°/错切); 一眼分辨表; det符号=翻面; 任意矩阵=转→缩→转(SVD). 交叉链 normalizing-flow(雅可比det=局部体积)+covariance-gaussian; 复用为 det/雅可比 几何直觉底座

## [2026-07-09] ingest | yolo (YOLO v1: You Only Look Once, Redmon/Divvala/Girshick/Farhadi, CVPR 2016, arXiv 1506.02640) bespoke(tangerine) 5图: 两阶段上千次逐候选 vs YOLO一次前向/7×7网格物体中心落哪格负责/一格30数(2框×5+20类)置信度=Pr(物体)×IOU/98框NMS去重/速度精度scatter; 4 concept (one-stage-detection, iou-intersection-over-union, non-max-suppression, mean-average-precision 全新,wiki首个检测paper); 数字: 7×7×30=1470, IOU交÷并=1/7, √w大小框误差2.7×, NMS三框走一遍, mAP小PR曲线; 63.4%@45FPS/Fast YOLO 52.7%@155FPS/Faster R-CNN 73.2@7FPS; λcoord=5 λnoobj=0.5; 24conv+2fc, 448×448

## [2026-07-09] expand | yolo 补训练章(原来只讲推理): 新增 §04 训练——责任框(物体归中心格,该格2框IOU高者当责任框,只它吃坐标+置信度损失→两框分工)+损失拆5块(①②责任框坐标/尺寸×λcoord5 ③责任框置信度目标=IOU ④空框置信度目标0×λnoobj0.5海量 ⑤有物体格20类)+为什么λ(49格大多空,正负失衡)+√w,h数字例(大小框2.7×,从§03移来)+训练流程(前20conv ImageNet 224²预训练分类→加4conv+2fc 448²训检测~135epoch); 加 fig-loss(左责任框选取右5损失项权重); glossary 11→12(g12责任框, g11加训练); 原§04/05 NMS/结果→§05/06, FIG顺延06

## [2026-07-10] expand+fix | yolo 深改为完整 YOLO v1 复习页: 区分原始 R-CNN/Fast/Faster R-CNN; 用同一只狗贯通责任格→双框竞争→0.56类分数→NMS; 修正√w,h示例(残差2.68×,平方损失7.20×); 补135epoch训练配方与SSE局限; 新增VOC2007错误画像(Fast R-CNN loc8.6/bg13.6 vs YOLO loc19.0/bg4.75)、模型互补(71.8→75.0,+3.2)、VOC2012 57.9与小物体短板、Picasso/People-Art跨域数据; 新增fig-errors与fig-art,全页SVG标签≥11px

## [2026-07-13] ingest | yolov2-yolo9000 (Redmon/Farhadi, CVPR2017, arXiv1612.08242) bespoke(deep+calibration-orange) 7图: v1四张问题单→v2修复映射/手选框vs IOU维度聚类+相同20%误差尺度自检/anchor中心sigmoid限位与宽高指数解码/26×26×512 passthrough重排为13×13×2048/同一权重288→544速度精度五档/WordTree路径0.8×0.75×0.9=0.54再乘objectness/真实消融63.4→78.6; 4 concept(anchor-boxes,dimension-clustering,multi-scale-training,hierarchical-classification)+复用one-stage/iou/mAP补source; 完整训练:Darknet-19 5.58B,分类160epoch+448微调10epoch,检测160epoch; 实验:anchor mAP69.5→69.2但recall81→88,VOC2007 76.8@67FPS/78.6@40FPS,VOC2012 73.4,COCO AP21.6/AP50 44.0/AP75 19.2/small 5.0,ImageNet detection总19.7/156弱监督类16.0且动物强服饰0AP; WordTree 9418类,COCO/ImageNet约1:4

## [2026-07-13] expand+fix | yolov2-yolo9000 §02/§03 补完整 anchor 教学链: 明确训练前“全数据集IOU聚类选5种模板”与训练时“真值中心选格+形状IOU选best anchor”是两次选择; 用同一416输入真值框(中心112,152px/宽高96,64px)贯穿网格换算→5 anchor IOU手算→2×2胜出→逐符号定义→tx=0,ty=ln3,tw=ln1.5,th=0→解码→乘stride32还原像素; 解释中心sigmoid限位/宽高exp倍率与正值/log空间对称/objectness sigmoid; 新增Fig02B匹配面板+符号表+四项解码卡,同步扩写anchor-boxes与dimension-clustering概念页,匹配规则由官方Darknet region_layer.c交叉确认

## [2026-07-13] fix | yolov2-yolo9000 VOC对比表列对齐: 原数值单元格右对齐、表头仍左对齐，mAP/FPS 标题与数据不在同一竖线; 给 benchmark 表加独立类并让第2/3列表头同样右对齐，不影响参数表等其他表格

## [2026-07-13] ingest | yolov3 (Redmon/Farhadi, 2018 technical report, arXiv1804.02767) bespoke(scope-green+signal-orange) 8图: v2单检测头vs v3三出口/13·26·52三层真实9 anchor+10,647候选/60×120行人框贯穿59×119 anchor→26头→格子→四数解码/正样本·ignore·负样本三分/softmax互斥vs独立sigmoid多标签/Darknet-53的1·2·8·8·4残差stage+速度手算/COCO AP与320·416·608速度档/四个失败实验; 4 concept(multi-scale-detection,darknet-53,multi-label-classification,anchor-truth-assignment)+复用anchor/dimension-clustering/multi-scale-training/residual/iou/cross-entropy/one-stage/mAP补source; 论文全骨架覆盖:框预测/分类/三尺度/骨干/训练/COCO评测/失败尝试/技术伦理; 数字:3×(4+1+80)=255,507+2028+8112=10647,small AP5.0→18.3,AP33.0/AP50 57.9/AP75 34.4,Darknet-53 Top-1 77.2/Top-5 93.8/78FPS

## [2026-07-13] ingest | yolov4 (Bochkovskiy/Wang/Liao, 2020 technical report, arXiv2004.10934) bespoke(detector-workshop cobalt+safety-yellow) 11图: Freebies训练账vs Specials推理账/CSPDarknet53→SPP-PAN→YOLOv3三段装车/4通道CSP分流手算/原特征直通+5·9·13 SPP四路512→2048通道+PAN双向流/四张320图拼640 Mosaic与框平移/SAT自攻→难图训练两阶段/格内0.99令logit 4.595→scale_x_y后2.293/60×120真值对9 anchor且阈值.213选四正样本/CIoU覆盖.66667+中心.03125+形状.03375=.73167/BoS负结果条形消融/COCO v3→v4与V100三档; 5 concept(bag-of-freebies-specials,cross-stage-partial-network,spp-panet-neck,mosaic-augmentation,complete-iou-loss)+复用one-stage/multi-scale-detection/training/anchor-assignment/NMS/mAP/IOU/darknet53/receptive-field/batchnorm补source; 全文骨架覆盖 related work/架构选择/BoF-BoS/额外改进/训练设置/分类与检测消融/骨干预训练/mini-batch/三代GPU结果/局限; 论文配方DIoU-NMS与当前master cfg greedynms差异留档; 最终608为AP43.5/AP50 65.7/AP75 47.3/small26.7,V100 62FPS

## [2026-07-13] ingest | sensenova-vision (Vision as Unified Multimodal Generation, Han et al., arXiv2607.06560v1) bespoke(multimodal-routing-console violet+cyan+amber) 11图: 专家head排→单生成总线/文本·图像·混合三路由/640×480框归一化往返/depth-normal-mask-pointmap四编码/颜色图例+最远点采样/多视图frame0对齐+1.25m pose token解码/SN-VC-50M四族比例/CE+rectified-flow双目标及论文50K vs repo beea1f7 200K/四族成绩单+MMVP与GenEval交换/分阶段收敛/structured plan错误向mask传播且人工修复改善; 4 concept(unified-multimodal-generation,decodable-vision-representation,color-legend-mask,camera-pose-tokenization)+复用flow-matching/cross-entropy/promptable-segmentation补source; 全文骨架覆盖related work/data/training/四族实验/generalist对照/convergence/qualitative与appendix语料和失败; 结论平衡:structured广泛领先,dense接近专家,segmentation/multi-view仍有专用先验差距,自由组合仅定性; 官方PDF确认论文与当前脚本LR均为2.5e-5,真正差异是50K vs 200K等配置

## [2026-07-13] expand+fix | yolov4 重做 SPP pooling + SAM: 池化从“默认缩图”改成kernel/stride/padding三参数模型,3×3 pad1滑窗逐格手算,13×13代入5/9/13三档均保持尺寸; SPP用13格同心窗口演示中心值4→max6/8/9,四路13×13×512 concat→2048再1×1压缩,PAN拆成独立双向图; spatial-wise明确为1×H×W共享门,point-wise明确为C×H×W逐元素门,双通道2×2算出同一左上角8×.25=2 vs 8×.75=6; 新增concept spatial-vs-pointwise-attention,重写pooling/spp-panet-neck; 标注论文Fig5/实验cfg含modified SAM但官方master@59596d7标准yolov4.cfg无[sam],Table5 +0.3 AP不是两种SAM严格消融; bespoke 11→13图

## [2026-07-13] fix | yolov4 Fig06 point-wise 卡片消失: 新卡片误用通用类名.point,撞上grid sensitivity图的绝对定位竖线样式(width10/height44/position absolute); 改为独立.pointwise类,恢复SAM左右两栏完整对照

## [2026-07-14] polish+expand | yolov4 全页中文与术语可达性审校: hero/TLDR/架构/SPP-PAN/SAM/Mosaic/SAT/anchor/训练配方/消融/结果与局限逐段去翻译腔和中英夹句; 新增12张可点击术语速查卡,正文术语改为直接点击弹解释,glossary 14→32并补主干/融合层/检测头/特征图与通道/步长与补边/拼接与相加/anchor/AP/FPS-BFLOPs/batch/logit-sigmoid/IOU-NMS/消融/训练旋钮及次要消融候选; 重写原先算到省略号的mAP概念页,3真值4预测从TP/FP→P/R→precision envelope→AP50=0.833,拆清COCO AP/AP50/AP75; convolution补yolov4 source

## [2026-07-14] ingest | meshflow (Continuous Mesh Generation with Flow Matching, CVPR2026 Highlight, arXiv2606.04621v2) bespoke(topology drafting table, blueprint-blue+edge-orange) 9图: 隐式/自回归/连续表示三路线、四顶点五边恢复两三角面、TokenMerge 8→2、mask→三环→法线连面、Rectified Flow 二维速度完整手算与Euler回走、32³体素+3D RoPE、训练配置冲突、重建/生成/双计时表、query边F1消融与源码差异账；4 concept(continuous-mesh-connectivity,mesh-token-merge,voxel-rope-conditioning,mesh-quality-metrics)+复用flow-matching/KL-VAE/DiT/RoPE补source。核心=连续边嵌入把离散拓扑变成Flow能生成的张量，MeshVAE约N/4 latent，28步并行；Toys4K CD2.33/HD4.23，摘要单物体~18×但主表batch均时~2.2×。审计保留paper v2与官方55f56f6：Eq(2)阈值方向、主文/补充DiT规模、补洞默认值三处不一致，并限定“并行”不等于全attention总FLOPs线性。

## [2026-07-14] rewrite | meshflow 说人话 — origin/main 已有 codex 的密版(errata 堆砌像代码审查),按 wiki 直觉先行风格全面重写 wiki/papers/meshflow.md(连续坐标vs离散开关=连边磁铁核心比喻),bespoke HTML 保留 codex 图与设计但把整段 §09 source-audit 压成一条紧凑"复现坑" note 并改标题 Limits;index 行改成直觉先行框架。yolov2/3/4/sensenova + 各概念页维持 codex 版(reset 到 origin 后仅叠加 meshflow 改写,不动其余)

## [2026-07-15] rewrite | cosmos-3 完整论文讲解 — 原页5节只覆盖部分架构且有“一套权重/单次前向/两塔都从Qwen初始化”三处误导，重写为12节12图：机器人收桌子贯穿旧管线→五模态入口→任务token排列→MoT双塔账→联合注意力矩阵→rectified-flow数字手算→MRoPE FPS时间轴→2200万Reasoner数据与两级过滤→Reasoner/SFT/Generator/mid/post训练接力→PAIBench/Physics-IQ/RoboLab/LIBERO真实结果→Reasoner/FPS/音频/动作四组消融→权重显存/多步去噪/专项后训练/成功率边界；HTML 16词条全可达，md同步扩写

## [2026-07-15] rewrite | vits 深度打磨 — 修正“端到端=没有任何中间量/没有失配”和“CMOS≈完全听不出差”两处过度表述，改成训练/推理双路线贯穿的12节语音工作台；新增五模块岗位图、完整变量定义与KL数字例、Flow正逆方向和30万步消融边界、MAS 3×5动态规划手算、SDP d=4→d−u=3.7→[3.7,0.8]去量化/增广/变分下界、多周期判别器折叠、五项损失工位、数据预处理与训练配方、LJ/VCTK/速度、消融与多样性、声音转换及六项局限；术语表扩到18项，md同步重写

## [2026-07-15] fix | cosmos-3 Fig10 时间线 — 原实现把竖线画成每个 stage 的负 margin 左边框，线偏离圆心且后绘制在编号圆点之上；改为 train 容器单一 ::before 背景线，精确对齐圆心，编号圆点提高层级遮住线，移除窄屏易错位的负 margin

## [2026-07-15] expand | cosmos-3 Reasoner→Generator 权重迁移 — 补 Fig10B 拆清复制的是 LayerNorm/QKV/O/MLP 参数，不复制运行时 softmax(QKᵀ)；Reasoner 的文本/ViT+因果mask+词表头+CE 对照 Generator 的带噪latent+双向mask+速度头+masked MSE；沿用 xσ=1.25/v*=−3 手算玩具权重 w=2 一步梯度更新，loss 30.25→14.30，坐实“复制只是初始化，Flow 训练才把它改造成去噪器”；补 VAE/audio/action 投影边界和附录 E.1 只证明条件侧 Reasoner 更好、未直接消融复制初始化的证据边界；glossary 16→18

## [2026-07-15] fix+expand | cosmos-3 Fig10B 梯度公式补全 — 原版直接写 dL/dw=13.75，没先定义玩具模型和损失；补 v̂(w)=w·xσ、L(w)=(v̂−v*)²=(w·xσ−v*)²，先记 e 再按链式法则拆 dL/dw=(dL/de)(de/dw)=2e·xσ，逐项解释 2e 与 xσ 从哪来；补 SGD 更新 w_new=w−ηdL/dw、η 定义和 w_best=v*/xσ=−2.4 自检，完整走 w:2→.625、loss:30.25→14.30，并明确单标量只是优化演示而非真实架构

## [2026-07-15] expand+fix | vits §06/§07 随机时长与 GAN 公式重讲 — 拆清训练辅助随机 qφ→u,ν 与推理高斯采样 e→inverse Flow→logw→exp→ceil 两条路线，用 d=[2,4,3] 验证 ceil(d−u)=d、两份噪声得到 [2,3,2]/[3,4,3]；逐项翻译时长 ELBO 的 d/c/θ/φ/p/q/E/两项与 ≥，用 p:.20→.40 手算 Ldur:.916→.223；GAN 不再默认前置知识，定义 z/y/G/D/D_l/T/N_l/L1/E，手算 D loss .13、G loss .49→.09、两层 feature matching .8，并写明 detach 后先练 D、再固定 D 练 G；修复原有 18 条 glossary 仅 5 条正文可达的问题

## [2026-07-15] polish | vits §06/§07 中文重写 — 保留公式与手算，重排中文因果顺序；删除“主 Flow 更认可数据 / q 提出样本 / 冒充 p 的能力 / 借塑形轴 / q 下班 / 两边轮流走”等翻译腔或刻意比喻，改成“p 计算概率密度 / q 在已知答案时采样 / 扣除采样偏差 / 每个时长由一维变二维 / 推理不再使用 q / 先练 D 再固定 D 练 G”；同步润色图注、公式卡和 glossary

## [2026-07-15] expand+fix | vits §06 条件分布记号补课 — 不再默认读者会联合条件概率；先把 qφ(u,ν|d,c_text) 拆成“竖线左边要抽什么 / 竖线读作已知 / 右边已经给了什么”，说明两侧逗号不是乘号、φ 是网络权重；用 d=[2,4,3] 与 enc("你好") 演示固定右边再采 u、ν，并对照 pθ 只看文本、qφ 训练时可看正确时长；把 E_q 展开成两次采样分数 −.8/−1.0 → 均值 −.9 → Ldur=.9 的完整操作链，补连续变量应称概率密度及术语直达

## [2026-07-15] expand+fix | vits §06 ELBO 来源补全 — 删除只会代数值却解释不了来源的单样本 p=.20/q=.50 例；从 ceil(w)=d ⇔ w=d−u 推出整数概率等于对 pθ(d−u,ν|c) 的完整积分，解释 ν 被边缘化；再逐行写出 ∫p=∫q·p/q=E_q[p/q]，说明除 q 是校正非均匀抽样；最后用 Jensen 把 log E[p/q] 变为 E[log p−log q]，明确只有这一步产生 ≥。A/B 两区域用 p=.12/.08、q=.75/.25 验证 E_q[p/q]=.20，且 −1.609≥−1.659；q 改为 .60/.40 时下界贴紧真实值。glossary 19→21

## [2026-07-15] visual+infra | vits 全页 KaTeX 公式系统 — 自托管 KaTeX 0.17.0 的 JS/CSS/字体/许可证，页面离线打开也能排版；仅渲染标记为 .tex 的正式公式，不扫描代码块和数字手算；CVAE/MAS/条件分布/ELBO 三步/GAN/feature matching/总损失共 11 处升级为 TeX，用青色等号、金色不等号和绿色抽样校正突出推导角色；长 ELBO 在 420px 改用先定义 p/q 的三行短式，桌面保留论文完整式；13 个响应式 TeX 源编译 0 错误，桌面/手机视觉验收通过

## [2026-07-15] expand+fix | vits Step 1 积分换元与换序补全 — 从 w∈(1,2] 的原始积分开始，逐行代入 u=2−w、dw=−du，并解释上下限 1→0 与负号如何抵消、|dw/du|=1 为什么没有额外系数；再把 [0,1)×ℝ 画成行列求和，说明概率密度 f≥0 时可按 Tonelli 交换积分顺序，用四格质量 .04/.06/.03/.07 验证两种顺序都得 .20；向量式改为 [0,1)^T×ℝ^T 且全文统一 dν du，消除原先无说明的 du dν 换序

## [2026-07-15] fix | vits Step 1A 显式展开 g — 补清 g(w,ν) 只是条件联合密度 pθ(w,ν|c_text) 的临时简称，c_text 从第一行起就藏在 g 里；在 g(2−u,ν) 与最终积分之间新增“代回 g 的定义”等式，区分 w→2−u 的变量替换与 g→pθ 的简称展开；注明 ν 是希腊字母 nu 而非英文 v，桌面/手机公式同步

## [2026-07-15] visual | vits 深蓝公式注释提对比度 — math-caption 正文由 11px/灰蓝提升为 12px/高亮冷白（对深蓝 12.37:1），行内公式改暖金底+深蓝字（12.10:1），避免原浅灰字落在米白 code 底上仅 1.81:1；Step 1A 两条说明拆成青色“换元与展开”和金色“负号”双轨标记，手机端改为标签在上、解释在下

## [2026-07-16] rewrite | krea-2 官方技术报告重做 — 以 Krea 2 Technical Report 为正文唯一主线，GitHub/Hugging Face 仅补 12B、Raw 52 步、Turbo 8 步与许可证；纠正“全程 0 AI 数据”（实际只限预训练图像）、双 VAE 串联、STPO 辅助项已知三处误读；重排为论点→数据过滤/SAE→caption/500 万实体覆盖→12B 单流 DiT 消融→rectified-flow 公式与 x₀=2 数字例→六阶段分布修改→DPO 两者一起降的完整公式/手算→四奖励 RL/rubric/GRPO-style 数字例→prompt expansion/多样性塌缩→style reference 披露边界→TDM/Raw/Turbo→训练与数据系统→MoE/MOPD/统一架构未来工作→已公开/未公开证据边界；视觉改为 Krea 官方样图上的“分布地图/创作模型实验室”系统，KaTeX 6 式、13 章、13 词条，桌面 1440 与手机 390 验收无横向溢出

## [2026-07-16] polish+fix | krea-2 中文与术语浮层 — 删除“铺地图 / 装方向盘 / 压路线 / 翻译成坐标”等硬比喻，改为“扩大能力范围 / 提高可控性 / 减少生成步数 / 准确理解用户意图”；修复页面自带浮层与 render.py 通用浮层重复初始化的问题，只保留一套交互；浅色浮层改用深绿强调色，亮绿仅留在深色区域，提升编号与边线对比度

## [2026-07-16] expand | krea-2 数据过滤术语补课 — 补清伪影与有意视觉风格的边界、高频/结构伪影实例；把常见 pHash 拆成缩放灰度→DCT→保留低频→中位数二值化→汉明距离，解释 hash_size=8 时先缩 32×32、最终保留 64 位，hash_size=12 时先缩 48×48、最终保留 144 位，并说明 colorhash 看颜色分布但不看位置、Krea 未披露判重阈值与合并规则；用 3×3 Laplacian 核手算纯色响应 0、孤立亮点 −600，标明报告未公开具体核与阈值；术语表 13→16

## [2026-07-16] expand+fix | krea-2 DCT 补课 — 删除“8×8 版缩成 32×32”的歧义，明确 hash_size=8 时原图先缩 32×32、DCT 后才保留左上 8×8；新增低频/高频直译、2×2 四张余弦基础图案和 [[20,0],[20,0]]=10×整体亮度+10×左右变化的逐格自检，补棋盘格为何是高频与 32×32→DCT→左上 8×8→64 位的完整链路；Laplacian 图顺延为 Fig04，术语表 16→17

## [2026-07-16] expand+fix | krea-2 长尾实体保护 — 删除“某个球员和一堆运动员聚在一起，抽样后本人全没了”的含糊口语；改用 10,000 张运动员图中某球员仅 10 张、随机保留 100 张时期望仅 0.1 张且全漏概率约 90.5% 的数字例，拆清视觉聚类负责去头部重复、Wikipedia 实体检索负责保护具体人物/地点/事物、采样后复查防止整个实体消失

## [2026-07-16] expand+fix | krea-2 全页公式符号审计 — Rectified Flow 补 L_RF/E/θ/‖·‖₂²/dxₜdt/v*/v̂ 与下标含义，DPO 补 Δref 完整展开、条件竖线/log/β/sigmoid/−log 和整句翻译，GRPO-style 补均值与总体标准差公式、i/j/n/Σ 定义及 .166 的逐步来源；明确 sR=0 的除零边界与 Krea 未披露完整策略损失，所有抽象符号均在首次公式附近直接可读

## [2026-07-16] fix | krea-2 L2 范数上下标对齐 — 符号表原写 ‖z‖²₂，与公式渲染的 ‖z‖₂² 顺序不一致；统一成“下标 ₂ 表示 L2 范数、上标 ² 表示再平方”，补 ‖[0.4,−0.2]‖₂²=0.4²+(−0.2)²=0.20 的同形公式，说明平方会消掉范数里的平方根

## [2026-07-16] expand | krea-2 技术报告覆盖补全 — 逐节对照官方报告补齐横向细节：数据补FAISS层级聚类/VLM+人工复核、Wikipedia PageRank前90%+Wikidata与分阶段阈值；架构展开GQA/MLA、三种图文流、time token由256px可用到512/1024失效、partial RoPE零样本先赢后输、五类VAE/Qwen3-VL跨层聚合/RMSNorm/Muon稳定条件；训练补256 tensorwise→512 rowwise→1024 bf16、iREPA/TREAD、shifted logit-normal timeshift、WSD/PMA和中训/SFT合并边界；Prompt Expansion补SFT数据分布、GDPO三层奖励、真实失败桶与hard-case采样；系统补FSDP2+TP/async-TP、activation checkpoint、可精确重放数据链、Kueue整组调度、Virtual Kubelet、坏节点分流、7类硬件指标、WEKA边界、208TB krablet与SKIP LOCKED队列；术语表17→24，md同步

## [2026-07-16] visual+fix | 全站术语角标点击态对比度 — 通用浮卡脚本给角标加jr-active后，页面自身!important深色文字压过激活态浅色，Krea 2表现为深绿底上的深绿数字；在render.py通用注入样式中把激活态文字明确设为高优先级浅色，并同步边框颜色、补focus-visible轮廓，刷新65个bespoke paper页；浏览器实测Krea 2点击态为rgb(49,91,10)底/rgb(243,242,238)字，浮卡正常打开

## [2026-07-16] ingest | Trading in the Zone《交易心理分析》(Mark Douglas / 张轶译) — 第二本 book，全 137 页逐章精读后拆成 1 概览 + 11 章精讲(titz-ch01..11)；提炼五个基本事实、七个持续一致性原则、赌场概率模型、三组交易者、四种交易恐惧；关键例子小孩和狗/大豆甩单/免费送钱/圣诞老人能量守恒/跑步5英里原则/大峡谷独木桥/20笔赌场练习；叠工程视角(过程指标vs结果指标、认知=文档信念=权重、大数定律)；版权原书只在 raw/ 留指针不入库

## [2026-07-16] expand | Krea 2 + Cosmos 3 基础设施概念层 — 两篇 Infra 不再堆框架名，正文先按数据管线/训练切分/GPU执行/互联通信/集群调度/故障恢复/服务部署分层，再补8个共享 concept：distributed-training-parallelism 用4卡例拆 FSDP2-HSDP/TP/CP-Ulysses，activation-checkpointing 用4层8GB→4GB说明重算换显存，gpu-kernels-and-compilation 手算3 kernel 54μs→融合38μs，training-checkpointing-and-recovery 算存档间隔与平均丢进度，large-scale-data-pipelines 对照 SILA-Lance-Ray 与 krablet-PostgreSQL-SKIP LOCKED，gpu-cluster-scheduling 算128卡 gang scheduling，gpu-interconnects-and-collectives 拆 PCIe/NVLink/InfiniBand/NCCL，model-serving-stack 拆 PyTorch/TensorRT/vLLM-Omni/Cache-DiT；Krea glossary 24→28，Cosmos glossary 25→29，所有新词条直链 concept
## [2026-07-17] concept | flash-attention（重写 IO 因果链）

- 补清“大矩阵为什么来回搬”：三个 kernel 分开执行，中间结果必须写回 HBM 才能交接。
- 纠正“切块自然省 IO”的误解：真正组合是分块 + kernel 融合 + 在线 softmax；小块在片上完成 softmax 与加权 V 后立即丢弃。
- 加入 4×4 搬运账本、N=8000 的 512 MB 量级例子，以及带 V 的在线 softmax 全流程手算；同时说明输入/输出块重读、反向重算和浮点舍入差异。

## [2026-07-17] ingest | ltx-2（Lightricks · arXiv 2601.03233v1）

- 完整覆盖 joint T2AV 动机、14B/5B 不对称双流、48 层四工序、双向 A/V cross-attention、3D/1D temporal RoPE、cross-modality AdaLN、Gemma 全层特征、thinking registers、音频/视频 causal VAE、flow matching、modality-CFG、1080p 多尺度重叠 tiles、训练数据、实验、局限与社会影响。
- 12 张 bespoke 图与 18 条可点击术语；用 0.40s 碰撞 attention、三层特征拼接、25 token/s、CFG 三分支、tile overlap、H100 22.30/1.22=18.28× 贯穿手算。
- 证据审计：内部质量人评未公开样本数/胜率/置信区间，训练规模与优化配置缺失；速度表不是同架构单变量消融；保留正文 14B+5B 与结论 13B+3B 的冲突。
- 官方实现核对 commit `9377758131b1ffde4b7f766804590a6617bf2ab9`：两向 cross-attn 读取同一份 pre-AV 快照，本流 timestep 负责 scale/shift、对方 sigma 负责 gate，thinking tokens 实为替换 padding 的 learnable registers。

## [2026-07-17] visual+fix | ltx-2 Fig 04 时间刻度与说明文字重合

- 时间刻度标签向时间轴下方伸出 29px，原先只留 20px 下边距，导致 `0.36s / 0.40s / 0.44s` 与后面的 softmax 手算叠在一起；桌面底部留白改为 64px，390px 窄屏改为 68px。

## [2026-07-17] visual+content | ltx-2 Fig 05 重画 AdaLN 与 gate 数据流

- 删除会换行成两排的孤立 `→ × →`，补上原图漏掉的 Cross-Attention：先分别算交换内容 `C` 与逐通道写回系数 `G`，再明确展示 `h′V = hV + G × C`；手机端改为纵向卡片。

## [2026-07-17] visual+content | ltx-2 Fig 07 重画 register 双向可见关系

- 删除无法表达连接关系的双椭圆装饰线；分开展示 5 个正文 token 与 3 个由 padding 改成的可学习 register，再用单一双向连接说明两组互相可见，并注明一次 attention 中同时更新。

## [2026-07-17] content+visual | ltx-2 补完整模型总览并重写 1080p 推理

- Fig 02 改为纯文本生成全路径：prompt 文本管线、两块随机 latent、一次 48-block 双流前向、外层 solver 循环、两套解码器与最终同步音视频；明确训练时才走 VAE encoder。
- §11 / Fig 10 改成 `0.5MP base → latent upscale → T/H/W 重叠分块精修 → latent 融合 → VAE decode` 四步，补 2.07MP÷0.5MP≈4.1× 的显存直觉、10/14 融合成 11 的手算，以及精修阶段音频执行路径未公开的边界。

## [2026-07-20] ingest | HDR · Hierarchical Denoising for Multi-Step Visual Reasoning

- 完整覆盖双向扩散/流式 AR 两难、Wan2.2-5B 总览、1/2/4/8/16/32 六层树、layer-wise flow matching、SHAP 可见集合与 flatten mask、共享 KV cache、O(KN²)→O(KavgN)、18k 训练配方、370 条六任务评测、主结果、层数/步数/数据/schedule 消融、实体机器人与 HDR-WAM、失败案例和证据边界。
- bespoke 页面 12 章 12 图，用 1→2→4→8 小树、L4-6 query、v⁰=2/ε=−1/t=.25、延迟账本贯穿；18 条术语可点击，桌面和手机均按独立布局设计。
- 新增 3 个 concept：hierarchical-latent-denoising、sparse-hierarchical-attention、autoregressive-vs-bidirectional-video-diffusion；复用 conditional-flow-matching 与 kv-cache。
- 公式审计发现附录 `ceil(50·(Ñ/32)^.66)` 实算 `[6,9,13,21,32,50]`，论文报告 `[5,8,13,20,32,50]` 实际对应 round；另保留代码未公开、干净层级 token 构造缺失、16.19s prefill 不应被 0.70s streaming latency 遮蔽等复现边界。

## [2026-07-21] expand | PPO → GRPO → Dr.GRPO / DAPO → GSPO 算法谱系

- 新增统一 topic，用同一道题四条回答和同一组 token 概率贯穿 PPO critic advantage、GRPO 组相对 advantage、Dr.GRPO 去偏、DAPO 四项长 CoT 配方与 GSPO 序列比率；所有公式逐项定义并说明每个分母、clip 和聚合操作为什么存在。
- 重写 PPO / GRPO / GSPO，纠正“GRPO 显存近乎减半”“token 级比率因只采一次所以无效”“所有主流模型都用 PPO”等过度概括；补 reward model、critic、reference policy 的职责边界。
- 新增 Dr.GRPO 与 DAPO concept，明确二者都处理逐回答长度归一化但缩放方式不同；记录 DAPO 的 0.2/0.28 非对称 clip、动态有效 batch 和截断软惩罚的适用边界。

## [2026-07-22] visual+concept | 自动概念页接入 KaTeX + 对数运算补课

- 自动渲染器支持显式 `\\(...\\)` 行内公式与 `\\[...\\]` 独立公式，并跳过代码块；只有真正含公式的页面才加载本地 KaTeX，避免把 `$NVDA` 一类普通文本误判成数学。
- 新增 logarithms concept，从 `log₂8=3 ⇔ 2³=8` 的定义出发，推导外加内乘、外减内除、系数进指数、不可拆 `log(x+y)` 与换底公式，并用 `log₂10≈3.321928` 反算验证。
- 将 PPO / GRPO / Dr.GRPO / DAPO / GSPO 核心目标和手算迁入 KaTeX；旧 concept 中被 Markdown 吃掉反斜杠的两处公式也恢复正确渲染。
## [2026-07-22] refine | drifting-models · 从 5 节速记重做为完整机制讲解

- 以论文 v2、附录、官方项目页与 JAX 实现重新核证：补 pushforward、核漂移逐项定义、一维数字例、反对称的单向逻辑、stopgrad 真实梯度路线、双向 softmax、特征空间、训练时 CFG、latent/pixel DiT、队列与训练配方。
- 实验不再只列最佳 FID：补吸引/排斥破坏消融、样本数/特征质量/核归一化、一步与多步的公平口径，以及机器人任务中的明确退步项。
- bespoke HTML 重做为 13 节、14 张内联图的 rust field-notes 页面，加入 KaTeX、完整模型总览、桌面/移动响应式布局与就地术语；新建 [[pushforward-distribution]] 概念页并回接 CFG、DiT、QK-Norm、perceptual loss、flow matching、DMD。
- stopgrad 段二次重写：纠正“冻结整个 f、跨轮比较”的误解，改成同一次前向里的活分支 / 目标快照分叉图；补无 stopgrad 时梯度为何抵消、旧靶验算与下一轮重新造靶的边界。
- 第 7、9 节补全数据流：解释特征空间负责选择语义邻居、冻结特征网仍通过输入 Jacobian 传梯度，并列出局部/全局/分区特征；从 patchify 开始追踪 latent/pixel 的 256 个图像 token、两路条件注入、272 长度序列与 unpatchify。纠正 32 个 style embedding 被误写成 32 个序列 token：它们先求和并入条件向量。

## [2026-07-22] rewrite | Qwen3-VL · 面向初学者的完整系统讲解

- 从 4 节摘要扩成 12 节完整页：用“像素 → Qwen3-ViT → 2×2 merger → 图文同序列 → 自回归答案”贯穿架构，并用 `12×16→6×8` 手算视觉 token 数与 merger 维度。
- DeepStack、Interleaved-MRoPE、文字时间戳全部改成“旧数据流为什么不够 → 新零件接在哪 → 数字例 → 代价与消融边界”；纠正“Thinking 总更强”“纯文本全面反超”“三项结构独自产生全部长视频增益”等过度结论。
- 补齐原报告九类预训练数据、四阶段预训练、120 万 SFT、off/on-policy 蒸馏、Reasoning/General RL、Thinking with Images 奖励漏洞、五种分布式并行、11 类评测口径、1M needle 测试条件和横评帧预算差异。
- bespoke HTML 重做为 15 张响应式内联图并接入 KaTeX；同步修订 M-RoPE 与 modality projector 概念页，并回接 MoE、分布式并行、SGLang 和 on/off-policy。

## [2026-07-22] ingest | DMD · One-step Diffusion with Distribution Matching Distillation

- 逐节覆盖 CVPR 主文与 22 页 arXiv 附录：从一步生成器初始化、反向 KL、两个 score、加噪重叠、动态 fake-score、时间权重、LPIPS 回归、CFG 蒸馏一路讲到 Algorithm 1/2/3、附录梯度推导和四套训练配方。
- 用同一条标量例从 `x_t=.66` 算出 real/fake score、`w=1.5`、生成器梯度 `−1.6`、参数更新与 stopgrad 伪损失，明确伪 MSE 只负责注入梯度，不是 KL 数值。
- 纠正旧概念页把原始 DMD 写成 4 步、把“不逐样本强制对齐”写成近似无配对的混淆；原论文严格为 1 NFE，DMD2/TDM 与后续 4/8 步应用分开记。
- 补齐 ImageNet / CIFAR / COCO 主结果、两项损失和时间权重消融、LPIPS/L2 补充实验、测速口径与显存/配对集/fake-score 追踪等局限。

## [2026-07-23] rebuild | DMD · 从复习摘要改成可逐行跟算的入门教程

- 开篇新增三网络、两拍更新、两条数据流的完整训练总览，明确训练脚手架与一步推理解耦；权重迁移改为“复制哪些参数、接口哪里变、重新学什么”。
- 补回此前缺失的近似输出梯度与时间权重母公式；所有公式统一增加用途说明和逐符号解释，CFG 也补完整公式与数字代入。
- §07 改成八行工作表，每行并排展示母公式、本轮代入和结果，从 `z=.5` 一直算到 `θnew=.86、xnew=1.36`，不再跳过公式直接塞数字。
- 重做 KL 方向、加噪交叠、双 score 支路、模式覆盖和训练循环图；模式示意真的绘制 8 个样本并分别落成 `8/0、6/2、4/4`，不再让图中文字与实际图形矛盾。
- 箭头专项回归：修正双 score 图把 `fake−real` 画成 `real−fake` 的顺序错误；流程箭头改为独立布局项，手机端只旋转箭头、不再把说明文字一起旋转；stopgrad 图明确画出从损失回到生成器的反传方向。

## [2026-07-23] visual fix | Qwen3-VL 图示布局回归

- Fig 02A 把图片形状、token 数字和解释拆成三行正常布局，修复极长页面示意块覆盖 `11,427`。
- Fig 06 的阶段箭头改成独立连接项，桌面端位于卡片之间、手机端向下排列；同类的 Fig 09 agent 六步箭头同步修复。

## [2026-07-23] ingest | DMD2 · Improved Distribution Matching Distillation

- 逐节覆盖 NeurIPS 2024 主文、附录与官方实现 commit `8d8fa556`：从原 DMD 配对回归的 700 A100·天成本，讲到去回归、fake-score 5:1 TTUR、真实图 GAN、四步时间表、backward simulation、共享 UNet bottleneck 分类头和三套训练配方。
- 公式不再把判别器与生成器方向挤在一行：分别列出 softplus 版 `L_D` 与非饱和 `L_G^GAN`，逐项解释 logit、期望和梯度归属；多步去噪与重新加噪也给出完整母公式和符号表。
- 用 `x_real=2.0`、第一步学生预测 `.4` 的一维例，算出传统真实图加噪输入 `1.043` 与真实推理输入 `−.077`，把训练—推理错位和 backward simulation 为什么必要算到最终差值 `1.120`。
- bespoke HTML 做成 15 节、14 张响应式图；所有流程箭头都是独立布局项，桌面横向、手机纵向，只改变箭头本身，不旋转说明文字。
- 保留关键边界：ImageNet 5:1 不是理论常数，SD v1.5 实际用 10:1；SDXL 一步仍靠 10K 配对短预热；一步 1.28 只在对齐采样器与老师口径后才能说“超过老师”；官方 FSDP / LoRA 性能问题只代表当时实现状态。

## [2026-07-23] rewrite | Drifting Models §09 · 先说这章干什么，再拆生成器

- 把 §09 从架构名词清单改成一条可追踪的部署数据流：先划清“训练脚手架最后删除 / 生成器 `fθ` 最后保留”，明确这一章不再介绍新的漂移算法。
- 先解释 latent 与 pixel 是两种独立模型、推理时二选一，再用 `4×4` 数字网格把 patchify / unpatchify 手工拆开，说明切块只是 Transformer 接口，不负责去噪。
- 逐项解释类别、guidance 与随机 style 索引；区分 AdaLN 的逐层调节和 16 个条件 token 的注意力入口，明确 32 个 style embedding 求和后不会增加序列长度。
- 用 latent L/2 把 `32×32×4 → 256×16 → 256×1024 → 272×1024 → 256×16 → 32×32×4` 从头算到尾，并补上“1 NFE 是调用一次 24 层生成器，不是只有一层”的口径。

## [2026-07-23] concept+rewrite | Score 从零讲起 · 补齐 DMD 老师训练与 Drifting 分界

- 重写 score-function 概念页：从“照片修复师怎样学会写修改批注”进入，完整走过真实图、随机噪声时刻、已知噪声、带噪输入、预测噪声与均方误差训练，不再默认读者已经学过扩散模型。
- 用同一组 `x₀=1.5、α=.8、σ=.6、ε=−.9` 验算 `xₜ=.66`，再从噪声预测和干净图预测两条等价路径都得到 score `1.50`；逐项解释 `ψ、t、α、σ、ε、μ、λ` 的职责。
- DMD 新增 real-score 生命周期与 Fig 06A：老师先在 DMD 外完成普通扩散预训练，进入 DMD 后冻结；动态 fake-score 仍只追踪学生最新分布。首页与总览同步标出这段前置，不再让 real score 像凭空出现。
- Drifting 新增生活化对照：DMD 是先培养一位修复老师再查询方向，Drifting 是每轮把真实样本和当前生成样本摊开后现场计算核漂移；明确后者不训练、不调用 score 网络，箭头相似不代表算法相同。

## [2026-07-23] rebuild | DMD2 · 从“改动清单”重排为零前置教程

- 新增 §00 独立入口：先用学生修照片的短类比分清 real score、fake score 与配对回归，再用 `x=1.2` 同一条标量例从加噪算到 `sreal−sfake≈1.3333`，不再默认读者已经把 DMD 记在脑中。
- 把 DMD2 重排成四个连续因果：删配对回归 → TTUR 补 fake-score 追踪 → GAN 直接读取真实图 → backward simulation 对齐多步输入；总览图逐项标出“哪项改动补哪个洞”。
- TTUR 新增过时 score 把正确步长 `.20` 放大成 `.80` 的数字例；GAN 将 `areal=1.2、afake=−.7` 逐项代入 softplus，并验证学生 logit 升到 `.2` 后生成器损失 `1.103→.598`。
- 训练循环补齐官方变量映射：`loss_dm / gen_cls_loss / loss_fake / cls_loss` 分别更新谁，明确 `loss_dm` 只是注入分布梯度的伪损失、`detach` 只截断梯度；backward simulation 同步澄清不是反向传播。

## [2026-07-24] ingest | Solaris · 双人 Minecraft 视频世界模型

- 新增 `wiki/papers/solaris-multiplayer-world-model.md` 与 bespoke `docs/papers/solaris-multiplayer-world-model.html`。
- 按“为什么多人难 → 同步数据 → player 张量与共享注意力 → Flow Matching 手算 → 四阶段训练 → Checkpointed Self Forcing → 评测与边界”重排，不照原文章节复述。
- 用 `x=2, ε=-1, σ=.25` 从混合、目标速度、损失一路算到 `x̂₀=2`；逐个解释 `B/P/T/H/W/C/D`、`Ls/Lt` 与两遍重算为何仍可反传。
- 收录 Table 2/3 的关键原值和反例：Solaris 五项 FID 最低，但 Movement VLM 低于 frame concat；KV-BP 改善 FID 的同时让三项动作指标下降。

## [2026-07-24] ingest | Towards Interactive Video World Modeling · 交互式世界模型综述

- 新增 `wiki/papers/interactive-video-world-modeling-survey.md` 与 bespoke `docs/papers/interactive-video-world-modeling-survey.html`。
- 以“走进房间再回头”的闭环例子解释 `o_{t+1}~pφ(o_{t+1}|Ht,at,ct)` 和 POMDP，再把全领域重组为界面、动作注入、记忆、生成主干、推理加速、评测六层。
- 将历史帧、latent memory、显式 3D memory、直接重建 3D 排成四级记忆；对照 Teacher / Diffusion / Self / LIVE / Geometry / Context Forcing，明确 forcing 改的是训练历史来源。
- 单独解释一致性与动作响应的冲突、少步蒸馏和两类缓存、四应用评测地图，并强调综述表格来自不同协议，不能当统一排行榜。
- 更新 `flow-matching`、`kv-cache`、`world-foundation-model`、`autoregressive-vs-bidirectional-video-diffusion` 与 `diffusion-transformer` 的 sources 和回链。

## [2026-07-24] ingest | SenseFlow · Scaling DMD to SD 3.5 / FLUX

- 新增 `wiki/papers/senseflow.md` 与 bespoke `docs/papers/senseflow.html`，按“DMD 前置 → 内循环失稳 → IDA → ISG → VFM 判别器 → 完整循环 → 实验与边界”重排，不照论文目录复述。
- 从 `V=KL(pg||pr)-KL(pg||pf)` 逐行说明 fake 追踪误差怎样污染外循环；用 `θ=2、φ=1.5、λ=.97` 算出 IDA 的 `φnew=1.515`，并保留理论依赖局部 Lipschitz、Fisher-to-KL 等假设的边界。
- 用 `.75→.60→.50` 同一条一维轨迹算完 ISG：老师前半段得到 `.50`，冻结学生后半段得到目标 `.65`，直接学生得到 `.45`，平方误差 `.04`；明确目标不是老师独跑全程。
- 核对官方代码 commit `fafc81b7`：SD3.5 Large 的 IDA 权重为 `.97`；ISG 实现用平滑绝对误差而非正文 L2，并在段端点留 50 index、老师前半段用 CFG=5；v2 附录也更正真实参考图走 DINOv2 而非 CLIP。
- 新增 `implicit-distribution-alignment`、`intra-segment-guidance`、`vfm-discriminator`、`hinge-loss` 四个 concept；实验同时记录 SDXL 的 Patch FID-T / CLIP 退步、CLIP diversity 约降 18.6%、一步需要额外 6000 iteration 微调等反例。

## [2026-07-24] revise | dmd
- 重排 §05/§06：把「梯度怎么推」（反向 KL → s_fake−s_real 的推导）挪到手算例之前，读者先懂公式再代数字，不再是「先算后解释」。
- §05 按多步推导规范重写：五步路线图 + 五样小工具（期望/换元抽样/链式法则/θ多处分头求/总概率=1）+ 逐步不跳（reparameterization→拆两块→real块→fake块两条路→消失项）+ 贯穿 running numeric（x=1.2, s_real=1.5, s_fake=.1667 → 原始方向 −1.333 → 裹权重得 gₓ=−1.6）。
- 「p_fake 也依赖 θ 为何不多一项」从脚注升为独立一步（score-function 恒等式 = 总概率恒为 1），并用 N(θ,·) 数值验证均衡/非均衡两组都 →0。
- 删除运行时 crossRefs 文本 hack（§06→§04 会污染新正文）；源码内 section 号与阅读序对齐。

## [2026-07-24] ingest | U-Net · 一边看清是什么，一边记住它在哪

- 按“像素分割 → 滑窗浪费 → U 形全图 → 尺寸账 → skip → overlap-tile → 边界损失 → 小数据训练 → 实验边界”重排原论文，不把现代 same-padding U-Net 冒充 2015 原版。
- 用完整尺寸链从 `572→570→…→28→…→388` 算清 23 个卷积层，并用 `64→crop 56→concat 1024` 解释为何原版跳连必须先裁剪。
- 从 `d₁=d₂=1、w₀=10、σ=5` 算出边界权重 `10.231`，再把错误概率 `.119` 算到加权损失 `21.76`；同时标明原文 Eq. (1) 少负号与实际最小化交叉熵的口径。
- 补齐 batch 1 / momentum .99、He 初始化 `√(2/576)=.0589`、3×3 控制网格弹性形变、三套数据与完整原表数字，并保留 DIVE-SCI 在 Rand / pixel error 上更优、论文无逐项消融等反例。
- 新增 semantic-segmentation、fully-convolutional-network、skip-connection、transposed-convolution、weighted-pixelwise-cross-entropy 五个 concept，并修正 softmax 页旧数字例的求和与概率。

## [2026-07-24] ingest | Drift-AR · 同一种熵信号，两头加速视觉自回归

- 不照论文目录复述，改按“为什么慢两遍 → 熵到底是什么 → 左线推测解码 → 右线单步漂移 → 两阶段训练 → 实验与缺口”组织；总览图先把两条加速线拼成完整系统。
- 用同一组注意力概率手算原始熵、`log r` 归一化、动态停止阈值，再把熵代入 `σ(E)`，从 `z_AR=1.2、ε=−.5` 算到两个不同的高斯起点；所有公式先说明用途，再逐项解释符号。
- 明确论文所谓 prediction entropy 实际是倒数第二层因果注意力熵，只是连续特征误差的代理；同时纠正正文把 `σ` 混叫 variance 的口径：公式里 `σ` 是标准差，方差是 `σ²`。
- 补齐两阶段权重退火、Phase II 冻结、Entropy-AdaLN、上下文动态早停、ImageNet / NextStep 主表、五项消融、解码步数与 `σmax` 敏感性；保留无接受率、无分项延迟、无硬件与训练时长、代码仓库暂未公开内容等复现缺口。
- 新增 speculative-decoding、causal-normalized-attention-entropy、entropy-parameterized-prior 三个 concept，并回接 AdaLN、EMA、高斯协方差、stopgrad、DMD 与对数。

## [2026-07-24] audit | 用新版论文讲解标准复查近期九篇

- 将 Claude 版论文讲解 skill 的新增细则合并进当前 `study-paper-ingest`：每节按前置引入、中文表达、公式讲解、行文逻辑、配图五维评分；任一项不超过 3 分必须返工并复评，同时保留现有更严格的公式顺序、running example、反例与证据边界规则。
- 逐章复核 Qwen3-VL、Solaris、交互式世界模型综述、SenseFlow、U-Net、Drift-AR、DMD、DMD2 与 Drifting Models；完整评分和返工证据记录在 `quality-audits/2026-07-24-recent-papers.md`。
- 对六篇低分页同步修订 Markdown 与 bespoke HTML：把符号定义移到公式之前，补齐公式“解决什么问题—怎样构造—为什么这样算”，并增加 MRoPE 旋转、on-policy KL、联合概率、动作调制、IDA/ISG、卷积尺寸、边界损失、熵先验与漂移更新等可复算数字例。
- DMD、DMD2 与 Drifting Models 各节复评分均不低于 4，保留现状，不为制造改动而重写已经闭环的内容。
- 九篇共 102 条 KaTeX 表达式强解析通过；HTML 重复 ID、页内锚点、本地链接、术语跳转和最终差异检查全部通过。

## [2026-07-24] ingest | minWM · 从双向视频扩散到四步因果世界模型

- 新增论文页 `wiki/papers/minwm.md` 与 bespoke 页面 `docs/papers/minwm.html`
- 以“可控→因果→少步→self-rollout 纠偏”重排技术报告，不照原论文段落平移
- 11 张 CSS 图分别覆盖完整流水线、三道交互门槛、三类轨迹数据、PRoPE 相对相机、teacher forcing 错位、ODE/CD 分叉、asymmetric DMD、首帧延迟、双 backbone、证据边界和开源状态
- 三组数字例已复核：ODE 平方误差 `.20`、CD 损失 `.005`、DMD 梯度 `−.4 → θ=1.04`
- 新增 `projective-rope`、`teacher-forcing-video-diffusion`、`causal-consistency-distillation` 三个概念页，并回链 DMD 与双向/因果视频扩散
- 对照论文 TeX 与官方仓库 commit `df522a26`，单独记录论文训练配方、脚本默认值、VAE 排除口径和 README 的 TBD 项

## [2026-07-26] ingest | Data-Forcing Distillation · 让 DMD 的老师重新看到真实视频

- 新增 `wiki/papers/data-forcing-distillation.md` 与 bespoke `docs/papers/data-forcing-distillation.html`；不照论文目录复述，改按“反向 KL 漏模式 → 三套网络 → DMD 原路径 → teacher score discrepancy → 精确抵消 → 一行代码 → 成立条件 → 数据与实验”组织。
- 用同一条主线解释 fake-score 始终读取学生视频、teacher 才按概率改读同条件真实视频；明确 DFD 不是把真实视频当随机噪声的逐像素标签，也不是从零取代 DMD2。
- 补齐五组可复算数字：两格反向 KL `.693`、score 正则抵消 `−.40→−.10`、伪目标损失 `.500→.405`、共享噪声差 `.4`、理论误差上界 `.09`，所有公式都在代数前定义符号。
- 覆盖 ViPE 96.6 万→30K 筛选、Wan T2V / Cosmos I2V / Self Forcing AR、GAN / 权重 / 预训练 / batch 消融、两步局限和社会风险；保留 teacher 多样性仍更高、AR 主要定性、batch 两列略降等反例。
- 新增 `teacher-score-discrepancy` 概念页，并回接 `dmd-distillation`、`score-function` 与 `entropy-kl`；对照 arXiv v2 和官方代码 commit `7281906`，记录摘要 100–300 与正文残留 50–100，以及论文“DFD 不需 GAN”与当前 README 仍继承 GAN 权重 `.03` 的两处差异。

## [2026-07-26] revise | Solaris §07 Checkpointed Self Forcing 重写

- 用户反馈第 7 章看不懂。原文只有一张显存对照图、一条 `X_in=[X_0,X_s]` 公式和一张没有读法的 mask 表；`L_s` / `L_t` 全章从未定义就出现在 figcaption 里。
- 重写成四段递进：①先定义"激活"和"1 份帧激活"这个记账单位，说清显存到底被谁吃掉；②拆出两条相乘的轴（每帧多步去噪已被原版 Self Forcing 砍掉；滑窗重叠才是 Solaris 要解的），并在此处才引入 `L_s`/`L_t`/`N`；③第一遍缓存什么、两组值各自当"历史"还是"待办"；④第二遍为什么拼起来就能一次算完，并补上 gradient checkpointing 的类比解释"Checkpointed"这个名字。
- 补可手算的显存账：`L_s=6, L_t=20` → 朴素 `20×6=120` 份 vs 两遍法 `2×20=40` 份；再把窗口放宽到 12 得 240 vs 40，坐实真正买到的是"显存不含 `L_s`"而不是那个固定倍数。
- Fig 10 mask 补三行逐格读法：clean 行为什么全禁 noisy 列、N3 为什么读不到 C3（等于抄答案）、N4 为什么读不到 C1（窗口只有 3 而非因为是未来）。
- 诚实标注：论文只说 teacher 上下文比 student 长，没给 `L_t` 帧数，也没有实测显存曲线；20 是示例值，`L_s=6` 才是论文配置。
- `render.py` 的 mathify 选择器加 `.sym code`，本页三处符号表改写成 `<code>` 让 KaTeX 接管（此前 `x_t` / `x_<t` 直接以原样文本显示）。

## [2026-07-26] revise | Solaris 全页按 rubric 扫一遍，补 §00 / §03 / §04 / §05 / §06 / §08

- §00 补"为什么训练要养两个模型"：双向 teacher 信息全但必须整段在手才能算（按一下 W 它还等着看第 100 帧），因果 student 能边玩边吐但从零训质量差 → 先训双向再改造成因果。此前只有一句"训练时有 teacher 和 student"，读者拿不到动机。
- §03 补论文唯一架构改动的手算：`P=2,T=2` 交错成 4-token 序列 + 谁能读谁的可见性表，再拿 §01 那根火把顺着表走三步（动作只注入 P1·t1 → P2·t1 读到它 → t2 继续读回）。另补共享序列的真实代价：6 帧 ×2 人 ×256 = 3,072 token，attention 944 万分数，单人 236 万，翻四倍。诚实标注论文没写明交错顺序。
- §03 补 `(B P) T D` 的 reshape 语义（小括号=压成一维，2 局 ×2 人 → 4 条独立样本），此前只说"因此不会误当"没说为什么。
- §04 修记号错误 `||e||²₂` → `‖e‖₂²`（正文文字说明的顺序是对的，写法反了）；补"速度为什么是 `ε−x`"的一步求导（逐项：`x` 常数得 `−x`，`ε` 常数得 `ε`，结果不含 `σ` 所以恒定），手算块加"验速度真是常数"两行。
- §05 每张 stage 卡片补"跳了会怎样"，并写明 Stage 3 是从 Stage 2 的 60K **分叉**而非接在终点，论文理由是省训练时间，两阶段有一段并行。
- §06 补"分布匹配"的定义与动机：滚在自己历史上 → 没有配对真值可比 → 改问整批像不像 teacher 生成的；新增 glossary 11 条。诚实标注论文没点名 DMD 哪一版。
- §08 补两个数为什么并列（FID 不知道你按没按 W，VLM 不在乎画面糊）、四条读表顺序、Building 列 `0.0` / `20.8` 的解读，以及 FID 与 VLM 打架的机理（压视觉分布=奖励更典型=更保守=动作跟随下降）。
- skill 加两条：figcaption / 表头 / 图内标注同样受 define-before-use 约束（solaris `Lₛ`/`Lₜ` 印在图注上就是这么断的）；"大家都知道"的小工具恰恰最该展开来路。

## [2026-07-26] revise | Solaris §07 补"它不只是时间换空间"

- 读者问"第 7 节讲的就是时间换空间吗"——原文那句 gradient checkpointing 类比读起来就是纯粹的等价交换，引出了这个问题。
- 补三条差异：①重算的不是同一段计算而是改写过的（vanilla checkpointing 原样重跑不需设计，这里 N 次串行改写成 1 次并行，所以才必须造 mask 复刻处境）；②买到的不只是同样结果+更少显存，原版对 KV 停梯度是"要不起"不是"不想要"，显存压下来才多出这条梯度路径，等于换了条曲线而非沿曲线滑动；③换来的空间不是固定倍数，是把 L_s 从式子里消掉。
- 诚实标注"多花多少时间"论文没给，且方向不显然：第二遍序列 2N、注意力平方项，FLOPs 未必更省，但一次并行前向的硬件利用率远高于 N 次串行小前向，wall-clock 可能反而好看；论文既无显存曲线也无速度表。

## [2026-07-26] revise | Solaris §07 补"第二遍照样占显存"与"存值≠存图"

- 读者问"第二遍相当于算一部分就传一部分梯度，所以不耗显存吗"——原文写了"第一遍不留、第二遍一条序列"，容易读成第二遍也不占。
- 补一条 warn：反向传播顺序是反的，第二遍前向必须整个跑完才能反传，峰值卡在前向结束那一刻；第二遍占的正是那 40 份，是从 120 降到 40 不是降到 0；省下的 80 份来自第一遍那 120 份图从来没建过。并注明分块反传/梯度累积（FlashAttention 那类）省的是一次前向内部的激活，与本节是两层问题、可叠加，论文没提。
- 补"存一个值 ≠ 存一条计算图"：X_0/X_s 是 2N 个张量，一条计算图是这帧穿过 DiT 每一层的全部中间结果，有多少层翻多少倍——这是"缓存几十份值换掉上百份图"能成立的前提，此前被默认为常识跳过了。
- 同步把 §7.4 里"激活可以当场丢掉"改成更准的"从来没建过"（no-grad 下框架根本不记录中间结果）。

## [2026-07-26] revise | Solaris §07 把"朴素滑窗为什么是 Lt×Ls"真正推出来

- 读者反馈两遍法那侧算得懂，但朴素那侧"不知道咋就多出那么多份图"。原文只有一句断言"总量是行数 × 每行长度"，没推。
- 换个数法：不数"每步留几份"，数"同一帧被留几次"。盯第 3 帧列出它第 3~8 步一直在窗口里、第 9 步滑出，正好 6 次 = L_s。关键补一句：这 6 次不是同一份激活被引用 6 回，是 6 次各自独立的前向，各留一份全新的中间结果。
- 补"那 KV cache 呢"这个必然的追问：推理能救训练不能——把历史 K/V 当常量是 cache 的前提，一旦要梯度穿过它们就只剩三条路（留整条 rollout 链 / 每窗重算 / 对 KV 停梯度），原版 Self Forcing 选第三条，Solaris 要把那条梯度拿回来所以只能在前两条里挑。
- 闭环补 §07 新小节"L_s 到底在哪一步消失的"：mask 表里 C2 被 L_s 个 noisy query 同时读，但只算了一份——串行时第 3 帧重算 6 遍各服务 1 步，并行时算 1 遍同时服务 6 个 query。L_s 不是被优化掉的，是重复计算被合并了。
- 修数字：原文 20×6=120 是上界，精确值 105（开头 5 步窗口没填满）。补两笔缩放账：L_s 6→12 朴素 105→174 而两遍法不动；L_t 拉到 100 时 585/200=2.9 倍、1134/200=5.7 倍，倍数趋近 L_s/2。全部 python 复核。
- 修两处自己写错的：①第 8 步窗口是 [3..8] 仍含第 3 帧，滑出发生在第 9 步（原写成第 8 步就没了，与"6 次"自相矛盾）；②L_s/L_t 符号表排在使用之后，违反刚写进 skill 的 define-before-use，已挪到轴二之前。

## [2026-07-26] tooling | 新增 lint_paper.py：把靠回忆过不了的自检变成脚本

- 起因：上一轮刚把 define-before-use 写进 SKILL §3.6.2、还专门加了"figcaption 也算正文"，紧接着在同一次会话的下一个编辑里就违反了它（Lₛ/Lₜ 符号表排在首次使用之后），而且此前已经这样错了两轮、两次人工 review 都放行。根因不是不认同规则，是检查方式错了：用"回忆"验（定义过吗？定义过啊）而规则要的是"位置比较"（定义在使用之前吗）。
- 结论：凡是能被"我记得我做了"骗过的规则，写多少遍 checklist 都会漏，得搬成脚本。
- lint_paper.py 分两级。ERROR（机械可判、必须清零）：glossary 孤儿/死链、标签开合不平衡、属性用中文引号、残留 markdown 反引号。WARN（启发式、要人眼）：define-before-use（带 500 字符就地定义容差）、figcaption 里出现未定义下标符号、§3.7 聊天语境词、中文夹没空格的英文。
- 调参过程本身是重点：第一版 45 个 ERROR 里一多半是误报——只认了 .sym 一种符号格子（存量页还有 .symbol/.var/.vars/.symbol-grid，.symbol 才是最多的）、把 log₂N 切出 g₂、把中文标签「目标」当符号、把 MLP/LPIPS/log/score/stopgrad 这类缩写和英文词当符号、把整条等式当符号、以及 <li[ >] 本来就不匹配 <link 却多减了一次。逐条核实真伪后才定稿，现在 13 ERROR / 24 WARN，ERROR 全是真的 glossary 孤儿。
- 回归测试：把 solaris 的符号表挪回错位置，linter 同时报出 define-before-use 和 figcaption 两条，确认能抓到当初那个 bug。
- 全站 backlog：13 页有 glossary 孤儿条目（attention 9 条最多，fish-speech 4、fft 2、ode-sde 2，其余各 1），都是"glossary 写了但正文没有 .jr 入口"这个 §8 里记过的老毛病。这次只建账不修。
- SKILL 加 §7.1 记这条方法论，并把原来那几条肉眼自检换成"跑 lint_paper.py --warn 零输出"；同时写明两条纪律：新写/重写的页 WARN 也要逐条处置不许无视；但不许为了让 linter 闭嘴而改坏内容（define-before-use 有"挪表"和"表本来冗余"两种正解）。

## [2026-07-26] fix | 清掉全站 27 条 glossary 孤儿 + 修符号格子里行内 code 被顶行

- lint_paper.py 查出 13 页共 27 条 glossary 孤儿（写了词条但正文没有 .jr 入口，点不进去）。attention 最惨：12 条词条只有 3 个入口，9 条是死的。这是 SKILL §8 记了很久但一直没人查的老毛病。
- 写 fix_gloss_orphans.py 批量补入口：自动识别每页用的是包裹式（`<a class="jr">RNN<sup>1</sup></a>`，attention/fish-speech）还是上标式（`术语<a class="jr">1</a>`，其余页）；挂点优先用词条主名（「GSPO（RL 阶段）」该挂 GSPO 不挂「RL 阶段」），主名没安全落点才退到最具体的别名；排除 SVG 内文字、已有链接内部、目录、大标题、figcaption。干跑核对全部落点后才 --apply，自动补了 25 条。
- 剩 2 条手工：attention g-08「residual connection」正文只写了裸 residual；ode-sde g-05「score 函数」所有出现都包在 concept 链接里，按本仓惯例把 .jr 追加到 </a> 之后。这个限制已写进脚本 docstring。
- 验证：把新旧两版的全部 .jr 都剥掉后逐字节对比，13 页完全一致 —— 27 处纯增量，正文一个字没动。浏览器实测 attention 12/12 入口都渲染正确、锚点跳转命中词条。
- 顺带修一个早就存在的排版 bug：`.symbol code{display:block}` 本意是让格子开头那个符号单独成行当标签，却把说明文字里的行内 code 也顶成块级，读起来像莫名其妙的断行（senseflow「负责让 p_f 追上 p_g」被拆成四行）。mathify 给这些 code 上了色之后更显眼。在 render.py 注入的样式里加 `code:not(:first-child){display:inline}` 兜底，影响 senseflow 3 处 + dmd2 1 处。
- 全站现在 0 ERROR / 24 WARN（WARN 全是 define-before-use 与 figcaption 的启发式提示，当 backlog）。

## [2026-07-26] revise | senseflow §05 重写 + 修 mathify 上标全局 bug

- 用户反馈第 5 节（ISG）看不懂、感觉省了细节。对照发现 HTML 版比 md 版少了一大截：md 里那段逐步手算（x_mid / x_tar / x_direct 每一步代入）在 HTML 里只剩 Fig 04 的结果数字，读者看到 `vreal=-2` 和 `xmid=.50` 完全不知道 .50 哪来的。
- §05 重写成五段：①anchor 是什么、为什么只有四个、τ=1 是噪声 τ=0 是干净（方向此前从未交代）+ 三个模型的 anchor 表（HTML 版原本丢了）；②ξ(t) 先逐符号定义再给公式（原来先用后定义），并把「ξ 局部振荡 → anchor 落在尖峰 → 学生学偏 → 这个点要代表整段」的因果链摊开；③两条路线的构造，先讲欧拉步 x_new = x_old + Δt·v 并点明去噪时 Δt 为负、负负得正这个符号陷阱；④一组数字从头算到尾（含 Δt 相加自检 −.15+−.10=−.25）；⑤三个"为什么"：为什么重抽 t_mid、为什么必须 stopgrad（不冻就能靠两边一起塌到平凡值把 loss 刷到 0）、为什么目标支路留学生走后半段。
- 第三个"为什么"论文没有正面论证，已明确标注是合理推测而非论文结论。代码差异那条补上"两端各留 50 个 index"的原因（避免某半段长度≈0 白走）。
- 全部算术 python 复核；散文里的 `τ_i → τ_{i-1}` 等裸 LaTeX 改成 unicode 下标（mathify 只管符号格子不管散文）。
- 修 `.calc` 块：这页的 .calc 没有 white-space:pre，原有写法是手写 <br>，我按 pre 写导致整块挤成一段。
- **修 mathify 全局 bug**：toTex 只有多字母下标规则（`_adv` → `_{\mathrm{adv}}`），没有对应的上标规则。于是 `L_G^adv` 里的 `^adv` 原样进 KaTeX，被解析成「`^a` 上标 + 正文 `dv`」，显示成 `L_G^a dv`。这是合法 LaTeX，所以 throwOnError 抓不到、katex-error 计数为 0。已把规则改成同时处理 `[_^]`。
- senseflow §07 四个 loss 格子写法本来就不统一（L_DMD/L_ISG 被 CONST_NAME 规则跳过保持 code 样式，另两个走 mathify），现统一写成与公式逐字一致的 LaTeX。
- SKILL 加一条：**katex-error==0 ≠ 渲染对了**，没报错但没亲眼看过的公式不算验过；同一条式子在符号格子和正式公式里出现两次时两处必须逐字一致。

## [2026-07-26] fix | 统一符号格子与公式的渲染路径（手写 LaTeX 走 verbatim）

- 起因：用户问"为啥要用两种不同的渲染方式"。确实是历史遗留——`.formula[data-display]` 由页内脚本直接 katex.render()，输入是手写标准 LaTeX；符号格子的 `<code>` 走 render.py 注入的 mathify，先过一层 toTex() 猜+改写再渲染。toTex 那层只是为了兼容存量页里随手写的松散记号（θbase / p_fake / L_G^adv），却会把我手写的规范 LaTeX 也改写一遍，两条路就分叉了。
- 改法：mathify 里凡是含反斜杠（= 手写 LaTeX 命令）的原样送 KaTeX，不再过 toTex；toTex 只服务于松散记号。这样同一条式子在格子和公式两处必然逐字一致。
- 踩坑：MATHIFY_BLOCK 是 Python 非 raw 字符串，源码写 `'\\'` 到 JS 只剩 `'\'`，是未闭合字符串字面量 → 整个 mathify IIFE SyntaxError 不执行 → 全站符号格子静默退化成灰底 code（0/49 mathified）。要写 4 个反斜杠。没 commit 前被浏览器实测抓到。
- 精确回归范围：全站 mathify 作用域内 8243 个 code，含反斜杠的只有 25 个唯一串（senseflow 8 + solaris 5 + 4 个存量 concept 页）。逐个在浏览器里验过渲染结果，含 unicode 希腊字母的 `\hat x_{t-Δt}^i`、`π(a|s)` 都正常。
- 顺带查出并修两个真 bug：① markdown 表格里 `` `a\|b` `` 的转义反斜杠 python-markdown 不会在 code span 里还原，留着被 mathify 当成 KaTeX 的 `\|`(‖)——Whisper 的 `<|zh|>` 渲染成 `<‖zh‖>`，rl-for-llm-people 的 `π(a\|s)` 渲染成 `π(a∥s)` 而同页邻居是正确的 `π(a∣s)`。在 md→html 之后加一道还原。② looksLikeMath 加规则：`<...>` 形状的是 token 不是数学，`<eos>` / `<|zh|>` 不再被当公式渲染。
- senseflow §07 的 `D_KL` 格子被 CONST_NAME 规则误伤（保持灰底 code，与公式里的漂亮下标不一致），改写成 `D_{\mathrm{KL}}` 走 verbatim。
- 最终验证：lint 80 页 0 ERROR；浏览器 iframe 实扫 22 个 paper（271 格）+ 12 个 concept（483 格），katex-error 全 0。

## [2026-07-26] skill | 把这轮的验证纪律固化进 SKILL（7.2–7.5）

- 7.2 验证必须做正向断言。血泪：mathify 注入的 JS 有个未闭合字符串 → 整块 IIFE SyntaxError 不执行 → 全站符号格子静默退回灰底 code，而 katex-error=0、lint 全绿、页面不崩。只查"有没有错"的检查看不见"功能压根没跑"。给了一段固定的验证片段（katexErr/unrendered 归零 + mathified/cells 正向对账 + skipped 逐条看），并写明 fetch() 不执行脚本、要验渲染必须真加载（iframe 要 await onload 后再等一拍，因为 mathify 是 setTimeout(run,0) 起的）。
- 7.3 改共用代码路径时回归范围要算出来。先用脚本算清"哪些输入会真的改变行为"（这次是含反斜杠的 code，8243 个里只有 25 个唯一串），再逐个验；验证用的选择器必须从被改代码里复制、不许凭记忆重写——我第一次扫 concept 页漏了 .concept-body code，恰是风险最高那类，cells:0 等于白扫还以为过了。
- 7.4 记两个本仓静默陷阱：render.py 注入块是 Python 非 raw 字符串，JS 里要一个反斜杠源码得写 4 个，写少了拼出未闭合字面量整块静默不执行；markdown 表格的 `\|` 是表格转义、code span 里不会自动还原。
- 7.5 约定符号格子写规范 LaTeX（含反斜杠 → verbatim，与 .formula 逐字一致），散文里的 code 不在 mathify 作用域、要用 unicode 下标。
- checklist 里那条"katex-error===0"换成跑 7.2 的正向断言片段。
- 片段本身已 dogfood：在 senseflow 上逐字跑出 48/49、skipped 只有 SDXL；又人为把页面还原成"mathify 没跑"的故障态复验，旧式检查 katexErr 仍是 0（会放行），新式 mathified 0/49 一眼暴露。

## [2026-07-26] ingest | GenCeption · 视频生成模型也能成为通用视觉骨干

- 新增 `wiki/papers/genception.md` 与 bespoke `docs/papers/genception.html`，另配三个概念页 `generation-to-perception` / `raymap` / `rgb-task-representation`。
- 主线：不给视觉任务接专用大头，而是尽量不动 WAN 2.1 的 VAE、文本编码器和 DiT——输入干净 latent、把时间固定成 `t=0`、只跑一次前向，并把速度输出取反。取反只是让初始输出方向更像干净数据，任务能力仍来自后训练；接口没被破坏才是关键（最终层还能接原 VAE decoder）。
- 目标格式统一成三通道 `[0,1]` 视频：深度、掩码、法线、DensePose 都这么编码，相机姿态拆成 raymap 的两张"Rothko"图，于是同一个 decoder + 同一条 L2 通吃。只有稀疏 3D 关键点被迫另开 token 支路。
- 数据：800 个 RenderPeople 人体 + 200 段 CMU 动作 + Blender 多渲染通道 → 7,500 段多标签视频。
- 保留了不整齐的结果：联合训练下前景分割受益，深度和相机姿态小幅回退，新增 token 的 3D 关键点严重退化——统一框架可行，但"尽量不改预训练接口"是有边界的。"一个 loss"也不是免费的，复杂度从 loss/head 搬到了 target formatter。
- 诚实标注：项目页代码截至 2026-07-26 仍 TBA；论文未公开深度映射系数 α 的取值规则、梯度裁剪/丢弃阈值、任务混合比例和 L2 的 reduction 方式。"世界模型"那部分主要是定性图，不足以支撑通用物理因果的结论。
- 收尾（本次补齐）：index.md 加 1 篇 paper + 3 个 concept 入口；`generation-to-perception` 与 `rgb-task-representation` 的 sources 已声称含 sensenova-vision，但那篇 md 里并没有反向引用，补上两处 `[[...]]` 让 ER 图闭合；genception.md 两处中英文之间漏的空格一并修掉。

## [2026-07-26] revise | sensenova-vision 补两个概念链接，并划清与「可解码视觉表示」的分界

- 上一条只修了 md 侧的反向引用（让 backlinks 生效）；bespoke 页那侧还没跟上，而这页的惯例是 md wikilink 与页内 concept 链接一一对应。
- 在 §01「统一的不是 backbone，是答案出口」补一段，同时链三个相邻概念并说清各管一头：`rgb-task-representation`（把稠密答案编码成三通道图，同一个 VAE decoder + 同一条 loss 通吃）、`generation-to-perception`（本来为了画得像才训练的生成通路被接去回答"看到了什么"）、`decodable-vision-representation`（产出来的东西能不能按确定规则还原成 benchmark 打得了分的框/点/深度值）。前两个回答"能不能用同一套通路把答案生成出来"，后一个回答"生成出来的还算不算数"。
- 现在 sensenova-vision 的 md wikilink 与 bespoke concept 链接完全一致（10 个，差集为空）。

## [2026-07-26] fix | toTex 把函数名 max 吞成 θ 的下标

- 现象：senseflow §02 的符号格子 `minθ maxφ` 渲染成 `min θ_max φ`，跟下面公式的 `\min_\theta\max_\phi` 对不上。
- 成因：toTex 先把 `θ` 换成 `\theta `（尾部带一个空格作分隔），随后"希腊字母后跟单词→变下标"那条规则用的是 `\s*`，于是把 `\theta  max` 里的 `max` 当成下标吃掉了（`max` 在 WORDS 里）。函数名规则再跑一遍，产出 `\theta_{\mathrm{\max }}` 这种嵌套垃圾。
- 修法两处：① 源码改成规范 LaTeX `\min_\theta\ \max_\phi`，含反斜杠走 verbatim，与公式逐字一致；② toTex 那条规则的 `\s*` 收成单个空格——那个空格正是希腊替换自己加的分隔符；原文里真有空格说明作者本就当两个记号，不该再吞。
- 影响面先算后改：全站符号格子里"希腊字母 + WORDS 词"的用法共 20 处，其中 19 处是紧贴写法（`σmax=.5` / `θbase` / `μfake` / `λreg` 等），收紧后行为完全不变；带空格的只有 senseflow 这一处，正是要修的。
- 扫描脚本本身先踩了个坑：Python 的 `\b` 认 Unicode 字母，`maxφ` 里 `max\b` 不匹配，第一版扫描因此漏掉了 senseflow 这条、差点得出"零影响"的错误结论。JS 的 `\b` 只认 ASCII，规则照样触发。复现 JS 语义要用 `(?![A-Za-z0-9_])` 代替 `\b`。
- 验证：node 复跑 `σmax=.5`→`\sigma_{\mathrm{max}}=.5`、`θbase`→`\theta_{\mathrm{base}}`、`μfake`→`\mu_{\mathrm{fake}}` 全部保留；浏览器实测 senseflow / drift-ar / dmd / dmd2 四页 katex-error 全 0，格子渲染数正向对账通过。

## [2026-07-26] revise | senseflow §02 补 V 的定义；散文裸 LaTeX 进 linter

- 用户问"minmax 的那个 V 是啥，也没讲"。确实：`V(θ,φ)` 在 §02 的公式里凭空出现，没有符号格子，"价值函数"这个名字全篇没出现过，而它的实际含义（`= KL(目标) − KL(追踪误差)`）要到 §03 才推出来。
- §02 补三块：① 加 `V(θ,φ)` 符号格子；② 用对照块讲清这条式子跟上一条只差一个字母但读法全变——`min_{p_g}` 对着分布本身求最小是理想写法，`min_θ max_φ` 里 `p_g` 换成了能算的 `p_f`、min 落到真能调的参数上，换掉的那一项就是全部代价；③ 新增小节"V 是什么：不是损失，是一场博弈的分数"，解释价值函数是两方共用的一个标量（生成器压小、fake 顶大），并回答"为什么 fake 要最大化"——`V` 里只有 `log p_f` 归它管，在学生采样点上把 `log p_f` 顶高就是极大似然，最优点正是 `p_f=p_g`，所以"最大化"不是跟生成器作对而是把自己校准到学生身上。最后点明 min-max 内外两层的分工并前向引用 §03。
- 又一次当场违反自己刚写的 SKILL 7.5：新写的散文里用了 `<code>\theta</code>` / `<code>\log p_f</code>`，散文不走 mathify，渲染出来是裸反斜杠。8 处改成 unicode。
- 这已是第三次同类翻车（solaris §07 也中过），所以搬进 lint_paper.py 当 ERROR：mathify 作用域外的 `<code>` 只要含 `\命令` 就报。用注入已知 bug 的方式验过检查本身有效（注入即报、清空即静），不是"扫出 0 就当过了"。
- 顺带给 senseflow 加了 `section>ul` 样式（此前全页没用过 ul）。

## [2026-07-26] fix | 散文数学终于会渲染了：mathify 加严格形状 + code.m 显式开关

- 用户指出 `p_g(X_t)` 在散文里还是灰底、露着下划线。这暴露了上一条约定本身的漏洞：我让"散文里写 unicode 下标"，可 `p_g` / `p_f` / `p_r` 的下标 g/f/r **在 unicode 里根本不存在**（只有 ₐₑₒₓₕₖₗₘₙₚₛₜ）。等于把问题从"裸反斜杠"挪成了"裸下划线"。
- 关键发现：mathify 的 looksLikeMath 本来就设计了区分数学下标与代码变量名的规则（`loss_dm` 跳过、`p_fake` 保留）。挡住散文的是**选择器**，不是分类器。
- 但直接把散文全放进作用域会误伤 commit hash（fafc81b7）、版本号（1e-5）、命令行开关（--apply）。所以给散文单独一套更严的形状：单个字母 + 下标/上标/括号参数，且必须含 `_ ^ (` 之一——光秃秃一个 `A`/`N` 不渲染（可能只是"选项 A"）。
- 形状匹配不上的（带空格的 `log p_f`、单独的 `θ`/`V`）走新增的显式开关 `<code class="m">`，任何位置都渲染，可写完整 LaTeX。
- 全站效果：13 页共 82 处散文数学现在会渲染（vits 19、dmd 17、senseflow 15…）。另有 13 页共 34 处仍是灰底，因为那些页压根没加载 KaTeX（`inject_mathify` 有这道门槛，否则 renderToString 会炸）——那些是纯文字页，要渲染得先给它们加 KaTeX head，属于另一个决定。
- senseflow §02 顺带把那个 `.calc` 对照块换成真正的 aligned KaTeX 公式（本来就是两条式子的对照，不该用等宽 ASCII 排）。
- linter 同步：`code.m` 与紧形状的豁免从"碰巧不匹配"改成明写，并注入三种情形回归验证——裸 code 写 LaTeX 报错、code.m 写 LaTeX 不报、裸 code 写紧形状不报，三条都符合预期。

## [2026-07-26] refactor | 数学统一成一套格式，删掉运行时猜测层

用户定调："就该统一成一套格式啊，用啥 unicode，直接用公式渲染不好吗"。对——这一整轮的 bug 几乎全是"两套格式 + 一层猜测"生出来的。

**Phase A** render.py 新增 ensure_katex_head()：页面有数学记号却没加载 KaTeX 就自动补 head（inject_mathify 原本会因此跳过，符号永远灰底）。35 页补上，剩 29 页确认无数学。

**Phase B** 新增 tex_migrate.py，把 toTex 的转换搬到离线：
- paper 侧 882 处 `<code>xₜ</code>` → `<code class="m">x_{t}</code>`（46 页）
- md 侧 613 处 `` `xₜ` `` → `\(x_{t}\)`（100 个会渲染的文件；wiki/papers/*.md 是不渲染的脚手架，故意没动）
- 全部经真 KaTeX 预校验。从 53 种非法一路修到 0，其中最险的是 is_math 把真代码当数学：archival_memory_search(query)、skimage.metrics.peak_signal_noise_ratio、requires_grad=false。另修 \softmax 不是 KaTeX 命令、x_{t_mid} 括号失配、希腊命令后的组合变音符、\sqrt 缺参数、字符表缺 ₊₋ᵥⁱ、logπ_ref 双下标、# 转义。
- 19 条"里面有个 − 或 → 就被当数学"的英文短语/图例/配置（fake score − real score、car-1 → red、"golden_retriever"）进 NOT_MATH 人工钉死。
- 结构完整性：把两版的 <code>…</code> 整体换成占位符后逐字节比对，只动了 code 内容。

**Phase C** MATHIFY_BLOCK 从 104 行砍到 40 行——toTex / looksLikeMath / 散文严格形状全删，运行时只剩"把 code.m 原样送 KaTeX"。linter 相应改成"裸 <code> 里的数学 = ERROR"（没有兜底了）。

过程中又踩一次同源的坑：linter 自己重写了一套 is_math，跟 tex_migrate 判定不一致，扫出 53 个假 ERROR（D_KL 被 CONST_NAME 规则误吞、NOT_MATH 短语被重复标记）。改成直接 import 同一个函数。SKILL 加 7.6 记这条：**发现两处表述同一件事，第一反应是让一处引用另一处，而不是同步维护。**

最终：36 页浏览器实测 785 个 code.m + 312 个 .tex 节点全部渲染、katex-error 0；lint 80 页 0 ERROR。

## [2026-07-26] fix | 收尾：md 里的裸 HTML code、以及迁移引入的一个 KaTeX 回归

- 我先前说"剩下未转的全在 <pre> 里"是错的——复查发现 <pre> 外还有 98 处。原因：部分 concept md 用的是**裸 HTML `<code>` 标签**而不是 markdown 反引号，我的 md pass 只处理了反引号。补一遍，6 文件 / 23 处。
- 另两处：`V4_QUALITY_48` 是配置常量不是数学（CONST_NAME 规则漏了"字母+数字"开头的），加规则排除；`π(a\|s)` 被 markdown 表格转义的反斜杠挡住（md pass 把含反斜杠的当成"已是 LaTeX"跳过），该行改写成 `\(\pi(a\mid s)\)`。
- **迁移引入的真回归**：render.py 判断自动页要不要加载 KaTeX 的条件是 `"<code>" in body_html`，字面匹配不带属性的标签。迁移后整页 code 都成了 `<code class="m">`，条件不成立 → 不加载 KaTeX → mathify 也不注入 → 那页数学永远灰底。改成匹配 `"<code"`。
- 这个回归是被 §7.2 的正向断言抓到的：katex-error 是 0、lint 也全绿，只有"分子 180 / 分母 181 对不上"暴露了它。要是只查报错就漏过去了。
- 全站现在 <pre> 外 0 处未标记；41 页浏览器实测 779 个 code.m + 337 个 tex 节点全部渲染、0 error。
- SKILL 同步清理：§4 那段描述旧 mathify"自动识别符号表 code"的说明已经是假的（Phase C 删掉了那层），改成指向 §7.5；§7.2 的验证片段换成新语义（数 code.m / .tex，并列出 bareMathLeft 供逐条看）；文件布局补上 tex_migrate.py 和 fix_gloss_orphans.py；glossary 那条手敲 diff 命令改成"lint_paper.py 已覆盖"。

## [2026-07-27] ingest | diffusion-unet

- 新增独立的 Diffusion U-Net 架构精读，不再把 2015 分割 U-Net 与 DDPM / ADM / LDM 的去噪器混在一页。
- 用同一组标量走通加噪、噪声预测损失与干净样本恢复；逐一定义公式参数，并补 GroupNorm、时间嵌入、AdaGN、skip concat、self/cross-attention 与 scheduler 的职责。
- 以 Stable Diffusion v1 官方配置核对 64×64×4 latent、320/640/1280/1280 通道与 attention 下采样率；用 ADM 消融区分证据与架构惯例。
- 新增 GroupNorm、扩散时间条件、噪声预测目标三个概念页，并与经典 U-Net、DiT、CFG、cross-attention 双向链接。

## [2026-07-28] ingest | SANA-Video 2.0

- 新增 SANA-Video 2.0 精读页与 bespoke HTML；按“视频 softmax 成本 → 线性状态压缩 → 3:1 周期精查 → Block AttnRes 跨深度取回 → 训练课程 → 后训练 → 实验 → 部署”重排，不沿论文目录平铺。
- 用同一条完整架构图先定位 LTX-VAE、Gemma、Hybrid Video DiT、AttnRes、flow solver 和 decoder；另用无重叠 CSS grid 重画 8 层注意力周期、三来源路由、时间步 shift 和完整 flow 数字例。
- 对 gated linear attention、router、flow matching、flow shift、Diffusion-DPO 与有效秩逐符号解释；验证 3-source softmax 混合得到 6.7256、奇异值 `[3,1]` 的有效秩为 1.7548。
- 分开记录质量、机制和系统证据：25% 是代理实验的 Pareto knee；AttnRes MSE 近乎打平，主要证据是深层有效秩 +11.7% 和块入口删除旧来源后 −82%～91%；Sol-Engine 的 kernel / cache / sparsity 不与架构 speedup 混乘。
- 新增四个概念页：gated-linear-attention、hybrid-linear-softmax-attention、block-attention-residuals、content-aware-flow-shift。

## [2026-07-29] ingest | Wonder · Video World Model Done Better

- 新增 Wonder 论文精读与 bespoke HTML；不沿论文目录平铺，而按“完整系统 → 控制 → 记忆 → 蒸馏 → 镜头漂移 → 实时运行 → 证据边界”组织，让四个问题和四组解法能拼成一张完整图。
- 用同一组数字走通像素投影、I2V/V2V 统一输入、历史 top-k 选块、Sparse Context Forcing mask、三学生四步接力和相对 softplus 控制损失；公式先定义每个符号，再代数。
- 完整录入 I2V/V2V 结果，并保留论文表格核算异常：Wonder I2V 五个已打印画质分项的均值约为 .8564，与表内 Avg .8558 不一致；没有原始评测文件时不擅自改论文数字。
- 把 16 FPS / 0.5 秒标成项目页口径，并明确缺少分辨率、推理 GPU、卡数、显存和测速细节；把“本轮 active attention 近似固定”与“完整历史 KV 存储仍增长”分开。
- 新增四个概念页：pixel-space-coordinate-field、sparse-context-forcing、mixture-of-students、gan-control-regularization；DMD 与 sparse attention 旧概念页补 Wonder 来源。

## [2026-07-29] ingest | DuplexOmni

- 新增 DuplexOmni 精读与 bespoke HTML；按“为什么串行系统会卡住 → 两条并行线 → 480 ms 时间片 → Thinker–Talker → 16 层 RVQ codec → Writer–Director → 数据、训练、实验与边界”重排，不照论文目录平铺。
- 把容易混淆的两组名字拆开：外部 thinking layer / S2 负责检索、计算和工具调用，模型内部 Thinker 负责把本片 token 与上下文变成 Talker 的发声条件；二者不是同一个模块。
- 用一条改签场景走通 S1 与 S2 的异步协作，并逐符号解释条件向量、RVQ 残差求和、Talker prefix、主 codec 层与 15 个 residual code predictor；480 ms、6 帧、80 ms/帧的换算已正向验算。
- 完整录入 ToR、Big Bench Audio、Daily-Omni、WER、延迟、消融和长度分桶；保留“无 S2 + ASR 的 ToR 反高于无 S2”这一非单调结果，不把消融硬写成整齐故事。
- 分开论文实验与当前开源实现：论文用两阶段交替冻结、128×H20；当前公开 recipe 默认先 Thinker 后 Talker，低延迟推理建议至少 8×H20，公开 checkpoint 为 16 层 codec，完整训练数据约 9 TB。
- 新增 full-duplex-multimodal-interaction 概念页，并补强 dual-model-architecture、thinker-talker、rvq-codec、multi-token-prediction 四个既有概念的 DuplexOmni 边界。

## [2026-07-30] revise | DuplexOmni · 按新版认知桥质量闸复查

- 按真实执行顺序重排三段公式：先由文字与隐状态得到条件，再把历史排成 Talker prefix，最后从主码补齐 RVQ 残差并解码波形；补回此前在 HTML 里先用后定义的 \(R_i\)。
- 把“改北京”的第 4 个时间片贯穿三节：\(C_4\) → \(P_4\) → \(q^0_{4,1}=57\) → 三层玩具 RVQ → \(r_{4,1}\) → 80 ms 波形，并明确示意索引不是论文实测值。
- 把训练与部署拆成两章，分清参数怎样更新、RTF 能否跟上播放、响应延迟三笔账；论文未报告实测 RTF 的边界保留。
- 为 ToR、Big Bench Audio、Daily-Omni、WER 和延迟补首次出现解释；新增 WER 原式、逐符号定义与四词 25% 手算。
- 修正总览图最后一格为“结果回到 S1”，新增三项 benchmark glossary；桌面与 390 px 下复核公式、横向表格和术语浮卡。

## [2026-08-04] ingest | Wan-Streamer v0.3 · Video = World + Event Stream

- 新增 Wan-Streamer v0.3 精读与 bespoke HTML；按“先排除误读 → 完整训练/交互拼图 → 世界与事件记录 → 条件概率手算 → 预训练迁移 → 流式架构 → 服务与证据边界”重排，不照 8 页技术报告平铺。
- 用同一个“角色喝水”例子贯穿 \(W\)、\(e_k=(\tau_k,c_k,d_k)\) 和三步联合概率；逐一定义 \(p_\theta\)、\(x_{\le k}\)、\(e_{<k}\) 与乘积符号，并强调连乘来自链式法则，不是假设事件独立。
- 回读官方 v0.1/v0.2，把块因果注意力、条件流匹配、Thinker–Performer 与 Ulysses 明确标为继承项；把 v0.3 新增的 world-event 预训练表述和括号式开放行为接口单列。
- 核算 25 FPS = 40 ms/帧、160 ms = 4 帧、640×368 相对 192×336 约 3.65× 像素量，以及 200+350=550 ms；分清流水线节拍、模型侧信号延迟与网络预算。
- 新增 world-event-decomposition、block-causal-attention、thinker-performer-streaming 三个概念页，并把全双工、条件流匹配、分布式并行旧概念补上 Wan-Streamer 来源。
- 证据账本明确保留缺口：v0.3 未给行为量化、消融、标注质量、训练规模、参数量与统一硬件对比，项目页定性演示不写成 benchmark 结论。

## [2026-08-05] revise | DuplexOmni · 按 2606.09186v1 全文重审

- 对照论文正文、Appendix A–C 与官方实现重新查漏；保留原有认知顺序，不按论文目录重复建页。
- 把六种控制标记串成“启动 S2 → 回传结果 → 用户抢话 → 旧任务作废 → 新条件重开”的闭环，并解释 ghost text 只保留语言计划、不会被合成或播放。
- 补回附录里的主场景分布与 S2 参与强度，分清“每条种子唯一主类型”和“同一对话可同时出现多种交互行为”两种统计口径。
- 重写训练章：解释从 Qwen3-Omni 初始化到底复用了什么，给出交叉熵共同骨架、逐符号定义和 0.8/0.5 概率手算；再映射到 Thinker 文本/控制 token 与 Talker 主码/残差码。
- 明确冻结只控制本轮更新对象；论文未公开 codec 损失权重与完整目标函数。补充图执行减少 GPU 调度开销、但不改变模型数学和必要矩阵计算的边界。

## [2026-08-05] ingest | LongCat-Video-Avatar 1.5

- 新增 LongCat-Video-Avatar 1.5 精读与 bespoke HTML；不照报告目录平铺，而按“完整部署拼图 → 数据 → Whisper 对齐 → flow 基础训练 → 逐帧 GRPO → DMD2 → 多人物 → 课程 → 评测与边界”重排。
- 用 8 秒样本贯穿 50 Hz 音频、33→5 层池化、25 FPS、4× VAE 时间压缩与约 50 个 latent 时刻；另用同一标量逐步算完 flow 输入、速度目标、损失、梯度和一次参数更新。
- 逐符号解释 per-frame advantage，并用四条视频的手部/动作奖励算出总 advantage；明确论文没有写全稳定化分母、奖励模型与权重，示例数值不伪装成报告超参。
- 拆清 DMD2 的 real score、fake score、Generator 三个角色和共享基础 DiT + 两套 LoRA 的内存含义；150→8 只写成 18.75× 更少网络调用，不外推墙钟加速。
- 完整录入五阶段 211k 训练、508 对 EvalTalker、770 群众、10 专家、13,240 判断、八项缺陷率与 Base/Fast 表；保留 v1.5 单人/多人均略低于自家 v1.0 的非整齐结果。
- 核算并披露数据漏斗的原图不一致：累计保留率的相邻差值与标注淘汰率有 .01–.22 点偏差；没有原始数据时不擅自修数。
- 新增 whisper-layer-pooling、per-frame-grpo、multi-person-audio-region-binding、multi-stage-video-data-curation 四个概念页；flow matching、DMD、GRPO、cross-attention 与 video VAE 补来源。

## [2026-08-06] ingest | Towards Physics of Multimodal Pretraining

- 新增论文精读与 bespoke HTML；按“统一模型 → 知识怎样流动 → 协同与竞争 → 为什么要早联合 → 70/25/5 配方 → 2T 放大与边界”组织，不照论文目录平铺。
- 用同一组标量走完 rectified-flow 的加噪位置与速度目标；逐符号解释增量 token 比例、PPL、混合损失、ΔPPL、L2/RMS 和图像注意力占比，并把 5% generation-token share 与真实算力占比严格分开。
- 把早联合证据拆成三层：1T timing sweep 存在视觉 token 总量混杂；固定 200B continuation 是可核对的更强证据；2T late 对照虽由作者声明视觉 token 等量，但公开排程不足以独立复算。
- 完整覆盖 CLEVR 概念剔除、六种顺序、四档共享结构、23 组比例、13.5B MoE/2T、训练与评测基础设施；保留单 seed、无置信区间、自动判分、复杂度阶梯非严格标尺和 MoE 总参不匹配等限制。
- 新增 multimodal-knowledge-flow、modality-synergy-competition、vision-laziness、asymmetric-multimodal-pretraining-recipe 四个概念页，并重写 early-fusion，分清训练时机上的 early unification 与 encoder-free 架构意义上的 early fusion。

## [2026-08-06] revise | Towards Physics of Multimodal Pretraining · 二次复审

- 把所有展示公式统一成“符号先定义、公式再出现”：补齐 flow 位移展开与约分、增量比例由来、PPL、ΔPPL、L2/RMS 和 attention 占比的定义顺序。
- 补全 Raw Pixels、CLIP+VAE、AR UniTok 三组对照各自拆掉的假设，以及六个知识流方向并非完全同初始化的实验细节。
- 2T 表补回语言 PPL，基础设施补回 16 层控制骨干、GQA、RoPE、QK-Norm、FlashAttention 等配置；概念页新增 ΔPPL 与损失权重的数字例子。
- 将 2T late 的“等量视觉 token”降级为作者声明：论文未披露最后 40% 的具体 L/U/G 排程，读者无法独立复算。误差分析新增专门限制卡。
- 桌面 1440 px 与手机 390 px 实看；手机端 8 列规模表改成四张纵向指标卡，公式、箭头、术语弹层和所有指标无需隐藏式横向滚动即可阅读。

## [2026-08-06] ingest | Wan-Streamer v0.2

- 新增独立精读与 bespoke HTML，不再只在 v0.3 页用两段话代过；按“延迟三口径 → 全系统 → 成本来源 → Thinker → Performer → KV → 时间线 → 证据边界”重排。
- 核算 640×368 相对 192×336 为约 3.65× 像素量、25 FPS 下 160 ms=4 帧，以及 200+350=550 ms；用灌装线区分吞吐节拍与单件响应时间。
- 用 16 token / 4 rank 和 12 段 K/V 的教学例解释 Ulysses、视频分片/音频不分片与预分片本地 cache；明确这些数字不是论文配置。
- 按真实依赖重画相邻单元时间线，避免箭头把第 k 段生成误画成同拍已经解码；补齐参数量、GPU、互联、去噪步数、训练配方和统一画质评测缺口。

## [2026-08-06] ingest | KlingAvatar 2.0

- 新增技术报告精读与影院分镜式 bespoke HTML；先给完整级联，再依次拆低清蓝图、高清锚帧、首尾帧短片、音频插帧与空间超分。
- 把音频/视觉/文本三专家的职责、模态冲突和分镜级 Negative Director 写成生活化例子；明确具体专家、prompt、轮数与冲突规则未公开。
- 用教学公式解释深层 DiT mask 如何门控身份特定音频，并标清它是对论文文字机制的转写；补完整 YOLO→DWPose→SAM2→复核的数据链。
- 用 HeyGen Overall 的 43.2/28.2/28.6 完整算出 GSB 1.26，并录入六轴全表；保留 Face–Lip 对 HeyGen/旧 Kling、Motion 对 HeyGen 低于 1 的非整齐结果。
- 证据边界单列模型规模、分辨率、FPS、五分钟耗时、GPU、蒸馏步数、数据与训练配方缺失；“更高效”不冒充已有测速结论。

## [2026-08-06] ingest | VideoFDB

- 新增 benchmark 精读与对话实验室风格 bespoke HTML；从“句中停顿别抢话”的生活例开始，再拼 AV2A/AV2AV、数据、agent、caption、judge 与硬时序全流程。
- 完整列出 11 类动态与感知/生成归属；逐一定义五种 timing policy、TO、期望 takeover、指示量和 TOR-Alignment，并用五条样本算出 80%。
- 补齐 226 test + 11 validation、时长、技术规格、130 位说话者与三轮标注；补三 judge 的 Within-1pt、ICC(A,k) 和 Visual Grounding 一致性较弱的边界。
- 录入主表、MiniCPM FPS sweep、captioning collapse、visual-stream ignorance、token doubling，以及 Anam/Keyframe 级联头像的 2.8–3.5 秒时序缺口；保留正文 87% 与图中 91% captioning 口径差异。
- 新增 conversational-nonverbal-dynamics 与 tor-alignment 概念页，并补全 full-duplex、rubric 与 LM-as-judge 的 VideoFDB 来源。

## [2026-08-06] ingest | Wan-Streamer v0.1

- 新增独立精读与六路线号风格 bespoke HTML；按“现实交谈问题 → 全系统 → 条件概率 → 块因果 → 两类输出 → flow 手算 → 三阶段训练 → 两卡服务 → 证据边界”重排，不照原论文目录逐段翻译。
- 把三个正式公式逐符号拆开：三段条件概率算到 0.24；沿用 z₀=2、ε=−1、τ=.25 的 running example，算出 zτ=1.25、目标速度 −3 与平方损失 .36。
- 重画六路因果闭环、三块可见矩阵、流路径、训练课程表和相邻单元服务时间线；明确第 k 拍生成 yₖ，第 k+1 拍才解码播出，避免箭头提前连接。
- 新增 native-streaming-contract、causal-streaming-vae、rolling-streaming-distillation 三个概念页；回链 block-causal、conditional-flow、CFG、teacher forcing、full-duplex 与 thinker-performer。
- 实验按测量边界拆开 160/200/550 ms，保留 192×336@25 FPS 的原型定位；模型规模、数据量、GPU 型号、蒸馏配方与自然度量化全部列为未公开。

## [2026-08-06] query | Ulysses 上下文并行具体怎么走
- 起因：wan-streamer-v03 页 v0.2 段只有一句「Performer 用 Ulysses」，术语表指向 distributed-training-parallelism，但概念页里 Ulysses 也只有一句含糊话（「轮流拿到 head 或序列片段」——听着像 Ring，其实不对）。
- 概念页新增「Ulysses 具体怎么走」专节：五步布局互倒（token 布局→本地投影→all-to-all 去→本地完整注意力→all-to-all 回），沿用页内 8000 token/4 卡例子把通信账算实（每卡每层 ~24.6 MB vs all-gather ~49.2 MB；8 卡时 14.3 vs 57.3，一个越切越省一个越切越亏，python 复核）。
- 补两个边界条件（并行度封顶 head 数/GQA 的 KV head 数；短序列不划算——正是 v0.2 音频 latent 不切的原因）和 Ring Attention 对照。

## [2026-08-06] query | all-to-all 怎么倒回去 / online softmax / Ring Attention 细节
- Ulysses 节补「回程」块矩阵图：整层激活切成 4×4 块（token 段 × head 组），token 布局=持有一行、head 布局=持有一列；去程按 head 切按 token 段拼，回程反着做，收发块数对称。
- 新增「Ring Attention 具体怎么走」节：Q 不动、K/V 沿环流动 4 轮的手排轮转表；点破它=flash-attention 的「分块+在线 softmax」从 HBM↔SRAM 抬到卡↔卡；三笔账（每轮 16.4 MB 藏进计算/显存随卡数线性扩/因果 mask 负载不均用 zigzag 修）+ 与 Ulysses 的取舍。
- online softmax 不重写，指回 flash-attention 页的完整手算（[1,3|2,5] 例，python 复核仍 36.8806 两法一致）。

## [2026-08-11] ingest | WorldTrace

- 新增 NVIDIA WorldTrace 论文精读与 bespoke HTML；不照论文目录平铺，改按“AR 记忆前置 → 地址/内容两种失败 → 固定 cache 总览 → slot-rank → P 矩阵 → Field → Landmark → LoopBench → 实验/资源/理论边界”组织。
- 用 A→B→C→D→A 贯穿全文：q=20、7 格 cache 算出摘要虚拟位置 14/15/16；用 4×6 的 P 把 `[2,4,8,10,20,30]` 压成 `[3,9,20,30]`；用 0°/180° 二维 Key 完整演示 naive 平均相消与 canonical unrotate/rerotate。
- 每条核心公式均先说明目的，再逐符号定义并带入数字；单独说明 canonical averaging 只保平均 pre-softmax score，不保证 softmax 权重与最终 attention 完全相等。
- 完整覆盖主表、四层 LoopBench、N=256 PAC sweep、LingBot 跨架构、slot split、Field/Landmark 混合、MemRoPE/YaRN、streaming writer、显存、运行时、算法与条件理论界限。
- 明确口径：WorldTrace-Field 主实验的 GPU attention cache 为 O(1)，但 recompute writer 的 CPU host state 每 latent frame +5.4 MB；严格 O(Ns) 状态是附录 streaming writer。官方未开放可下载代码，scene-entry 阈值等复现细节仍缺。
- 新增 addressable-kv-memory、canonical-rope-keys、field-vs-landmark-memory 三个概念页，并补充 kv-cache / RoPE 的长期寻址与相位平均边界。

## [2026-08-11] revise | longcat-video-avatar-1-5 §04 重写
- 起因：§04 三个数字（400/33/1280）来历全空、layerstrip 的「均值 4.5」不知所云、音频进 DiT 只有一句话。
- 按四步重排：① 数字来历（log-Mel 10ms 一列→卷积减半=50 Hz；8×50=400；embedding+32 层=33；1280=隐藏维；30 秒滑窗）；② 层轴分组平均+玩具手算（[4.5,12.5,20.5,28.5,33]）+HuMo 出处；③ 时间轴两段账（对帧率 50→25、对刻度 25 FPS→÷4 latent，audio projector 聚合约 4 帧/160ms）；④ 进 DiT（文本 cross-attn 之后插入、adaLN 闸门防灾难性遗忘）。
- 边界框收口：projector 结构/窗口、5 通道进 K/V 排法、分组边界与 singleton、只用最后层的消融——论文均未给。
- 同步 md §5 与 whisper-layer-pooling 概念页（补 HuMo 出处）；sources 加 HuMo（arXiv 2509.08519 已核实）；lint 0/0、glossary 16↔16、浏览器逐屏核过。

## [2026-08-11] clarify | klingavatar-2 继承自 1.0 的三个训练细节

- 纠正“参考帧四周留空”：1.0 原文是训练视频帧周围随机加入 empty pixels，属于空间 padding，不是时间补帧；用 512→640、脸宽占比 50%→40% 的教学例解释小脸与远景鲁棒性，并列出未公开的边距、填充值与后处理。
- 拆清人工退化参考图：正常参考图的副本被加入纹理扭曲、模糊、过强对比度/饱和度和偏色，作为负 CFG 条件；补通用 CFG 方向式和 .2/.6/s=2 数值例，同时标明公式与退化配方并非论文公开实现。
- 拆清 DWPose 嘴部加权：关键点→嘴部区域→映射到损失分辨率→局部误差加权，并区分“论文明确写了定位与加权”和“区域形状、膨胀、倍率等实现未披露”；同时与 2.0 的整人 SAM2 mask 链分开。

## [2026-08-11] ingest | DyaPlex

- 新增 NVIDIA/HKUST DyaPlex 精读与双塔流式控制台风格 bespoke HTML；按“交互闭环 → 冻结语音塔 → 四部位 codec → 双人交错 → 真实时间坐标 → cross-RoPE → 训练/推理 → 数据/指标/实时”重排。
- 完整解释语音权重没有直接变成骨骼权重：32 层动作塔通过新 Q/K/V 投影逐层读取冻结 PersonaPlex 隐藏状态；22 码、4096 词表四 band、主实验 18 个身体码与定性 face 分支严格分开。
- 用 46-token 帧验算 4096→89 帧→7.12 秒、1024→22 帧→1.76 秒；用动作帧 2 对语音帧 0–3 画严格因果矩阵，避免扁平 token 下标冒充时间。
- 完整录入 Seamless 数据、训练配置、五类指标、主表/消融/人评和 A6000 Ada runtime；保留正文 top-k 200 与附录无 top-k、组件时延非端到端、DualTalk 迁移崩塌等边界。
- 新增 dyadic-motion-interleaving、time-aligned-speech-motion-rope 概念页，并补 full-duplex、RVQ、RoPE、cross-attention 来源。

## [2026-08-11] ingest | FacePlex

- 新增 FacePlex 精读与滚动表情流水线风格 bespoke HTML；从“离线 audio-to-face 切块为何失败”开始，串起 FLAME 输出、音频/隐藏/动作三队列、RFM、RCA、训练、数据、结果、延迟与边界。
- 用同一组四槽标量完整算出 `[.75,.5,.25,0]` 的插值状态、`U=X−ε` 速度和 `.25U` Euler 更新，并用求导说明速度目标由直线路径产生；所有公式逐符号定义。
- 拆清 RCA 的“未来”是 PersonaPlex 已经生成但暂存的音频：同一动作生命周期覆盖 h(t−3)…h(t+3)，代价为 3×80=240 ms 固定等待，不是读取未知用户未来。
- 完整覆盖 67,200 synthetic self-play、UniLS best-of-12、PLRS 过滤、1138 h 合计数据、训练配置、主表、人评、RFM/RCA/data/mask 与 Euler-N 消融；full RCA 并非每项指标第一。
- 明确正文/附录的联合训练与冻结缓存、混合数据与 syntheticv2 corpus 两组口径冲突；新增 rolling-flow-matching、rolling-cross-attention、flame-facial-motion 概念页，并补 flow/full-duplex/cross-attention 来源。

## [2026-08-11] revise | worldtrace §05 重写
- 起因：P 矩阵凭空出现——没讲为什么要统一记法，PK=[3,9,20,30] 没走一步乘法，两条 attention 公式列完即走，toy 数字没贯通到 softmax。
- 补齐四块：① 动机（Field 平均/Landmark 挑帧/滑窗丢弃都是「按配方抄写」，统一成 P 才能在 §12 用同一套理论；「标量=暂时关掉相位问题」点明教学隔离）；② P 的读法 caption + 逐行手算（½×2+½×4=3…）；③ 端到端数字（配 V、q=.1：完整版 6 条名单输出 51.0，Field 压缩版 4 条输出 53.7，偏差 5%，大头权重两版都落最近帧——python 复核）；④ 边界框补第二条：P 是分析记法，实现不存 L×T 矩阵、writer 增量维护。
- 附带：PV 与 K 同一分组的配对理由挪进散文；softmax 格子前移修 define-before-use WARN；md 同步。lint 0/0，浏览器逐屏核过。
- 环境：render.py 被其他会话加了 yaml/markdown 依赖，本机 pip 走 --break-system-packages 装上。

## [2026-08-11] revise | worldtrace §12 扩写
- 起因：理论节只有 J(P) 一条公式加两句定理转述，α/γP/ε/δ 全是黑箱，还漏了 Proposition 1。
- 按四步重排：① Prop 1（输出误差 ≤ 分布失配 × V 最大行范数——为什么后面只盯分布），α_q/α̂_q 直接用 §05 算过的两组权重坐实；② J(P) 的 γP 摊回读法（给合并槽多少权重=按配方摊回来源帧；组内被迫平分/没存的帧全零两条结构约束）；③ 2×2 手算表：分散型 Field .021 vs Landmark .211，回访型 Field .880 vs Landmark .080，各赢一行各差一个数量级（python 复核）；④ ε-coherent/δ-covered 条件原文化转述+上界数字（.217×.097≈.021 与直接算一致因为构造 γ 就这么配；δ 上界 .12 不紧 vs 直接 .08），oldest-out=δ 覆盖的流式近似。
- warn 补论文原话的理由：ε/δ 没实测是因为量它需要超训练视野的未压缩 rollout，那时参考 attention 本身在退化，只能靠预测行为间接检验。md 同步。lint 0/0，浏览器核过。

## [2026-08-11] revise | worldtrace 补扫——按论文大纲逐节对照,补四个覆盖缺口
- 教训：前两轮是按「有无手算例/边界框」的表面特征判质量,§12 漏 Prop 1 就是这么漏的。这轮拿论文完整 section 大纲逐条对照,查出四个缺口全部补上：
- §01 补附录 C 逐频率分析：128 维分 44 时间+42×2 空间,22 个频率 θ_f=10000^(−f/22) 从 1.0 到 1.5×10⁻⁴;距离 30 时快频绕 π 约十次变随机数、慢频只转 0.26° 仍扛语义——超纲不是全盘乱码而是快频先变噪声,canonical key 能救内容的物理基础。
- §08 补 3.5 Position-Content Coupling 的解法：slot indexing 钉死地址、canonical 变换吸收搬移,槽内容变成纯 content-only 自由度——两种 writer 才能共用读取系统互换混搭。
- §12 补 B.3 误差二分：重定位项+压缩项;重定位是可寻址性的代价(拿分布内位移换 OOD 失败),无解析界、由 §10「只换地址」表实测;理论只管压缩项。另补 recent-window mass(recent 行 identity 原样复刻 α^rec,压缩误差只出在旧史)。
- §13 补 G.2/H.2：不和 MG3 比的原因(记忆重训进骨干,无冻结 checkpoint 可外挂);未来方向三条(在线 k-means 调边界/soft-sparse 行/直接优化 P)。
- md 四处同步。lint 0/0,KaTeX 2869 条 0 失败,浏览器核过 §01 新段。

## [2026-08-11] revise | dyaplex + faceplex 双遍扫(大纲对照遍)
- DyaPlex：§02 补「6/4 码=RVQ 残差层数」+四部位输入维度表(78/180/57/56)+两个易读错点(4096 词表实为四独立 codebook 并集;因果化=左 pad 零前瞻+下采样 4×→2×);§01 补 17 路交错输入求和+动作塔 1024 vs 语音塔 4096 的容量取舍;§06 补 {H^ℓ} 预计算一次;§08 指标口径(FGD=裸 66D 关节版、同名不同算法不可跨论文比;BeatAlign 机制;P-FD 比的是 GT 对 vs GT+Gen 对)+表头补 ×10⁻³ 单位+GT (Random) 定标行(13/33,DyaPlex 5.6/7.3 比乱配真动作还贴)。
- FacePlex：§05 补每层构成(self-attn→RCA→FFN→velocity head)+style/anchor 是什么(角色参考动作/已出队干净帧);§06 补真实数据格式化管线(Seamless 自带 112D FLAME、音频门控+归一+重过 Mimi/STT 成同构 shard)+三路 dropout 的用途(CFG+流式 warm-up、null embedding);§08 补 N 消融质量面(N=1 嘴部误差反而最低,质量不随步数单调,N=2 是均衡非上限)。
- 两 md 同步;lint 2 页 0/0;KaTeX 2871 条 0 失败;浏览器核过改动处。
- 流程固化：每篇论文最少 review 两遍(通读批判遍+大纲对照遍),已写入长期记忆。

## [2026-08-11] revise | faceplex 拆包两处过度压缩句
- 用户细则：过于省略=通俗易懂的违规项（一句话步骤>2 或未解释术语>2 必拆）。已写入长期记忆 rubric。
- 真实数据管线句（门控/归一/Mimi/STT/shard 五步一口气）拆成四条有序步骤，每步带为什么；shard 就地定义。
- dropout 句拆开：null embedding=可学空白占位；CFG 就地解释（有/无条件预测相减放大遵循）；warm-up 的因果讲透（启动时 anchor 天然缺失）。

## [2026-08-11] revise | faceplex 补 L 的定义
- L 全页当分母（Δτ=1/L）、当槽数（τ_i 公式）、算等待（(L−1)×80ms），却没有一格正面说它是什么。§02 符号格补：L=滚动队列槽数（同时在制的片段数），一个数管两头——步长 1/L 与等待 L−1 轮；md 同步补到手算段。
