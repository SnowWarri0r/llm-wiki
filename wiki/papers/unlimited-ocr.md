---
name: unlimited-ocr
type: paper
source: https://github.com/baidu/Unlimited-OCR/blob/main/Unlimited-OCR.pdf
upstream: https://github.com/baidu/Unlimited-OCR
ingested: 2026-06-22
authors: Baidu Inc. · Technical Report 2026
year: 2026
---

# Unlimited OCR · 像人抄书一样，一口气解析几十页

百度 2026-06-22 放出的端到端 OCR 技术报告。它接着 DeepSeek-OCR 那条"光学压缩"线往下做，但只动了一个地方：把解码器里**所有**注意力层换成自己提的 **R-SWA（Reference Sliding Window Attention）**，让 KV cache 在整个解码过程恒定不增。结果是——别的 OCR 模型只能一页一页 for-loop 跑，它能在一次前向里把几十页文档从头读到尾。

## 一句话
**把解码器的注意力换成"只盯着原图 + 刚写的最后 128 个字"，KV cache 就恒定了——于是几十页文档能一口气解析完，而不是一页一页重置记忆。**

## 它要解决的痛点
- **LLM 当解码器的甜头与代价**：DeepSeek-OCR 让 OCR 翻红，核心是拿 LLM 当解码器借语言先验。但代价同样明显——输出越长，[[kv-cache]] 越堆越大，显存涨、生成越来越慢。人抄一整本书不会越抄越慢，模型却会。
- **for-loop 不是真·长程**：现有模型没一个能在单次前向里解析十几页，全靠"一页一图、每页重置记忆"的外部调度拼起来。这把一个连贯的长程任务碎成一堆孤立短任务——是工程绕路，不是真能力。
- **现有的省 KV cache 办法都不合适**：标准全注意力 KV cache 线性涨；linear attention 会让视觉/参考 token 反复做状态更新，把图像特征越揉越糊、认字精度掉。需要一种"图永远清晰、只对输出做局部记忆"的注意力。

## 核心贡献
1. **R-SWA**：[[reference-sliding-window-attention]] —— 每个生成 token 注意两段：① **全部参考 token**（视觉 token + prompt，全局可见、永不淘汰）+ ② 只看**前 n 个输出 token**（n 默认 128，因果滑窗）。KV cache 因此恒定为 `L_m + n`，不随输出长度 T 涨。
2. **沿用 DeepEncoder 的光学压缩**：[[optical-context-compression]] —— SAM-ViT 串 CLIP-ViT + 桥接处 16× 压缩，1024×1024 的 PDF 图压到 **256 个视觉 token**。输入侧先压狠，解码侧再用 R-SWA 兜住，两头一夹就 unlimited 了。
3. **3B-A0.5B MoE 解码器**：继承 DeepSeek-OCR 的 [[moe]]，3B 总参、推理只激活 0.5B，效率高。
4. **结果**：OmniDocBench v1.5 拿 **93.23**（比 DeepSeek-OCR baseline 的 87.01 高 6.22，比 DeepSeek-OCR 2 的 89.17 还高 4），v1.6 拿 93.92 端到端 SOTA；40+ 页一次性解析编辑距离仍 < 0.11。

## 关键概念
- [[reference-sliding-window-attention]] · 本文的发动机：全局参考 + 局部输出滑窗 → 恒定 KV cache
- [[optical-context-compression]] · DeepEncoder 把整页文字压成几百个视觉 token，输入侧的省法
- [[kv-cache]] · R-SWA 要兜住的就是它：从线性增长压成常数
- [[sparse-attention]] · R-SWA 是稀疏注意力家族的一种"两段式"特例
- [[moe]] · 解码器 3B 总参只激活 0.5B
- [[flash-attention]] · kernel study 用 FA v3，R-SWA 下 per-call 时延恒定（DeepSeek-OCR 越跑越慢）

## 我的批注
- 最妙的一刀：**只改注意力，不重训编码器**。从 DeepSeek-OCR checkpoint 续训 4000 步，冻结 DeepEncoder 只训 LLM，2M 数据。改动极小却拿了 SOTA——说明 R-SWA 对 dense OCR 不仅不掉点，还"免费午餐"涨点。
- 为什么"免费涨点"？作者推测：全注意力在输出变长时容易发散；R-SWA 把注意力夹在"原图 + 最近 128 字"里，反而逼模型更专注 dense OCR、靠滑窗里的最近输出来定位"我抄到哪了"。
- R-SWA vs 普通 SWA 的关键区别：**视觉 token 被排除在状态转移之外**（永远全局可见、不淘汰），所以不会像普通滑窗那样把图越看越糊。这点是它能保住认字精度的命门。
- 灵感来自人抄书：注意力只在三处——源书、刚写的几个字、下一个字；已抄完的"软遗忘"。这是个很好的 working-memory 类比，落到架构上就是 prefix 全局 + 输出滑窗 + 淘汰旧输出。
- 作者明说 R-SWA 是**通用的"参考型"长程注意力**，不止 OCR——ASR、翻译这类"盯着一个固定参考、长程输出"的任务都能用。这是比 OCR 本身更大的点。

## 跟 wiki 里其他 paper 的关系
- [[qwen3-asr]] / [[whisper]] · 同为"参考→长程输出"的任务，作者点名 R-SWA 也适用 ASR
- [[vit]] / [[clip]] · DeepEncoder 就是 SAM-ViT 串 CLIP-ViT
- [[flash-attention]] · 都在攻"注意力的 IO/显存成本"，一个改 IO 调度、一个改注意力可见范围

## 历史定位
- 2024 **GOT-OCR / dense OCR 兴起** · 端到端 VLM 把检测+识别合一，一次前向解析整页
- 2025-10 **DeepSeek-OCR** · DeepEncoder 光学压缩（16×）+ 3B-MoE 解码器，OCR 翻红；但 KV cache 随输出线性涨
- 2026-06 **Unlimited-OCR（本篇）** · 解码器全换 R-SWA，KV cache 恒定 → 一次前向解析几十页 + 顺手涨点 SOTA
