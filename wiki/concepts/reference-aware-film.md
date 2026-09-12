---
name: reference-aware-film
type: concept
sources: [taomate]
updated: 2026-09-09
---

# Reference-aware FiLM · 用一组全局旋钮校准颜色和亮度

## 一句话

内容记忆回答“当前 token 应该找哪段历史”，适合 attention；通道均值、对数标准差等外观统计要同时影响所有视频 token，适合用 FiLM 生成逐通道缩放和偏移。

## 公式

TaoMate 在残差路径里写成：

\[
\hat h=\tilde h+\gamma(c)\odot\operatorname{RMSNorm}(\tilde h)+b(c).
\]

- \(\tilde h\in\mathbb R^{N\times D}\)：读完内容记忆后的 \(N\) 个视频 token、每个 \(D\) 维。
- \(c\)：动态外观与首段锚点的通道均值、对数标准差拼成的条件向量。
- \(\gamma(c),b(c)\in\mathbb R^D\)：小网络从 \(c\) 预测的逐通道缩放与偏移；会广播到所有 \(N\) 个 token。
- \(\odot\)：对应通道相乘；最前面的 \(\tilde h\) 是保底残差。

## 数字例子

把一个 token 缩成两维。设 \(\tilde h=[2,-1]\)，RMSNorm 后为 \([1.265,-.632]\)，外观条件给出 \(\gamma=[.1,-.2]\)、\(b=[-.05,.03]\)：

\[
\hat h=[2,-1]+[.1265,.1264]+[-.05,.03]=[2.0765,-.8436].
\]

自检：若最后一层零初始化使 \(\gamma=b=0\)，则 \(\hat h=\tilde h\)，接入模块的第 0 步不会改变基座输出。

## 为什么不把颜色统计也当 memory token

attention 为每个 query 选择不同记忆，适合姿态、布局、音素等局部内容；颜色均值和对比度是整段共同的基准。FiLM 让同一组通道旋钮一致地作用于全体 token，避免每个位置各自“理解”全局亮度。

## 边界

FiLM 只会执行条件给出的校准，坏统计照样会把整段带偏。TaoMate 的消融中，无 gate 的 FiLM 比只用 memory 更差，证明调制路径必须配合可靠性筛选。

## 链接

- [[taomate]] · 参考感知 FiLM 的完整上下文
- [[cross-attention]] · 内容记忆使用的另一条读取路径
- [[residual-connection]] · 为什么新模块可以从恒等映射开始
