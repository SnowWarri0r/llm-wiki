---
name: rollout-aligned-causal-context-distillation
type: concept
sources: [taomate]
updated: 2026-09-09
---

# Rollout-aligned causal-context distillation · 用部署时会遇到的历史出题

## 一句话

老师能看干净双向轨迹，线上学生却只能接着自己的旧输出继续生成；训练因此混入不同长度的自回归 rollout、学生生成前缀和轻度受损历史，让学生提前见到部署时的输入分布。

## 三个旋钮

1. rollout 长度：TaoMate 以 0.8 / 0.2 概率抽 5 / 10 块；更长 rollout 能制造累积误差，但训练更贵。
2. 前缀来源：以 0.1 概率换成停止梯度的学生输出，打破“历史永远正确”的假设。
3. 历史可靠性：非首段历史沿 flow-matching 正向路径轻度重加噪，\(\sigma\sim U(0,.15)\)；固定视觉锚点不受扰动。

## 数字例子

平均 rollout 长度是

\[
\mathbb E[H]=.8\times5+.2\times10=6\text{ 块}.
\]

若一个 batch 有 100 条轨迹，长期平均约 80 条滚 5 块、20 条滚 10 块；其中约 10 条使用学生前缀。自检：这只是期望数量，每个 batch 的实际抽样会波动。

## 它不是新的最终损失

这套方法主要改变“学生在什么历史条件上接受监督”。TaoMate 正文说最终用 DMD 搬运老师分布，再加视频 PCM 约束相邻去噪阶段；但 arXiv v1 没有附上它所指的补充材料，所以精确目标和采样表不能从公开论文核验。

## 边界

人工扰动和学生错误只是在逼近真实部署分布；它们不保证覆盖所有长期故障。固定锚点不加噪能保身份，也意味着模型没有练习“用户参考本身很差”的情形。

## 链接

- [[taomate]] · 具体概率、参数与证据边界
- [[autoregressive-vs-bidirectional-video-diffusion]] · 训练/部署上下文差从哪里来
- [[dmd-distillation]] · 全局分布匹配目标
- [[flow-matching]] · 重加噪沿哪条路径移动
- [[stop-gradient]] · 学生前缀为什么只当输入、不反传整段历史
