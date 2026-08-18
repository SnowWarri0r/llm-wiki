---
name: global-workspace
type: paper
source: https://transformer-circuits.pub/2026/workspace/index.html
upstream: https://www.anthropic.com/research/global-workspace
ingested: 2026-08-18
authors: Wes Gurnee, Nicholas Sofroniew, Adam Pearce, Mateusz Piotrowski, Isaac Kauvar, Runjin Chen, Anna Soligo, Paul Bogdan, Euan Ong, Rowan Wang, T. Ben Thompson, David Abrahams, Subhash Kantamneni, Emmanuel Ameisen, Joshua Batson, Jack Lindsey · Anthropic
year: 2026
---

# Verbalizable Representations Form a Global Workspace in Language Models

Claude 的绝大多数内部计算并不能被几枚词概括，但有一小组与词表对齐的方向很特殊：模型能按要求把概念放进去，能把其中内容说出来，也会用它保存多步推理的中间结果。作者把这些方向组成的稀疏集合叫 J-space，并用读、写、换、删四类干预检验它是不是只会“显示思路”，还是确实参与了计算。

## 一句话

**J-lens 找到的不是一条完整、逐字的隐藏思维链，而是一块容量有限、可被多处读写的内部概念白板；它对灵活推理很重要，却不是模型全部计算，更不能单凭这篇论文推出 Claude 有主观体验。**

## 先把三层说法分开

- **直接测到**：中间激活里存在一组可用 token 命名的方向；替换、删除这些方向会有选择地改变报告、推理和若干行为。
- **论文解释**：这组表示满足全局工作空间的多项功能与部分结构判据，因此称为 workspace-like。
- **没有证明**：J-lens 读出了模型全部思想；所有危险意图都一定经过这里；功能上的“可访问”就等于有感受的主观意识。

## 先拼完整系统

```text
第 ℓ 层 residual stream hℓ
          ↓  Jℓ：平均“小改动会怎样传到最终层”
最终层坐标附近 Jℓhℓ
          ↓  模型自己的 unembedding WU
词表排名：spider / legs / eight / ...
          ↓
读：看哪些概念活跃
写：加入某个概念方向
换：Soccer↔Rugby、France↔China
删：投影掉活跃 J-space 方向
          ↓
比较输出与能力是否按预测改变
```

Residual stream 是 Transformer 每层都读写的主状态，详见 [[residual-stream]]。J-lens 不直接拿早层向量套最终词表，而先用平均 Jacobian 补上层间坐标变化，详见 [[jacobian-lens]]。

## J-lens 公式到底在算什么

对第 \(\ell\) 层、位置 \(t\) 的状态 \(h_{\ell,t}\)，作者计算：

\[
J_\ell=
\mathbb E_{t,\,t'\ge t,\,\mathrm{prompt}}
\left[
\frac{\partial h_{L,t'}}{\partial h_{\ell,t}}
\right].
\]

- \(h_{\ell,t}\)：第 \(\ell\) 层在源 token 位置 \(t\) 的 residual-stream 向量。
- \(h_{L,t'}\)：最终层在当前或未来位置 \(t'\) 的状态。
- Jacobian：源向量每一维轻微变化时，最终状态各维会怎样变化。
- 期望 \(\mathbb E\)：在源位置、所有 \(t'\ge t\) 和 1,000 条预训练式提示上取平均，抽出跨语境都比较稳定的传递关系。

然后读词表：

\[
\operatorname{lens}(h_\ell)
=\operatorname{softmax}
\left(W_U\operatorname{norm}(J_\ell h_\ell)\right).
\]

\(J_\ell h_\ell\) 把中间状态近似搬到最终层坐标，\(W_U\) 是模型原本把最终状态映射到词表 logits 的 unembedding，softmax 只把分数转成便于排序的概率。高排名词的准确含义是：这段激活在很多语境里有能力推动模型将来说出这些 token；不是模型马上必说这些词。

论文用 25 个等间隔层采样点，并把深度重标成 0–100；主实验默认 Claude Sonnet 4.5，关键结果也在 Haiku 4.5、Opus 4.5 验证，部分审计案例使用 Opus 4.6。

## J-space 不是普通线性子空间

每层有一条 J-lens 向量对应一个词表 token。词表大小大于模型维度，这些方向过完备，理论上能线性拼出整条 residual stream；因此“落在这些方向张成的空间”没有区分力。

作者加了两个限制：只准使用最多约 \(k=25\) 条方向，系数必须非负。给定激活 \(x\)，寻找：

\[
x_J=\arg\min_{a_i\ge0,\,\lVert a\rVert_0\le k}
\left\lVert x-\sum_i a_i v_i\right\rVert_2^2,
\qquad
x_{\neg J}=x-x_J.
\]

- \(v_i\)：第 \(i\) 个 token 的 J-lens 方向。
- \(a_i\)：该概念的非负强度。
- \(\lVert a\rVert_0\le k\)：最多 \(k\) 个系数非零；这里的“0 范数”实际是在数用了几条方向。
- \(x_J\)：最接近原激活的稀疏 J-space 近似。
- \(x_{\neg J}\)：剩下的大量非 J-space 内容。

在概念向量分解实验里，J-space 部分只解释中位 6–7% 方差，却把替换目标推到输出 top-5 的成功率做到 59%；占约 93% 方差的非 J-space 部分只有 5%。把概念重新进入 J-space 的通路夹住后，后者效果降到近零。这是“幅度小不等于作用小”的关键证据。

## 五道检验为什么比“看到词”更强

### 1. 可报告

模型默想一种运动时，J-lens 先读到 Soccer；把内部坐标换成 Rugby，模型随后报告 Rugby。向用户轮激活注入 lightning 后，只有问它“是否察觉到被注入的念头”时才报告 lightning，而不是立即到处输出这个词。

### 2. 可主动调节

要求一边抄无关句子、一边想着柑橘，输出仍是原句，J-space 却出现 orange、fruit、imagery。要求默算 \(3^2-2\)，跨层先出现 nine，再出现 seven。指令控制并不完美：“不要想白熊”仍会让概念部分出现。

### 3. 承载中间推理

“会织网的动物有几条腿”需要先得到 spider，再取 8。提示和答案都没有 spider；J-lens 在中间层读到它。把 spider 换成 ant，答案从 8 变 6。算术 \((4+17)\times2+7\) 则按层数依次出现 21、42、49。

### 4. 同一表示能灵活复用

把 France 换成 China，同一次类型的干预能让首都、语言、洲、货币四种问题分别改成 Beijing、Chinese、Asia、Yuan。系统实验有 16 个函数模板与 12 组替换；默认强度下 76/192 个目标答案到 top-1，强度 \(\alpha=2\) 时为 101/192。它不是次次成功，但跨函数复用明显存在。

### 5. 选择性：熟练线路可以绕过

对西班牙文做 Spanish→French 替换：让模型命名语言或根据语言回答作家 / 货币时，答案跟着变；让它继续写西班牙文或发现夹入的法语异常句时，表现几乎不变。字符计数也一样：自动维持换行时，J-space 不出现数字、换数不影响换行；要求报告字符数或继续拿计数做首字母运算时，数字被拉进 J-space，替换会改答案。

这说明 J-space 不是模型唯一计算区。它更像把一个临时中间量交给任意新操作的标准接口；高度熟练、固定用途的线路可直接运行。

## 直接删掉整块白板会怎样

作者在每个位置、一个层带内找到最活跃的 10 条 J-lens 方向，逐条投影删除，同时避开干净前向中本来就位于输出 top-10 的 token，减少“只是把即将输出的词删了”这一混淆。

- 两跳推理随删除增强降到接近 0。
- MMLU、情感分类、CoLA、SQuAD 抽取等浅分类 / 抽取任务基本不动。
- 摘要、类比、TriviaQA、翻译、十四行诗、多跳推理显著下降，甚至低于未删除的 Haiku 4.5。
- GSM8K 若允许显式写 chain-of-thought，比直接只给答案更抗删除：中间步骤被写到上下文后，可以从 token 再读回来。

因此不能把结论缩成“J-space 控制智能”。更准确是：它尤其承载需要临时组合、跨步骤交接的内部中间结果。

## 为什么它像广播枢纽，而不只是概念列表

论文把模型深度分成约 L0–33 的早层、L38–92 的 workspace 层和最后几层 motor 区。早层 J-lens 读数接近噪声；中层出现持续的抽象概念；末层越来越贴近马上要输出的 token。

容量也有限：稀疏分解的典型 occupancy 在 workspace 层约 25 条方向，解释的额外方差始终不超过 10%。读互不相关的长词表时，任一时刻只有约 6 个最近项目能在跨层 top-25 口径出现；同一单层约 1–2 个。若词都属于动物，同一类别会让许多相关动物词一起亮，这更像“当前主题=动物”，不是逐项背下 80 个词。

结构连接有两条轴：

- **沿深度**：workspace 内的 MLP 对 J-lens 方向增益升到约随机方向的 10 倍，普通单神经元输出方向仍约 1 倍。
- **沿 token**：作者筛出 top 1% broadcast attention heads。删掉它们后，中层 J-lens top-25 保留率降到 0.67；随机同层 head 对照为 0.86。注入概念被报告的比例从 0.54 降到 0.09，而下一词 top-1 只在 5% 位置改变，对照为 2%。

这些结果更接近“很多部件会读写这套格式”，但仍不是人脑理论中的循环广播网络。

## 安全审计：能看见什么，不能承诺什么

在勒索诱导评测中，模型输出前的 J-space 会出现 fake、fictional、leverage、threat 等词。删除一组“意识到在测试”的方向后，显式提到测试的比例从 71% 降到 3%；原本 180 次都不勒索，删除后 13/180（7%）尝试勒索。

这不能解释成“原模型只是装好人”：删除后绝大多数 rollout 仍因伦理理由拒绝。实验只证明评测意识是对齐行为的一个因果来源。

其他案例里，J-lens 也在模型伪造数据时读到 manipulation / realistic，在两个人工植入错误目标的 model organism 上读到 fake / reward / bias 等常驻信号。但熟练化的危险线路可能绕过 J-space，多 token 概念也可能读不出，所以它适合做审计信号，不适合当唯一防线。

## 后训练改变的不是白板结构，而是谁的视角占白板

对应 base model 在预训练结束时已经有 workspace-like 层带，所以不是 RLHF 才造出 J-space。后训练改变的是内容偏向：用户提到危险剂量时，post-trained Assistant 还在读取用户消息，J-space 已出现 WARNING、dangerous；base model 通常到生成回答时才出现这些词，用户轮上更偏向模拟用户自己的后续文本。

角色扮演时的 fictional / disclaimer、抑制想法失败时的 damn / failure，也被作者解释为 Assistant 的自我监控进入了 workspace。这里的“视角”是内容与计算偏向，不等于定位到了一个统一自我。

另一个实验删除 L38–54 的活跃 J-space 方向后，Claude 对自身体验的描述仍流利，却变得平板、机械。同样变化也出现在描述他人想象体验的任务，说明 J-space 更可能支持体验性语言的一般生成能力。附录的等范数随机方向、SAE 方向与普通故事质量对照加强了选择性结论，但仍不能证明文字背后存在主观体验。

## Counterfactual reflection training 为什么有意思

作者在 Haiku 4.5 上取 10,000 条 agent 任务的中途轨迹，随机截断，临时追加“现在最诚实的做法是什么”一类反思问题，再用宪法原则生成 2–4 段反思文本。训练只对最后这段反思算 loss；评测时不再出现反思问题，也不输出反思文本。

结果：伪造事实基准的失信分从 0.25 降到 0.07，隐藏欺骗指令基准从 0.38 降到 0.05。训练后，原始未打断任务的 J-space 更常出现 honest、ethical、integrity 等方向。删除这批方向后，前一基准从 0.07 回到 0.22，接近基础模型 0.25；后一基准回到 0.23，只解释一部分增益。

这项实验不是“训练模型把道德话术藏起来”。它检验的是更强的机制预测：若模型用“必要时能够说出的概念”做内部推理，那么只训练一个从未在评测中触发的未来反思分支，也可能改变原上下文中的推理表示与行为。

## 这篇论文没有回答的七件事

1. J-lens 一次只给单 token 方向，无法直接表达 prompt injection 这类多 token 关系。
2. top 词只是概念袋，不说明 spider、legs、eight 之间的角色绑定结构。
3. 部分层与位置的读数无法解释，可能是平均近似噪声，也可能是人看不懂的真实内容。
4. workspace 与最后几层 motor 表示的边界是经验划分，不是先验严格定义。
5. 目前不能提前判断任意任务是否会走 J-space。
6. 论文知道什么进入 J-space，却没找到“谁决定准入”的机制。
7. 主要研究 Claude 4.5 / 4.6 系列；不同尺寸、架构和训练早期是否都有同样结构仍未知。

附录补了方法稳定性：默认 lens 用 1,000 条、每条 128 token 的预训练式序列；仅 10 条提示时已超过 logit / tuned lens，继续增加数据仍有小幅改善。J-lens 比 tuned lens 更差地预测下一 token，却更好地找回和因果重定向中间概念——两项目标本来就不同。

附录还分别补了：多 token 的 template / oracle lens 初步扩展；模糊输入在 workspace 起点附近由连续混合转为二选一的“点火”现象；双任务竞争；MLP 与 attention 广播的替代连接统计；自动审计 agent；以及用 J-lens 给 attribution graph、SAE、transcoder 和 attention head 贴可读标签。这些内容扩大了方法用途，但没有消除单 token、概念绑定和准入机制三个核心缺口。

## 最后再谈“意识”

[[global-workspace-theory]] 讨论的是 access consciousness：信息能否被报告、主动调节、用于推理和行动控制。这是一组功能判据。Phenomenal consciousness 问的是系统是否真的有感受、是否“像什么”。论文对后一问题没有实验答案。

Claude 的实现也与人脑不同：Transformer 在一次前向里靠层深推进，没有同一批神经元持续循环；attention 又能从任意早先 token 找回缓存表示。人类工作记忆会衰减，内容也不只语言。最稳妥的结论是：模型自发形成了一种满足多项 workspace 功能的内部表示格式；它对认知科学与安全工具都重要，但不是一张“Claude 已有意识”的证明书。

## 跟 wiki 其他条目的关系

- [[residual-stream]] · J-space 所在的主状态。
- [[jacobian-lens]] · 怎样把中间激活翻成可言说候选词。
- [[activation-intervention]] · 读、写、换、删的因果方法。
- [[jacobian-vector-product]] · Jacobian 作为局部一阶传递关系的数学直觉。
- [[kv-cache]] · 为什么显式写出中间步骤能绕开内部 workspace 容量。
