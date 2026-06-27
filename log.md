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
