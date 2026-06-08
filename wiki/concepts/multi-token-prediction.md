---
name: multi-token-prediction
type: concept
sources: [minimind-o]
updated: 2026-06-08
---

# Multi-Token Prediction · MTP · 一步预测好几个

## 一句话
**每个解码步一次吐多层 code**，而不是一次一个 —— minimind-o 的 Talker 用它配合"延迟错位"把 8 层 Mimi codebook 摊成阶梯并行，序列不膨胀，又不丢残差依赖。

## 直觉 · RVQ 的 8 层不该排成 8 倍长队

[[rvq-codec]] 把每帧音频量化成**多层 code**（Mimi 是 8 层：第 1 层粗轮廓，往后逐层补残差细节）。一秒 12.5 帧、每帧 8 层 → 如果像普通自回归那样一个 code 一个 code 地吐，序列瞬间变 8 倍长，又慢又难训。

MTP 的办法：**每个解码步一次预测多层**（模型在每个位置有多个输出头 / 一个能出多路的结构）。这样序列长度回到"每步一列"，不膨胀。但有个坑：RVQ 的层是**残差依赖**的（第 k 层量化前 k−1 层的残差），直接同帧 8 层一起吐会丢掉这个依赖——所以真正用起来要配**延迟错位**（下一节）。

## 关键 · 阶梯并行（delay pattern）· 依赖斜着保住

要点先说清：**纯"同帧 8 层一起吐"会丢残差依赖**，那是裸近似。真正用的是**延迟错位**——把第 k 层在时间轴上往后挪 k−1 帧，于是每个解码步吐的是一条**对角线**（不同帧的不同层）。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 360" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="mtp-d" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4a6b3a"/></marker></defs>
  <text x="360" y="24" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#3a3128">每层延迟错位 → 解码步吐对角线（绿=帧 f0 的 8 层）</text>
  <!-- 行标签 -->
  <g font-size="9" fill="#7a6f5d" text-anchor="end">
    <text x="74" y="67">cb1·延0</text><text x="74" y="97">cb2·延1</text><text x="74" y="127">cb3·延2</text><text x="74" y="157">cb4·延3</text>
    <text x="74" y="187">cb5·延4</text><text x="74" y="217">cb6·延5</text><text x="74" y="247">cb7·延6</text><text x="74" y="277">cb8·延7</text>
  </g>
  <!-- 格子 -->
  <g class="reveal d1" font-size="9" text-anchor="middle">
    <!-- r0 -->
    <rect x="90" y="50" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="110" y="67" fill="#fff">f0</text>
    <rect x="134" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="154" y="67" fill="#3a3128">f1</text>
    <rect x="178" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="198" y="67" fill="#3a3128">f2</text>
    <rect x="222" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="242" y="67" fill="#3a3128">f3</text>
    <rect x="266" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="286" y="67" fill="#3a3128">f4</text>
    <rect x="310" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="330" y="67" fill="#3a3128">f5</text>
    <rect x="354" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="67" fill="#3a3128">f6</text>
    <rect x="398" y="50" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="67" fill="#3a3128">f7</text>
    <!-- r1 -->
    <rect x="134" y="80" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="154" y="97" fill="#fff">f0</text>
    <rect x="178" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="198" y="97" fill="#3a3128">f1</text>
    <rect x="222" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="242" y="97" fill="#3a3128">f2</text>
    <rect x="266" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="286" y="97" fill="#3a3128">f3</text>
    <rect x="310" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="330" y="97" fill="#3a3128">f4</text>
    <rect x="354" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="97" fill="#3a3128">f5</text>
    <rect x="398" y="80" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="97" fill="#3a3128">f6</text>
    <!-- r2 -->
    <rect x="178" y="110" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="198" y="127" fill="#fff">f0</text>
    <rect x="222" y="110" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="242" y="127" fill="#3a3128">f1</text>
    <rect x="266" y="110" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="286" y="127" fill="#3a3128">f2</text>
    <rect x="310" y="110" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="330" y="127" fill="#3a3128">f3</text>
    <rect x="354" y="110" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="127" fill="#3a3128">f4</text>
    <rect x="398" y="110" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="127" fill="#3a3128">f5</text>
    <!-- r3 -->
    <rect x="222" y="140" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="242" y="157" fill="#fff">f0</text>
    <rect x="266" y="140" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="286" y="157" fill="#3a3128">f1</text>
    <rect x="310" y="140" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="330" y="157" fill="#3a3128">f2</text>
    <rect x="354" y="140" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="157" fill="#3a3128">f3</text>
    <rect x="398" y="140" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="157" fill="#3a3128">f4</text>
    <!-- r4 -->
    <rect x="266" y="170" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="286" y="187" fill="#fff">f0</text>
    <rect x="310" y="170" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="330" y="187" fill="#3a3128">f1</text>
    <rect x="354" y="170" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="187" fill="#3a3128">f2</text>
    <rect x="398" y="170" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="187" fill="#3a3128">f3</text>
    <!-- r5 -->
    <rect x="310" y="200" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="330" y="217" fill="#fff">f0</text>
    <rect x="354" y="200" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="374" y="217" fill="#3a3128">f1</text>
    <rect x="398" y="200" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="217" fill="#3a3128">f2</text>
    <!-- r6 -->
    <rect x="354" y="230" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="374" y="247" fill="#fff">f0</text>
    <rect x="398" y="230" width="40" height="26" rx="2" fill="#eaeef3" stroke="#9fb3c8"/><text x="418" y="247" fill="#3a3128">f1</text>
    <!-- r7 -->
    <rect x="398" y="260" width="40" height="26" rx="2" fill="#4a6b3a"/><text x="418" y="277" fill="#fff">f0</text>
  </g>
  <!-- 对角线箭头：帧 f0 的链 -->
  <path class="reveal d2" d="M108,64 L416,272" fill="none" stroke="#4a6b3a" stroke-width="1.6" marker-end="url(#mtp-d)"/>
  <text class="reveal d2" x="84" y="332" font-size="9.5" fill="#4a6b3a">↘ 帧 f0 的残差链 c1→c8：沿对角线串，下层落点时上层早已出 → 依赖完整保住</text>
  <!-- t7 列高亮 -->
  <rect class="reveal d3" x="395" y="47" width="46" height="242" fill="none" stroke="#b8841c" stroke-width="2" stroke-dasharray="4 3"/>
  <g class="reveal d3" font-size="9" fill="#9a6a10">
    <text x="455" y="120">步 t7 这一列：</text>
    <text x="455" y="136">并行吐 8 个码，</text>
    <text x="455" y="152">但是 8 个不同帧</text>
    <text x="455" y="168">(f7..f0)，互相</text>
    <text x="455" y="184">无残差依赖 → 可并行</text>
  </g>
  <!-- 底部解码步轴 -->
  <g class="reveal d1" font-size="8.5" fill="#7a6f5d" text-anchor="middle">
    <text x="110" y="302">t0</text><text x="154" y="302">t1</text><text x="198" y="302">t2</text><text x="242" y="302">t3</text><text x="286" y="302">t4</text><text x="330" y="302">t5</text><text x="374" y="302">t6</text><text x="418" y="302">t7</text>
  </g>
</svg>
</figure>

看**绿色对角线**（帧 f0 的 8 层）：`cb1[f0]` 在 t0 出、`cb2[f0]` 在 t1 出……`cb8[f0]` 在 t7 出。等到 t7 要出 `cb8[f0]` 时，**同帧的 cb1..cb7[f0] 早在前 7 步定下、在上下文里了** → 残差链 `c_k 看 c_<k` 一点没丢，只是从"帧内竖串"改成"沿解码步斜串"。而**同一步并行的那一列**（黄框 t7：f7..f0）是 8 个**不同帧**的码，本就无依赖，所以能并行。

## 三档对比 · 它在中间

| 方案 | 帧内 8 层怎么解 | 每帧步数 | 帧内残差依赖 |
|---|---|---|---|
| 裸并行 | 同帧 8 层都 condition 在一个 h 上一起吐 | 1 | **丢了（近似）** |
| **delay/阶梯（minimind-o）** | 错成对角，链沿解码步走 | ~1 列 | **完整保留** |
| fish 串行快 AR | 帧内嵌套 8 个串行小步 | 8 | 完整保留 |

阶梯是 fish"帧内 8 串行小步（稳但慢）"和"裸并行（快但丢依赖）"之间的折中：**用空间错位换时间并行，不牺牲因果**。它跟 fish 的真正差距不在"吃没吃依赖"，而在 fish 帧内多绕 8 个串行小步更稳、阶梯一步一列更流式友好（质量差更多来自模型大小和一次 forward 提交多帧的 exposure）。详见 [[dual-ar]] 的串行快 AR。

## 参数 · 共享主体 + 轻量 codebook adapter（其实就是每层一个 LoRA）

给 8 层各配一整套 embedding + 输出头，参数会爆，0.1B 装不下。minimind-o 的做法是 **LoRA 式的低秩增量**：一份全尺寸**共享主体**，每层只挂一个**低秩（rank=256）adapter** 做修正。而且**输入侧（embedding）和输出侧（head）对称地都这么干**。

**输出头 `TalkerHead`**（出 8 层 logits，`model/model_omni.py`）：

```python
self.base = nn.Linear(768, vocab, bias=False)                 # 共享主体：一份全尺寸
self.adapters = [Linear(768,256)→GELU→Linear(256,vocab)       # 每层一个低秩 adapter
                 for _ in range(8)]
def forward(self, x):
    base_out = self.base(x)                                   # 共享 logits 只算一次
    return [base_out + adapter(x) for adapter in self.adapters]  # 8 层 = 共享 + 各自低秩增量
```

最后一行就是 LoRA 的式子 `W·x + (B·A)·x`：8 层共用主体 `W`，每层只学一个瘦 `768→256→vocab` 的增量。模型在赌 **8 层的"hidden→码"映射大体相同、差异是低秩的**。输入侧 `TalkerEmbedding` 对称：每层"共享表 + 低秩 adapter"查嵌入，再**对 8 层求平均**塌成一帧一个向量喂回自回归。

为什么省 + 为什么稳：

| | 给每层配整套 | 共享 base + LoRA |
|---|---|---|
| 主体 | 8 ×（768×vocab） | **1 ×（768×vocab）** |
| 每层额外 | — | 768×256 + 256×vocab（被 rank 卡瘦） |

主体只留一份省参数；每层增量被 rank=256 卡过，**强制各层只能在共享主体上做低秩偏移**，既不跑偏又自带正则。这是 0.1B 里塞下 8 路 codebook 的关键。（Talker 的输入还叠了 Thinker 中间层条件：`embed_proj(bridge)×text_scale + codec_proj(audio_emb)×audio_scale`，scale 是可学标量。）

## 跟流式的关系 · 边想边补

阶梯天然适合流式：每个解码步吐一列、Mimi 增量还原 24kHz 波形，不用等整句说完就能播。Thinker 一边吐文本，Talker 一边沿对角线补 codes，配 [[vad]] 还能 barge-in 打断。

## 一个区分 · 跟"投机解码的 MTP"同名不同用
DeepSeek 等用 MTP 指"训练时多预测几个未来 token 当辅助目标 / 加速"。这里 minimind-o 的 MTP 是**同一帧的多层 codebook 并行预测**——同名，但解决的是 RVQ 多层的序列膨胀问题，别混。

## 代码出处
- minimind-o `model/model_omni.py:57-76` —— `TalkerHead`（共享 base Linear + 8 个低秩 adapter，输出 list of 8 logits）/ `TalkerEmbedding`（共享 base Embedding + 8 个低秩 adapter，对 8 层求平均）
- Talker 输入融合在 `model_omni.py:301`（bridge 条件 + audio embedding 按可学 scale 相加）
- 思路谱系：RVQ 多码本的并行/延迟预测（fish-speech 的 dual-AR、MusicGen 的 delay pattern 同源问题）

## 链接
- [[rvq-codec]] · 多层 codebook 就是 MTP 要并行预测的对象
- [[thinker-talker]] · Talker 用 MTP 渲染 codes
- [[dual-ar]] · fish-speech 处理多码本的另一种结构
- [[minimind-o]] · 用 MTP 的 0.1B Omni
