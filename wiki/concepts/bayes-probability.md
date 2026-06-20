---
name: bayes-probability
type: concept
sources: []
updated: 2026-06-18
---

# 条件概率 / 链式法则 / 贝叶斯 · 拿观测更新信念

## 一句话
**条件概率** `P(A|B)` = 在 B 已知的前提下 A 的概率。**链式法则**把联合概率拆成一串条件 `P(x₁,x₂,…)=P(x₁)P(x₂|x₁)…`——这正是语言模型逐 token 生成的根。**贝叶斯** `P(因|果)=P(果|因)·P(因)/P(果)` 帮你**反过来推**:用观测把"先验信念"更新成"后验信念"。

## 直觉 · 三件套

**① 条件概率 = 缩小范围再看占比。** `P(A|B)` 就是"只看 B 发生的那些情况里,A 占多少"。`P(A|B)=P(A 且 B)/P(B)`——把分母从"全部"换成"只有 B"。

**② 链式法则 = 联合概率可以一步步条件展开。**
```
P(x₁,x₂,x₃) = P(x₁)·P(x₂|x₁)·P(x₃|x₁,x₂)
```
一句话的概率 = 第一个词的概率 × 给定第一个词第二个词的概率 × … **这就是 [[causal-language-model]] / LLM 在干的事**:`P(下一词 | 前文)` 一个个连乘,生成整句。

**③ 贝叶斯 = 翻转条件 + 更新信念。** 你常知道 `P(果|因)`(有病时检测阳性的概率),却想要 `P(因|果)`(检测阳性时真有病的概率)。贝叶斯帮你翻过来:
```
P(因|果) = P(果|因) · P(因) / P(果)
后验          似然      先验    证据(归一化)
```
读法:**先验**(没看检测前对"有病"的信念=患病率)→ 乘上**似然**(这个观测在该假设下多可能)→ 得到**后验**(看完检测后更新的信念)。

## 数字例子 · 阳性 ≠ 有病(base rate 陷阱)
某病**患病率 1%**;检测**准确率 99%**(有病 99% 测出阳性、没病 99% 测出阴性)。你测出**阳性**,实际有病的概率是多少?直觉喊"99%",贝叶斯说**只有 50%**。拿 10000 人摊开看:

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <defs><marker id="bp-h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="#7a6f5d"/></marker></defs>
  <!-- root -->
  <rect class="reveal d1" x="300" y="22" width="120" height="30" rx="3" fill="#faf4e1" stroke="#3a3128"/>
  <text class="reveal d1" x="360" y="42" text-anchor="middle" font-size="11" fill="#3a3128">10000 人</text>
  <!-- level2 -->
  <line class="reveal d2" x1="340" y1="52" x2="250" y2="78" stroke="#7a6f5d" stroke-width="1.2" marker-end="url(#bp-h)"/>
  <line class="reveal d2" x1="380" y1="52" x2="490" y2="78" stroke="#7a6f5d" stroke-width="1.2" marker-end="url(#bp-h)"/>
  <rect class="reveal d2" x="180" y="80" width="130" height="32" rx="3" fill="#f3d9d9" stroke="#9b2c2c"/>
  <text class="reveal d2" x="245" y="96" text-anchor="middle" font-size="10" fill="#7a2020">有病 100</text>
  <text class="reveal d2" x="245" y="108" text-anchor="middle" font-size="8" fill="#7a6f5d">患病率 1%</text>
  <rect class="reveal d2" x="430" y="80" width="130" height="32" rx="3" fill="#e8efe4" stroke="#4a6b3a"/>
  <text class="reveal d2" x="495" y="96" text-anchor="middle" font-size="10" fill="#2f5a2a">没病 9900</text>
  <text class="reveal d2" x="495" y="108" text-anchor="middle" font-size="8" fill="#7a6f5d">99%</text>
  <!-- level3 -->
  <line class="reveal d3" x1="220" y1="112" x2="170" y2="140" stroke="#7a6f5d" stroke-width="1.1" marker-end="url(#bp-h)"/>
  <line class="reveal d3" x1="270" y1="112" x2="300" y2="140" stroke="#7a6f5d" stroke-width="1.1" marker-end="url(#bp-h)"/>
  <line class="reveal d3" x1="470" y1="112" x2="420" y2="140" stroke="#7a6f5d" stroke-width="1.1" marker-end="url(#bp-h)"/>
  <line class="reveal d3" x1="520" y1="112" x2="560" y2="140" stroke="#7a6f5d" stroke-width="1.1" marker-end="url(#bp-h)"/>
  <rect class="reveal d3" x="118" y="142" width="96" height="30" rx="3" fill="#efc9c9" stroke="#9b2c2c" stroke-width="1.6"/>
  <text class="reveal d3" x="166" y="161" text-anchor="middle" font-size="10" fill="#7a2020">99 阳(真)</text>
  <rect class="reveal d3" x="266" y="142" width="70" height="30" rx="3" fill="#f7f1de" stroke="#bbb"/>
  <text class="reveal d3" x="301" y="161" text-anchor="middle" font-size="9" fill="#7a6f5d">1 阴(漏)</text>
  <rect class="reveal d4" x="372" y="142" width="96" height="30" rx="3" fill="#efc9c9" stroke="#9b2c2c" stroke-width="1.6"/>
  <text class="reveal d4" x="420" y="161" text-anchor="middle" font-size="10" fill="#7a2020">99 阳(误)</text>
  <rect class="reveal d4" x="520" y="142" width="96" height="30" rx="3" fill="#f7f1de" stroke="#bbb"/>
  <text class="reveal d4" x="568" y="161" text-anchor="middle" font-size="9" fill="#7a6f5d">9801 阴</text>
  <!-- 结论 -->
  <text class="reveal d5" x="360" y="206" text-anchor="middle" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">阳性共 99+99 = 198 人，真有病只 99 → P(病|阳) = 99/198 ≈ 50%</text>
  <text class="reveal d5" x="360" y="228" text-anchor="middle" font-size="9.5" fill="#7a6f5d">病太罕见(先验低),99% 准也架不住 9900 个没病的人贡献一堆误报</text>
</svg>
</figure>

```
贝叶斯公式直接算:
P(病|阳) = P(阳|病)·P(病) / P(阳)
P(阳) = P(阳|病)P(病) + P(阳|没病)P(没病) = 0.99·0.01 + 0.01·0.99 = 0.0099 + 0.0099 = 0.0198
P(病|阳) = 0.99·0.01 / 0.0198 = 0.0099 / 0.0198 = 0.5   →  50%
```
关键:**先验(患病率 1%)太低**,哪怕检测 99% 准,海量没病的人也会贡献等量误报 → 阳性里真假各半。这就是为什么贝叶斯逼你**别忽略 base rate**。

## 落点
- **语言模型 = 概率链式法则**:`P(句子)=∏P(下一词|前文)`,生成就是逐项采样(见 [[sampling-decoding]])。
- **扩散反向过程 = 贝叶斯**:已知"加噪过程"`P(噪|净)`,反推`P(净|噪)`一步步去噪(见 [[markov-chain]] / [[score-function]])。
- **后验更新**:RLHF、推断、A/B 决策都是"先验 + 证据 → 后验"。
- **熵/KL**([[entropy-kl]])量的就是这些分布之间差多少。

## 代码出处 / 来源
- 概率论标准内容:条件概率、链式法则、贝叶斯定理、全概率公式
- 落点:朴素贝叶斯分类、扩散模型、语言建模、贝叶斯推断

## 链接
- [[causal-language-model]] · LM 就是概率链式法则 P(下一词|前文) 连乘
- [[sampling-decoding]] · 从每步的条件概率里采样生成
- [[entropy-kl]] · 量两个概率分布差多少
- [[closed-form-kl]] · 高斯分布间 KL 的闭式
- [[markov-chain]] · 扩散反向 = 用贝叶斯从噪声推干净
