---
name: ode-sde
type: paper
source: https://arxiv.org/abs/2011.13456
ingested: 2026-06-12
authors: [Yang Song, et al.]
year: 2021
---

# ODE vs SDE · 确定性流与随机流（底层 + 数值例子）

## 一句话
ODE 是"风场里放颗弹珠顺箭头滑，确定地走出一条路"；SDE 是"同一个风场但每步随机踹一脚，走出一团落点"。两者由"概率流 ODE = 扩散 SDE 的同分布替身"连起来——flow-matching 站 ODE 这头，diffusion 站 SDE 那头。

## 它要解决的痛点
flow-matching / diffusion 到底差在哪？根上的差别不是"哪个模型好"，而是**采样路径上有没有噪声项**：ODE 确定（同起点→同一条路），SDE 随机（同起点→一团落点）。把这件事用风场/醉汉的直觉 + 真数字演算讲清楚，是读懂两类生成模型的前置。

## 核心贡献（这页讲清的）
- **ODE = 确定性流**：`dx/dt=f(x,t)`，跟着速度场积分，轨迹唯一。flow-matching 采样 = 解这个 ODE。
- **SDE = ODE + 随机踹**：`dx=f·dt+g·dW`。drift（确定推力，同 ODE）+ diffusion（每瞬间高斯噪声 dW）。扩散模型前向/反向都是它。
- **桥（Song 2021）**：每个扩散 SDE 配一个概率流 ODE，两者每一刻**边际分布相同**。SDE 追抖动个体、ODE 追密度水流，同一团云。→ DDIM 把扩散当 ODE 跑，少步快采。
- **数值解 + 真例子**：ODE 用 Euler、SDE 用 Euler–Maruyama。取 `f(x)=−x, dt=0.5, g=2`，从 x=10 出发：ODE 第一步永远 10→5；SDE 跑 A 落 6.13、跑 B 落 3.30。噪声乘 **√dt 不是 dt** = 随机游走"按 √时间扩散"。

## 关键概念 → 概念页
- [[ode-vs-sde]] · ML 落地的工程对照（训练目标、推理步数、为什么 SD3/Flux 转向 flow-matching）
- [[flow-matching]] · 站 ODE 这头：直接学速度场、少步快采
- [[score-function]] · 站 SDE 那头：扩散学它来构造反向漂移

## 我的批注 / 疑问
- 一句话记牢：**ODE 确定（弹珠顺风场）/ SDE 随机（醉汉每步被踹）/ 桥是同一团云的两种看法**。数值上 √dt 是"随机比确定顽固"的全部来历，也是扩散采样比流模型慢的根。
- 这页是底层 + 数值直觉版；FM-vs-diffusion 的工程取舍细节在 [[ode-vs-sde]] 概念页，不重复。
- 待查：reverse-time SDE（Anderson 1982）反向漂移里那个 score 项具体怎么冒出来；DPM-Solver 怎么用高阶解法把 ODE 步数再压。
