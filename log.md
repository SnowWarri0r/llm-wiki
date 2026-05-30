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
