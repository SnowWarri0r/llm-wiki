---
name: x-vector
type: paper
source: https://www.danielpovey.com/files/2018_icassp_xvectors.pdf
upstream: https://doi.org/10.1109/ICASSP.2018.8461375
ingested: 2026-06-22
authors: David Snyder, Daniel Garcia-Romero, Gregory Sell, Daniel Povey, Sanjeev Khudanpur (JHU) · ICASSP 2018
year: 2018
---

# X-Vectors · 给一段语音拍张"声纹身份证"

说话人识别（声纹）领域的代际转折点。在它之前，主流是纯统计的 i-vector（2011）；这篇把那套换成一个用神经网络端到端学的固定长度嵌入——x-vector。它是 Kaldi 里的看家声纹模型（标准 recipe `sre16/v2`），也是后来 ECAPA-TDNN 一系的祖宗。

## 一句话
**训一个网络去"认人"，训完把分类头扔掉，中间那层固定长度向量就是声纹——靠 statistics pooling 把任意长语音压成定长。**

## 它要解决的痛点
- **i-vector 吃不动大数据**：i-vector 靠 GMM-UBM + 因子分析这套统计模型，数据给到一定量就饱和，再多也不涨。神经网络反过来——数据越多越强，这是它最大的筹码。
- **变长语音 → 定长向量这一步**：语音可以是 3 秒也可以是 30 秒，逐帧特征是不定长序列，但比对两个人是不是同一个，需要两个**等长**向量算距离。怎么把不定长压成定长是核心难题——答案是 [[statistics-pooling]]。
- **对噪声/信道不鲁棒**：i-vector 分不清"说话人差异"和"换了麦克风/有背景噪声"。x-vector 因为是监督训练，可以靠**数据增强**（往干净语音里掺噪声+混响）硬学出鲁棒性——这步 i-vector 学不动。

## 核心贡献
1. **x-vector 这个嵌入本身**：[[speaker-embedding]] —— 把一段语音映射成一个 512 维向量，代表"是谁在说"而不是"说了什么"。同一个人的不同录音向量靠得近，不同人离得远。
2. **statistics pooling 层**：[[statistics-pooling]] —— 网络中间放一层，把逐帧（不定长）的高层表示用**均值+标准差**汇成定长向量。这是"变长→定长"的魔法所在。
3. **TDNN 主干**：[[time-delay-neural-network]] —— 帧级用时延网络，每往上一层"看"的时间窗口翻倍，到第 3 层一个输出帧已经聚合了 15 帧上下文。
4. **数据增强当免费午餐**：拿 MUSAN（babble/音乐/噪声）+ 模拟混响把训练数据翻好几倍，监督训练能充分吃下去，换来跨信道鲁棒性。

## 关键概念
- [[speaker-embedding]] · 语音→定长"身份向量"的总思路，含 i-vector→x-vector→ECAPA 的代际，和 PLDA/余弦打分
- [[statistics-pooling]] · 变长→定长的核心机制（mean+std over time）
- [[time-delay-neural-network]] · 帧级主干，膨胀上下文，conv1d-with-dilation 的前身
- [[pooling]] · statistics pooling 是 pooling 家族里"沿时间轴聚合"的一种

## 我的批注
- 最值得记的一句：**训练目标和使用方式不是一回事**。训练时让网络做分类（认出这段是 N 个人里的哪个），训完把 softmax 分类头扔掉，从倒数第二段（segment6）抠出来的向量当通用声纹用。分类只是个"逼网络学会区分人"的代理任务。
- x-vector 是从 segment6 的**仿射输出**（过 ReLU 之前）抠的，不是最后一层。论文里试过 segment6 比 segment7 好。
- "x" 没什么深意，就是接着 i-vector 起的名（i→x）。
- statistics pooling 取**均值+标准差**而不是只取均值，是因为标准差带了"这段语音里嗓音波动有多大"的信息，对区分人有用。这点很容易被忽略。
- 它跟 [[whisper]] / [[qwen3-asr]] 是两条完全不同的路：ASR 关心"说了什么"（内容），x-vector 关心"谁说的"（身份）。同样是音频编码器，目标正交。
- 现代接班人是 ECAPA-TDNN（加了 SE 注意力 + 多层特征聚合 + attentive stats pooling），但骨架还是这套"帧级 TDNN → 沿时间 pool → 段级嵌入"。

## 跟 wiki 里其他 paper 的关系
- [[whisper]] / [[qwen3-asr]] · 同为音频编码，但 x-vector 抽"谁"、ASR 抽"什么"，目标正交
- [[resnet]] · ECAPA 那代往 TDNN 里加了残差，这里 x-vector 还是朴素堆叠
- [[bert]] · 同样是"训一个代理任务（MLM/分类）→ 拿中间表示当通用嵌入"的套路

## 历史定位
- 2011 **i-vector**（Dehak）· GMM-UBM + 因子分析，纯统计，声纹十年主力
- 2018-04 **x-vector**（本篇）· 神经网络端到端嵌入 + statistics pooling + 数据增强，吃大数据完胜 i-vector
- 2020 **ECAPA-TDNN**（Desplanques）· 加 SE 注意力 + 多尺度聚合 + attentive stats pooling，至今强 baseline
