---
name: gradient-backprop
type: concept
sources: []
updated: 2026-06-18
---

# 梯度 / 反向传播 · 往哪调参数能让 loss 变小

## 一句话
**梯度** = 每个参数"动一点点,loss 变多少"拼成的向量,指向**上坡最陡**的方向;训练就沿**负梯度**下坡(`参数 ← 参数 − lr·梯度`)。**反向传播** = 用链式法则从 loss 往回**一层层**把每个参数的梯度算出来,复用中间结果不重算。

## 直觉 · 蒙眼下山

训练 = 在一个"参数 → loss"的山谷里找最低点。你蒙着眼,只能感觉**脚下哪个方向最陡**,然后往下坡迈一小步,反复。
- **导数**(1 个参数):loss 对这个参数的斜率——它变大一点,loss 涨还是跌、涨跌多快。
- **梯度**(一堆参数):每个参数各自的斜率(偏导)拼成的向量。它指向**让 loss 涨最快**的方向 → 取**反方向**就是降最快。
- **学习率 lr**:步子多大。太大跨过谷底来回震荡,太小挪半天。

```
参数_new = 参数_old − lr · 梯度        # 沿负梯度走一小步
```

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="gb-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#9b2c2c"/></marker></defs>
  <!-- loss 碗 -->
  <path class="draw d1" d="M70,46 C 250,46 250,180 360,180 C 470,180 470,46 650,46" fill="none" stroke="#3a3128" stroke-width="2" pathLength="1000"/>
  <text class="reveal d1" x="360" y="224" text-anchor="middle" font-size="10" fill="#7a6f5d">参数 w →</text>
  <text class="reveal d1" x="46" y="120" text-anchor="middle" font-size="10" fill="#7a6f5d" transform="rotate(-90 46 120)">loss</text>
  <!-- 当前点：贝塞尔 t≈0.4 处 (218,93)，真落在曲线上 -->
  <circle class="reveal d2" cx="218" cy="93" r="6" fill="#9b2c2c"/>
  <text class="reveal d2" x="196" y="80" text-anchor="middle" font-size="11" fill="#9b2c2c">现在 w</text>
  <!-- 负梯度步：到 t≈0.6 处 (262,131)，沿坡往下 -->
  <line class="reveal d3" x1="224" y1="98" x2="259" y2="129" stroke="#9b2c2c" stroke-width="2.2" marker-end="url(#gb-h)"/>
  <text class="reveal d3" x="356" y="108" text-anchor="middle" font-size="11" fill="#9b2c2c">−lr·梯度 → 沿坡下一步</text>
  <!-- 谷底 -->
  <circle class="reveal d4" cx="360" cy="180" r="6" fill="#1f4d3a"/>
  <text class="reveal d4" x="404" y="184" text-anchor="start" font-size="11" fill="#1f4d3a">谷底（loss 最小）</text>
  <text class="reveal d5" x="360" y="28" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#3a3128">梯度指上坡最陡 → 取负方向迈一小步 → 反复滚到谷底</text>
</svg>
</figure>

## 反向传播 · 链式法则从后往前

网络是**函数套函数**:`loss = L( f( g( h(x) ) ) )`。要 loss 对最里层参数的梯度,靠**链式法则**把一串局部导数乘起来:
```
dL/d(里层) = dL/df · df/dg · dg/dh · dh/d(里层)
```
**关键省法**:从 **loss 那头往回算**(back-prop),每一层把"上游传来的梯度"乘上"本层的局部导数",再传给更里一层。这样每个中间结果**只算一次、被复用**——不然每个参数都从头乘一遍会爆炸。前向算一遍存下中间值,反向再扫一遍收梯度。

## 数字例子 · 手算一步
一个最小网络:`L = (w·x − y)²`,给定 `x=2, y=5`,当前 `w=3`,学习率 `lr=0.1`。

**前向**(算 loss,顺手存中间值):
```
a = w·x = 3·2 = 6
err = a − y = 6 − 5 = 1
L = err² = 1
```
**反向**(链式法则,从 L 往回到 w):
```
dL/d(err) = 2·err = 2·1 = 2          # L=err² 的导数
d(err)/da = 1                         # err=a−y
da/dw     = x = 2                     # a=w·x
dL/dw = 2 · 1 · 2 = 4                 # 三段乘起来
```
**走一步**:
```
w ← w − lr·(dL/dw) = 3 − 0.1·4 = 2.6
```
**验证变好了**:新 `a=2.6·2=5.2`,`err=0.2`,`L=0.04` —— 从 1 掉到 0.04,loss 真降了。这一步就是 SGD 的全部:前向出 loss、反向出梯度、沿负梯度挪一点。

## 为什么深网络要小心梯度
链式法则是**一长串相乘**:每段都 <1 → 乘到底**消失**(学不动);每段都 >1 → **爆炸**(炸飞)。所以才有:
- **[[residual-connection]] / [[lstm]]**:加法路径 ≈ 每步乘 1,给梯度修条高速路。
- **[[qk-rmsnorm]] / [[layernorm]]**:把数值摁在稳定区间,别让某段导数过大过小。
- **梯度裁剪 / 好的初始化**:同样为治这串连乘。

## 代码出处 / 来源
- 标准内容:梯度下降、反向传播(Rumelhart et al. 1986)、链式法则
- 现代:autograd(PyTorch/JAX 自动建反向图),你不用手推,但要懂它在干嘛

## 链接
- [[cross-entropy]] · 最常被求梯度的那个 loss(梯度 = p − onehot)
- [[residual-connection]] · 加法路径给梯度修高速路,治消失
- [[lstm]] · cell state 的加法更新同理,梯度不消失
- [[softmax]] · softmax+交叉熵的梯度特别干净
- [[matrix-rank]] · 反向传播本质是一连串矩阵乘(每层局部导数)
