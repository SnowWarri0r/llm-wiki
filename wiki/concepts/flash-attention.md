---
name: flash-attention
type: concept
sources: [unlimited-ocr]
updated: 2026-06-22
---

# FlashAttention · 注意力的"省搬运"算法（精确，非近似）

## 一句话
标准注意力把 N×N 的大分数矩阵吐进慢显存(HBM)再读回来,**卡在内存搬运上**。FlashAttention 把 Q/K/V **切成小块、只在快内存(SRAM)里一块块算**,靠**在线 softmax** 拼出和一次算全**一模一样**的结果——大矩阵从不落地。结果:2~4× 快、显存从 O(N²) 降到 O(N),且**输出逐位相同**。

## 直觉 · 瓶颈不是算力，是来回搬大矩阵

注意力 `softmax(Q·Kᵀ)·V`,中间 `Q·Kᵀ` 是 **N×N**(N=序列长)。N=8000 就是 **6400 万个数**。算它不慢——慢在**把这么大一个矩阵写进 HBM、再读回来做 softmax、再读回来乘 V**。

GPU 的内存层级（见 [[ai-memory-hierarchy]]）:**小而极快的 SRAM** 和 **大而慢的 HBM**。标准注意力让 N×N 矩阵在 HBM 里**来回搬三趟**,带宽全耗在这——这叫 **memory-bound**(算力大半在干等)。

<figure style="margin:26px 0; padding:22px; background:#f1eee8; border:1px solid #c7bca8; border-radius:4px;">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="fa-r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker>
    <marker id="fa-g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#1f4d3a"/></marker>
  </defs>
  <!-- 标准注意力 lane -->
  <text class="reveal d1" x="40" y="32" text-anchor="start" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">标准注意力 · N×N 落 HBM 来回搬</text>
  <g class="reveal d1" font-size="9" text-anchor="middle" fill="#3a3128">
    <rect x="44" y="48" width="70" height="30" rx="3" fill="#faf4e1" stroke="#7a6f5d"/><text x="79" y="67">算 Q·Kᵀ</text>
    <rect x="190" y="44" width="150" height="40" rx="3" fill="#f3d9d9" stroke="#9b2c2c"/><text x="265" y="61" font-weight="700" fill="#7a2020">HBM: N×N 大矩阵</text><text x="265" y="75" font-size="8" fill="#7a6f5d">6400 万个数(N=8k)</text>
    <rect x="416" y="48" width="64" height="30" rx="3" fill="#faf4e1" stroke="#7a6f5d"/><text x="448" y="67">softmax</text>
    <rect x="556" y="48" width="60" height="30" rx="3" fill="#e8efe4" stroke="#4a6b3a"/><text x="586" y="67">×V 出</text>
  </g>
  <g class="reveal d2" stroke="#9b2c2c" stroke-width="1.3" marker-end="url(#fa-r)">
    <line x1="114" y1="63" x2="186" y2="63"/><line x1="340" y1="63" x2="412" y2="63"/><line x1="480" y1="63" x2="552" y2="63"/>
  </g>
  <text class="reveal d2" x="360" y="104" text-anchor="middle" font-size="9" fill="#9b2c2c">大矩阵在慢内存(HBM)里来回搬三趟 = 瓶颈(memory-bound)</text>

  <line x1="40" y1="124" x2="680" y2="124" class="reveal d2" stroke="#c7bca8" stroke-width="1" stroke-dasharray="4 4"/>

  <!-- Flash lane -->
  <text class="reveal d3" x="40" y="152" text-anchor="start" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f4d3a">FlashAttention · 小块进 SRAM,大矩阵不落地</text>
  <g class="reveal d3" font-size="9" text-anchor="middle" fill="#3a3128">
    <rect x="44" y="168" width="84" height="30" rx="3" fill="#faf4e1" stroke="#7a6f5d"/><text x="86" y="187">Q/K/V 切块</text>
    <rect x="210" y="162" width="220" height="42" rx="4" fill="#cde0d4" stroke="#1f4d3a" stroke-width="1.6"/><text x="320" y="180" font-weight="700" fill="#1f4d3a">SRAM: 一块块算 + 在线 softmax</text><text x="320" y="195" font-size="8" fill="#7a6f5d">只装得下一小块,快</text>
    <rect x="556" y="168" width="60" height="30" rx="3" fill="#e8efe4" stroke="#4a6b3a"/><text x="586" y="187">出结果</text>
  </g>
  <g class="reveal d4" stroke="#1f4d3a" stroke-width="1.3" marker-end="url(#fa-g)">
    <line x1="128" y1="183" x2="206" y2="183"/><line x1="430" y1="183" x2="552" y2="183"/>
  </g>
  <text class="reveal d5" x="360" y="226" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#1f4d3a">N×N 从不写进 HBM → 显存 O(N)、省掉来回搬 → 结果一模一样</text>
</svg>
</figure>

## 三个招
**① Tiling(分块)**:把 Q、K、V 切成小块,每次只把一小块搬进 SRAM 算,**N×N 完整矩阵从头到尾不写 HBM** → 显存 O(N²)→O(N)。

**② 在线 softmax(online softmax)**:难点——softmax 要除以**一整行的和**,但分块时一次只看到部分 key,提前不知道总和。招:**边走边维护 running 最大值 `m` 和 running 求和 `l`**;新块带来更大的 max,就**回头把已算的部分按 `e^(旧max−新max)` 缩小**再加新块。不用攒齐整行,结果跟一次看全**完全一致**。

**③ 反向重算**:训练反向本要用 N×N 矩阵,FlashAttention **不存它、现场拿 Q/K/V 重算**——重算(算力便宜)比从 HBM 读回(带宽贵)还划算。

## 数字例子 · 在线 softmax 拼出和一次算一样
一行分数 `s = [1, 3 | 2, 5]`,分两块:左 `[1,3]`、右 `[2,5]`。

**一次看全 4 个**(减最大值 5 防溢出):
```
exp: [e^-4, e^-2, e^-3, e^0] = [0.018, 0.135, 0.050, 1.000]
和 = 1.203   → 权重 [0.015, 0.112, 0.041, 0.831]
```
**在线(一块块来)**:
```
块1 [1,3]: running max m=3
           running 和 l = e^(1-3)+e^(3-3) = 0.135 + 1 = 1.135
块2 [2,5]: 新 max m'=5（比 3 大！）
   ① 旧的按 e^(m−m')=e^(3−5)=0.135 缩小:  l ← 1.135 × 0.135 = 0.153
   ② 加块2:  l ← 0.153 + e^(2-5)+e^(5-5) = 0.153 + 0.050 + 1.000 = 1.203 ✓
```
running 和 **1.203 = 一次算的 1.203**,逐位对上 → 权重也一样。关键就是那句:**来了更大的 max,就把已经算的乘 `e^(旧−新)` 缩一下再续**。(输出向量同理:已累计的加权 V 也乘这个因子再加新块。)

## 跟 sparse-attention 的区别(别混)
- **[[sparse-attention]]**:**跳过一些 token 对**(只算局部/选定的),是**近似**——结果会变,省的是算力。
- **FlashAttention**:**一对都不跳**,是**精确**——结果逐位不变,省的是**内存搬运**。
- 一个改"算什么"(算法),一个改"怎么搬数据"(IO)。两者**正交,可叠加**。

## 代码出处 / 来源
- FlashAttention:Dao et al. 2022;FlashAttention-2/3 持续优化;现已是 PyTorch `scaled_dot_product_attention` 默认后端之一
- 关键词:IO-aware、tiling、online softmax、recomputation

## 链接
- [[self-attention]] · 它优化的就是这个 softmax(Q·Kᵀ)V
- [[softmax]] · 在线 softmax 用的就是"减最大值"那套,只是改成 running
- [[ai-memory-hierarchy]] · SRAM 快小 / HBM 大慢 —— FlashAttention 全部动机的根
- [[sparse-attention]] · 对照:近似(改算法) vs 精确(改 IO)
- [[kv-cache]] · 长上下文推理常 FlashAttention + KV cache 一起上
