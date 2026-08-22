---
name: content-aware-flow-shift
type: concept
sources: [sana-video-2, causal-rcm]
updated: 2026-08-17
---

# Content-Aware Flow Shift · 不同视频多练不同噪声段

## 一句话

flow matching 仍学习同一个目标，但抽时间步时根据视频质量、运动或 token 数改变概率密度，把训练预算放到更有用的难度区间。

## shift 的公式

给时间步的 logit 加 \(\log s\)：

\[
\operatorname{logit}(t_s)=\operatorname{logit}(t)+\log s,
\]

等价于：

\[
t_s=\frac{st}{1+(s-1)t}.
\]

若原中位数 \(t=0.5\)，shift 3 后是 0.75；shift \(1/3\) 后是 0.25。

## SANA-Video 2.0 怎样用

- 预训练：高运动、非最高画质 clip 偏向高噪声；高画质、非高运动 clip 偏向低噪声。
- continual / SFT：关闭内容分支，按 latent token 数把 shift 从 3 调到 6。
- 目标函数没换；改变的是哪些 \(t\) 更常被抽到。

不要把它理解成“高质量视频只学细节、运动视频完全不学细节”。概率密度只是倾斜，没有删除其余时间步。

## Causal-rCM 的静态用法（同一变换的三处同源）

不做内容自适应、s 固定也一样常用。一个更直觉的等价读法：RF 里定义噪声/信号幅度比 \(r=t/(1-t)\)，shift 变换恰好是 \(r\to s\cdot r\)——每一站噪声浓度调浓 s 倍（与 logit 加 \(\log s\) 是同一句话：\(\operatorname{logit}(t)=\log r\)）。为什么高维数据要调浓：k 个强相关像素取平均，噪声标准差降 \(\sqrt{k}\)、信号不动，等效信噪比抬 \(\sqrt{k}\)；同样 t=1/2 小图已面目全非、高清视频还看得清轮廓。Causal-rCM 里三处同源：老师合成数据 shift 3、训练时间采样 UniformShift(5)、推理停靠站——均匀网格 {3/4, 1/2, 1/4} 过 shift 5 得 {15/16, 5/6, 5/8}（t=1/2 即 r=1，调浓 5 倍即 t=5/6）。

## 链接

- [[flow-matching]] · 被重新分配训练时间步的基础目标。
- [[diffusion-timestep-conditioning]] · 网络怎样知道当前噪声等级。
- [[sana-video-2]] · 阈值、阶段和验证分桶。
- [[causal-rcm]] · 静态 shift 3/5 的三处同源用法与推理停靠站换算。
