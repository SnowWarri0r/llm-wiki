---
name: ai-memory-hierarchy
type: concept
sources: []
updated: 2026-06-16
---

# AI 服务器内存层级 · HBM / LPDDR5X / DDR5 / CXL / 光互连 · 快但小↔慢但大

## 一句话
AI 机架里的内存不是一种东西，而是一条**"越快越贵越小、越慢越便宜越大"的阶梯**——HBM 紧贴 GPU、SOCAMM(LPDDR5X) 在 CPU 边上管容量、再往外是 DDR5 / CXL 内存池 / 光互连共享池。理解这条阶梯，才看得懂"NVIDIA 砍内存"那种新闻到底砍的是哪一层。

## 直觉 · 内存就是一摞抽屉，越近越快越装不下

你写代码时早懂这个套路：寄存器 < L1/L2 cache < 内存 < 磁盘，越靠近 CPU 越快但越小。AI 服务器是同一套思路放大到机架级——只是层数和名字换了：

- **离 GPU 越近** → 带宽越高、延迟越低、但**单位容量极贵、装不了多少**。
- **越往外推** → 容量能堆很大、便宜，但**延迟一级级掉下去**。

工程上永远在这条阶梯上做取舍：算得最热的数据(权重、激活、KV cache)塞最快的那层，冷一点、大块的容量往外放。

## 这条阶梯长什么样

<figure style="margin:26px 0; padding:22px; background:#f1eee8; border:1px solid #c7bca8; border-radius:4px;">
<svg viewBox="0 0 720 348" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="mh-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#7a6f5d"/></marker>
    <marker id="mh-up" viewBox="0 0 10 10" refX="5" refY="2" markerWidth="6" markerHeight="6" orient="auto"><path d="M1,9 L5,1 L9,9 z" fill="#7a6f5d"/></marker>
  </defs>

  <!-- ===== 轴一：距离 / 容量（单调） ===== -->
  <text class="reveal" x="40" y="32" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#3a3128">距离 / 容量轴：← 离 GPU 近 · 容量小 · 贵　　　远 · 容量大 · 便宜 →</text>
  <line class="reveal d1" x1="40" y1="48" x2="688" y2="48" stroke="#7a6f5d" stroke-width="1.2" marker-end="url(#mh-h)"/>

  <!-- 五格 -->
  <g class="reveal d1">
    <rect x="44" y="64" width="120" height="40" rx="4" fill="#f3d9d9" stroke="#9b2c2c"/>
    <text x="104" y="82" text-anchor="middle" font-size="10.5" font-weight="700" fill="#7a2020">HBM4</text>
    <text x="104" y="96" text-anchor="middle" font-size="7.5" fill="#7a6f5d">贴 GPU 的显存</text>
  </g>
  <g class="reveal d2">
    <rect x="184" y="64" width="130" height="40" rx="4" fill="#fbeed6" stroke="#b8841c"/>
    <text x="249" y="82" text-anchor="middle" font-size="10" font-weight="700" fill="#8a5310">LPDDR5X · SOCAMM</text>
    <text x="249" y="96" text-anchor="middle" font-size="7.5" fill="#7a6f5d">CPU 侧容量内存</text>
  </g>
  <g class="reveal d3">
    <rect x="334" y="64" width="100" height="40" rx="4" fill="#e8efe4" stroke="#4a6b3a"/>
    <text x="384" y="82" text-anchor="middle" font-size="10.5" font-weight="700" fill="#2f5a2a">DDR5</text>
    <text x="384" y="96" text-anchor="middle" font-size="7.5" fill="#7a6f5d">本地大内存</text>
  </g>
  <g class="reveal d4">
    <rect x="454" y="64" width="110" height="40" rx="4" fill="#e3edf5" stroke="#3d5a6c"/>
    <text x="509" y="82" text-anchor="middle" font-size="10" font-weight="700" fill="#284a5e">CXL 内存池</text>
    <text x="509" y="96" text-anchor="middle" font-size="7.5" fill="#7a6f5d">电学·跨机共享</text>
  </g>
  <g class="reveal d5">
    <rect x="584" y="64" width="104" height="40" rx="4" fill="#efe3f1" stroke="#6a3a8e"/>
    <text x="636" y="82" text-anchor="middle" font-size="10" font-weight="700" fill="#4e2a6e">光互连池</text>
    <text x="636" y="96" text-anchor="middle" font-size="7.5" fill="#7a6f5d">optics·拉远共享</text>
  </g>
  <text class="reveal d4" x="104" y="120" text-anchor="middle" font-size="8" fill="#7a6f5d">带宽最高·容量最小</text>
  <text class="reveal d4" x="636" y="120" text-anchor="middle" font-size="8" fill="#7a6f5d">容量最大·可跨机共享</text>

  <line x1="40" y1="136" x2="688" y2="136" class="reveal d3" stroke="#c7bca8" stroke-width="1" stroke-dasharray="4 4"/>

  <!-- ===== 轴二：延迟（不单调，光互连打破它） ===== -->
  <text class="reveal d3" x="40" y="158" font-family="Fraunces,serif" font-style="italic" font-size="12" font-weight="700" fill="#6a3a8e">延迟轴：不是单调变大 —— 光互连正是来打破它的（远 ≠ 一定最慢）</text>

  <!-- y 轴提示：上=延迟更大 -->
  <line class="reveal d3" x1="312" y1="262" x2="312" y2="180" stroke="#7a6f5d" stroke-width="1" marker-end="url(#mh-up)"/>
  <text class="reveal d3" x="306" y="192" text-anchor="end" font-size="8" fill="#7a6f5d">延迟</text>
  <text class="reveal d3" x="306" y="202" text-anchor="end" font-size="8" fill="#7a6f5d">更大</text>

  <!-- 折线：DDR5 低 → 电学CXL 跳高 → 光互连回落进 gap（注意 x 对齐上面的格子） -->
  <polyline class="draw d4" points="384,248 509,196 636,222" fill="none" stroke="#6a3a8e" stroke-width="2.2" pathLength="1000"/>
  <g class="reveal d5">
    <circle cx="384" cy="248" r="4.5" fill="#4a6b3a"/>
    <circle cx="509" cy="196" r="4.5" fill="#3d5a6c"/>
    <circle cx="636" cy="222" r="4.5" fill="#6a3a8e"/>
  </g>
  <g class="reveal d5" font-size="9" text-anchor="middle">
    <text x="384" y="266" fill="#2f5a2a">DDR5 ~115ns 本地</text>
    <text x="509" y="186" fill="#284a5e">电学 CXL 200–300ns</text>
    <text x="636" y="242" fill="#4e2a6e">光互连 填回 gap</text>
  </g>

  <text class="reveal d5" x="40" y="296" font-size="9" fill="#3a3128">电学 CXL 池化把延迟 <tspan fill="#9b2c2c" font-weight="700">跳高到 200–300ns</tspan>；光互连把池化延迟 <tspan fill="#6a3a8e" font-weight="700">拉回 115–300 之间（比电学 CXL 还低）</tspan></text>
  <text class="reveal d5" x="40" y="314" font-size="9" fill="#7a6f5d">→ 这才是它的卖点：容量像大池子，延迟却接近本地</text>
  <text class="reveal d5" x="40" y="338" font-size="8.5" fill="#7a6f5d">"NVIDIA 砍内存" 砍的是上排中间 LPDDR5X(SOCAMM) 那格，最左 HBM 一点没动</text>
</svg>
</figure>

| 层 | 在哪 | 角色 | 特点 |
|---|---|---|---|
| **HBM**(HBM4) | 堆叠在 GPU 旁(封装内) | 喂 GPU 算的超高带宽显存 | 最快、最贵、容量最小；放权重 / 激活 / [[kv-cache]] |
| **LPDDR5X · SOCAMM** | CPU 侧,插槽式紧凑模组 | CPU 边上的容量内存 | 比 HBM 慢、便宜、能堆更多；SOCAMM 是 NVIDIA 定的 ~14×90mm 模组形态 |
| **DDR5** | 主板本地内存条 | 传统服务器大内存 | 本地延迟 ~115ns,容量大 |
| **CXL 内存池** | 机架内,走 CXL 协议 | 多机/多卡**共享**的内存池 | 电学互连,延迟掉到 200–300ns |
| **光互连池** | 跨机架,走光(optics) | 把内存池**拉远 + 共享** | 填 DDR5↔CXL 之间那段延迟鸿沟,容量可极大扩 |

## 为什么会往"池化 + 光互连"走

本地容量这一层(就是 SOCAMM/LPDDR5X 那格)同时撞上**三堵墙**:
- **供给墙**:HBM / LPDDR5X / DDR5 三条产线抢同一批晶圆,LPDDR5X 还得跟手机抢;NVIDIA 的需求有 ~60% 供给缺口(TrendForce 口径)。
- **功耗墙 + 散热墙**:本地多堆内存,电和热扛不住。

三堵墙一起堵死"每台机器自己堆更多本地内存"这条路 → 出路是**把内存从单机里拆出来、做成一大池、多机共享**。但池化有代价:延迟会掉。延迟账本:

```
本地 DDR5      ~115 ns
电学 CXL 池    200–300 ns   ← 慢了一截
光(optics)    来填这段差   ← 既拉远池化、延迟又不至于掉到 CXL 那么差
```

这就是这条线的赌注:**内存不再是"每张卡自己的",而是一池子用光纤拉给整个集群共享。**

## 案例 · 2026-06 的 "SOCAMM 砍单" 误读
2026-06-04,有爆料称 NVIDIA Rubin 平台每机架 SOCAMM 内存从 55TB 砍到 28TB(腰斩),美光($MU)当天跌约 10%,市场读成"AI 内存需求要崩"。

但拆开看:**被砍的是 CPU 侧 LPDDR5X(SOCAMM),贴 GPU 的 HBM4 一点没动**(仍 288GB/GPU、~20.7TB/机架)。而且砍的原因是**供给造不出来逼的取舍,不是需求没了**——紧俏到要做减法。这反而强化了"本地容量到顶 → 转向池化 + 光互连"的结构性判断。

> 一句话:看到"砍内存"先问**砍的是哪一层**——砍 HBM 才是算力需求降温的信号,砍 LPDDR5X 更可能是供给瓶颈逼出来的腾挪。

## 代码出处 / 来源
- PhotonCap《The Cut Was Not HBM: The SOCAMM Selloff》(2026-06,photoncap.net)
- 数据口径:SemiAnalysis(砍单爆料)、TrendForce(LPDDR5X 供给缺口)
- 相关玩家:$MU 美光(内存)、$NVDA(平台)、$MRVL Marvell(收 Celestial AI / XConn 押光互连)

## 链接
- [[kv-cache]] · 最吃 HBM 那层带宽/容量的典型数据
- [[nvls]] · 多 GPU 之间的低延迟通信,跟内存池化是一对"把数据搬得更快"的努力
- [[prefill-decode]] · decode 阶段被 HBM 带宽卡脖子,正是内存层级的痛点场景
- [[flash-attention]] · 把注意力矩阵留在 SRAM 不落 HBM,这页是它的动机根
