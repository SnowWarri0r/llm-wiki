---
name: differentiable-thought-representation
type: concept
sources: [relat]
updated: 2026-06-28
---

# 可微思考表示 · 别硬选一个 token，取嵌入的加权混合

## 一句话
要让"选哪个 token"这一步能反传梯度，就不硬选（argmax 不可导），而是对词表 logits 做 softmax 得分布 α，用它加权各 token 的嵌入算一个**期望嵌入**——既留在嵌入空间里，又对下游损失可微。

## 直觉 · argmax 把梯度切断了
推理时"下一个 token 选谁"是个**硬选择**（argmax）。硬选择是**台阶函数、不可导**：你没法对"选了 cat 还是 dog"求梯度，于是任何想**反传穿过这一步**的优化（比如 [[relat]] 的重建损失要更新前面的参数）都断在这里。

解法是**连续松弛**：与其挑一个 token，不如**按概率把所有 token 的嵌入混起来**。概率从 logits 经 [[softmax]] 来，混合是加权平均——整条路就可导了。

下图用两个 token 的情形看（横轴 `z = logit_cat − logit_dog`，纵轴 = 给 cat 的权重）：硬选是台阶、软化是光滑 S 形。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 660 312" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:'JetBrains Mono',monospace;">
  <!-- axes: x=z (y=258), y=value (x=80); v=0→248 v=1→78 ; x(z)=340+62z -->
  <line class="reveal d1" x1="80" y1="60" x2="80" y2="258" stroke="#9fb3c8" stroke-width="1"/>
  <line class="reveal d1" x1="80" y1="258" x2="600" y2="258" stroke="#9fb3c8" stroke-width="1.1"/>
  <g class="reveal d1" font-size="9" fill="#5b6b7d" text-anchor="end">
    <text x="74" y="81">1</text><text x="74" y="166">0.5</text><text x="74" y="251">0</text>
  </g>
  <g class="reveal d1" font-size="9" fill="#5b6b7d" text-anchor="middle">
    <text x="92" y="272">-4</text><text x="340" y="272">0</text><text x="588" y="272">4</text>
  </g>
  <text class="reveal d1" x="612" y="261" text-anchor="start" font-size="9" fill="#5b6b7d">z</text>
  <!-- 软化 softmax: 光滑 sigmoid -->
  <polyline class="reveal d3" points="92,244.9 154,240.0 216,227.8 278,202.3 340,163.0 402,123.7 464,98.2 526,86.0 588,81.1" fill="none" stroke="#3d4a9e" stroke-width="2.4"/>
  <!-- 硬选 argmax: 台阶 + 跳变 -->
  <polyline class="reveal d2" points="92,248 340,248" fill="none" stroke="#9b2c2c" stroke-width="2.2"/>
  <polyline class="reveal d2" points="340,78 588,78" fill="none" stroke="#9b2c2c" stroke-width="2.2"/>
  <line class="reveal d2" x1="340" y1="248" x2="340" y2="78" stroke="#9b2c2c" stroke-width="1.4" stroke-dasharray="4 3"/>
  <circle class="reveal d2" cx="340" cy="248" r="3.4" fill="#eef2f7" stroke="#9b2c2c" stroke-width="1.4"/>
  <circle class="reveal d2" cx="340" cy="78" r="3.4" fill="#9b2c2c"/>
  <!-- legend top-left (empty zone) -->
  <g class="reveal d4">
    <rect x="96" y="66" width="232" height="46" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <line x1="108" y1="82" x2="132" y2="82" stroke="#9b2c2c" stroke-width="2.2"/><text x="138" y="85" font-size="9.5" fill="#3a3128" text-anchor="start">硬选 argmax · 台阶(跳变)</text>
    <line x1="108" y1="102" x2="132" y2="102" stroke="#3d4a9e" stroke-width="2.4"/><text x="138" y="105" font-size="9.5" fill="#3a3128" text-anchor="start">软化 softmax · 光滑 S 形</text>
  </g>
  <!-- captions below plot, color-coded, no crossing -->
  <text class="reveal d5" x="80" y="290" text-anchor="start" font-size="9.5" fill="#9b2c2c">argmax：z=0 跳变 → 连续都不是；两侧平 → 梯度=0 → 反传断</text>
  <text class="reveal d5" x="80" y="306" text-anchor="start" font-size="9.5" fill="#3d4a9e">softmax：处处光滑可导(可导⟹连续) → 梯度顺 z 反传</text>
</svg>
</figure>

**层级：可导 ⊊ 连续。** argmax 在 z=0 跳变（空心点=右极限取不到、实心点=跳到的值），连"连续"都不算；softmax 是光滑曲线、处处可导（可导自然连续）。中间还有"连续但不可导"一档，典型是 `|x|` 在 0 点的尖角——softmax 连这种尖角都没有。所以"连续松弛"这名字偏松：反传真正要的是**可导**，softmax 给的是**光滑**（比连续更强）。

## 怎么做的
```
某一步词表 logits  ℓ ∈ ℝ^V
1. 软化成分布:  α = softmax(ℓ / τ)      τ=温度
2. 期望嵌入:    ê = αᵀ W_emb            W_emb 是 token 嵌入表(V×d)
ê 是"各 token 嵌入按 α 加权的混合"，落在嵌入空间、且对 ℓ(进而对参数)可微
```
τ 小 → α 接近 one-hot（接近硬选）；τ 大 → 更平滑的混合。这跟 Gumbel-Softmax 是近亲：都用 softmax 松弛把离散采样变得可微。

## 数字例子 · 一步算到底
词表只有 3 个词，二维嵌入：`cat=[1,0]  dog=[0,1]  run=[1,1]`。某步 logits `ℓ=[2,1,0]`，τ=1：
```
softmax: e²,e¹,e⁰ = 7.389, 2.718, 1   和=11.107
  α = [0.665, 0.245, 0.090]            ← "cat" 最可能但没锁死
期望嵌入 ê = 0.665·[1,0] + 0.245·[0,1] + 0.090·[1,1]
           = [0.665+0.090, 0.245+0.090]
           = [0.755, 0.335]
```
✓ 自检：硬选会得到 `cat=[1,0]`、而且"选 cat"这步不可导；软混合得到 `ê=[0.755,0.335]`——**大部分是 cat、掺一点 dog/run**，是一个连续向量。关键是 α 由 logits 平滑算来，所以 `ê` 对 logits 可导，梯度能从下游(如 [[relat]] 的重建损失)一路传回去调参。代价：`ê` 不是任何真实 token 的嵌入，而是"介于之间"的混合（推理出最终答案时仍可硬解码，只有测试时优化阶段用软的）。

## 链接
- [[relat]] · 用它把潜在思考做成可微的，重建损失才能反传
- [[softmax]] · 软化 logits 成分布 α 的那一步
- [[reconstruction-as-fidelity]] · 下游那个要反传回来的损失
- [[cross-entropy]] · 重建损失的形式
