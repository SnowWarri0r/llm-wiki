---
name: flash-attention
type: concept
sources: [unlimited-ocr]
updated: 2026-07-17
---

# FlashAttention · 快的不是少算，而是少把中间结果写回显存

## 一句话

普通注意力常拆成三次 GPU 计算：先算分数矩阵，再做 softmax，最后乘 `V`。三次计算之间，前一步的结果要先写回 HBM，后一步再读出来。最占地方的恰好是两个 `N × N` 中间矩阵。

FlashAttention 把三步合成一次计算，并把 `Q/K/V` 分块：一小块分数在片上高速存储中算出来，立刻完成 softmax 更新和 `V` 的加权累加，用完就丢。它仍然计算所有 token 对，也仍会按分块顺序重复读写一部分输入或输出块；省掉的是两个完整 `N × N` 中间矩阵的落地读写。

> **先把最容易误解的地方说死：只把矩阵切小，并不会自动减少 IO。真正起作用的是「分块 + kernel 融合 + 在线 softmax」这套组合。**

## 为什么大矩阵非得来回搬？

先看 GPU 上的两层存储：

- **HBM**：显卡的主显存。容量大，能长期放 `Q/K/V` 和中间结果，但离计算单元较远。
- **片上 SRAM / 寄存器**：紧挨着计算单元，喂数据很快，但容量很小，只够放几块数据；一次 kernel 结束后，这些空间会被下一项计算复用。

这里的 **kernel**，可以先理解成“一次提交给 GPU 的完整函数”。普通注意力通常是三次函数调用：

1. 矩阵乘 kernel：读 `Q,K`，算出 `S = QKᵀ`。
2. softmax kernel：读 `S`，算出概率矩阵 `P = softmax(S)`。
3. 矩阵乘 kernel：读 `P,V`，算出 `O = PV`。

问题出在 **kernel 的交接处**。第 1 个 kernel 算完后，第 2 个 kernel 还没开始；第 1 个 kernel 占用的片上小空间不能拿来长期保存整张 `S`。所以它只能把 `S` 写回 HBM。第 2 个 kernel 再从 HBM 读出 `S`，算完 `P` 后又把 `P` 写回 HBM；第 3 个 kernel 接着把 `P` 读出来。

不是 GPU 喜欢来回搬，而是**三项工作分开做时，中间结果必须放到双方都能访问的 HBM，才能完成交接**。

<figure style="margin:26px 0;padding:22px;background:#f1eee8;border:1px solid #c7bca8;border-radius:6px;">
  <div style="font:700 13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#3a3128;margin-bottom:16px;">同一份注意力，两种数据路线</div>
  <div style="display:flex;flex-wrap:wrap;gap:18px;">
    <div style="flex:1 1 260px;min-width:0;padding:18px;border:1.5px solid #9b2c2c;background:#fffaf5;">
      <div style="font-weight:800;color:#7a2020;margin-bottom:12px;">普通实现 · 三个 kernel 分开交接</div>
      <div style="padding:9px;background:#faf4e1;border:1px solid #c7bca8;">① 读 Q/K → 算 S</div>
      <div style="text-align:center;color:#9b2c2c;font-weight:800;padding:5px 0;">↓ 写 HBM · 再读</div>
      <div style="padding:9px;background:#f3d9d9;border:1px solid #9b2c2c;"><strong>完整 S：N×N</strong></div>
      <div style="text-align:center;color:#9b2c2c;font-weight:800;padding:5px 0;">↓ softmax 后再写 HBM · 再读</div>
      <div style="padding:9px;background:#f3d9d9;border:1px solid #9b2c2c;"><strong>完整 P：N×N</strong></div>
      <div style="padding:9px;margin-top:8px;background:#faf4e1;border:1px solid #c7bca8;">③ 读 P/V → 算 O</div>
    </div>
    <div style="flex:1 1 260px;min-width:0;padding:18px;border:1.5px solid #1f4d3a;background:#f7fbf8;">
      <div style="font-weight:800;color:#1f4d3a;margin-bottom:12px;">FlashAttention · 一个融合 kernel</div>
      <div style="padding:9px;background:#e8efe4;border:1px solid #4a6b3a;">读一小块 Q/K/V 到片上</div>
      <div style="text-align:center;color:#1f4d3a;font-weight:800;padding:5px 0;">↓ 当场做完</div>
      <div style="padding:9px;background:#cde0d4;border:1px solid #1f4d3a;"><strong>小块 S → softmax 更新 → 加权 V</strong></div>
      <div style="text-align:center;color:#1f4d3a;font-weight:800;padding:5px 0;">↓ 小块 S 用完即丢</div>
      <div style="padding:9px;background:#e8efe4;border:1px solid #4a6b3a;">只保留每行的 m、l 和输出累加值</div>
      <div style="padding:9px;margin-top:8px;background:#faf4e1;border:1px solid #c7bca8;">扫完所有块 → 得到最终 O</div>
    </div>
  </div>
  <figcaption style="margin-top:14px;color:#6d6254;font-size:.9em;">左边慢在两次交接都要把 N×N 中间结果放进 HBM；右边让中间小块在片上“出生、用完、消失”。</figcaption>
</figure>

## 算一笔最小的 IO 账

假设序列只有 4 个 token，先不管每个 token 的向量有多宽。分数矩阵 `S` 和概率矩阵 `P` 都是 `4 × 4`，各有 16 个数。

普通三-kernel 写法仅为了交接这两个中间矩阵，就要搬：

| 动作 | HBM 搬运量 |
|---|---:|
| 第 1 个 kernel 把 `S` 写回 HBM | 16 个数 |
| softmax kernel 读出 `S` | 16 个数 |
| softmax kernel 把 `P` 写回 HBM | 16 个数 |
| 最后一个 kernel 读出 `P` | 16 个数 |
| **仅中间矩阵合计** | **64 个数** |

FlashAttention 若每次处理 `2 × 2` 的分数小块，会依次算 4 块。每块 `Sᵢⱼ` 都只在片上短暂停留：算出 4 个分数，马上更新这一行的 softmax 统计量和输出累加值，然后覆盖这 4 个位置去算下一块。于是上面那 **64 个中间数的 HBM 搬运变成 0**。

这不等于总 IO 为 0。片上空间放不下全部 `Q/K/V/O`，扫下一块时仍要重新读写其中一部分。具体哪一边重复，取决于循环顺序：原始论文把 `K/V` 块放在外层，所以每块 `K/V` 只读一次，`Q` 和尚未完成的 `O` 会分批重读；一些后续实现会换一种排法。

FlashAttention 做的是一笔交换：

- 多付一些输入/输出块的重复读写，反向传播时再多付一点重算；
- 换掉完整 `S` 和 `P` 的写回、读出，以及训练时对它们的长期保存。

当 `N` 很大时，这笔账很划算。比如 `N = 8000`，一个 `N × N` 矩阵有 6400 万个数。若每个数占 2 字节，一张就是约 128 MB；按上面“`S` 写一次读一次、`P` 写一次读一次”的直观实现，单个注意力头光中间矩阵就要搬约 **512 MB**，还没算 `Q/K/V/O`。

### 三笔账不要混在一起

- **计算量**没有从平方变线性：每个 query 仍然要和所有 key 做点积，仍是 `O(N²d)`。这里的 `d` 是一个注意力头的向量宽度。
- **额外中间存储**从完整的 `S/P` 两张 `N × N` 矩阵，降成每行少量统计量。论文给出的结论是：不计输入和最终输出，只需 `O(N)` 额外空间。
- **HBM 搬运量**大幅减少，但也不是 0，更不是简单的 `O(N)`。论文把普通注意力写成 `Θ(Nd + N²)` 次 HBM 访问，把 FlashAttention 写成 `Θ(N²d²/M)`；`M` 表示片上 SRAM 能容纳多少个数。`M` 越大，一块能装得越多，重复扫描就越少。

这三个结论可以同时成立：**算的 token 对一样多，临时存下来的东西少得多，跨 HBM 搬的数据也少得多。**

## 为什么切块以后片上放得下？

完整 `S` 的形状是 `N × N`。`N = 8000` 时，它有 6400 万个位置，片上存储当然塞不下。

但如果一次只取 64 行 `Q` 和 64 行 `K`，临时分数块只有 `64 × 64 = 4096` 个位置。它可以在片上完成三件事：

1. 算 `QᵢKⱼᵀ`，得到这一小块分数；
2. 把这块分数并入当前行的 softmax；
3. 立刻乘对应的 `Vⱼ`，并入输出累加值。

随后这块分数就没用了，可以直接覆盖。继续读下一块 `Kⱼ,Vⱼ` 即可。

所以，“切块能省 IO”还差半句话：**切到片上放得下之后，趁数据还在片上，把后续计算一口气做完。** 如果只是把 `S` 切成小块，算完仍逐块写回 HBM，最后再读回来做 softmax，IO 并没有消失。

## softmax 明明要看完整一行，为什么能一块块算？

这正是在线 softmax 解决的问题。

对某个 query 来说，普通 softmax 要先看到它对所有 key 的分数，才能算分母。FlashAttention 不保存整行分数，只为这一行保留三个小状态：

- `m`：到目前为止见过的最大分数，用来防止指数溢出；
- `l`：以 `m` 为基准的指数和，也就是 softmax 分母的累计值；
- `a`：以同样权重累计的 `V`，也就是输出的分子；全部块处理完后，最终输出 `o = a/l`。

状态的数量只跟 query 行数和 `V` 的宽度有关，不需要保存 `N × N` 张量。

## 数字例子 · 不保存权重，也能直接得到最终输出

只看一个 query。它对 4 个 key 的分数是：

```text
s = [1, 3 | 2, 5]       竖线表示分成两块
V = [10, 20 | 30, 40]   为了手算，把每个 V 简化成一个数
```

### 先一次看全，算出标准答案

最大分数是 5。所有分数减 5 后再取指数：

```text
指数权重 = [e⁻⁴, e⁻², e⁻³, e⁰]
         ≈ [0.0183, 0.1353, 0.0498, 1.0000]

分母 l = 0.0183 + 0.1353 + 0.0498 + 1
       = 1.2034

分子 a = 0.0183×10 + 0.1353×20 + 0.0498×30 + 1×40
       = 44.3835

最终输出 o = a/l = 44.3835/1.2034 ≈ 36.8806
```

### 再分两块算，中间不保存 4 个 softmax 权重

先处理第一块 `[1,3]` 和对应的 `V = [10,20]`：

```text
m₁ = 3
l₁ = e^(1−3) + e^(3−3)
   = 0.1353 + 1
   = 1.1353

a₁ = e^(1−3)×10 + e^(3−3)×20
   = 0.1353×10 + 1×20
   = 21.3534
```

第二块出现了更大的分数 5，所以新的基准从 3 改成 5。旧结果原来以 3 为基准，现在要乘 `e^(3−5) = 0.1353`，统一换成以 5 为基准：

```text
m₂ = 5

l₂ = l₁×e^(3−5) + e^(2−5) + e^(5−5)
   = 1.1353×0.1353 + 0.0498 + 1
   = 1.2034

a₂ = a₁×e^(3−5) + e^(2−5)×30 + e^(5−5)×40
   = 21.3534×0.1353 + 0.0498×30 + 1×40
   = 44.3835

最终输出 o = a₂/l₂ = 44.3835/1.2034 ≈ 36.8806 ✓
```

它和一次看全得到的 `36.8806` 对上了。更重要的是：每块的权重已经乘进 `V`，因此不必把完整概率矩阵 `P` 留给最后一步。

## 为什么“多算一点”反而更快？

GPU 的矩阵计算单元很强，但前提是数据及时送到。若计算单元算完一小步，就得等几百 MB 数据从 HBM 进出，再高的峰值算力也会闲着。这叫 **memory-bound**：速度受数据搬运限制，不是受乘加次数限制。

FlashAttention 提高了“每搬一个字节，顺手完成多少计算”。工程上把这个比例叫**算术强度**。它还会在反向传播时根据 `Q/K/V` 重算某些分数，看起来多算了一遍；但矩阵乘很适合 GPU，而保存和读回 `N × N` 中间矩阵更贵，所以实际用时反而更短。

一句话：**它用 GPU 富余的计算，换掉更稀缺的 HBM 带宽和显存容量。**

## 它到底有没有改变注意力结果？

没有改变注意力的数学定义：每个 query 仍然和所有 key 做点积，也仍然计算完整 softmax；它不是稀疏化，也没有删 token 对。因此论文称它为 **exact attention**。

不过，“精确”不等于浮点数逐 bit 必然相同。分块后加法顺序变了，有限精度下可能出现很小的舍入差异。准确说法是：**算法没有引入近似，数学结果相同；具体实现未必与另一种 kernel 排布 bit-for-bit 一致。**

## 跟 sparse attention 的区别

- **[[sparse-attention]]**：跳过一部分 token 对，改了“算哪些关系”，通常是近似换算力。
- **FlashAttention**：一个 token 对都不跳，改了“计算顺序和数据怎么搬”，主要省 IO 和中间显存。
- 两者并不冲突：稀疏模式若有合适的 kernel，也能再套 IO-aware 的分块办法。

## 代码出处 / 来源

- Dao et al., [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135), NeurIPS 2022。
- [Dao-AILab/flash-attention 官方实现](https://github.com/Dao-AILab/flash-attention)。

## 链接

- [[self-attention]] · 被重新排布的原始计算：`softmax(QKᵀ)V`
- [[softmax]] · 在线 softmax 仍是“减最大值防溢出”，只是把一次看全改成边看边更新
- [[ai-memory-hierarchy]] · 为什么片上 SRAM 快但小、HBM 大却更远
- [[gpu-kernels-and-compilation]] · kernel 融合为什么能少一次中间结果交接
- [[sparse-attention]] · 对照：改计算范围，还是只改 IO 调度
- [[kv-cache]] · 长上下文推理里另一块重要的显存与带宽开销
