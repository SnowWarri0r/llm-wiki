---
name: mrt
type: paper
source: https://arxiv.org/abs/2605.27235
upstream: https://mrt-cvpr.github.io
ingested: 2026-06-15
authors: [Canva Research]
year: 2026
---

# MRT · Masked Region Transformer · 分层图像生成与编辑

## 一句话
不产出拍平的图，而是一摞可编辑的 RGBA 图层（画布+背景+K 前景）；同一个 20B 模型靠"哪些图层是干净给定、哪些是噪声待生成"这一个 masking 开关，切出文生层 / 拆图成层 / 层改层三任务。建在 Qwen-Image 上，CVPR 2026。

## 它要解决的痛点
拍平的图一旦生成就难改——挪个 logo、换句文案就得整张重画。分层 = "图像版逐元素编辑"：每个元素单独挪/改/重组，可复用设计素材。分层生成此前在规模上没被好好做过。

## 核心贡献
- **选择性 token masking 选任务**：[[selective-token-masking]] —— 每层从干净 latent(给定、不预测)还是噪声(待生成)初始化，这个开关本身就是任务。三任务的 clean/noisy 划分：
  - `text→layers`：合成图/背景/前景全噪声 → 从文字生成整摞
  - `image→layers`：合成图 clean、其余噪声 → 拆图(分割+补全)
  - `layers→layers`：合成图+已有层 clean、新/目标层噪声 → 加层/改风格
  干净↔噪声 token 间 full attention。是 [[qwen-image-2]] "条件→目标"的升级版(任意子集当条件)。
- **Anonymous Region Transformer**：[[layered-image-generation]] —— 每层裁剪成 region token([[video-vae]]/WAN-2.1-VAE)，前景/背景/合成 token 一起 full attention；"匿名"=不给身份标签、靠位置+内容推角色。
- **空间位置靠 RoPE 坐标复制**：把原图层 token 的 [[rotary-position-embedding]] 坐标**原样复制**给对应的条件 token，使两者有"相同的空间位置线索"——这正是图层能**任意重新摆位**的机制（解掉旧版"怎么编码空间位置"的待查）。
- **Overflow 画布层**：全尺寸透明画布留住超出可见区的溢出像素(60%+ 设计有溢出)，并支持**半透明背景合成**；避免旧做法(ART/PrismLayers)边界截断丢像素。
- **DMD 蒸馏少步**：[[dmd-distillation]] —— 50→8 步，6.26× 提速(FID 16.02→18.58)，16 步几乎不掉(16.21)；image→layers 单 H100 ~2.3s，~20 层峰值提速 108.5×、省 50~90% 激活显存。
- 底座 Qwen-Image(~20B, 60 层/hidden 3584/24 头)，**全参数微调**(非 LoRA，因平图→分层分布漂移大)，FSDP2、64×H200；数据 10M+ 多语设计(43M+ 图层 / 7M+ 溢出元素)。

## 训练 / 评测 / 消融（实数)
- **训练**：两阶段渐进——512×512 约 7 万步(全 10M 数据) → 1024×1024 约 2 万步；AdamW，lr 1e-4 恒定，全局 batch 1024(64×H200×16)；**layer-grouping 增广**(随机合并重叠/相邻层)提鲁棒性。
- **评测**(vs 并发的 Qwen-Image-Layered，域外 100 设计)：`PSNR_merged` 按层数分档 MRT 27.34 / 25.91 / 25.72（[4,8)/[8,16)/[16,32) 层），Qwen 仅 25.81 / 23.06 / 22.18——**层越多 MRT 优势越大**。用户研究胜率：质量 79.5% / 完整 68.9% / 粒度 82.6%。指标含 PSNR/SSIM 的 layer 版(只算非透明像素)与 merged 版、FID_merged。
- **消融**：模型 scaling(FLUX 13B→Qwen 20B) FID 17.79→16.15；数据 scaling(0.5M→10M) 16.15→15.63；overflow 支持略升 FID 但换来可编辑性；多任务联训几乎不掉点且体验更好；layer-grouping 稳定 +0.3 左右 PSNR。
- **局限**(作者自陈)：对真实照片泛化弱(缺真实光影)；图层粒度 ill-posed 无唯一 ground-truth；半透明/复杂叠加的遮挡补全难；阴影/反射学不好(设计数据缺)。

## 关键概念 → 概念页
- [[selective-token-masking]] · 一个 mask 切三任务(clean=给定/noisy=生成)；[[qwen-image-2]] 条件思路的推广
- [[layered-image-generation]] · 产出 RGBA 图层而非拍平图 + overflow + alpha + 三大难点
- [[qwen-image-2]] · 同 Qwen-Image 底座；"干净条件 vs 噪声目标"的分层升级版；同 DMD 蒸馏
- [[diffusion-transformer]] · region transformer 跑在 Qwen-Image MMDiT 上
- [[video-vae]] · WAN-2.1-VAE 抽 region latent
- [[rotary-position-embedding]] · 复制 RoPE 坐标 = 图层可重摆位的机制
- [[dmd-distillation]] · 50→8 步少步化；[[closed-form-kl]] 最小化师生转移分布 KL
- [[drifting-models]] · 少步化/蒸馏对照线

## 我的批注 / 疑问
- 一句话记牢：**别产出拍平图，产出一摞能单独编辑、还留住溢出的 RGBA 图层；masking 哪些干净/噪声 = 切任务**。是 [[qwen-image-2]] "塞不塞原图"推广成"任意子集图层当条件"。
- 旧"怎么编码空间位置"的待查已解：**RoPE 坐标从原图层复制到条件 token**，给重摆位用。
- 最务实的一条工程账：**层越多 MRT 越赢**(PSNR 差距随层数拉大、峰值提速 108.5×、省 50~90% 显存)——分层生成的成本本来随层数爆炸，MRT 把它压平了，这才是"at scale"的意义。
- 待查：layer-grouping 增广的合并策略细节；半透明背景合成的训练目标怎么定 alpha。
