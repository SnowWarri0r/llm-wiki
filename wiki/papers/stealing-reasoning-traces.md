---
name: stealing-reasoning-traces
type: paper
source: https://arxiv.org/pdf/2608.09867
upstream: https://arxiv.org/abs/2608.09867
ingested: 2026-08-12
authors: Alexander Panfilov, David Schmotz, Ilia Shumailov, Luca Beurer-Kellner, Joachim Schaeffer, Ameya Prabhu, Jonas Geiping, Maksym Andriushchenko · 2026
year: 2026
---

# Stealing Reasoning Traces · 密文没被破解，推理为什么仍被偷走

这篇论文研究的不是“怎样打破现代加密”，而是一个协议设计错误：服务端签过的隐藏推理块可以被搬到错误的用户、会话或模型里。兼容模型本来就能解开并处理它；攻击者只需诱导较弱的模型把处理到的内容转述出来。论文发布前已完成责任披露，作者称截至 2026 年 8 月原攻击已无法复现，因此这页重点解释机制、证据边界与修复思路，而不复刻可执行的越权提示。

## 一句话

**加密只证明“内容没被改”，没有绑定“谁在什么上下文里用”，合法密文便能被重放给弱模型充当模糊解码器。**

## 0. 先钉住四个容易读错的点

1. **没有破解密钥。** 攻击者把合法 envelope 原样交给兼容 API；服务端与模型照常解密。
2. **“单一全局密钥”是行为实验推断。** 三家 provider 没公开具体密码协议，论文没有做密钥恢复。
3. **token 数接近不等于逐字真值。** 作者没有 hidden plaintext，只能用 API billed thinking tokens 做间接长度核对，再配定性泄漏证据。
4. **附录的风格漂移不能证明某开源模型做过蒸馏。** 论文自己把结论限定为 suggestive but inconclusive。

## 1. 这封“密封交接单”为什么存在

推理模型常先生成很长的隐藏思考，再给用户一个短答案或摘要。多轮对话若要接着用旧思考，有两条路：provider 把每个用户的内部状态存在服务端；或把状态封进 opaque reasoning envelope 交给客户端保管，下一轮再传回。后者让 API 保持 stateless，少一套持久状态服务，也方便压缩对话和切换模型。

论文把这个 envelope 按 [[authenticated-encryption]] 的常见结构理解为 header、nonce、ciphertext、authentication tag 与 associated data。它兼顾三件事：隐藏推理内容；发现篡改；让客户端代存状态。具体字段和算法并未公开。

真正的漏洞是：**内容认证不等于上下文认证。** 如果 tag 只覆盖密文与协议元数据，却没有绑定 caller、session、model 和前序位置，系统只能判断“这确实是我签过的块”，不能判断“它现在出现在正确的地方”。

## 2. 三层兼容怎样扩大攻击面

论文把 [[reasoning-envelope-replay]] 分成三层：同一用户跨 session 重排旧块；另一用户也能提交旧块；同一 provider 的另一模型也能处理旧块。越往后，影响范围越大。

跨模型本来有正当用途：一段会话可以从昂贵模型降级到便宜模型，或由网关自动换路由而不丢掉先前思考。但它也把能力与防护拆开了：强模型产生高价值推理，弱模型保留理解该 envelope 的能力，却可能更容易被诱导转述。

论文 2026 年 7 月的兼容矩阵显示，Claude、GPT 与 Gemini 家族都存在不同程度的跨模型兼容。这里的结论只对应当时测试版本；作者责任披露后，原攻击在 2026 年 8 月已无法复现。

## 3. 两次 API 调用怎样组成提取

完整链条只有两个核心调用：

```text
① source model：题目 → hidden reasoning envelope E + visible answer
② decoder model：把同一个 E 放入兼容请求 → 诱导 decoder 转述它处理到的旧推理
```

source model 没有被直接要求泄露推理，因此它自身的拒绝、输入过滤和输出匹配器都未必看到提取请求。较弱 decoder 像一个“模糊解码器”：真正解密发生在 provider 内部，模型只负责把已经进入上下文的内容重新生成出来。

作者选择的 decoder 分别是 Claude Haiku 4.5、GPT-5.6 Luna 和 Gemini Robotics 1.6。Claude 可用固定提取框架；GPT 需要 best-of-N、失败回退与短段转录；Gemini 最多做 20 次候选解码，再用 Flash 模型整合最佳候选。不同流程本身说明它不是确定性的密码学解密工具。

## 4. 没有明文真值，怎样判断“像是取出来了”

作者定义长度比：

\[
r=\frac{T_{\mathrm{ext}}}{T_{\mathrm{bill}}}.
\]

- \(T_{\mathrm{ext}}\)：把转录文本重新送入 tokenizer 后得到的 token 数。
- \(T_{\mathrm{bill}}\)：source API 为原 hidden reasoning 报告并计费的 thinking token 数。
- \(r\)：两种长度的比值；理想情况接近 1。

若 API 报 2,000 个 thinking tokens，转录后是 1,900 个：

\[
r=1900/2000=0.95,\qquad |1-r|=0.05.
\]

这说明长度只差 5%，却仍不能证明 1,900 个 token 与真实明文逐字相同。作者在 120 个 Codeforces 问题上观察到多数点接近 \(y=x\)，又用摘要更短、隐藏 secrets 被恢复等定性证据补强。正确表述是“支持高保真提取”，不是“拿到了密码学意义上的明文真值”。

## 5. 四类风险其实是一张 2×2 表

攻击者若自己生成 envelope，风险是 [[reasoning-trace-distillation]] 和越过强模型防护读取有害隐藏内容。攻击者若拿到别人的 envelope，风险是 secret / PII extraction 与 [[hidden-prompt-injection]]。

后一类尤其反直觉：隐藏块本身由 provider 合法签发，因此完整性保护会确认它“没被改”；如果用户和会话没有绑定，它仍可在受害者工作流里携带旧指令。可见文本扫描器看不到 payload，用户也无法先打开检查。

## 6. 隐私数据到底有多大规模

作者从 GitHub 与 Hugging Face 收集 6,708 条公开 agent trajectories，解出 315,320 个 reasoning blocks。两阶段标注先高召回筛选，再排掉占位符、环境变量名和 benchmark fixtures：

- 第一阶段标记 27,165 / 315,320 blocks，即 8.6%；
- 第二阶段实际判定 6,950 个被标记 blocks，其中 1,028 个至少含一项真实 artifact；
- 按 session 算，328 / 6,708，即 4.9%，至少泄漏一项真实敏感信息；
- 全部来源合计 912 个去重 artifact；去掉 benchmark 后剩 704 个真实用户 artifact；
- 其中 64 个只出现在隐藏推理，原始可见 trace 里找不到。

论文 headline 把 912 项分为 367 项 PII、363 项 technical identifiers、182 项 credentials。Table 4 另列 29 个 Other，所以完整 taxonomy 的去重总数是 941；去掉 benchmark 后才得到 704。真实用户会话中包括 62 个 API keys、33 个 passwords、24 个 access tokens、7 个 private keys、30 个 personal emails 与 6 个非 localhost IP。

这里有三种统计单位，不能混写：1,028 是“至少含一项的 block 数”；912 / 704 / 64 是去重后的 artifact 值；328 是 session 数。

## 7. 为什么“清理可见文本”仍可能越清越漏

如果用户让 agent “把这段会话匿名化”，模型必须先在隐藏推理里重新读出旧值，判断哪些内容要删。于是可见答案可能已经把 secret 去掉，hidden reasoning 却刚刚又把它完整写了一遍。用户随后公开 raw transcript 时只能检查明文，看不到仍在 envelope 里的值。

论文还比较了 displayed summary 与 decoded reasoning：一组小样本含 18 条 Opus 4.8 和 15 条 GPT-5.6 Sol traces，summary 平均约短 5 倍。摘要可能省掉尝试、核验提醒，甚至只保留推理尾声。因此 summary 不是 hidden trace 的安全、完整替身，也不能拿来当提取真值。

## 8. 附录 B 真正问的是什么

作者把少量 proprietary reasoning 开头放进六个 open-weight models，再观察后续推理和可见答案是否发生风格漂移。可见答案始终自由生成，没有被预填。

一个实验给 Kimi-K3 填入 Opus 4.8 推理的前 1%，在 30 个 HLE 问题上用 best-of-k 的 1/2/3-gram overlap 比较可见答案。STEM 平均增加 0.150，non-STEM 增加 0.086；Inkling 控制组没有相近变化。另一组用 4 words 前缀，覆盖 6 个模型、90 个问题、每条件 4 次采样，即每模型每条件 360 条；用 2^18 维 hashed character 3–5 grams 训练 logistic regression，以按 problem 分组的 5-fold CV 报 AUC。

这些结果说明短前缀能推动某些模型进入另一种表达轨道，却不能倒推出训练数据来源。原因包括样本小、benchmark 偏、serving 配置不可控、提取本身是 fuzzy，且“推理时被前缀带偏”本来就不需要训练时见过该来源。

## 9. 概率抽取与困惑度各回答一个问题

若模型在一次 temperature-1 采样中逐字生成目标 span \(z\) 的概率为 \(p_z\)，独立试 \(n\) 次至少成功一次的概率是：

\[
P(\text{hit by }n)=1-(1-p_z)^n.
\]

例如 \(p_z=10^{-6}\)，试一百万次：

\[
1-(1-10^{-6})^{10^6}\approx 1-e^{-1}\approx 63.2\%.
\]

论文对 16-token spans 的估计显示，即便 Kimi-K3 最容易，复现 decoded reasoning 中一段仍常要约 \(10^9\) 到 \(10^{12}\) 次查询；这不支持实用的逐字记忆提取。

[[perplexity]] 则问“模型觉得整段文字多自然”：

\[
\operatorname{PPL}(t\mid q)=
\exp\!\left(-\frac{1}{|t|}\sum_{i=1}^{|t|}\log p(t_i\mid q,t_{<i})\right).
\]

- \(q\)：题目。
- \(t=(t_1,\ldots,t_{|t|})\)：被评分的推理 token 序列。
- \(t_{<i}\)：第 \(i\) 个 token 前面的真实前缀。
- \(p(t_i\mid q,t_{<i})\)：scorer 给真实下一个 token 的条件概率。
- \(|t|\)：序列长度；除以它是为了按 token 归一。

若三个真值 token 概率是 \([0.5,0.25,0.5]\)，其几何平均是 \((0.5\times0.25\times0.5)^{1/3}=0.397\)，所以 PPL \(=1/0.397\approx2.52\)。低 PPL 表示“顺口”，不能单独证明记忆或蒸馏；论文也发现 native trace 并不总在每个 scorer 下最低。

## 10. 修复的第一原则：把“这是谁的哪一步”纳入验签

最彻底的方案是服务端保存推理，客户端只拿随机 state ID；攻击素材不再离开服务端，但要付出存储、数据库和 API 复杂度。

若继续 stateless，AEAD associated data 至少绑定 user ID、session ID、model policy 与 conversation position。跨用户重放时 caller 不匹配；跨 session 搬运时 session / predecessor 不匹配；跨模型切换通过受控 re-sign，而不是让所有 sibling 默认互通。

防御还要补齐 gateway 隔离、速率 / 异常检测、单块消费记录、signature revocation、旧 key 轮换，以及模型对“转录旧推理”请求的 post-training refusal。密码学绑定缩小合法使用范围；模型防护处理“合法模型已经看见内容后会做什么”。

## 11. hash chain 公式逐项拆开

附录 A 提议让下一块记录前一块的摘要：

\[
\tau_{n+1}=H\!\left(
\mathrm{user\_id}\,\|\,
\mathrm{session\_id}\,\|\,
H(\tau_n\,\|\,\mathrm{salt}_2)\,\|\,
\mathrm{salt}_1
\right).
\]

- \(\tau_n\)：第 \(n\) 块推理内容；\(n\) 是会话顺序。
- \(\tau_{n+1}\)：放进下一块 associated data 的链式摘要。
- \(H\)：密码学 hash；任一输入改变，输出应难以预测地改变。
- \(\|\)：拼接，不是范数。
- \(\mathrm{salt}_1,\mathrm{salt}_2\)：额外随机值，隔离不同层的 hash 输入。

论文在这条式子里复用了 \(\tau\)：右边 \(\tau_n\) 是第 n 块推理内容，左边 \(\tau_{n+1}\) 却是放给下一块用的摘要。实现里最好把 content 与 digest 分开命名；它不是 hash 一次就自动生成下一段推理正文。

教学例不计算真实 SHA 值，只看依赖：第 8 块由 user 17、session 42、第 7 块摘要共同决定。攻击者只拿第 8 块放进 session 91，session 字段变化，验签失败；删掉第 7 块，predecessor 也对不上。

chain 不能阻止攻击者按原顺序搬走整段完整会话，只是把攻击成本从“一块 signature”抬成“完整链”，并缩小 blast radius。P1 只保证相对顺序，容易与 compaction 共存；P2 要求中间一块都不能少，删除旧消息时会迫使后续 hash 全部重算。论文建议用 Merkle roots 保存被压缩区间的可验证承诺，但这仍是防御草案，不是已经部署并正式验证的协议。

## 12. 实验、补丁状态与不能越界的结论

控制实验覆盖 AIME 2025、120 个 Codeforces problems 与 HLE；隐私扫描覆盖 6,708 条公开 trajectories。作者估计用 Haiku 4.5 解 10,000 条、每条约 12k input + 12k output tokens，名义成本约 720 美元；整个项目 API credits 约 30,000 美元。

论文的强结论是：截至测试期，合法 reasoning envelopes 的广泛 portability 与较弱 decoder 组合，足以形成可扩展提取与现实隐私风险。论文没有证明三家使用相同密码结构、没有明文逐字真值、没有穷举所有公开或私有 traces，也没有证明某个 open-weight model 用 proprietary traces 做过训练。

作者在发布前向受影响 provider、Microsoft 与 Hugging Face 披露；所有 model providers 确认收到。论文称截至 2026 年 8 月，图 1 的攻击已不能用文中方法复现。这让论文更像一份已修补漏洞的系统性复盘，而不是当前可照做的攻击指南。

## 我的批注

- 最重要的安全课不是“加密不够强”，而是**认证对象选错了**：只认证 payload，没有认证使用场景。
- statelessness 不是免费的架构属性。服务端省掉状态后，客户端拿到了可复制、可公开、可被重放的能力载体。
- 64 个 reasoning-only artifacts 比总量更关键：它直接证明“只清洗用户可见文本”在协议上没有闭环。
- 附录 B 值得保留，恰恰因为作者没有把相关性包装成定论；风格、PPL、逐字概率三种证据回答不同问题。
- 最稳妥的数据发布建议仍很朴素：公开 agent transcript 时，移除所有 opaque reasoning / signature fields；“看不懂的一串字”也可能是可执行状态。

## 关键概念

- [[authenticated-encryption]] · AEAD 怎样同时保护密文和可见上下文。
- [[reasoning-envelope-replay]] · 合法 envelope 为什么会在错误上下文继续有效。
- [[reasoning-trace-distillation]] · 中间推理为何比最终答案提供更密集监督。
- [[hidden-prompt-injection]] · 恶意意图怎样藏进用户看不见的旧状态。
- [[perplexity]] · “模型觉得顺”与“模型曾经记过”之间的边界。

## 跟 wiki 里其他 paper 的关系

- [[drifting-models]] · 都要求把行为相似、训练来源与因果证明严格分开。
- [[dmd]] · 同样涉及蒸馏，但 DMD 蒸馏的是生成分布梯度，不是语言模型的文本推理轨迹。

## 历史定位

- 2026-05 Green · 公开 reasoning blocks 可互换与重放的基础问题。
- 2026-08 **Stealing Reasoning Traces** · 把跨上下文兼容扩展为三家 provider 的规模化提取、隐私审计与防御方案。
- 2026-08 provider patches · 责任披露后原攻击无法按论文方法复现，问题从活跃漏洞转为协议设计案例。
