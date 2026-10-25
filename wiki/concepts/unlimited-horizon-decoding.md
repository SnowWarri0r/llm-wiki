---
name: unlimited-horizon-decoding
type: concept
sources: [unlimited-ocr-2]
updated: 2026-10-27
---

# 无限时程解码 · 重叠一页分块预填，边界页 KV 复用，用完即放

## 一句话

每步算得再省，几百页的视觉 KV 全部预填驻留显存照样爆；把文档切成重叠一页的 chunk 顺序处理，复用重叠页的 KV 保续接，释放非活跃 chunk，显存只装一个 chunk。

## 直觉

SR-SWA 解决的是"每一步看多少"，这里解决的是"显存里放多少"。两件事独立：哪怕每个 query 只看 640 个 token，全部 300 页的视觉 KV 仍得先算出来放着才能被挑。人抄书也不会把整本书摊在桌上，而是翻到当前这几页，翻页时上一页还露着一角——那一角就是重叠的边界页。

## 怎么做的

```
输入：N 页，指令 q，chunk 大小 W，文本尾长 T
1. 切成 K 个 chunk，相邻 chunk 重叠 1 页（K=1 即不切）
2. C ← ENC(C_1 ⊕ q)                       # 只有第一个 chunk 带指令
   y_1 ← DECODE(C)
3. for k = 2..K:
     C ← C_img_overlap                     # 重叠页的视觉 KV，直接复用
         ⊕ ENC(C_k | C_img_overlap)        # 本 chunk 其余页以重叠页为上下文预填
         ⊕ C_txt_tail                      # 上一 chunk 末尾 T 个文本 token 的 KV
     y_k ← DECODE(C)
4. Y = y_1 ⊕ … ⊕ y_K
```

续接靠两样东西：重叠页的视觉 KV（跨页表格、续行有图可看）和上一段末尾的文本 KV（滑窗接得上，知道抄到哪了）。

## 数字例子

MarathonDocBench 百页级实测（论文表 4）：

| | 峰值 KV（B=1） | 吞吐（B=16） |
|---|---|---|
| 标准解码（全部预填驻留） | 47.00 GB | 360 TPS |
| 无限时程解码 | **1.77 GB** | **1,315 TPS** |

显存 26.6×，吞吐 3.65×。吞吐涨是因为显存省下来后同样的卡能开更大并发。

代价没报：重叠页在两个 chunk 里各编码一次，chunk 越小重复越多；W 和 T 的取值论文没给。

## 链接

- [[unlimited-ocr-2]] · 提出，已集成进 SGLang
- [[sparse-reference-sliding-window-attention]] · 管"每步看多少"的那一半
- [[kv-cache]] · 被分块管理的对象
- [[prefill-decode]] · 这里是多次 prefill 交替 decode
- [[lynnreal-omni]] · 长视频接龙的"边界 latent 冻结复用"是同一思路
