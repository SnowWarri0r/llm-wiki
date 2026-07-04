---
name: selective-token-masking
type: concept
sources: [mrt]
updated: 2026-06-28
---

# 选择性 token masking · 用"哪些给定/哪些待生成"当任务开关

## 一句话
同一个扩散模型，靠"哪些 token 从干净 latent（给定、不预测）初始化、哪些从噪声（待生成）初始化"这个开关，把生成/分解/编辑统一成一个模型——换 mask = 换任务，权重不动。

## 直觉 · 任务的本质都是"已知一部分、求另一部分"
通常一个任务配一个模型或一个 head。但仔细看：文生图（什么都不给、全要生成）、把图拆成层（给平图、求图层）、给图层加一层（给若干层、求新层）——本质都是"**已知 X、求 Y**"，只是 X、Y 的划分不同。

[[mrt]] 的洞见：把"已知的"那部分 token **喂真 latent、不加噪、不参与预测**（masked clean），把"要求的"那部分 token **从噪声开始、当扩散目标**（noisy）。那么"**哪些是 clean**"这个掩码本身就**编码了任务**。换一组 clean/noisy 划分 = 换一个任务，模型一个字不改。

## 怎么做的
```
token 分两类:
  masked clean  = 给定条件, 用真 latent z, 不加噪, loss 不管它
  noisy         = 待生成目标, 用 z_t(加了噪), 是扩散要预测的
前向: 两类 token 一起做 full attention → noisy 能"看见"clean(条件)
loss: 只在 noisy token 上算
```
关键是 **full attention 让目标 token 看得见条件 token**，所以生成出来的部分跟给定的部分一致。

## 数字例子 · MRT 三任务，同一模型只换 mask
设计 = `{z合成图, z背景, z前景¹…ᴷ}`。哪些 clean(给定🔒)、哪些 noisy(生成⚙)：
```
任务            合成图   背景    前景层      = 哪个 mask
text→layers     ⚙噪声   ⚙噪声   ⚙噪声       全噪声 → 从文字生成整摞
image→layers    🔒给定   ⚙噪声   ⚙噪声       只给平图 → 拆成层(分割+补全)
layers→layers   🔒给定   🔒给定   🔒已有/⚙新层  给若干层 → 加一层/改一层
```
✓ 自检：三行用的是**同一个 20B 模型**，差别只在"哪几格是 🔒、哪几格是 ⚙"。`image→layers` 把合成图设 clean、其余 noisy，模型就在"看着这张平图"的条件下把图层 token 去噪出来——等于学会了"看平图、拆图层"。这比"每个任务训一个网络"省得多，且三任务互相之间还能借力（[[mrt]] 实测多任务联训几乎不掉点）。

## 跟别的"遮一部分"的关系
- 是 [[qwen-image-2]]"编辑=把原图 latent 拼进条件"的**推广**：那里只能把"一整张原图"当条件，这里**任意子集 token 都能当 clean 条件**。
- 跟 [[masked-language-model]]（BERT 遮词预测）同一个母题——"遮住一部分、用其余预测它"，只是这里在 latent 扩散上、且 mask 的粒度是"整层"。

## 链接
- [[mrt]] · 用它把 text/image/layers→layers 三任务统一成一个模型
- [[qwen-image-2]] · 它的前身思路（条件里塞原图）；本概念是其推广
- [[layered-image-generation]] · masking 的对象就是一摞图层 token
- [[masked-language-model]] · 同母题：遮一部分、用其余预测
- [[diffusion-transformer]] · clean/noisy token 在同一个 DiT 里 full attention
