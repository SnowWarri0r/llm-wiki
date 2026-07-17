---
name: thinking-tokens
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Thinking Tokens · 用 padding 槽换来的可学习上下文寄存器

## 一句话

把原本浪费的 padding 位置换成可学习 token，让它们在双向注意力里收集整句信息。

## 直觉

批处理文本常补到固定长度，短 prompt 后面的大量 PAD 通常被 mask 掉，不参与计算。LTX-2 将这些位置替换成可学习 registers，并取消它们的 mask。正文 token 可以把信息写进去，后续 DiT 再把这些额外 token 当作文本条件读取。

它像给一句话附上几张模型自己填写的隐藏便签，但便签不是自然语言，也不会展示推理步骤。“thinking”是作者命名，不应等同于 chain-of-thought 或 reasoning。

## 怎么做的

```text
固定长度 8，prompt 占 5：
原输入  [t1][t2][t3][t4][t5][PAD][PAD][PAD]
替换后  [t1][t2][t3][t4][t5][R1 ][R2 ][R3 ]

→ 全双向 connector：8 个位置互相注意
→ 输出正文 token + 已写入上下文的 R1/R2/R3
→ 作为 DiT 的 text cross-attention 条件
```

当前官方实现会重复一组 learnable registers 以填满序列，并将 attention mask 变为全可见。视频、音频各有独立 connector，因此可以把同一句 prompt 整理成不同条件表征。

## 数字例子

假设双向 connector 的某个 register 对 5 个正文 token 的 attention 权重是：

```text
[0.10, 0.15, 0.45, 0.20, 0.10]，和 = 1
token 的“碰撞相关度” = [0, 0, 1, .5, 0]
register 聚合值 = .10×0 + .15×0 + .45×1 + .20×.5 + .10×0 = .55
```

register 因而得到一份全句摘要信号。真实表示是高维多头向量，例子只演示“可学习槽如何通过 attention 聚合”。

## 跟特殊 token 的对比

| token | 位置 | 主要用途 |
|---|---|---|
| `[CLS]` | 通常固定 1 个开头位 | 汇总序列用于分类 |
| padding | 补齐长度，通常被 mask | 不承载信息 |
| thinking/register | 替换 padding，可被读写 | 提供多个额外上下文槽 |

## 链接

- [[ltx-2]] · text connector 使用该机制
- [[cross-attention]] · DiT 从这些条件 token 读取信息

