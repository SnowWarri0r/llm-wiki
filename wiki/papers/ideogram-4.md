---
name: ideogram-4
type: paper
source: https://ideogram.ai/blog/ideogram-4.0/
upstream: https://github.com/ideogram-oss/ideogram4
ingested: 2026-06-04
authors: [Ideogram Team]
year: 2026
---

# Ideogram 4.0 · 9.3B 单流 DiT, 把排版做进权重

## 一句话
Ideogram 第一个开源权重模型（2026-06-03）：9.3B 的**单流 Diffusion Transformer**，用 **Qwen3-VL（VLM）当文本编码器**、**只用结构化 JSON caption 训练**（显式给调色板/bounding box/文字），9.3B 的体量把文本渲染和版面控制做到开源第一、逼近闭源 GPT Image 2。

## 它要解决的痛点
普通 T2I 模型吃一句自然语言 prompt，**版面和文字基本靠运气** —— 你说"左上角放标题"，它未必听。设计场景要的是精确控制：这个元素放哪、用什么颜色、写什么字。Ideogram 4 的赌注是：与其让模型从模糊语言里猜，不如**把结构（位置、颜色、文字）显式喂进去**，训练和推理都用同一套 JSON。

## 核心贡献
- **单流 DiT**（34 层）：文本和图像 token 共享同一条 self-attention 序列、每层共享投影 —— 对比 SD3/FLUX 的双流 MMDiT（文本图像各一套投影）。结构更简、参数更省。详见 [[diffusion-transformer]]。
- **VLM 当文本编码器**：文本编码器是 [[qwen3-vl]]-8B-Instruct（text-only 模式），而且 DiT 吃它**13 个中间层的 hidden state 拼接**，不是单层、也不是无外部编码器。更深的语言理解喂给生成。
- **结构化 JSON caption（最大差异点）**：模型**只**在结构化 JSON 上训练，每条 caption 穷举画面每个元素 + style 块 + 可选 bbox + 调色板。训练/推理同格式，推理前还按 schema 校验。详见 [[structured-caption-conditioning]]。
- **flow matching + 非对称 CFG**：训练目标是 flow matching（预测速度场，ODE 从噪声到干净 latent，见 [[flow-matching]]）；采样用 Euler，**非对称 CFG**——无条件支整个丢掉文本只跑图像 token，两支独立调，能分开调"听话程度"和"画质"。详见 [[classifier-free-guidance]]。
- **2K 原生 + 透明背景 + 一套权重多分辨率**：噪声 schedule 随分辨率自适应，256–2048px 一套权重通吃。

## 关键概念 → 概念页
- [[diffusion-transformer]] · 单流 vs 双流 DiT
- [[classifier-free-guidance]] · 非对称 CFG
- [[structured-caption-conditioning]] · JSON caption 训练
- [[flow-matching]] · 训练目标（速度场）
- [[kl-vae]] · DiT 工作的 latent 空间由它压缩出来（地基）
- [[qwen3-vl]] · 当文本编码器的 VLM，取 13 个中间层
- [[mrope]] · 3D Multimodal RoPE 把文本图像放一个位置系，bbox 靠它 honor
- [[qk-rmsnorm]] · 单流 DiT 深层 attention 的稳训手段

## 我的批注 / 疑问
- 这是 fish-speech 那条"把启发式塞进权重"主线的视觉版：与其在推理时拼 prompt 工程，不如训练时就用结构化监督——"the more relationships each caption pins down, the more grounded supervision"。
- 9.3B 打赢 80B Hunyuan 的文本渲染，再次印证**数据/监督形态 > 纯堆参数**（dMel、Whisper 同款规律）。
- bbox 用 [[mrope]] 的位置系来 honor，这点很漂亮：布局控制不是外挂模块，是借位置编码天然实现的。
- License 非商用，商用要付费；nf4 量化能塞进单张 24GB。
