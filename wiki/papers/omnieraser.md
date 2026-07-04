---
name: omnieraser
type: paper
source: https://arxiv.org/abs/2501.07397
upstream: https://arxiv.org/html/2501.07397v3
ingested: 2026-06-29
authors: [Runpu Wei, Zijin Yin, Shuo Zhang, 等 · PRIS-CV(北邮)]
year: 2025
---

# OmniEraser · 用视频帧白送的 ground-truth 教模型"连影子一起抹掉"

## 一句话
对象消除的真痛点不是"把物体抠掉",而是**连它的影子/反光一起干净抹除、且别凭空补出个新东西**。OmniEraser 两手都解决:数据上用**视频帧白送真 ground-truth**([[video-frame-paired-supervision]])——物体在场的帧当输入、物体离开后的帧当目标,影子在后一帧里真的没了;模型上用**双条件输入**([[object-background-guidance]])把"要删的物体"也喂进去,让 [[flux-1]] DiT 明确知道哪块该清空,不再瞎补。

## 它要解决的痛点
普通 inpainting 抹物体有两个老毛病:
1. **凭空补新物体 / shape-like 伪影**:模型只拿背景上下文当引导([[object-background-guidance]] 的反面),它"不知道这块该变空",于是照着周围猜出个新东西填进去。
2. **影子/反光赖着不走**:训练数据多是 copy-paste / 随机 mask 合成的,里头根本没有真实的物理光影,模型从没见过"物体走了影子也该消失",自然学不会。

根子都在**监督信号假**:没有"物体连同其物理效果一并消失"的真实成对样本。

## 核心贡献
- **Video4Removal 数据集**([[video-frame-paired-supervision]] + [[background-subtraction]]):134,281 个三元组,全自动从视频帧挖。流水线三步——① MOG 高斯混合背景建模分前景/背景(前景像素占比阈值 0.15);② 给每个前景帧用 MSE 找时间上最近、光照最接近的背景帧配对;③ GroundingDINO + [[sam]] (SAM2) 自动出物体 mask(**只圈物体、不圈影子**),并滤掉快速运动的模糊帧。关键设计:**mask 只盖物体,但目标帧里影子真没了 → 模型被迫端到端学"物体↔效果"的关联**。
- **Object-Background Guidance 双条件输入**([[object-background-guidance]]):把四样东西在 latent 维拼接——被抠物体的 latent、背景的 latent、噪声、二值 mask——过一个可训练 linear 投影再进 DiT。等于把"要删什么(物体)"也明确告诉模型,而不是只给"周围长啥样(背景)"。消融:只给背景 FID 119.94 → 加物体条件 39.52(砍 66%)。
- **模型**:底座 [[flux-1]]-dev 的 [[dit]],只在 self-attention + FFN 插 [[lora]](rank 32)轻量微调;文本提示固定一句 `"There is nothing here"`;mask 做膨胀/腐蚀/外接框增广,扛用户画的不规则 mask。
- **RemovalBench 基准**:70 对精心制作的物体+ground-truth,1024×1024,固定机位拍、人工 SAM mask(排除效果区)。
- 结果:RemovalBench 上 FID 39.52(前 SOTA Attentive-Eraser 55.49)、LPIPS 0.133(0.146)、CMMD 0.208;RORD-Val 上 FID 43.71 / PSNR 22.13 全面领先;数据集消融 Video4Removal 39.52 vs RORD 85.27(砍 62%)、MULAN 97.49。50 人主观评测也偏好它。

## 关键概念 → 概念页
- [[video-frame-paired-supervision]] · 核心 cleverness:视频帧白送"物体在/不在"的真成对数据
- [[object-background-guidance]] · 双条件输入,把"要删的物体"也喂给模型
- [[background-subtraction]] · MOG 高斯混合从视频里分前景/背景
- [[object-effect-removal]] · 任务定义:连影子/反光一起抹,vs 普通 inpaint
- 复用:[[flux-1]] 底座 · [[dit]] 主干 · [[flow-matching]] 训练 · [[lora]] 微调 · [[sam]] / [[promptable-segmentation]] 出 mask · [[lpips]] 评测

## 我的批注 / 疑问
- 一句话记牢:**对象消除的胜负手在数据,不在模型——谁能拿到"物体连影子一并消失"的真 ground-truth 谁就赢。视频里物体自己会走,等于免费帮你拍了 before/after。** mask 故意不圈影子是点睛:不标注、靠目标帧逼模型自己学到"这影子属于这物体"。
- 双条件输入跟 [[krea-2]] / [[rae-dit]] 那种"在更好的 latent / 数据上做扩散"是一条线:底座都用 [[flux-1]],真正的增量在喂什么、怎么喂。
- 来源:arXiv 2501.07397v3 HTML 全文 + PRIS-CV GitHub;机制(MOG 0.15 阈值 / MSE 配帧 / GroundingDINO+SAM2 / 134,281 / FLUX.1-dev + LoRA r32 / "There is nothing here" / 双消融 FID)已确证。
- 待查:linear 投影层的具体通道维怎么对齐(论文没细说);RemovalBench 70 对相对其它 benchmark 是否偏小、泛化到 in-the-wild 复杂场景的失败案例分布。
