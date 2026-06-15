---
name: mrt
type: paper
source: https://arxiv.org/abs/2605.27235
ingested: 2026-06-15
authors: [Canva Research]
year: 2026
---

# MRT · Masked Region Transformer · 分层图像生成与编辑

## 一句话
不产出拍平的图，而是一摞可编辑的 RGBA 图层（画布+背景+K 前景）；同一个 20B 模型靠"哪些图层是干净给定、哪些是噪声待生成"这一个 masking 开关，切出文生层 / 拆图成层 / 层改层三任务。建在 Qwen-Image 上，CVPR 2026。

## 它要解决的痛点
拍平的图一旦生成就难改——挪个 logo、换句文案就得整张重画。分层 = "图像版逐词编辑"：每个元素单独挪/改/重组，可复用设计素材。分层生成此前在规模上没被好好做过。

## 核心贡献
- **masking 选任务**：每层从干净 latent(给定、不预测)还是噪声(待生成)初始化，这个开关本身就是任务——全噪声=text→layers；合成图干净/层噪声=image→layers(拆图，分割+补全)；已有层干净/新层噪声=layers→layers(加层/改风格)。干净↔噪声 full attention。是 [[qwen-image-2]] "条件→目标"的升级版(任意子集当条件)。
- **Anonymous Region Transformer**：每层裁剪成 region token(WAN-2.1-VAE，见 [[kl-vae]])，前景/背景/合成 token 一起 full attention；"匿名"=不给身份标签、靠位置+内容推角色 → 每层留完整空间信息、可任意重摆。
- **Overflow 画布层**：全尺寸透明画布留住超出可见区的溢出像素(60%+ 设计有溢出)，避免旧做法边界截断丢像素。
- **DMD 蒸馏 50→8 步**：6× 提速(FID 16.02→18.58)，~2.3s/张(H200)，~20 层峰值 108.5×。
- 底座 Qwen-Image(~20B, 60 层/hidden 3584/24 头)，全参数微调(非 LoRA)，10M+ 多语设计。

## 关键概念 → 概念页
- [[qwen-image-2]] · 同 Qwen-Image 底座；"干净条件 vs 噪声目标"的分层升级版；同 DMD 蒸馏
- [[diffusion-transformer]] · region transformer 跑在 Qwen-Image MMDiT 上
- [[kl-vae]] · WAN-2.1-VAE 抽 region latent
- [[closed-form-kl]] · DMD 最小化师生转移分布的 KL
- [[drifting-models]] · 少步化/蒸馏对照线

## 我的批注 / 疑问
- 一句话记牢：**别产出拍平图，产出一摞能单独编辑、还留住溢出的 RGBA 图层；masking 哪些干净/噪声 = 切任务**。是 [[qwen-image-2]] "塞不塞原图"推广成"任意子集图层当条件"。
- 来源：arxiv 全文走 ar5iv 镜像 + 项目页核实，机制(masking/anonymous region/overflow/DMD)已确证。
- 待查：anonymous region 的 token 怎么编码空间位置(给重摆位用)；overflow 画布训练目标怎么定半透明；image→layers 的分割+补全质量边界。
