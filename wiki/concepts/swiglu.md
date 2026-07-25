---
name: swiglu
type: concept
sources: [dit, krea-2, drifting-models]
updated: 2026-07-22
---

# SwiGLU · 带门的 FFN

## 一句话
把 transformer 的 FFN 改成"一条算内容、一条当门，两条逐元素相乘"——让网络自己决定哪些特征放过去。

## 直觉
普通 FFN：`x → 升维(d→4d) → 激活(GELU) → 降维(4d→d)`，一条路、一个激活函数。

SwiGLU 加了个**门**：开两条并行投影，一条当"内容"，另一条过一个平滑激活(Swish)当"开关"，两条**逐元素相乘**——门接近 0 的位置内容被掐掉，门大的地方放过。直觉上比"算一遍激活一遍"多了一层**自己给自己开关**的能力，实测同算力下更强，所以 LLaMA、PaLM、现代 [[diffusion-transformer]] 家族(SD3/FLUX)都用它。

注意：**原版 [[dit]](2022) 用的是 GELU，不是 SwiGLU**——SwiGLU 是后来给 DiT 家族的现代化升级，别记串了。

## Swish 和 sigmoid 长啥样
- **sigmoid** `σ(z)=1/(1+e⁻ᶻ)`：一条 S 形曲线，把任意实数压进 **(0,1)**，过 (0, 0.5)，左趋 0 右趋 1。天然是个**软开关**（0=关、1=开），所以适合当"门"。
- **Swish** `z·σ(z)`：像**磨圆的 ReLU、负区还往下凹个小坑**。右边 z 大时 σ→1 故 ≈ z（跟 ReLU 重合）；左边 z 大负时趋 0；最低点约 z≈−1.3、值≈−0.28，再回到 0。比 ReLU 多了"平滑 + 负区留一点信息"。

<figure>
<svg viewBox="0 0 660 350" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:'JetBrains Mono',monospace;">
  <!-- axes cross at origin (z=0, v=0) = (330,285); x=330+60z, y=285-85v -->
  <line class="reveal d1" x1="330" y1="148" x2="330" y2="335" stroke="#bfb398" stroke-width="1.2"/>
  <polygon class="reveal d1" points="330,143 326,152 334,152" fill="#bfb398"/>
  <line class="reveal d1" x1="84" y1="285" x2="612" y2="285" stroke="#bfb398" stroke-width="1.2"/>
  <polygon class="reveal d1" points="617,285 609,281 609,289" fill="#bfb398"/>
  <text class="reveal d1" x="622" y="289" text-anchor="start" font-size="10" fill="#7a6f5d">z</text>
  <!-- y ticks (value axis, at z=0) -->
  <g class="reveal d1" font-size="9" fill="#7a6f5d" text-anchor="end">
    <text x="322" y="204">1</text><text x="322" y="246">0.5</text><text x="322" y="300">0</text>
  </g>
  <line class="reveal d1" x1="326" y1="200" x2="334" y2="200" stroke="#bfb398"/><line class="reveal d1" x1="326" y1="242.5" x2="334" y2="242.5" stroke="#bfb398"/>
  <!-- x ticks (negative left, positive right) -->
  <g class="reveal d1" font-size="9" fill="#7a6f5d" text-anchor="middle">
    <text x="150" y="303">-3</text><text x="210" y="303">-2</text><text x="450" y="303">2</text><text x="570" y="303">4</text>
  </g>
  <g class="reveal d1" stroke="#bfb398"><line x1="150" y1="281" x2="150" y2="289"/><line x1="210" y1="281" x2="210" y2="289"/><line x1="450" y1="281" x2="450" y2="289"/><line x1="570" y1="281" x2="570" y2="289"/></g>

  <!-- ReLU (对照, dashed): 0 for z<0, =z for z>0 -->
  <polyline class="reveal d2" points="90,285 330,285 426,149" fill="none" stroke="#7a6f5d" stroke-width="1.4" stroke-dasharray="5 4"/>
  <!-- sigmoid -->
  <polyline class="draw d3" pathLength="1000" points="90,283.5 150,281.0 210,274.9 270,262.1 300,252.9 330,242.5 360,232.1 390,222.9 420,215.5 450,210.1 480,206.5 510,204.0 540,202.5 570,201.5" fill="none" stroke="#1f3a5f" stroke-width="2.4"/>
  <!-- Swish: dips negative for z<0 (min -0.28 @ z=-1.28), 0 at z=0, then ≈z -->
  <polyline class="draw d4" pathLength="1000" points="90,291.1 150,297.1 180,301.1 210,305.3 240,308.3 253.3,308.7 270,307.9 300,301.1 330,285.0 360,258.6 390,222.9 420,180.8 441,149.1" fill="none" stroke="#9b2c2c" stroke-width="2.6"/>

  <!-- legend (top-left empty corner) -->
  <g class="reveal d5">
    <rect x="90" y="152" width="214" height="74" rx="4" fill="#faf4e1" stroke="#bfb398"/>
    <line x1="102" y1="170" x2="126" y2="170" stroke="#1f3a5f" stroke-width="2.4"/><text x="132" y="173.5" font-size="9.5" fill="#3a3128" text-anchor="start">sigmoid · 0→1 软开关</text>
    <line x1="102" y1="192" x2="126" y2="192" stroke="#9b2c2c" stroke-width="2.6"/><text x="132" y="195.5" font-size="9.5" fill="#3a3128" text-anchor="start">Swish=z·σ(z) · 平滑 ReLU+小坑</text>
    <line x1="102" y1="214" x2="126" y2="214" stroke="#7a6f5d" stroke-width="1.4" stroke-dasharray="5 4"/><text x="132" y="217.5" font-size="9.5" fill="#3a3128" text-anchor="start">ReLU(对照) · 负区死平 0</text>
  </g>

  <!-- markers + labels (all in empty space, no line crossing) -->
  <circle class="reveal d6" cx="330" cy="242.5" r="3.5" fill="#1f3a5f"/>
  <line class="reveal d6" x1="290" y1="242" x2="326" y2="242.5" stroke="#1f3a5f" stroke-width="0.8"/>
  <text class="reveal d6" x="286" y="245" text-anchor="end" font-size="9" fill="#1f3a5f">σ(0)=0.5</text>
  <circle class="reveal d6" cx="253.3" cy="308.7" r="3.5" fill="#9b2c2c"/><text class="reveal d6" x="250" y="328" text-anchor="middle" font-size="9" fill="#9b2c2c">Swish 最低≈−0.28 @ z≈−1.3（负 z）</text>
  <text class="reveal d6" x="468" y="268" text-anchor="middle" font-size="9.5" fill="#9b2c2c">Swish ≈ z（右边贴着 ReLU）</text>
  <text class="reveal d6" x="548" y="232" text-anchor="middle" font-size="9.5" fill="#1f3a5f">sigmoid 饱和到 1</text>
</svg>
</figure>

一句话对照：**sigmoid 是 0→1 的软开关（当门）；Swish = z × 这个软开关 = 右边像 z、左边趋 0、负区有个小凹坑的平滑 ReLU**。SwiGLU 的"门"用的就是 Swish 这种"软"地决定放过多少。

## 怎么做的
```
FFN_SwiGLU(x) = ( Swish(x·W_gate)  ⊙  x·W_up ) · W_down

Swish(z) = z · sigmoid(z)   (也叫 SiLU，一条平滑、负区不全为 0 的曲线)
⊙ = 逐元素相乘
```
三个矩阵(W_gate / W_up / W_down)而非两个，为保持参数量，中间维度从 4d 缩到约 2.67d(×2/3)。

## 数字例子
设某 token 算出两条投影：门 `g = x·W_gate = [2, -1]`，内容 `u = x·W_up = [3, 4]`。

**第一步 · 门过 Swish**(Swish(z)=z·σ(z))：
```
σ(2) ≈ 0.88 → Swish(2)  = 2·0.88  =  1.76
σ(-1)≈ 0.27 → Swish(-1) = -1·0.27 = -0.27
```

**第二步 · 门 ⊙ 内容**：
```
gated = [1.76, -0.27] ⊙ [3, 4] = [1.76·3, -0.27·4] = [5.28, -1.08]
```
再过 `W_down` 降维。✓ 自检：第二维门的输入是 −1(负)→ Swish 压到 −0.27(接近 0)→ 把内容 4 几乎掐灭(−1.08)；第一维门输入 2(正)→ 放大内容到 5.28。**门在挑哪些内容通过**，这是普通 GELU FFN(单路、无门)给不了的。

## 跟普通 FFN 的对比
| | 普通 FFN | SwiGLU |
|---|---|---|
| 投影矩阵 | 2 个 | 3 个(gate/up/down) |
| 激活 | GELU 单路 | Swish 当门 ⊙ 内容 |
| 中间维度 | 4d | ≈2.67d(补回参数量) |
| 谁用 | 原版 DiT、早期 Transformer | LLaMA / PaLM / SD3 / FLUX |

## 链接
- [[dit]] · DiT 家族的 FFN；原版用 GELU，现代换 SwiGLU
- [[diffusion-transformer]] · 现代 DiT 主干的 FFN 就是它
- [[normalization]] · 同属"transformer 块内部零件"
