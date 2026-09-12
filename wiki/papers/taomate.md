---
name: taomate
type: paper
source: https://arxiv.org/abs/2607.24359
upstream: https://github.com/TaoLiveAIGC/TaoMate
ingested: 2026-09-09
authors: Qijun Gan · Chenwei Zhang · Meiguang Jin · Junfeng Ma · Qiu Shen
year: 2026
---

# TaoMate · 让实时数字人既记得刚才，也不忘最初是谁

## 一句话

TaoMate 把历史拆成三份：首段参考永远保留、最近两块留在带位置的 KV cache、更早内容压成固定大小的音视频记忆；每个干净块生成后再用“旧记忆 + 新观察 + 首段锚点”更新长期状态，并把三个去噪阶段做成跨块流水线。

## 先看完整拼图

1. 当前文字、首段参考、最近两块和固定容量记忆共同生成下一块音视频 latent。
2. 完成块先停止梯度，再压成视频结构、音频结构、通道统计和低频外观四类观察。
3. 视频与外观更新受首段相似度控制；音频允许更快变化，但仍被首段声音参考轻轻拉住。
4. 内容记忆用独立 attention 读取，外观统计用 FiLM 调整特征；两者都不塞回主动 KV cache。
5. 训练混合 5/10 块 rollout、少量学生前缀与历史重加噪；推理把三步去噪分给不同设备并行推进不同块。

## 四个最容易混淆的点

- “固定容量”不是完整存档，而是会遗忘的在线摘要。
- 压缩视觉锚点与 KV cache 里的首段原始 latent 同源但不是同一个张量：前者供长期检索，后者保留位置与细节。
- gate 不是决定“这一块要不要生成”，而是决定“这一块有多少资格改写长期记忆”。
- 35 FPS 是三 GPU 的流水线结果；单卡端到端只有 11.1 FPS，论文单卡的 16.32 DiT FPS还排除了 VAE 和后处理。

## 关键数字

- 22.1B 生成器，48 层中每隔 4 层接一次记忆，共 12 层；新增约 97.8M 可训练参数。
- 视频记忆 48 token（24 个首段锚点 + 24 个动态状态），音频记忆 64 token。
- 视频更新 `(βv, λv)=(.15,.20)`；音频 `(.10,.10)`；外观 `(.03,.60)`。
- 6,139 条双向 LTX-2.3 teacher 合成轨迹；每块 3 个去噪步。
- 一分钟 1,441 帧：单卡 130.3±1.3 秒；三卡 35 FPS，约 41.2 秒完成。

## 关键概念

- [[anchor-tethered-persistent-memory]] · 新内容怎样更新，但不把身份越改越偏
- [[reference-aware-film]] · 内容为什么走 attention，颜色亮度为什么走 FiLM
- [[rollout-aligned-causal-context-distillation]] · 训练时怎样让学生见到自己的坏历史
- [[stage-parallel-denoising]] · 三个去噪阶段怎样同时处理不同视频块
- [[kv-cache]] · [[stop-gradient]] · [[flow-matching]] · [[dmd-distillation]]

## 证据边界

arXiv v1 正文多次写“详见补充材料”，但其 9 页 PDF 与 TeX 源包都没有附上补充材料；公开仓库也只提供推理代码。因此精确 DMD/PCM 损失、完整采样日程、Color Δ 与 Long Consistency 的公式当前无法从作者材料核验。本页会解释它们各自承担什么任务，但不伪造缺失公式。

## 我的批注

- 真正的新意是把“带位置的短期连续性”和“无位置的长期证据”拆成两条通道，而不是把 KV cache 简单做大。
- 消融很关键：memory 单独有效，直接加不受控 FiLM 反而变差，加入锚点 gate 才全面最好，说明“记住”不等于“相信所有记忆”。
- 实时结论成立于论文给定的三张 GPU 配置；公开 README 尚未给出复现论文三阶段流水线和 35 FPS 的命令。
