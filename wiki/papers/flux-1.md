---
name: flux-1
type: paper
source: https://blackforestlabs.ai/ (FLUX.1 模型卡 / Black Forest Labs)
ingested: 2026-06-17
authors: [Black Forest Labs]
year: 2024
---

# FLUX.1 · 先双流后单流 + 两道蒸馏

## 一句话
Black Forest Labs(原 Stable Diffusion / Latent Diffusion 核心作者)的 12B 整流流 Transformer。架构招牌:**先双流 [[mmdit]] 后单流的混合**;再叠两道正交蒸馏——[[guidance-distillation]](把 CFG 两遍前向压成一遍)做 dev、[[dmd-distillation]] 步数蒸馏到 4 步做 schnell。

## 它要解决的痛点
延续 SD 路线把开源文生图天花板顶高:更强对齐(混合架构) + 更省推理(两道蒸馏)。

## 核心贡献
- **混合架构**:前段双流 MMDiT 块(文字图像各用各的 FFN/AdaLN 对齐),后段单流块(所有 token 共享权重更省)。先用贵的对齐、再用省的收尾。区别于全双流 [[stable-diffusion-3-5]] 和全单流 [[ideogram-4]]。
- **引导蒸馏 → dev**:把 [[classifier-free-guidance]] 的每步 2 次前向蒸成 1 次,引导强度当输入;老师是闭源 pro。省一半算力不掉质量。
- **步数蒸馏 → schnell**:在 dev 上把采样步数蒸到 4 步;与引导蒸馏正交。
- 仍是整流流([[flow-matching]]) + T5-XXL/CLIP 文本编码 + [[kl-vae]] latent。
- 三档:pro(闭源旗舰/API) / dev(引导蒸馏,开放权重非商用) / schnell(再步数蒸馏,Apache 2.0 全开放)。

## 关键概念 → 概念页
- [[mmdit]] · 前段双流块(后段切单流)
- [[guidance-distillation]] · CFG 两遍→一遍,做 dev
- [[dmd-distillation]] · 步数蒸馏到 4 步,做 schnell
- [[classifier-free-guidance]] · 被蒸的那个两遍外推
- [[flow-matching]] · 整流流训练目标
- [[kl-vae]] · latent 空间

## 我的批注 / 疑问
- 一句话记牢:**先双流对齐、再单流干完;引导蒸馏省每步2×、步数蒸馏省步数,两个正交叠成 schnell**。跟 [[stable-diffusion-3-5]] 同源不同路。
- 来源:Black Forest Labs 模型卡 + HF 社区技术分析;机制(12B/双单混合/dev引导蒸馏/schnell 4步/三档协议)已确证。无正式 arXiv 论文(发布走 blog + model card)。
- 待查:双流→单流切换在第几层、双/单块各多少;引导蒸馏后 guidance 输入的有效区间;FLUX 与 SD3 在文字渲染/手部的实测差异。
