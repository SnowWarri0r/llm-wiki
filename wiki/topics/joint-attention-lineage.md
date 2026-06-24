---
name: joint-attention-lineage
type: topic
sources: [stable-diffusion-3-5, flux-1, hidream-o1, cosmos-3]
updated: 2026-06-24
---

# Joint-Attention 谱系 · 从 cross-attention 到 MMDiT / Unified / MoT

## 一句话
多模态模型都从"独立文本编码器 + cross-attention"搬到了"一条序列 + 联合自注意力"；剩下的分歧只有两点——**权重分不分流、要不要因果**。

## 共同的大招：concat + 联合自注意力
早期文生图（早期 SD、DALL·E）是这样：文本走一个**独立编码器**，再用 [[cross-attention]] 把文本"注入"图像去噪。文本和图像始终是两套东西，隔着一道 cross-attention 说话。

[[mmdit]]、[[unified-transformer]]、Cosmos 3 的 [[mixture-of-transformers]]——**全都把不同模态的 token concat 进同一条序列，做一次联合自注意力**，让文本和图像在同一张注意力表里直接互看，不再隔 cross-attention。这是它们共同的"异曲"。

但"concat + 联合注意力"内部，还有两个**正交**的选择，决定了它们的"不同工"。

## 两个旋钮
**旋钮 A · 每个模态/流的权重，共享还是分流？**
- 共享一套 → Unified Transformer
- 每流一套（双流 / 双塔）→ MMDiT、MoT
- 为什么分流：文本和图像统计差异大，各给一套权重免得抢参数打架；代价是参数≈翻倍。

**旋钮 B · 注意力是全双向，还是混合（因果 + 双向）？**
- 全双向 → MMDiT
- 混合（文本/AR 走因果、生成走双向）→ Unified Transformer、MoT
- 为什么要混合：只有让文本 token 走**因果**，模型才能像 LLM 那样**自回归吐文本**（理解/推理）。纯生成模型不需要因果。

把这两个旋钮当坐标轴，四种架构正好落在 2×2 网格的四个角：

<figure>
<svg viewBox="0 0 660 470" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:'JetBrains Mono',monospace;">
  <!-- column headers (权重) -->
  <text class="reveal d1" x="250" y="40" text-anchor="middle" font-size="13" font-weight="700" fill="#1f3a5f">权重共享（一套）</text>
  <text class="reveal d1" x="520" y="40" text-anchor="middle" font-size="13" font-weight="700" fill="#1f3a5f">权重分流（双流/双塔）</text>
  <text class="reveal d1" x="385" y="22" text-anchor="middle" font-size="10" fill="#7a6f5d">旋钮 A · 权重 →</text>
  <!-- row labels (注意力) in left gutter -->
  <text class="reveal d2" x="60" y="146" text-anchor="middle" font-size="12" font-weight="700" fill="#4a6b3a">混合</text>
  <text class="reveal d2" x="60" y="162" text-anchor="middle" font-size="9" fill="#7a6f5d">理解+生成</text>
  <text class="reveal d2" x="60" y="320" text-anchor="middle" font-size="12" font-weight="700" fill="#b8841c">全双向</text>
  <text class="reveal d2" x="60" y="336" text-anchor="middle" font-size="9" fill="#7a6f5d">纯生成</text>
  <text class="reveal d2" x="22" y="240" text-anchor="middle" font-size="10" fill="#7a6f5d" transform="rotate(-90 22 240)">旋钮 B · 注意力 ↑</text>

  <!-- TL: 共享 + 混合 = Unified Transformer -->
  <rect class="reveal d3" x="120" y="70" width="252" height="150" rx="6" fill="#d8e6ce" stroke="#4a6b3a" stroke-width="1.4"/>
  <text class="reveal d3" x="246" y="116" text-anchor="middle" font-size="15" font-weight="700" fill="#181410">Unified Transformer</text>
  <text class="reveal d3" x="246" y="142" text-anchor="middle" font-size="10" fill="#3a3128">一套权重 · 混合注意力</text>
  <text class="reveal d3" x="246" y="162" text-anchor="middle" font-size="10" fill="#3a3128">文本因果 + 生成双向</text>
  <text class="reveal d3" x="246" y="190" text-anchor="middle" font-size="9.5" fill="#4a6b3a">理解 + 生成 · 一套权重最省</text>

  <!-- TR: 分流 + 混合 = MoT -->
  <rect class="reveal d4" x="388" y="70" width="252" height="150" rx="6" fill="#c8d4e2" stroke="#1f3a5f" stroke-width="1.6"/>
  <text class="reveal d4" x="514" y="110" text-anchor="middle" font-size="15" font-weight="700" fill="#181410">MoT</text>
  <text class="reveal d4" x="514" y="128" text-anchor="middle" font-size="10" fill="#7a6f5d">Cosmos 3</text>
  <text class="reveal d4" x="514" y="150" text-anchor="middle" font-size="10" fill="#3a3128">双塔分权重 · 混合注意力</text>
  <text class="reveal d4" x="514" y="170" text-anchor="middle" font-size="10" fill="#3a3128">AR 因果 + 扩散双向</text>
  <text class="reveal d4" x="514" y="196" text-anchor="middle" font-size="9.5" fill="#1f3a5f">理解 + 生成 + 动作</text>

  <!-- BL: 共享 + 全双向 = 单流 DiT -->
  <rect class="reveal d5" x="120" y="245" width="252" height="150" rx="6" fill="#f0e0a8" stroke="#b8841c" stroke-width="1.4"/>
  <text class="reveal d5" x="246" y="291" text-anchor="middle" font-size="15" font-weight="700" fill="#181410">单流 DiT</text>
  <text class="reveal d5" x="246" y="317" text-anchor="middle" font-size="10" fill="#3a3128">一套权重 · 全双向</text>
  <text class="reveal d5" x="246" y="337" text-anchor="middle" font-size="10" fill="#3a3128">文图共享、都双向去噪</text>
  <text class="reveal d5" x="246" y="365" text-anchor="middle" font-size="9.5" fill="#b8841c">纯生成（如 FLUX 后段单流块）</text>

  <!-- BR: 分流 + 全双向 = MMDiT -->
  <rect class="reveal d6" x="388" y="245" width="252" height="150" rx="6" fill="#f0e0a8" stroke="#b8841c" stroke-width="1.6"/>
  <text class="reveal d6" x="514" y="291" text-anchor="middle" font-size="15" font-weight="700" fill="#181410">MMDiT</text>
  <text class="reveal d6" x="514" y="309" text-anchor="middle" font-size="10" fill="#7a6f5d">SD3.5 / FLUX 前段</text>
  <text class="reveal d6" x="514" y="331" text-anchor="middle" font-size="10" fill="#3a3128">双流分权重 · 全双向</text>
  <text class="reveal d6" x="514" y="351" text-anchor="middle" font-size="10" fill="#3a3128">文本仅当条件</text>
  <text class="reveal d6" x="514" y="378" text-anchor="middle" font-size="9.5" fill="#b8841c">纯生成 · 不会生成文本</text>

  <!-- bottom note -->
  <text class="reveal d6" x="380" y="430" text-anchor="middle" font-size="10" fill="#7a6f5d">整张网格都活在"concat + 联合自注意力"里 · 它替代的是网格外的老办法：独立文本编码器 + cross-attention</text>
</svg>
</figure>

## 对照表
| | concat 一条序列 | 每模态权重 | 注意力 | 能干啥 |
|---|---|---|---|---|
| 老式（cross-attn） | 否（文本单独编码器） | — | — | 只生成（文本仅当条件） |
| **MMDiT** | 是 | 分流（双流） | 全双向 | 只生成（**不能生成文本**） |
| **单流 DiT** | 是 | 共享 | 全双向 | 只生成 |
| **Unified Transformer** | 是 | 共享 | 混合 | 理解 + 生成 |
| **MoT（Cosmos 3）** | 是 | 分流（双塔） | 混合 | 理解 + 生成 + 动作 |

## 关键的"不同工"
MMDiT 和 Unified Transformer 最实质的区别，是那个**混合注意力**带来的能力差：

- **MMDiT 全双向 = 本质还是个纯生成（扩散）模型**。文本 token 虽然进了同一条序列、也参与联合注意力，但它**只是条件**——MMDiT **不会自回归生成文本**，你没法让它说话/推理。文本流有自己的权重，只是为了被图像 token 更好地读取。
- **Unified Transformer 的混合注意力**（文本因果 + 生成双向）才让一个模型**既能像 LLM 因果吐文本（理解），又能像 DiT 双向去噪（生成）**。这是 MMDiT 给不了的。
- **MoT** = MMDiT 的"双流分权重" + Unified 的"混合注意力" 合一，再加动作模态。

## 一句话带走
**大家都从"独立编码器 + cross-attention"搬到了"一条序列 + 联合自注意力"；剩下的分歧就两点——权重分不分流、要不要因果（= 要不要顺带会生成文本）。** MMDiT 选"分流 + 全双向"，强在画图但不会说话；Unified / MoT 选"混合注意力"，所以理解生成一把抓。

## 链接
- [[mmdit]] · 分流 + 全双向：SD3.5 / FLUX 的文图双流联合注意力
- [[unified-transformer]] · 共享 + 混合：一个 transformer 同时理解+生成
- [[mixture-of-transformers]] · 分流 + 混合：Cosmos 3 的双塔
- [[cross-attention]] · 网格外的老办法，被联合自注意力取代
- [[diffusion-transformer]] · 生成那一侧的共同底座（DiT）
- [[stable-diffusion-3-5]] / [[flux-1]] / [[cosmos-3]] · 各自的落地 paper
