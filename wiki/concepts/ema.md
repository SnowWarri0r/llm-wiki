---
name: ema
type: concept
sources: [dino, krea-2, senseflow, drift-ar]
updated: 2026-07-24
---

# EMA · 指数滑动平均 · 一行就够

## 一句话
一行更新规则 `新 = m·旧 + (1−m)·新值`，一个数原地滚 —— 把抖动磨平、追出一条更稳的"趋势线"，不用存任何历史。

## 直觉 · 一个低通滤波器

EMA 就是个**惯性 / 拖影 / 低通滤波器**：每来一个新值，**保留 m 份旧平均、掺进 (1−m) 份新值**。`m`（动量）接近 1（0.9 / 0.99 / 0.999）。新值只能轻轻推动平均一点点，所以瞬时的抖动被磨平，留下平滑的趋势。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 260" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <g class="reveal d1" stroke="#3a3128" stroke-width="1"><line x1="60" y1="40" x2="60" y2="220"/><line x1="60" y1="220" x2="690" y2="220"/></g>
  <text class="reveal d1" x="690" y="238" text-anchor="end" font-size="9" fill="#7a6f5d">步数 →</text>
  <!-- 原始抖动信号 -->
  <polyline class="draw d2" pathLength="1000" points="70,200 120,150 170,190 220,120 270,160 320,100 370,140 420,90 470,120 520,80 570,110 620,85 670,95" fill="none" stroke="#9fb3c8" stroke-width="1.4"/>
  <!-- EMA 平滑滞后 -->
  <polyline class="draw d3" pathLength="1000" points="70,200 120,180 170,184 220,158 270,159 320,135 370,137 420,118 470,119 520,103 570,106 620,98 670,97" fill="none" stroke="#1f3a5f" stroke-width="2.6"/>
  <g class="reveal d4" font-size="10">
    <rect x="500" y="46" width="16" height="3" fill="#9fb3c8"/><text x="522" y="51" fill="#7a6f5d">原始（抖）</text>
    <rect x="500" y="64" width="16" height="4" fill="#1f3a5f"/><text x="522" y="70" fill="#1f3a5f" font-weight="700">EMA（平滑·滞后）</text>
  </g>
  <text class="reveal d4" x="380" y="248" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#3a3128">EMA 跟着原始走，但磨平抖动、慢半拍</text>
</svg>
</figure>

好处：**不用存历史**，一个数就够（对比"简单滑动平均"要存最近 N 个值再求平均）。

## 怎么做的 · 为什么叫"指数"

把递归展开：

```
avg ← m·avg + (1−m)·x_new
```

k 步之前的那个值，在当前平均里的权重是 **(1−m)·m^k** —— 随 k **指数衰减**。近的值占大头、远的平滑淡出。

**m 是"记忆长度"旋钮，有效窗口 ≈ 1/(1−m)：**
- m=0.9 → 记最近 ~10 步
- m=0.99 → ~100 步
- m=0.999 → ~1000 步

数值感受一下（m=0.9，新值恒为 10，从 0 起）：

```
0 → 1 → 1.9 → 2.71 → 3.44 → … → 慢慢爬向 10
```

m 越接近 1，爬得越慢、越稳。

## 哪里都在用
- **[[dino]]**：teacher 权重 = EMA(student 权重)（momentum encoder，追一个更稳的自己）；centering 的 c = EMA(teacher 输出均值)。
- **[[senseflow]] 的 IDA**：公式同样是 `φ←λφ+(1−λ)θ`，但不是模型追自己的历史。`φ` 属于 fake 网络，`θ` 属于刚更新的生成器；这次插值负责把学生在稀疏 anchor 上的新变化软传给 fake 网络，fake 随后仍用自己的稠密时间步去噪损失继续训练。
- **[[batchnorm]]**：推理用的 running mean / var 是训练时的 EMA。
- **Adam 优化器**：一阶动量 m_t、二阶 v_t **都是梯度的 EMA**（见 [[adam]]）。
- **EMA 权重**：把训练后期的模型权重做 EMA 当最终 checkpoint，往往更稳更好。
- **[[drift-ar]] 的推测解码阈值**：目标模型每次验证都会产生新的注意力熵，先用 `0.9·旧平均+0.1·新熵` 平滑，再乘 `γ=0.8` 作为动态停止线，避免某一块图像的瞬时熵把策略带偏。

## 代码出处
- 一行：`avg = m * avg + (1 - m) * x`（或 `avg.mul_(m).add_(x, alpha=1-m)`）
- PyTorch `torch.optim.swa_utils.AveragedModel`（EMA 权重）、各框架 BatchNorm/Adam 内部

## 链接
- [[dino]] · teacher 和 center 都用 EMA
- [[senseflow]] · IDA 形式像 EMA，但混合的是两个职责不同、结构相同的网络
- [[adam]] · 动量和方差都是梯度的 EMA
- [[batchnorm]] · running 统计量是 EMA
- [[drift-ar]] · 用目标注意力熵的 EMA 调整草稿停止阈值
