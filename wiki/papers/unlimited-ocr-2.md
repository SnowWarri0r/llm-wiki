---
name: unlimited-ocr-2
type: paper
source: raw/unlimited-ocr-2.txt
upstream: https://github.com/baidu/Unlimited-OCR
ingested: 2026-10-27
authors: Baidu ERNIE Team（核心：Shu Wei, Jingjing Wu, Qunyi Xie）· Technical Report 2026-10-27（仓库内 Unlimited-OCR-2.pdf，尚无独立 arXiv 号）
year: 2026
---

# Unlimited OCR 2 · 只看正在抄的那一页，几百页也不变慢

百度一代 Unlimited OCR 用 R-SWA 把**文本侧**的 KV cache 钉成常数，几十页能一口气抄完；但每写一个字仍要看**全部页面**的视觉 token，页数上到几百，每步的视觉注意力成本又线性涨回来了。二代把解码器里所有注意力换成 **SR-SWA**：Page Gate 先把可看的视觉范围缩到"当前页（及其相邻块）"，Token Sieve 再在候选里按预算挑 top-k 个远程块，于是每个 query 的参考集是固定容量的。配上分块预填 + 边界页 KV 复用的"无限时程解码"，几百页文档也能在固定显存里连续解析。

## 一句话

**一代固定了"记多少已写的字"，二代固定了"看多少页的图"：每个 token 只看当前页 + 预算内 top-k 远程块 + 最近的输出，百页级每步快 7.0×（对全注意力）/ 5.6×（对 R-SWA），自建 MarathonDocBench（100 篇、103–300 页）拿 77.06，第二名 33.74。**

## 它要解决的痛点

- **一代堵住了一半**：R-SWA 把输出滑窗固定在 128 字，KV cache 的文本段不再涨；但视觉段是"全部页面永远可见"，N 页 × 每页 256 token 的 prefix 随 N 线性涨，每步注意力也随 N 线性涨。百页级这就是主瓶颈——表 2 直接写一代"有 40 页输入上限"，MarathonDocBench 上没法报。
- **人抄书不是这么抄的**：抄到第 150 页时眼睛只盯着第 150 页，偶尔为了跨页的表格、续行瞟一眼前一页，不会把整本书摊在脑子里。多页文档的视觉依赖天生是**页间稀疏、页内集中**。
- **替代方案各有毛病**：线性 / 循环注意力把历史压成紧凑状态，细粒度视觉证据（认字、跨页检索）保不住；硬选择的稀疏路由（CSA、MiniMax Sparse Attention）要辅助监督或 warmup；DashAttention / HiLS 这类把路由分数直接进前向、端到端训的路线是作者选的参照。
- **显存还有第二道墙**：就算每步算得快，几百页的视觉 KV 全部预填驻留显存仍然爆——标准解码 B=1 峰值 KV 47.00 GB。

## 核心设计

1. **SR-SWA（[[sparse-reference-sliding-window-attention]]）**：沿块稀疏注意力的做法把输入切固定块，每个 query 保留固定局部窗 L(q)，远程参考集 S(q) 分两级构造——
   - **Page Gate**：query 属于页 g(q)，候选块只留"与该页有交集"的块（块边界和页边界无关，跨页块也算进来）。位置编码拆成两段 `[p_page, p_intra]`：页坐标按 0–1 交替、页内坐标单调递增——页坐标有界，页数再多也不会位置爆炸。
   - **Token Sieve（[[routing-bias-sparse-router]]）**：每个候选块压成一个摘要键 k̄_b，打分 s_b = q̃ᵀk̄_b/√d，过 **α-entmax** 得稀疏路由分布 π，取 top-k。选中块的概率转成**去均值的 log 先验** β_b = log π_b − mean(log π)，直接**加到注意力 logits 里**；softmax 在"局部窗 ∪ 选中块"上归一化。因为路由偏置参与 logits，解析损失的梯度能直接传回路由器——不用辅助 KL 蒸馏损失。
   - 结果：保留集 R(q) = L(q) ∪ ⋃_{b∈S(q)} B_b 的大小与文档长度无关。
2. **无限时程解码范式（[[unlimited-horizon-decoding]]）**：文档切成相邻重叠 1 页的 chunk，顺序处理；下一 chunk 的 cache = 重叠页的视觉 KV ⊕ 以它为上下文新预填的本 chunk ⊕ 上一 chunk 末尾 T 个文本 token 的 KV；非活跃 chunk 的视觉 KV 释放。只有一个 chunk 驻留显存。指令 q 只跟第一个 chunk 走。已集成进 SGLang。
3. **骨干不动**：DeepSeek-OCR 的 DeepEncoder（16× 光学压缩）+ 3B-A0.5B MoE 解码器（图里写 A570M），从一代 checkpoint 起训。
4. **数据引擎**：2M 多页 + 10M 单页；伪标签来自 MinerU2.5-Pro 和 PaddleOCR-VL-v1.6（按各自擅长域分工）；合成文档管线补版式多样性；VLM 多维特征分析做平衡过滤；多页子集再过 MinerU-Popo 精修 + 启发式规则对齐相邻页边界的结构。
5. **训练**：1 epoch，25×8 H800，全局 batch 1,600，最长 64K token，AdamW + cosine，初始 lr 2.5e-4，冻结 DeepEncoder 和 aligner 只训 LLM，MS-Swift。
6. **MarathonDocBench**：100 篇、103–300 页、205k 标注版面元素（平均每篇 2,050 个），比 MPDocBench（≤30 页）长约一个量级；跨页文本 / 表格更密。结构标注（框、类型、层级、阅读序、跨页续接）由强单页解析器初始化 + 人工精修；文本转写由同一解析器初始化 + VLM 迭代精修 + 分歧人工裁决。

## 关键数字

- **MPDocBench**（≤30 页，Overall↑）：Unlimited-OCR 2 **84.59**；Qwen3.8-Max 78.30；Qwen-3.8-Flash-Next 77.36；Gemini-3.8-Flash 76.25；一代 Unlimited-OCR **61.89**。跨页 T-TextEdit 0.100（最好）、T-TableTEDS 89.54（最好）；HeadingTEDS 60.10。
- **MarathonDocBench**（100–300 页）：**77.06**；Kimi-K3 33.74；Gemini-3.8-Flash 28.61；Qwen-3.8-Flash-Next 27.83；Gemini-3.1-Pro 26.97；GLM-5.3-Flash 7.51。差距 +43.3。
- **OmniDocBench v1.6**（单页）：94.02 vs 一代 93.92（+0.10）；Table TEDS 89.60 vs 90.16（−0.56）；同表 TeleOCR 96.91、OvisOCR2 96.47 更高——单页不是它的主场。
- **效率**：百页级每步 7.0×（vs 全注意力）、5.6×（vs R-SWA），Gundam 模式、batch 3、每页固定生成 1,024 token；无限时程解码 B=1 峰值 KV 47.00 → 1.77 GB（26.6×），B=16 吞吐 360 → 1,315 TPS（3.65×）。
- 长度曲线：2–30 页到 250+ 页准确率基本平；对比模型随页数掉，Qwen3.8-Flash-Next 在 223 页失败。

## 关键概念 → 概念页链接

- [[sparse-reference-sliding-window-attention]] — Page Gate + Token Sieve 的两级参考集（新）
- [[routing-bias-sparse-router]] — 把路由概率当 logit 偏置、端到端训路由（新）
- [[unlimited-horizon-decoding]] — 重叠分块预填 + 边界页 KV 复用（新）
- [[reference-sliding-window-attention]] — 一代的发动机，二代在它上面加视觉侧稀疏
- [[optical-context-compression]] — DeepEncoder 16×，输入侧不变
- [[kv-cache]] — 二代把视觉段也钉成常数
- [[sparse-attention]] — 块稀疏 + 查询相关路由那一支
- [[moe]] — 3B 总参激活 0.5B

## 我的批注 / 疑问

- 一代解决"记多少字"，二代解决"看多少图"，两代合起来才是真·unlimited：文本段靠滑窗，视觉段靠页门 + 筛子，显存靠分块。三道闸各管一维，读的时候别混。
- **最该追问的空白：没有任何消融**。Page Gate 单独多少、Token Sieve 单独多少、k 取几、块多大、局部窗多宽、entmax 的 α——正文一个数都没给（README 只提"例如 512 个工作参考 token"）。一代对 MPDocBench 61.89 → 二代 84.59 的 +22.7 里，有多少来自 SR-SWA、多少来自新加的 2M 多页数据和 MinerU-Popo 跨页标注，没法拆。
- 一代在 MPDocBench 上只有 61.89、低于一堆通用 VLM，这和一代报告"几十页一次解析"的口径不太一样——两代共用一套多页评测后，一代的长页能力其实不如宣传稳。
- 单页 OmniDocBench 基本持平（+0.10），表格还掉 0.56；TeleOCR / OvisOCR2 高出 2–3 分。这篇的价值全在多页，别拿它当单页 SOTA。
- 路由器的设计很像 HiLS / DashAttention 那一路：路由分数不走蒸馏而是作为 logit 偏置进前向——好处是梯度直接来自解析损失；但 α-entmax 让分布真稀疏（本页例子里最差块概率恰为 0），top-k 之外的块零概率，log 先验只对选中块有定义，这两件事是配套的。
- 页坐标"0–1 交替"意思是位置编码只区分"本页 / 相邻页"奇偶，不记绝对页号——外推到任意页数不爆，但也等于放弃了"第 7 页和第 150 页哪个远"这种信息。作者在局限里承认全局结构（标题层级）是短板，HeadingTEDS 两个基准都是各类里最低（60.10 / 48.20），和这个设计是一致的。
- 口径小错位：正文说"Figure 6 汇总主结果"，柱状图其实是 Figure 5；激活参数文中 500M、图中 570M；仓库 arXiv 徽章链到的 2606.23050 是一代论文，二代目前只有仓库里的 PDF。
- 延迟是"每步 ms"在固定每页 1,024 token、batch 3 下量的；端到端时间、prefill 开销、分块重叠页的重复编码成本都没报。

## 跟 wiki 里其他 paper 的关系

- [[unlimited-ocr]] · 直接前作，本文把它从"长时程"推到"无限时程"
- [[hierarchical-denoising-visual-reasoning]] · 同样用固定连接数的稀疏注意力控成本（SHAP）
- [[wonder-video-world-model]] · 另一个"固定保留集 + 检索远端"的稀疏上下文做法（Sparse Context Forcing）
- [[lynnreal-omni]] · 长视频接龙里"紧凑上下文 + 边界 latent 冻结复用"和这里的边界页 KV 复用是同一个思路

## 历史定位

- 2025-10 DeepSeek-OCR · 光学压缩 + MoE 解码器，OCR-2.0 单页端到端
- 2026-06 Unlimited OCR · R-SWA 钉住文本 KV，几十页一次前向（"长时程"）
- 2026-10 **Unlimited OCR 2** · SR-SWA 钉住视觉参考集 + 分块解码钉住显存，百页级（"无限时程"，作者称 OCR-3.0）
- 待看 · 作者点名下一步是加线性注意力保全局信息，补标题层级这块短板
