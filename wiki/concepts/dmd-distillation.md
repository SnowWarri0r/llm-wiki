---
name: dmd-distillation
type: concept
sources: [qwen-image-2, mrt]
updated: 2026-06-15
---

# DMD 蒸馏 · NFE · 把 40 步压成 4 步

## 一句话
把多步扩散老师蒸成少步学生，目标不是抄老师的轨迹，而是让学生的**出图分布**匹配老师的分布；NFE（跑几次网络）从几十降到几步 → 近实时生成。

## 直觉 · NFE 是什么 + 为什么不抄轨迹

**NFE（Number of Function Evaluations）** = 生成一张图**跑几次网络前向**。扩散采样要迭代去噪 N 次 = N NFE。40 步扩散 = 40 NFE = 40 次前向 = 慢；**4-NFE = 只跑 4 次 ≈ 快 10 倍**。（接 [[ode-sde]] 的"采样步数"。）

**DMD（Distribution Matching Distillation，分布匹配蒸馏）**：老师 = 40 步扩散（慢、好），学生 = 4 步生成器（快）。一个 4 步学生**走不了**老师那 40 步的精细路径，所以 DMD **不要求逐样本抄轨迹**，只要求"**学生画出来的一沓图，整体看跟老师那沓一样好、一样多样**"——即两者**分布**对上。

> 类比：不让学生一笔一画临摹老师那 40 步，只要求"你交上来的一摞作品，整体水准和多样性跟老师那摞一样"。

## 怎么做的 · 两个 score 之差推学生

DMD 用**两个 score（分布密度上升方向）之差**当更新方向推学生：

```
update ∝  teacher_score(x)  −  fake_score(x)
          ↑指向真实数据分布 p   ↑指向学生当前分布 q
```

- **teacher_score**：来自冻结的扩散老师，指向"真实数据该往哪"。
- **fake_score**：一个**额外训练的模型**（[[qwen-image-2]] 里那个"辅助 fake-score 模型"，用 [[flow-matching]] 训），实时拟合**学生当前**的输出分布。
- 两者相减 = "**吸向老师分布 − 斥离自己当前分布**" → 把学生分布 q 推向老师分布 p。本质是最小化两者的 KL（[[closed-form-kl]] / [[markov-chain]]）。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 260" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="dmd-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#7a6f5d"/></marker>
    <marker id="dmd-o" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#bf5a1e"/></marker>
  </defs>
  <!-- 上：NFE 对比 -->
  <text class="reveal d1" x="60" y="38" font-size="10" font-weight="700" fill="#1f3a5f">推理步数（NFE）</text>
  <g class="reveal d1" font-family="JetBrains Mono,monospace" font-size="9" text-anchor="middle">
    <rect x="60" y="50" width="56" height="26" rx="3" fill="#faf4e1" stroke="#7a6f5d"/><text x="88" y="67" fill="#3a3128">噪声</text>
    <rect x="470" y="50" width="56" height="26" rx="3" fill="#c8d4e2" stroke="#1f3a5f"/><text x="498" y="67" fill="#1f3a5f">图(老师)</text>
  </g>
  <line class="reveal d2" x1="116" y1="63" x2="466" y2="63" stroke="#9fb3c8" stroke-width="1.3" stroke-dasharray="5 4" marker-end="url(#dmd-h)"/>
  <g class="reveal d2" fill="#9fb3c8"><circle cx="180" cy="63" r="2.5"/><circle cx="240" cy="63" r="2.5"/><circle cx="300" cy="63" r="2.5"/><circle cx="360" cy="63" r="2.5"/><circle cx="420" cy="63" r="2.5"/></g>
  <text class="reveal d2" x="290" y="46" text-anchor="middle" font-size="8.5" font-weight="700" fill="#9b2c2c">老师 ~40 NFE（慢）</text>
  <g class="reveal d3" font-family="JetBrains Mono,monospace" font-size="9" text-anchor="middle">
    <rect x="60" y="92" width="56" height="26" rx="3" fill="#faf4e1" stroke="#bf5a1e"/><text x="88" y="109" fill="#8a3f12">噪声</text>
    <rect x="250" y="92" width="64" height="26" rx="3" fill="#f2dcc2" stroke="#bf5a1e"/><text x="282" y="109" fill="#8a3f12">图(学生)</text>
    <line x1="116" y1="105" x2="246" y2="105" stroke="#bf5a1e" stroke-width="2" marker-end="url(#dmd-o)"/>
    <text x="181" y="98" text-anchor="middle" font-size="8.5" font-weight="700" fill="#bf5a1e">4 NFE（快 ~10×）</text>
  </g>
  <line x1="40" y1="138" x2="680" y2="138" class="reveal d3" stroke="#bfb398" stroke-width="1" stroke-dasharray="4 4"/>
  <!-- 下：分布匹配 -->
  <text class="reveal d4" x="60" y="162" font-size="10" font-weight="700" fill="#bf5a1e">怎么蒸：让学生分布 q 追上老师分布 p</text>
  <g class="reveal d4" fill="#cce5e1" stroke="#1a6a64"><ellipse cx="540" cy="210" rx="70" ry="42" opacity="0.6"/></g>
  <text class="reveal d4" x="540" y="214" text-anchor="middle" font-size="10" font-weight="700" fill="#0f4a45">老师分布 p</text>
  <g class="reveal d5" fill="#f2dcc2" stroke="#bf5a1e"><ellipse cx="210" cy="210" rx="56" ry="34" opacity="0.7"/></g>
  <text class="reveal d5" x="210" y="214" text-anchor="middle" font-size="10" font-weight="700" fill="#8a3f12">学生分布 q</text>
  <text class="reveal d6" x="368" y="184" text-anchor="middle" font-size="9" font-weight="700" fill="#bf5a1e">teacher_score(吸向 p) − fake_score(斥离 q)</text>
  <line class="reveal d6" x1="272" y1="210" x2="462" y2="210" stroke="#bf5a1e" stroke-width="2.6" marker-end="url(#dmd-o)"/>
  <text class="reveal d6" x="368" y="240" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11" font-weight="700" fill="#3a3128">吸向老师、斥离自己 → q 追上 p（眼熟吗？=Drifting）</text>
</svg>
</figure>

**眼熟吗**：这跟 [[drifting-models]] 的"**吸引真数据 − 排斥自己**"几乎是同一个套路——DMD 就是"吸向老师分布、斥离自己当前分布"；也跟 [[diffusion-opd]] 的分布匹配一条线。

## 代码出处
- 原始：Yin et al. "One-step Diffusion with Distribution Matching Distillation"（DMD）
- [[qwen-image-2]]（40 步→4-NFE）、[[mrt]]（50 步→8 步、6× 提速）都用它做少步化

## 链接
- [[ode-sde]] · NFE = 采样步数；少步快采的根
- [[drifting-models]] · 吸引-排斥几乎同构（一步生成）
- [[diffusion-opd]] · 同分布匹配蒸馏线
- [[closed-form-kl]] · 分布匹配本质是最小化 KL
- [[qwen-image-2]] · [[mrt]] · 用它把多步压成少步
