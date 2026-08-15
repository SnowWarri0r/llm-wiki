---
name: diffusion-timestep-conditioning
type: concept
sources: [diffusion-unet, dit, sana-video-2, asyncpatch-diffusion]
updated: 2026-08-14
---

# Diffusion Timestep Conditioning · 告诉去噪网络“现在噪到哪一步”

## 一句话

同一个去噪网络要处理从纯噪声到近乎干净的所有状态；先把时刻 \(t\) 编成向量，再送进每个 block，让网络随噪声强度切换工作方式。

## 为什么不能只喂 \(x_t\)

输入数值本身不一定能唯一说明噪声等级。早期步骤要先搭全局结构，晚期步骤只需修小纹理。不给 \(t\)，相当于让同一个修图师不知道现在拿到的是草稿还是终稿。

## 正弦时间嵌入

一个常见写法是：

\[
e_{2i}(t)=\sin\left(\frac{t}{10000^{2i/d}}\right),\qquad
e_{2i+1}(t)=\cos\left(\frac{t}{10000^{2i/d}}\right)
\]

\(d\) 是嵌入维度，\(i\) 选择不同频率。高频分量分得清相邻时刻，低频分量表示长范围进度。

## 数字例子

用两档频率 \(1\) 与 \(0.1\) 做四维玩具版：

\[
e(t)=[\sin t,\cos t,\sin(0.1t),\cos(0.1t)]
\]

当 \(t=0\)：

\[
e(0)=[0,1,0,1]
\]

当 \(t=\pi\)：

\[
e(\pi)\approx[0,-1,0.309,0.951]
\]

同一个时刻被多档“钟表指针”共同编码，不需要为 1000 个时刻各存一张互不相关的表。

## 怎样进入 ResBlock

时间向量先过 MLP，再投影成 scale 与 shift。OpenAI guided-diffusion 的代码形式是：

\[
h'=(1+s_t)\operatorname{GN}(h)+b_t
\]

\(h\) 是当前空间特征，\(s_t\) 与 \(b_t\) 都由时间嵌入生成。若 \(\operatorname{GN}(h)=[-1,1]\)：

```text
时刻 A：scale=.5, shift=.2 → [-1.3, 1.7]
时刻 B：scale=-.2, shift=.1 → [-.7, .9]
```

输入特征相同，仅时刻不同，block 的处理结果就不同。这才是“条件注入”真正改动的地方。

## 链接

- [[diffusion-unet]] · 时间嵌入送进每个残差块
- [[group-normalization]] · 被 scale / shift 调制的归一化
- [[adaptive-layernorm]] · DiT 用 LayerNorm 实现的后继版本
- [[positional-encoding]] · 同一套正弦编码最早在 Transformer 里表示位置
- [[asyncpatch-diffusion]] · 把广播到全图的标量时刻升级为二维时间图，并在各层做空间 FiLM
