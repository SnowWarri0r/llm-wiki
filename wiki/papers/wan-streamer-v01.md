---
name: wan-streamer-v01
type: paper
source: https://arxiv.org/abs/2606.25041
upstream: https://wan-streamer.com/v0.1/
ingested: 2026-08-06
authors: Wan Team, Alibaba Group · arXiv v3 · 2026
year: 2026
---

# Wan-Streamer v0.1 · 一个模型怎样边听、边看、边说、边生成画面

Wan-Streamer v0.1 是整条版本线的地基。它先不追求高清，也不把普通视频预训练包装成世界—事件表示，而是回答一个更基础的问题：能否让同一个 Transformer 持续接收用户的文字、声音和画面，同时生成智能体的文字、声音和画面，并把模型侧响应压到约 200 ms。

## 一句话

**把双方六路信号排进一条因果时间线；每 160 ms 感知一次、生成一次，再把输出写回历史。**

## 先纠正四个容易读错的点

1. “一个 Transformer”不等于只有一块网络。音视频仍需要因果 VAE、编码器和解码器；统一的是中间的序列模型与交互状态。
2. 文本不靠扩散生成。文本用 next-token 交叉熵；连续音频和视频 latent 才用条件流匹配。
3. Thinker 与 Performer 是同一模型的部署分工，不是两个独立训练、互相传台词的模型。
4. 论文证明的是 192×336、25 FPS 下的可运行原型。自然倾听、打断和主动说话主要靠定性演示，缺少统一量化评测。

## 论文覆盖地图

| 原文章节 | 页面落点 |
|---|---|
| 1 Introduction | 级联管线为何卡住；全双工为什么是建模约束 |
| 2.1 Overview | 六路信号、条件概率、文本与音视频两类目标、生成结果写回历史 |
| 2.2 Data | 理解、生成、端到端交互三类数据；未公开规模 |
| 2.3 Training | 独立任务预训练 → 端到端交互 → 低延迟蒸馏 |
| 2.4 Inference | 两卡 Thinker–Performer 时间线、吞吐与延迟 |
| 3 Experiments | 两张口径不同的延迟表、定性自然度与打断能力 |
| 4 Related Works | 纯语音全双工、级联数字人、端到端音视频系统的边界 |
| 5 Conclusion | 192p proof of concept、后续升级方向 |

## 1. 先看完整系统

用户侧与智能体侧各有文字、音频、视频，共六路信号。当前用户观测先经因果编码器变成 token 或 latent；单一 Transformer 在完整历史上更新语言与交互状态；文本输出走 next-token prediction，音视频输出走联合条件流匹配；因果解码器把干净 latent 还原成声音和画面。生成结果不仅播出，还会追加回历史，成为下一单元的上下文。这条 [[native-streaming-contract]] 是 v0.1 的核心。

## 2. 条件概率式只是在写“每一段都接着上一段算”

第 \(k\) 个 160 ms 单元中，用户观测记为 \(u_k=(u_k^t,u_k^a,u_k^v)\)，智能体回应记为 \(y_k=(y_k^t,y_k^a,y_k^v)\)。上标 \(t/a/v\) 分别指文字、音频、视频；下标 \(k\) 指时间单元，不是向量坐标。

\[
p_\theta(y_{1:K}\mid u_{1:K})
=\prod_{k=1}^{K}p_\theta(y_k^t,y_k^a,y_k^v\mid u_{\le k}^t,u_{\le k}^a,u_{\le k}^v,y_{<k}^t,y_{<k}^a,y_{<k}^v)
\]

- \(p_\theta\)：参数为 \(\theta\) 的模型给出的条件概率；
- \(K\)：整段交互被切出的单元数；
- \(u_{\le k}\)：用户从开始到当前单元的全部观测；
- \(y_{<k}\)：智能体在当前单元之前已经生成并写回的回应；
- \(\prod\)：把每个单元的条件概率相乘；
- 竖线右侧：当前预测时已经知道的上下文。

三段回应的条件概率若依次为 0.8、0.6、0.5，整条回应路径的概率就是 \(0.8\times0.6\times0.5=0.24\)。这来自概率链式法则，不是假设三个单元互相独立。

## 3. 文本与音视频为什么不能用同一个输出目标

文本 token 是离散编号，模型可以直接在词表上预测“下一个编号是谁”。音频和视频 latent 是连续向量，没有有限词表可枚举，所以论文让它们从高斯噪声沿速度场回到干净 latent。两条输出路径共享同一份因果上下文，因此台词、语调、口型、视线和动作在解码前已经相互影响，而不是先出语音再补动画。

## 4. 条件流匹配从路径到损失

对音频或视频模态 \(m\in\{a,v\}\)，干净目标是 \(z_0^m\)，采样噪声是 \(\epsilon^m\sim\mathcal N(0,I)\)，流时间是 \(\tau\in[0,1]\)。论文用直线把两端连起来：

\[
z_\tau^m=(1-\tau)z_0^m+\tau\epsilon^m,
\qquad
\frac{\partial z_\tau^m}{\partial\tau}=\epsilon^m-z_0^m
\]

取标量例 \(z_0=2\)、\(\epsilon=-1\)、\(\tau=0.25\)：中间点是 \(0.75\times2+0.25\times(-1)=1.25\)，目标速度是 \(-1-2=-3\)。若模型预测 \(-2.4\)，平方误差为 \((-2.4)-(-3))^2=0.36\)。

正式损失是：

\[
\mathcal L_{\mathrm{FM}}^m
=\mathbb E_{\epsilon^m}
\left[\left\|
f_\theta(z_\tau^a,z_\tau^v,c_k,\tau)
-\frac{\partial z_\tau^m}{\partial\tau}
\right\|_2^2\right]
\]

\(c_k\) 是已经到达的用户观测与已经写回的智能体历史；\(f_\theta\) 是统一 Transformer 对速度的预测；\(\|r\|_2^2\) 是把误差向量每个分量平方后相加；\(\mathbb E\) 表示对不同噪声样本求平均。论文没有公开音频与视频损失的具体权重。

## 5. 块因果注意力怎样同时保住因果与并行

普通 token-causal attention 会让同一 160 ms 里的音视频 token 也一个接一个等待。[[block-causal-attention]] 把时间线切成块：第 3 块可以看第 1、2、3 块，但不能看第 4 块；同一块里的 token 则可以互相看。25 FPS 下每帧 40 ms，因此 160 ms 正好是 4 帧。块太长会降低反应频率，块太短会增加调度、通信和解码开销。

## 6. 三阶段训练不是把所有能力一次硬塞进去

第一阶段从 Qwen 语言模型权重初始化统一 Transformer，混合训练图像、音频、视频理解，ASR/TTS、对话与多种生成任务；第二阶段把用户与智能体六路信号真正交错起来，学习响应时机、倾听、打断和长上下文；第三阶段把带 [[classifier-free-guidance]]、更多求解步的强教师蒸馏成少步学生。

为了防止长会话越滚越差，学生还要读取自己前面生成的历史继续训练，而不是永远读真实历史。这个 [[rolling-streaming-distillation]] 把 [[teacher-forcing-video-diffusion]] 的训练—推理分布差距拉回来。论文只说明使用 self-forcing 与 distribution matching，没有披露教师/学生步数、CFG scale、rollout 长度和完整损失。

## 7. Thinker–Performer 为什么能并行

训练时仍是一套端到端模型；部署时分到两张 GPU。Thinker 编码当前用户单元、更新 KV、预测文字/状态，并把上一单元 latent 解码播出；Performer 根据新 KV 运行流匹配求解器，生成下一单元干净音视频 latent。第 \(k\) 拍 Performer 生成 \(y_k\)，第 \(k+1\) 拍 Thinker 才解码并播出 \(y_k\)。[[thinker-performer-streaming]] 的重点是让当前感知、上一段解码与下一段生成重叠，而不是减少模型做的数学工作。

## 8. 160 ms、200 ms、550 ms 是三笔账

- 160 ms：稳态流水线节拍。Performer 计算加通信必须小于这个时间，否则积压。
- 约 200 ms：一份用户信号经过编码、状态更新、latent 生成和解码的模型侧 signal-to-signal 延迟。
- 约 550 ms：200 ms 模型侧加论文预留的 350 ms 双向网络预算；不是所有网络环境的实测值。

## 9. 实验应按测量边界读

论文把语音系统的 model latency、first packet、TTFB、endpointing 与端到端延迟分栏，因为这些数字不能直接排大小。Wan-Streamer 的 550 ms 包含用户感知到同步音视频回应的完整远程路径；视觉生成竞品表里的 20–40 FPS、first-frame delay 或 audio-to-visual delay，往往只覆盖渲染组件，不含外部 ASR、LLM 和 TTS。

定性演示显示空闲时仍有呼吸、视线和微表情，用户说话时会点头或调整姿态，用户打断后能缩短或改变回答，也能因看到新物体或表情主动开口。但论文没有给自然度、口型同步、打断成功率、主动发言准确率或长时一致性的量化指标。

## 10. 报告没有告诉我们的事

- 模型参数量、具体 Qwen 初始化版本和各模块尺寸；
- 理解、生成、双工交互数据的规模、比例与清洗方法；
- 两张 GPU 的型号、显存、互联和各阶段耗时；
- 教师/学生求解步数、CFG scale、rollout 长度与蒸馏损失；
- 自然度、身份一致性、唇音同步、打断和主动说话的量化评测；
- 开源权重、推理代码和可复现训练配方。

## 我的批注

- 最重要的贡献不是 200 ms 本身，而是把“能不能随时听见用户、能不能把刚生成的动作记进历史”写成训练结构，而不是服务层补丁。
- 条件流匹配把音频和视频放进同一个连续生成问题，但“联合条件”不等于论文已经证明每种动作都与每段语音准确同步；目前证据仍以样例为主。
- 两卡流水线不改变统一模型的语义，却把最贵的多步求解与延迟敏感的状态更新拆开，这是后续 v0.2 能只扩 Performer 的前提。
- v0.1 是很强的系统原型报告，不是可逐项复现的训练论文。它公开了三条核心公式和服务时间线，却把模型、数据、蒸馏与硬件账留白很多。

## 版本位置

- [[wan-streamer-v01]]：统一时间线、全因果栈、联合音视频流匹配与初版两卡服务。
- [[wan-streamer-v02]]：把 192×336 提到 640×368，用多卡 Performer 保持延迟。
- [[wan-streamer-v03]]：把普通视频拆成持久世界与事件流，加入开放文本行为。

## 相关概念

- [[native-streaming-contract]]
- [[causal-streaming-vae]]
- [[block-causal-attention]]
- [[conditional-flow-matching]]
- [[rolling-streaming-distillation]]
- [[thinker-performer-streaming]]
- [[full-duplex-multimodal-interaction]]
