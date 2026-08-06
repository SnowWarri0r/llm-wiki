---
name: videofdb
type: paper
source: https://arxiv.org/abs/2605.30256v1
upstream: https://research.nvidia.com/labs/dir/videofdb/
ingested: 2026-08-06
authors: NVIDIA / David AI · arXiv v1 · 2026
year: 2026
---

# VideoFDB · 语音助手“看见你”之后，真的会看眼色吗

## 一句话

VideoFDB 不考“画面里有什么”，而考视觉信号有没有改变对话行为：用户停顿时别抢话、点头时继续说、用眼神打断时及时让出话轮。它用 237 段真实双人视频、11 类互动动态、三轴 rubric 与 TOR-Alignment，发现当前模型常把视频当成截图描述，或干脆忽略视觉；语音后接头像的级联系统则来不及在用户说话时做非语言回应。

## 论文覆盖地图

| 原文 | 本页重点 |
|---|---|
| 1–2 | VQA、语音全双工和头像评测分别漏了什么 |
| 3 | 237 clips、11 dynamics、采集与三轮标注 |
| 4 | 感知/生成三轴、judge 流程与五类 timing policy |
| 5 | 全部主表、FPS sweep、三种失败模式、级联头像 |
| Appendix A–F | 数据规格、TOR 公式、judge 一致性、模型接入、逐类结果与例子 |

## 1. 先从一个生活场景理解它在考什么

你说：“你觉得我应该买……”然后看向旁边、停 1.5 秒，显然还在想后半句。只听声音的系统可能把静音当作话轮结束，立刻抢答；能持续看视频的系统应该把视线回避与思考表情结合起来，继续等你说完。

反过来，系统正在说话，你点头“嗯嗯”只是表示听懂了，不是要抢话。它若一看到动作就停，也是不自然。VideoFDB 关心的正是这种“同一个沉默或动作，在不同对话角色下含义不同”。

## 2. 四种缩写先分清

- A2A：音频输入、音频输出；能全双工说话，但看不见。
- AV2A：音频+视频输入、音频输出；这是当前多数 vision-speech agent。
- A2AV：音频输入，语音后接头像视频输出；看起来有脸，但头像通常只跟着语音动。
- AV2AV：音视频输入、音视频输出；既能看见用户的非语言信号，也能独立生成自己的表情、点头和手势。论文指出当时没有公开可评的完整系统。

## 3. 一条样本怎样走完整评测

两位参与者的视频通话分别在本地录音录像，避开网络延迟污染。人工三轮找出并复核某个关键动态窗口 \([t_{start},t_{end}]\)。评测时只把其中一侧当作用户流，实时送给被测模型，录下模型输出。

输出语音转成带时间戳文字；用户整段视频和动态前音频分别由模型生成视觉/副语言 caption；再把动态类型、事件窗口、双方 transcript 与 caption 一起送给 judge。judge 按预先写好的 0–5 rubric 打分；时序部分还由时间戳直接算 TOR-Alignment，不完全依赖 judge 主观判断。

## 4. 11 类动态到底分什么

**只考感知**：带停顿的视线回避、摸头/咳嗽等 adaptor、思考停顿、非语言打断。

**感知与生成都考**：面部情绪、非语言 backchannel、笑声。

**只考生成**：语言打断、语言 backchannel、话轮交接、情绪匹配。

感知评分轴是 Fluency、Conversational Flow、Semantic Grounding；生成评分轴是 Fluency、Dyadic Affect Match、Nonverbal Cue Appropriateness。不是每类都打满三轴：例如思考停顿主要看有没有自然等待，情绪匹配主要看输出音视频情绪是否对应。

## 5. 数据集不是 237 个问答题

237 段由 226 个 test 与 11 个 validation 组成；test 中感知/生成分别 105/121。中位 clip 时长 46 秒，test 动态窗口中位 2.5 秒。源视频至少 720p、30 FPS，音频至少 24 kHz；130 位说话者来自美国和加拿大，只有英语，两人视频会议场景。

每段保留关键动态前 1–3 轮和最多一轮后续，让“为什么这个停顿意味着别抢话”仍有上下文。它是单个动态的单轮评测集，不支持用来训练，也不能代表多人、线下、移动镜头或跨文化非语言习惯。

## 6. 为什么总分之外还要硬算时序

同样是“暂时没说话”，规则可能相反：用户正在思考，系统应保持安静；系统正在讲话，用户点头附和，系统应继续。论文把需要时序判断的样本映射到五种 policy：

1. STAY-SILENT：停顿/视线回避时不要抢话；
2. CONTINUE-SPEAKING：非语言附和或无关小动作时别误停；
3. YIELD-REQUIRED：用户打断后 1.5 秒内让出话轮；
4. SMOOTH-HANDOFF：用户交棒后在标注窗口内开口；
5. BACKCHANNEL-PRODUCED：在窗口内给短于 1 秒、少于 2 词的附和，但不要拿走完整话轮。

## 7. TOR-Alignment 从变量到手算

先定义第 \(i\) 个 clip 里系统是否“拿走完整话轮”：

\[
TO_i=\begin{cases}
0,&\text{输出是沉默或短 backchannel},\\
1,&\text{输出是完整发言}.
\end{cases}
\]

\(i\) 是样本编号；\(TO_i\) 是二值 takeover；普通 takeover rate 是 \(N\) 条样本的均值 \(TOR=\frac1N\sum_i TO_i\)。但不同动态的理想方向相反，所以只报 TOR 会混乱。

论文为每个 timing class \(c_i\) 指定期望 \(TO^*_{c_i}\)：继续讲话和顺滑接棒期望 1；保持安静、让出话轮与短附和期望 0。再定义：

\[
A_i=\mathbf 1[TO_i=TO^*_{c_i}],\qquad
\mathrm{TOR\!\text{-}Alignment}=\frac1N\sum_{i=1}^{N}A_i.
\]

\(A_i\) 是本条是否遵守对应规则的 0/1 指示量；\(N\) 是样本数。五条教学样本的实际 takeover 为 \([0,1,1,1,0]\)，期望为 \([0,1,0,1,0]\)，只有第三条“该让出却继续说”失败，alignment 为 \((1+1+0+1+1)/5=80\%\)。

YIELD-REQUIRED 期望 0，不是要求永远沉默，而是要求当前被打断的完整发言结束；之后可以重新进入下一话轮。

## 8. LM judge 怎么验证，不是直接拿来就信

judge 按 0–5 的动态专属 rubric 评分。作者让 Llama-3.1-70B、GPT-4o 与 Claude Sonnet 4.6 对同一批结果独立打分，再检查一致性。三轴两两相差不超过 1 分的比例为 77.7%、88.7%、80.6%；三 judge 平均的 ICC(A,k) 分别是 0.84、0.90、0.75。

这说明 Fluency 与 Flow 的共识较强，Visual Grounding 较弱。最终实验使用 GPT-4o 单 judge，因此三 judge 一致性是验证证据，不等于主表真的取三者平均。caption 错了，judge 看到的视觉事实也会错；人类真值在 judge 下也不是固定满分。

## 9. 主结果：加视频没有稳定变好

| 模型 / 模式 | Overall | Flow | Grounding | TOR-Align / 中位延迟 |
|---|---:|---:|---:|---:|
| Human | 4.20 | 4.20 | 4.24 | 90% / 1400 ms |
| Gemini 2.5 AV | 3.17 | 2.81 | 3.37 | 72% / 3160 ms |
| GPT Realtime AV | 2.75 | 2.50 | 3.02 | 72% / 5400 ms |
| MiniCPM-o 4.5 AV | 3.40 | 3.54 | 3.63 | 73% / 720 ms |
| MiniCPM-o 4.5 audio-only | 3.44 | 3.76 | 3.10 | 72% / 920 ms |
| MiniOmni2 AV | 1.19 | 1.37 | 1.54 | 64% / 3080 ms |

没有模型在所有感知轴上同时比自己的 audio-only 版本更好。MiniCPM 的视频版视觉 grounding 更高，却整体和 Flow 略低；这正说明“能描述视觉内容”与“把视觉用于话轮管理”不是同一能力。

## 10. 三种失败模式

- **Captioning collapse**：MiniOmni2 的大量回复变成“画面里有一位……”而不是继续对话；论文正文说 87%，图中分类结果为 91% visual captioning。两处口径不一致，本页保留这个差异。VITA 还会输出能力免责声明，并在约 74% 响应里出现 token doubling。
- **Visual-stream ignorance**：GPT Realtime mini 的 AV 与 audio-only 回复常只是互相改写，画面很少改变时机或内容。
- **视觉越密，语音越乱**：MiniCPM-o 4.5 在 2 FPS 达峰；8→10 FPS 时 overall 3.04→2.81，Fluency 3.55→2.33。更多帧占用共享融合容量，并没有自动换来更强理解。

## 11. 语音后接头像为什么结构上吃亏

Gemini 2.5 + Anam 的生成 Overall 为 2.80、TOR-Alignment 44% / 2840 ms；+ Keyframe 为 2.39、31% / 3520 ms；人类是 3.92、78% / 900 ms。两套级联的 Fluency 仍有 3.48/3.43，但 Nonverbal Cue Appropriateness 只有 1.71/1.13。

原因不是头像画得一定差，而是音频驱动头像要等语音出现才有动作。用户正在说时，它无法独立点头、微笑或做短 backchannel；语音→头像的额外链路又把信号拖后 2.8–3.5 秒。要补这个缺口，头像层必须能独立于语音持续生成非语言行为，或直接采用端到端 AV2AV 模型。

## 12. 怎样正确使用这个 benchmark

它适合发现“视觉有没有进入对话控制环”，而不是衡量一般 VQA、知识问答、头像清晰度或多轮人格一致性。总分要和逐动态分、timing、captioning 比例一起读；模型接入方式并不完全相同，例如 MiniOmni2 实际半双工、VITA 每条只取 4 帧、MiniCPM 音频按 1 秒块送入，比较不能忽略这些实现差异。

## 13. 局限

数据只有英语、北美参与者、两人视频会议与单个动态窗口；非语言信号受文化和拍摄方式影响。中途系统 prompt 有时压不过模型预训练的问候习惯。caption 与 judge 构成两层模型依赖，Visual Grounding 的 judge 一致性也是三轴最低。论文 v1 还处于预发布阶段，数据和代码承诺后续公开。

## 链接

- [论文 v1](https://arxiv.org/abs/2605.30256v1)
- [NVIDIA 项目页](https://research.nvidia.com/labs/dir/videofdb/)
- [[full-duplex-multimodal-interaction]]
- [[conversational-nonverbal-dynamics]]
- [[tor-alignment]]
- [[rubric-based-evaluation]]
- [[llm-as-judge]]
