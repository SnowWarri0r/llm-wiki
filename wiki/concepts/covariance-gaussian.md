---
name: covariance-gaussian
type: concept
sources: [drift-ar]
updated: 2026-07-24
---

# 协方差 / 多元高斯 · 数据散成什么形状的椭圆

## 一句话
方差说一个维度"散多开";**协方差矩阵 Σ** 说多个维度"各自散多开 + 两两一起动不动"——它描述一团数据的**椭圆形状**。妙处:**Σ 的特征向量 = 这个椭圆的轴 = PCA 主成分**(又是 [[eigenvector]] 那条不转的轴),多元高斯就是这个椭圆形状的钟形云 `N(μ, Σ)`。

## 直觉 · 从方差到协方差

- **方差**(1D):数据离均值平均有多远的平方,`Var(x)=平均((x−μ)²)`。一个数,说"散多开"。
- **协方差**(两维一起):`Cov(x,y)=平均((x−μₓ)(y−μᵧ))`,说**x 和 y 是不是一起动**:
  - `>0` 同涨同跌(x 大时 y 也大);`<0` 一涨一跌;`≈0` 没关系。
- **协方差矩阵 Σ**:把所有维度两两的关系装进一个方阵,对角线是各自方差、非对角线是两两协方差:
```
Σ = [Var(x)   Cov(x,y)]
    [Cov(x,y) Var(y)  ]
```

## 几何 · Σ 的特征向量就是椭圆的轴(= PCA)

把一团 2D 数据画出来,它大致是个**椭圆云**。这个椭圆:
- **朝哪歪、哪个方向最长** → 由 **Σ 的特征向量**决定(椭圆的长轴/短轴方向);
- **每个轴多长** → ∝ **√对应特征值**(那个方向散得多开)。

这就是 **PCA**:数据**散得最开的方向 = Σ 最大特征值对应的特征向量**(第一主成分)。降维就是只留前几根长轴、扔掉短轴。**——跟你上次学的特征向量是同一条轴**,只不过这次矩阵换成了"数据的协方差"。

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs>
    <marker id="cv-a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker>
    <marker id="cv-b" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#1f4d3a"/></marker>
  </defs>
  <!-- 椭圆云在左半区，中心 (220,150)，沿 -30° 拉长 -->
  <ellipse class="draw d2" cx="220" cy="150" rx="120" ry="42" fill="none" stroke="#7a6f5d" stroke-width="1.4" stroke-dasharray="5 4" transform="rotate(-30 220 150)" pathLength="1000"/>
  <g class="reveal d1" fill="#3949ab" opacity="0.6">
    <circle cx="150" cy="186" r="4.5"/><circle cx="172" cy="166" r="4.5"/><circle cx="190" cy="183" r="4.5"/>
    <circle cx="205" cy="160" r="4.5"/><circle cx="214" cy="140" r="4.5"/><circle cx="232" cy="152" r="4.5"/>
    <circle cx="243" cy="129" r="4.5"/><circle cx="266" cy="135" r="4.5"/><circle cx="267" cy="113" r="4.5"/>
    <circle cx="289" cy="120" r="4.5"/><circle cx="291" cy="100" r="4.5"/>
  </g>
  <circle class="reveal d2" cx="220" cy="150" r="3.5" fill="#3a3128"/>
  <!-- 长轴 = 最大特征向量（红，右上） -->
  <line class="reveal d3" x1="220" y1="150" x2="302" y2="103" stroke="#9b2c2c" stroke-width="2.6" marker-end="url(#cv-a)"/>
  <!-- 短轴 = 第二特征向量（绿，右下，垂直） -->
  <line class="reveal d4" x1="220" y1="150" x2="245" y2="193" stroke="#1f4d3a" stroke-width="2.4" marker-end="url(#cv-b)"/>

  <!-- 右侧图例栏（字号加大、远离椭圆） -->
  <rect class="reveal d3" x="430" y="100" width="14" height="14" rx="2" fill="#9b2c2c"/>
  <text class="reveal d3" x="452" y="112" text-anchor="start" font-size="13" font-weight="700" fill="#9b2c2c">长轴 = Σ 最大特征向量</text>
  <text class="reveal d3" x="452" y="132" text-anchor="start" font-size="11" fill="#7a6f5d">数据散得最开 → 第一主成分</text>
  <rect class="reveal d4" x="430" y="168" width="14" height="14" rx="2" fill="#1f4d3a"/>
  <text class="reveal d4" x="452" y="180" text-anchor="start" font-size="13" font-weight="700" fill="#1f4d3a">短轴 = 第二特征向量</text>
  <text class="reveal d4" x="452" y="200" text-anchor="start" font-size="11" fill="#7a6f5d">散得最少 · 轴长 ∝ √特征值</text>

  <text class="reveal d5" x="360" y="270" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#3a3128">协方差椭圆的轴 = Σ 的特征向量</text>
</svg>
</figure>

## 数字例子 · 手算协方差矩阵
三个点 `(1,1), (2,2), (3,3)`(完全在 `y=x` 这条线上):
```
均值 μ = (2, 2)
去中心: (−1,−1), (0,0), (1,1)
Var(x) = 平均((−1)²,0²,1²) = (1+0+1)/3 = 2/3
Var(y) = 同理 = 2/3
Cov(x,y) = 平均((−1)(−1), 0·0, 1·1) = (1+0+1)/3 = 2/3
```
```
Σ = 2/3 · [1 1]      （比例上就是 [[1,1],[1,1]]，那个 2/3 不影响方向）
          [1 1]
```
**算它的特征向量**(就是 [[eigenvector]] 那套):`[[1,1],[1,1]]` → 特征值 `2`(向量 `[1,1]`)和 `0`(向量 `[1,−1]`)。
- 最大特征向量 `[1,1]` = **正是数据所在的那条 `y=x` 线** → 第一主成分。
- 另一个特征值 `0` = 垂直方向 `[1,−1]` 上数据**完全没散开**(点都在线上)。

所以"数据躺在一条线上" ⟺ "协方差矩阵秩 1" ⟺ "只有一个非零特征值"——[[matrix-rank]] / [[eigenvector]] / PCA 在这里**全是同一件事**。

## 多元高斯 N(μ, Σ)
一维高斯是钟形曲线 `N(μ, σ²)`;多维就是 `N(μ, Σ)`——`μ` 定中心、`Σ` 定**椭圆形状**(圆形 = Σ 是 σ²I,各向同性;歪椭圆 = Σ 有非对角项)。扩散模型、VAE 的隐变量、概率建模全在用它。两个**同协方差**高斯的 KL 还会塌成均值差的平方(见 [[closed-form-kl]])。

## 代码出处 / 来源
- 标准统计 / 线性代数:协方差矩阵、多元高斯、PCA = 协方差的特征分解
- 落点:[[kl-vae]]、扩散噪声、[[closed-form-kl]]

## 链接
- [[eigenvector]] · 协方差的特征向量 = 椭圆的轴 = 主成分(同一条轴)
- [[matrix-rank]] · 数据躺一条线 = 协方差秩 1 = 一个非零特征值
- [[closed-form-kl]] · 同协方差高斯的 KL 塌成均值差²
- [[svd]] · PCA 也可直接对(中心化)数据做 SVD 得到
- [[reading-2x2-matrices]] · 2×2 矩阵的几何读法(两列=基向量落点),协方差是它的一种
- [[kl-vae]] · latent 常建模成高斯
