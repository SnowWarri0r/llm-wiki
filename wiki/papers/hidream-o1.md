---
name: hidream-o1
type: paper
source: https://arxiv.org/abs/2605.11061
upstream: https://github.com/HiDream-ai/HiDream-O1-Image
ingested: 2026-06-10
authors: [HiDream.ai]
year: 2026
---

# HiDream-O1-Image · Pixel-level Unified Transformer

## 一句话
一个原生统一的图像生成基座：把原始像素、文本、任务条件全塞进一个 transformer 的同一条 token 序列——**没有 VAE、没有独立文本编码器**，画之前还用一个推理 agent 先"想"一遍版面。8B 打平/超更大模型。

## 它要解决的痛点
主流文生图是拼出来的：VAE 压图、独立文本编码器读字、生成器画画——三套参数、三个语义空间，靠中间接口对齐，带来 VAE 信息瓶颈 + 文图语义错位 + 单任务专用。HiDream-O1 把它们塌成一个端到端 transformer。

## 核心贡献
- **Pixel-level Unified Transformer (UiT)**：像素+文本+条件三类 token 进同一条序列、一个 transformer 处理。详见 [[unified-transformer]]。
- **无 VAE · 像素空间扩散**：扩散直接在原始 RGB 上做，patch embedding 替掉 VAE 压缩、去掉 latent 瓶颈；大 patch 控住 token 数，配 perceptual loss(LPIPS/DINO) 防糊。详见 [[pixel-space-diffusion]]、[[kl-vae]]（被替掉的）。
- **混合注意力**：文本/条件 token causal（像 LLM 读 prompt）、生成 token full（像 DiT 双向去噪），一条流缝合 LLM + DiT。backbone 直接是 LLM（8B 从 [[qwen3-vl]]-8B 初始化）→ 无独立文本编码器。
- **O1 · Reasoning Prompt Agent**：Gemma 的"thinking"，对模糊 query 先推理版面/属性/物理/文字再细化 prompt 喂 UiT。
- **训练**：flow matching（[[flow-matching]]）+ perceptual；512→1024→2048 三段渐进；后训 SFT + RLHF（[[grpo]]）。结果：GenEval 0.90（8B，超 Qwen-Image 0.87），200B+ Pro 0.92；CVTG-2K 文字渲染超 FLUX.2。

## 关键概念 → 概念页
- [[pixel-space-diffusion]] · 无 VAE，直接在像素上扩散
- [[unified-transformer]] · 像素+文本+条件一条流 + 混合注意力
- [[kl-vae]] · 被替掉的压缩器（对照 latent 路线）
- [[qwen3-vl]] · backbone 初始化来源
- [[flow-matching]] · 训练目标（+ perceptual loss）
- [[grpo]] · 后训 RLHF
- [[ideogram-4]] · 另一条"统一"哲学（统一在监督形态）

## 我的批注 / 疑问
- 这篇是 latent-DiT 那套的反向操作 + 集大成：[[kl-vae]] 扔了、文本编码器收进主干、[[grpo]] 拿来对齐、[[qwen3-vl]] 当骨架——把我之前学的零件反着重组了一遍。
- 跟 [[ideogram-4]] 是文生图统一的两条路：ideogram 统一在"监督形态"（结构化 caption），HiDream 统一在"架构"（无 VAE + 文本编码器进主干）。两者都用 Qwen3-VL 但角色相反（外挂编码 vs 当主干）。
- "像素空间很贵"是误解：token 数由 patch 大小定不由分辨率，大 patch 切原图 ≈ latent+小 patch 的 token 数；真正换掉的是 VAE 这个外挂压缩器 + 它的信息瓶颈。
- 待查：patch 具体多大、生成 token 的 full attention 跟扩散 timestep 怎么配（论文没细给）。
