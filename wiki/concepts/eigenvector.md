---
name: eigenvector
type: concept
sources: []
updated: 2026-06-18
---

# 特征向量 / 特征值 · 被矩阵作用后"只缩放、不转向"的方向

## 一句话
矩阵 `W` 作用在向量上一般又转又拉;但有几个**特殊方向**,`W` 作用后**方向纹丝不动、只被拉长或缩短**——这些方向叫**特征向量**,拉伸倍数叫**特征值 λ**(`Wv = λv`)。它们是这个矩阵"最自然的骨架轴",[[svd]]、PCA、稳定性分析全建在它上。

## 直觉 · 大多数方向会转，少数不转

把矩阵当一个**变换**:`y = W x` 把向量 `x` 搬到新位置 `y`。随手挑个向量喂进去,它通常**既被转了向、又被改了长**。

但总有那么几个**特殊方向**:喂进去,出来还**指着原来那条线**(方向没变),只是变长或变短了。
```
Wv = λv      # 出来 = 原方向 × 一个数 λ
```
- `v`:特征向量(那条不转向的方向;它的长度无所谓,关键是"哪条线")。
- `λ`:特征值(沿这条线被拉伸几倍。λ>1 拉长、0<λ<1 缩短、λ<0 反向、λ=0 压成 0)。

类比:一张橡皮膜被你按某种方式拉扯,膜上大多数小箭头会被又转又抻;但**沿某两个特殊方向画的箭头,只会原地变长变短、不会歪**——那两个方向就是这次拉扯的特征向量。

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="ev-i" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#7a6f5d"/></marker>
    <marker id="ev-o" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker>
    <marker id="ev-e" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#1f4d3a"/></marker>
  </defs>
  <!-- 普通方向：被转向 -->
  <text class="reveal d1" x="180" y="30" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#9b2c2c">普通方向 · 被转向</text>
  <line class="reveal d1" x1="120" y1="170" x2="120" y2="100" stroke="#7a6f5d" stroke-width="2" marker-end="url(#ev-i)"/>
  <text class="reveal d1" x="120" y="186" text-anchor="middle" font-size="8" fill="#7a6f5d">喂进去 x</text>
  <line class="draw d2" x1="120" y1="170" x2="200" y2="118" stroke="#9b2c2c" stroke-width="2" marker-end="url(#ev-o)" pathLength="1000"/>
  <text class="reveal d2" x="240" y="120" text-anchor="middle" font-size="8" fill="#9b2c2c">出来 Wx：歪了</text>
  <!-- 特征方向：不转只缩 -->
  <text class="reveal d3" x="540" y="30" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="12.5" font-weight="700" fill="#1f4d3a">特征方向 · 只变长</text>
  <line class="reveal d3" x1="460" y1="180" x2="520" y2="120" stroke="#7a6f5d" stroke-width="2" marker-end="url(#ev-i)"/>
  <text class="reveal d3" x="448" y="150" text-anchor="middle" font-size="8" fill="#7a6f5d">v</text>
  <line class="draw d4" x1="460" y1="180" x2="580" y2="60" stroke="#1f4d3a" stroke-width="2" marker-end="url(#ev-e)" pathLength="1000"/>
  <text class="reveal d4" x="618" y="78" text-anchor="middle" font-size="8" fill="#1f4d3a">Wv = λv</text>
  <text class="reveal d4" x="600" y="120" text-anchor="middle" font-size="8" fill="#1f4d3a">同一条线、只拉长 λ 倍</text>
  <line class="reveal d4" x1="455" y1="185" x2="600" y2="40" stroke="#1f4d3a" stroke-width="0.6" stroke-dasharray="3 3"/>
  <text class="reveal d5" x="360" y="214" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="11.5" font-weight="700" fill="#3a3128">特征向量 = 被 W 作用后唯一不转向的那条线，λ = 沿它拉几倍</text>
</svg>
</figure>

## 怎么找出来 · 手算一个 2×2(全程)

目标:找满足 `Wv = λv` 的 `λ` 和 `v`。拿这个矩阵:
```
W = [2 1]
    [1 2]
```

**第 1 步:挪到一边。** `Wv = λv` → `Wv − λv = 0` → `(W − λI)v = 0`(`I` 是单位矩阵,凑出同形状好相减):
```
(W − λI) = [2−λ   1 ]
           [ 1   2−λ]
```

**第 2 步:要有"非零的 v"解,这个矩阵必须是"压扁的"(行列式=0)。** 否则 `(W−λI)v=0` 只有 `v=0` 的废解。所以列**特征方程** `det(W − λI) = 0`:
```
det = (2−λ)(2−λ) − 1·1 = (2−λ)² − 1 = 0
→ (2−λ)² = 1  →  2−λ = ±1  →  λ = 1 或 λ = 3
```
两个特征值出来了:**λ = 3 和 λ = 1**。(行列式=0 的直觉:`det` 衡量这个变换把面积放大几倍;=0 表示它把整个平面压扁到一条线上,才会有"被压没"的非零方向——那方向就是特征向量。)

**第 3 步:把每个 λ 代回去,解出对应的 v。**
```
λ=3:  (W−3I)v = [−1  1][v₁]=0  → −v₁+v₂=0 → v₁=v₂  → v=[1, 1]（任意倍数都行）
                [ 1 −1][v₂]
λ=1:  (W−1I)v = [ 1  1][v₁]=0  →  v₁+v₂=0 → v₁=−v₂ → v=[1,−1]
                [ 1  1][v₂]
```

**第 4 步:验证(代回原式 `Wv=λv`)。**
```
W·[1, 1]ᵀ = [2+1, 1+2] = [3, 3] = 3×[1,1]   ✓ λ=3
W·[1,−1]ᵀ = [2−1, 1−2] = [1,−1] = 1×[1,−1]  ✓ λ=1
```
搞定:这矩阵的特征向量是斜 45° 的 `[1,1]`(拉 3 倍)和 `[1,−1]`(拉 1 倍)。

## 特征分解 · 沿特征方向看，W 就是"各自缩放"
把特征向量当新坐标轴(拼成矩阵 `Q`),特征值摆成对角(`Λ`),那么:
```
W = Q Λ Q⁻¹
读法（从右往左）：Q⁻¹ 把向量换到"特征方向坐标" → Λ 沿每根特征轴各乘 λ → Q 换回原坐标
```
意义:**在特征方向这套坐标里,一个复杂矩阵就退化成"每根轴各自乘个数"**——最简单的形态。反复作用 `Wⁿ = QΛⁿQ⁻¹`,`λ` 最大的那根方向会越滚越主导(幂迭代、PageRank、系统稳定性都靠这条)。

## 它的局限 → 为什么还需要 SVD
特征分解很美,但挑食:
- **只对方阵**(d×d),长方形矩阵没有特征向量。
- 特征向量 `Q` **不一定正交**(不一定互相垂直),`λ` 可能是负数甚至复数。

[[svd]] 是它对**任意矩阵**的推广:不直接看 `W` 的特征向量,而是看 `WᵀW` 的(它必对称、必半正定),得到的方向一定正交、奇异值 σ 一定非负。对称矩阵时两者重合(σ = |λ|)。

## 代码出处 / 来源
- 线性代数标准内容:特征值/特征向量、特征方程 det(W−λI)=0、特征分解
- 落点:[[svd]]、PCA、幂迭代/PageRank、ODE 稳定性

## 链接
- [[svd]] · 把特征分解推广到任意矩阵(看 WᵀW 的特征向量)
- [[matrix-rank]] · 非零特征值/奇异值的个数 = 秩
- [[dot-product]] · "正交"= 点积为 0;特征向量是否正交是关键区别
- [[markov-chain]] · 转移矩阵的最大特征向量 = 稳态分布
