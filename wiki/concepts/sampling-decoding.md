---
name: sampling-decoding
type: concept
sources: []
updated: 2026-06-18
---

# 采样 / 解码策略 · 从概率分布里挑下一个 token

## 一句话
模型每步用 [[softmax]] 吐出**整个词表上的概率分布**;"解码"就是怎么从里面挑下一个 token([[tokenization]]):**greedy**(取最大,稳但呆)/ **按概率采样** + **温度**调随机 / **top-k、top-p** 砍长尾防胡说 / **beam search** 同时搜多条。这一步直接决定生成是稳重还是天马行空。

## 直觉 · 模型只给概率，挑哪个是另一回事

模型本身不"输出一个词",它输出一个**概率分布**(经 [[softmax]],和为 1)。比如下一个 token:
```
the 0.50 | a 0.30 | cat 0.12 | dog 0.06 | (长尾一堆) 0.02
```
怎么从这个分布落到具体一个 token,有几种策略,各有脾气:

- **Greedy(贪心)**:永远取概率最大的(`the`)。确定、可复现,但**呆板、爱重复**("the the the"、套话循环)。
- **按概率采样**:照概率掷骰子——0.5 的概率选 `the`、0.3 选 `a`…**有多样性、更像人**,但偶尔会**抽到长尾里的烂词**(那 0.02 的一堆,蹦出莫名其妙的词)。
- **温度 T**:采样前把分布调软硬(见 [[softmax]]):T 小→尖锐→接近 greedy(保守);T 大→平→更随机(天马行空)。
- **top-k / top-p**:先**砍掉长尾**再采样,防止抽到烂词(下面细说)。
- **beam search**:同时保留 b 条"当前最优"的句子路径往下扩,最后挑整体最好的。适合**翻译/确定性**任务,不适合要创意的开放生成。

## top-k 与 top-p · 砍长尾的两种砍法

<figure style="margin:26px 0; padding:22px; background:#eef1f5; border:1px solid #aab4c4; border-radius:4px;">
<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- 概率柱状图（左半区） -->
  <line class="reveal d1" x1="60" y1="180" x2="380" y2="180" stroke="#7a6f5d" stroke-width="1"/>
  <g class="reveal d1" text-anchor="middle">
    <rect x="74" y="80" width="44" height="100" fill="#3949ab"/><text x="96" y="74" font-size="9" fill="#28306e">0.50</text><text x="96" y="196" font-size="9" fill="#3a3128">the</text>
    <rect x="134" y="120" width="44" height="60" fill="#3949ab"/><text x="156" y="114" font-size="9" fill="#28306e">0.30</text><text x="156" y="196" font-size="9" fill="#3a3128">a</text>
    <rect x="208" y="156" width="44" height="24" fill="#9aa4bf"/><text x="230" y="150" font-size="9" fill="#7a6f5d">0.12</text><text x="230" y="196" font-size="9" fill="#7a6f5d">cat</text>
    <rect x="268" y="168" width="44" height="12" fill="#9aa4bf"/><text x="290" y="162" font-size="9" fill="#7a6f5d">0.06</text><text x="290" y="196" font-size="9" fill="#7a6f5d">dog</text>
    <rect x="328" y="172" width="30" height="8" fill="#c9b8b8"/><text x="343" y="166" font-size="8" fill="#9b2c2c">长尾</text>
  </g>
  <!-- 砍线（top-k=2 / top-p=0.8 在这里重合：留 the+a=0.8） -->
  <line class="reveal d2" x1="192" y1="60" x2="192" y2="188" stroke="#9b2c2c" stroke-width="1.6" stroke-dasharray="5 3"/>
  <text class="reveal d2" x="135" y="52" text-anchor="middle" font-size="9" fill="#1f4d3a">← 留</text>
  <text class="reveal d2" x="270" y="52" text-anchor="middle" font-size="9" fill="#9b2c2c">砍掉长尾 →</text>

  <!-- 右侧图例 -->
  <rect class="reveal d3" x="430" y="58" width="13" height="13" rx="2" fill="#3a3128"/>
  <text class="reveal d3" x="450" y="69" text-anchor="start" font-size="12" font-weight="700" fill="#3a3128">greedy</text>
  <text class="reveal d3" x="450" y="86" text-anchor="start" font-size="10" fill="#7a6f5d">只取最高 → the(呆板易重复)</text>
  <rect class="reveal d4" x="430" y="104" width="13" height="13" rx="2" fill="#9b2c2c"/>
  <text class="reveal d4" x="450" y="115" text-anchor="start" font-size="12" font-weight="700" fill="#9b2c2c">top-k = 2</text>
  <text class="reveal d4" x="450" y="132" text-anchor="start" font-size="10" fill="#7a6f5d">固定留前 2 个(the,a)→ 重新归一再采</text>
  <rect class="reveal d5" x="430" y="150" width="13" height="13" rx="2" fill="#1f4d3a"/>
  <text class="reveal d5" x="450" y="161" text-anchor="start" font-size="12" font-weight="700" fill="#1f4d3a">top-p = 0.8</text>
  <text class="reveal d5" x="450" y="178" text-anchor="start" font-size="10" fill="#7a6f5d">留累计概率到 0.8 的最小集合(动态个数)</text>
  <text class="reveal d5" x="450" y="200" text-anchor="start" font-size="9" fill="#7a6f5d">这例两者都砍在 the+a 后(0.5+0.3=0.8)</text>
</svg>
</figure>

- **top-k**:只留**概率最高的 k 个**候选,其余清零,重新归一化再采。`k` 固定。
- **top-p(nucleus)**:从高到低**累加概率,够到 p 就停**,只留这批(**个数随分布动态变**——分布尖时留得少、平时留得多)。比固定 k 更自适应。

实际生成常**组合用**:`temperature + top-p`(或 top-k)是最常见的一套旋钮。

## 数字例子 · 手算各策略
分布 `the=0.50, a=0.30, cat=0.12, dog=0.06, 长尾=0.02`:
```
greedy:    直接取 the                       （永远 the）
top-k=2:   留 {the:0.50, a:0.30} → 归一化 → {the:0.625, a:0.375} → 按这个采
top-p=0.8: 累加 0.50(the) → 0.80(+a) 够 0.8 停 → 留 {the,a} → 归一化同上
top-p=0.95:累加 0.50→0.80→0.92(+cat)→0.98(+dog) 够 0.95 停 → 留 {the,a,cat,dog}
温度 T=2:  先把 logits 减半再 softmax → 分布变平 → 长尾概率抬高 → 更敢冒险
温度 T=0.5:logits 翻倍 → 分布变尖 → 几乎只剩 the → 接近 greedy
```
(温度怎么把分布调尖/调平的算例见 [[softmax]]。)

## 落点
- **重复/套话** → 多半 greedy 或温度太低;**胡说/跑题** → 温度太高或没设 top-p。调这几个旋钮就是在"稳重 ↔ 创意"之间找平衡。
- **要可复现**(评测、确定性输出)→ greedy 或温度 0。
- **翻译/摘要**这类有"标准答案"的 → beam search;**聊天/写作**这类开放生成 → 温度 + top-p 采样。

## 代码出处 / 来源
- top-p/nucleus sampling:Holtzman et al. 2019《The Curious Case of Neural Text Degeneration》
- 实现:HuggingFace `generate(do_sample, temperature, top_k, top_p, num_beams)`

## 链接
- [[softmax]] · 概率分布和温度的来源,这页是它的下游"怎么挑"
- [[tokenization]] · 挑出来的是一个 token
- [[next-token-forward-pass]] · 每步前向出 logits,解码挑下一个
- [[cross-entropy]] · 训练时的损失;采样是推理时怎么用这个分布
