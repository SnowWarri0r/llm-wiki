---
name: reference-sliding-window-attention
type: concept
sources: [unlimited-ocr]
updated: 2026-06-22
---

# R-SWA · Reference Sliding Window Attention · 参考滑窗注意力

## 一句话
每个生成 token 只看两段：全部"参考"（视觉+prompt，全局可见）+ 最近 n 个输出 token（滑窗），于是 KV cache 恒定不增。

## 直觉
灵感是**人抄书**。抄一整本时，注意力其实只落在三处：手边的**源书**（一直摊开）、**刚写下的几个字**（确认抄到哪了）、**下一个要写的字**。已经抄完的几十页？不会每写一个字就回头通读一遍——它们**软遗忘**了。正是这种"不全记"让人能低负荷地连续抄几百页不变慢。

把这套搬进注意力：
- **源书 = 参考 token**（视觉 token + prompt）→ 永远全局可见，不淘汰。
- **刚写的几个字 = 输出滑窗**（最近 n 个，n 默认 128）→ 因果滑动。
- **已抄完的早期输出** → 滑出窗口就从 KV cache 淘汰（软遗忘）。

它替代的是 [[kv-cache]] 随输出长度线性膨胀的标准全注意力。也不同于 linear attention——linear attention 会让参考 token 反复做状态更新，把图像特征越揉越糊；R-SWA **把视觉 token 排除在状态转移之外**，所以图永远清晰、认字不掉点。这是它跟普通 sliding window attention（[[sparse-attention]] 家族）最关键的区别。

## 怎么做的
```
生成第 t 个 token 时,它能看见的集合 N(t) =
   P              ← 前缀 prefix: 全部视觉 token + prompt, 长度 L_m, 全局可见
 ∪ D_n(t)         ← 输出滑窗: 最近 n 个已生成 token (因果)

KV cache 当成一个容量 L_m + n 的队列:
   每生成一个新 token → 淘汰队列里第 (L_m+1) 个(最老的那个输出 token)
   → 前缀那段 L_m 永远留着,输出那段恒为 n
```

所以 KV cache 大小 = `L_m + min(n, T)` ≤ `L_m + n`，**不随生成长度 T 增长**。标准 MHA 则是 `L_m + T`，线性涨到爆。

## 数字例子
设前缀 `L_m = 300`（视觉 token + prompt），滑窗 `n = 128`。解码一本几十页的书，输出 `T = 10000` 个 token：

```
标准 MHA  cache = L_m + T   = 300 + 10000 = 10300
R-SWA     cache = L_m + n   = 300 + 128   = 428
─────────────────────────────────────────────────
比值 ρ = 428 / 10300 ≈ 0.0415  →  只用 4%,省了 96%
```

而且 T 越大省得越狠：T=100000 时 MHA 要 100300，R-SWA 还是 **428**（ρ→0）。✓ 自检：把 T 一直加大，MHA 那条线性涨，R-SWA 这条压平在 428 不动——这就是"unlimited"的底气。显存和每步算力都恒定，所以几十页一次前向跑下来速度不掉。

## 跟标准注意力 / 普通 SWA 的对比
| | 标准全注意力 (MHA) | 普通 SWA | R-SWA |
|---|---|---|---|
| KV cache | L_m + T（线性涨） | 常数 | 常数 L_m+n |
| 看得到全部参考(图)? | 能 | 滑出去就看不到 | **永远能**（前缀全局） |
| 视觉 token 会被"揉糊"吗 | 不会 | 会（随滑窗状态转移） | **不会**（排除在状态转移外） |

## 链接
- [[unlimited-ocr]] · 提出 R-SWA 的 paper
- [[kv-cache]] · R-SWA 要兜住的对象：从线性压成常数
- [[sparse-attention]] · R-SWA 是稀疏注意力的"前缀全局 + 输出滑窗"两段式特例
- [[optical-context-compression]] · 配套的输入侧省法（前缀 L_m 本身已经被压小）
- [[flash-attention]] · kernel 落地用 FA v3，R-SWA 下 per-call 时延恒定
