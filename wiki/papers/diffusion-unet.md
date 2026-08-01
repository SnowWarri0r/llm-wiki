---
name: diffusion-unet
type: paper
source: https://arxiv.org/pdf/2006.11239
upstream: https://github.com/openai/guided-diffusion
ingested: 2026-07-27
authors: Jonathan Ho et al. · Prafulla Dhariwal & Alex Nichol · Robin Rombach et al. · 2020–2022 architecture lineage
---

# Diffusion U-Net · 同一张网，反复回答“这一步该擦掉什么”

这不是某一篇论文的逐章摘要，而是一条架构谱系：DDPM 把 U-Net 改成带时间条件的去噪器；ADM 用系统消融把残差块、归一化和注意力磨成熟；LDM / Stable Diffusion 再把去噪搬进 VAE latent，并用 cross-attention 接上文字。读懂这一页，才能真正看懂“扩散模型每一步调用 UNet”到底调用了什么。

## 一句话

**扩散 U-Net 每次接收带噪图或 latent、噪声时刻和条件，经过多尺度残差块与注意力，输出一张同尺寸的噪声或速度图；采样器拿这个输出走一步，再把新状态喂回来。**

## 它要解决的痛点

1. **同一个网络要处理完全不同的噪声强度**：早期输入接近纯噪声，晚期输入已经能看见物体；不告诉网络 \(t\)，同一团数值可能对应不同清理任务。
2. **去噪既要看局部纹理，也要看整张图的布局**：卷积擅长局部，多尺度 U 形结构扩大视野，低分辨率 attention 再补全局关系。
3. **文字条件不是一个类别编号**：Stable Diffusion 让图像位置做 Query、文字 token 做 Key/Value，用 cross-attention 把“猫”“红色”“左边”送进不同空间位置。
4. **采样要重复调用很多次**：网络只负责预测方向，scheduler 才负责从 \(x_t\) 算到 \(x_{t-1}\)。两者必须分清。

## 从经典 U-Net 保留了什么，换掉了什么

- 保留：下采样、瓶颈、上采样、同尺度 skip concat。
- 换掉：普通卷积块升级成带残差的 ResBlock；每个块都吃时间嵌入；低分辨率层插 self-attention；文生图版本插 cross-attention。
- 输出也换了：经典 U-Net 输出每像素类别；扩散 U-Net 输出与输入同形状的噪声、干净样本或速度。

## 一条数字从训练走到恢复

取一个标量代替整张 latent：

\[
x_t=\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon
\]

令 \(x_0=2\)、\(\bar\alpha_t=0.64\)、\(\epsilon=-0.5\)，则：

\[
x_t=0.8\times2+0.6\times(-0.5)=1.3
\]

U-Net 看到 \(x_t=1.3\) 和时刻 \(t\)，若预测 \(\hat\epsilon=-0.3\)，训练损失是：

\[
L=(\hat\epsilon-\epsilon)^2=(-0.3-(-0.5))^2=0.04
\]

把预测噪声代回去估计干净值：

\[
\hat x_0=\frac{x_t-\sqrt{1-\bar\alpha_t}\hat\epsilon}{\sqrt{\bar\alpha_t}}
=\frac{1.3-0.6\times(-0.3)}{0.8}=1.85
\]

若预测完全正确，\(\hat\epsilon=-0.5\)，就得到 \(\hat x_0=2\)，与原值对上。

## 扩散 ResBlock

OpenAI guided-diffusion 的典型块：

```text
x
├─ GroupNorm → SiLU → 3×3 Conv
│  → 用 timestep embedding 生成 scale / shift
│  → GroupNorm × (1+scale) + shift
│  → SiLU → Dropout → 零初始化 3×3 Conv
└────────────────────────────── + → output
```

GroupNorm 按单个样本、分组归一化，不依赖 batch。[[group-normalization]] 的两数例子：

\[
h=[1,3],\quad \mu=2,\quad \sigma=1,\quad \operatorname{GN}(h)=[-1,1]
\]

若当前时刻生成 \(scale=0.5, shift=0.2\)：

\[
(1+0.5)[-1,1]+0.2=[-1.3,1.7]
\]

同一份空间特征因此会随时刻改变处理方式。详见 [[diffusion-timestep-conditioning]]。

## 时间嵌入

DDPM 用 Transformer 同款正弦位置编码表示 \(t\)，再过 MLP；每个 ResBlock 都收到同一条时间向量的投影。它不是告诉网络“第 327 层”，而是告诉网络“当前噪声有多重”。

早期高噪声阶段更像搭构图；晚期低噪声阶段更像修边缘。没有时间条件，相当于让同一个修图师闭着眼判断现在该重画构图还是擦掉一粒噪点。

## 为什么 attention 放在较小的特征图

把 \(H\times W\) 个位置摊成 \(N=HW\) 个 token，attention 权重矩阵有 \(N^2\) 个格子：

```text
64×64：N=4096 → N²=16,777,216
16×16：N= 256 → N²=    65,536
```

后者小 256 倍。因此 DDPM 只在 16×16 做 self-attention；ADM 扩到 32×32、16×16、8×8，并发现多头和多尺度 attention 都能改善 FID。

## Stable Diffusion 的 tensor 地图

官方 Stable Diffusion v1 配置把 512×512 RGB 图经 8 倍 VAE 压缩成 64×64×4 latent。U-Net 基础通道 320，倍率为 `[1,2,4,4]`：

```text
64×64×4
→ 64×64×320
→ 32×32×640
→ 16×16×1280
→  8× 8×1280
→ 16×16×1280
→ 32×32×640
→ 64×64×320
→ 64×64×4
```

每层两个 ResBlock；`attention_resolutions=[4,2,1]` 是相对 64×64 latent 的下采样倍率，所以对应 16×16、32×32、64×64。这里的 “resolution” 在配置里其实写的是 downsample rate，名字很容易读反。

## 文字怎样进入 U-Net

[[cross-attention]] 里，图像特征做 Query，文字 token 做 Key / Value：

\[
\operatorname{Attn}(Q,K,V)=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt d}\right)V
\]

假设某个图像位置的 \(Q=[1,0]\)，两个文字 token“猫 / 天空”的 Key 分别是 \([1,0]\)、\([0,1]\)。点积是 `[1,0]`，softmax 后约为 `[0.731,0.269]`。这个位置会拿到 73.1% 的“猫”信息、26.9% 的“天空”信息。真实模型有更多 token、更多维度和多头，但账就是这笔账。

## 训练和采样不是一回事

训练时，一张干净样本只随机抽一个 \(t\)，加一次噪，U-Net 前向一次，算一次 MSE。采样时从纯噪声开始，U-Net 在每个 scheduler 时刻都要重新前向：

```text
x_T
→ U-Net 预测方向
→ scheduler 算 x_{T-1}
→ U-Net 再预测
→ scheduler 再走一步
→ …
→ x_0
```

U-Net 不自己决定“下一步走多远”；DDPM、DDIM、Euler、DPM-Solver 都能拿同一类网络输出，用不同规则更新状态。[[classifier-free-guidance]] 还会在同一步比较有条件与无条件输出，再放大提示词带来的差值。

## ADM 证明哪些改造真有用

在 ImageNet 128×128 消融里，基础 U-Net 的 FID 为 15.33（700K step）。多头 attention、多尺度 attention、BigGAN 式残差上下采样分别改善结果；组合后 FID 再降 3.14，约为 12.19。残差输出除以 \(\sqrt2\) 反而让 FID 变差 0.16。AdaGN 对照更直接：13.06 对 15.08，说明时间 / 类别条件不只“加进去”，拿来调归一化更有效。

## 跟经典 U-Net、DiT 的关系

- [[unet]]：分割祖先；输出类别图，卷积块没有扩散时间条件。
- **Diffusion U-Net**：保留 U 形多尺度与 skip，换成残差块、时间条件和注意力，输出去噪方向。
- [[dit]]：把卷积 U-Net 整体换成 Transformer，但仍可以预测同一套 \(\epsilon\)、\(x_0\) 或速度目标。

所以“diffusion”是训练 / 采样过程，“U-Net / DiT”是承担预测的网络骨架。两者不是同一个维度。

## 我的批注

- 真正让经典 U-Net 变成扩散 U-Net 的不是“多了噪声”，而是**同一套权重必须随 \(t\) 改变行为**，时间条件是结构核心。
- skip connection 不只是补纹理；它让高分辨率路径不必每一步都绕过最窄瓶颈，对反复去噪尤其重要。
- attention 放低分辨率是很工程的折中：先让卷积把 4096 个位置压到 256 个，再做全局沟通。
- Stable Diffusion v1 的 U-Net 约 860M 参数，后来 DiT 取代它，不代表 U 形思想失效；多尺度、长短路径和条件调制仍以别的形式保留下来。

## 跟 wiki 里其他页的关系

- [[unet]] · 经典分割 U-Net 的完整尺寸账与 concat skip
- [[noise-prediction-objective]] · 从加噪、预测噪声到恢复 \(x_0\)
- [[group-normalization]] · 为什么扩散 U-Net 常用 GN 而不是依赖 batch 的 BN
- [[diffusion-timestep-conditioning]] · 正弦时间嵌入怎样变成 scale / shift
- [[cross-attention]] · Stable Diffusion 里文字进入图像特征的通道
- [[classifier-free-guidance]] · 同一步条件 / 无条件两次输出怎样组合
- [[diffusion-transformer]] · DiT 如何接替 U-Net

## 历史定位

- 2015 **U-Net** · 为医学分割建立下采样—上采样—横向跳连
- 2020 **DDPM** · Wide-ResNet U-Net + GroupNorm + 时间嵌入 + 16×16 self-attention
- 2021 **ADM** · AdaGN、多头多尺度 attention、残差上下采样与系统消融
- 2022 **LDM / Stable Diffusion** · 在 VAE latent 去噪，用 spatial transformer 接文字
- 2023 **DiT** · 用 Transformer 接替扩散 U-Net

