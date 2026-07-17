---
name: asymmetric-dual-stream-transformer
type: concept
sources: [ltx-2]
updated: 2026-07-17
---

# Asymmetric Dual-Stream Transformer · 不对称双流 Transformer

## 一句话

音频和视频各走一条专用流水线，层数对齐、宽度不同，再在每层交换信息。

## 直觉

视频要处理画面中的 `x、y、时间`，音频主要处理时间；让两边用同宽网络，像给声音处理也配一整套二维画布，算力未必花在需要的地方。完全拆成两个模型又会回到“先生成一个、再补另一个”的单向管线。

不对称双流取中间路线：

- **分开**：VAE、self-attention、FFN 和通道宽度都按模态定制；
- **对齐**：两条流有相同层数，可以在每一层的相近抽象深度交换；
- **互通**：用双向 cross-attention 让音频改视频、视频也改音频。

它替代的是“完全共享一条流”和“两个独立模型串联”这两个极端。

## 怎么做的

```text
layer 1: video self/text ─┐  ┌─ audio self/text
                          ↔  双向 cross-attention
layer 2: video self/text ─┤  ├─ audio self/text
                          ↔
...                       │  │
layer 48                  └──┘
```

LTX-2 的论文主线是 14B 视频流 + 5B 音频流。两边不是共享权重；“shared depth”是层数和交换位置对齐，不是同一参数矩阵被调用两次。

## 数字例子

总参数 19B 中：

```text
video = 14B，占 14/19 ≈ 73.7%
audio =  5B，占  5/19 ≈ 26.3%
video/audio 容量比 = 14/5 = 2.8
```

这只是参数分配，不等于视频计算量恰好是音频 2.8 倍；token 数、注意力形状和实现 kernel 也影响 FLOPs 与速度。

## 跟其它路线对比

| 路线 | 好处 | 主要问题 |
|---|---|---|
| 单一共享流 | 交互直接、结构统一 | 容量和位置编码难兼顾模态差异 |
| 两个模型串联 | 可复用现成 T2V/V2A | 后生成者只能服从先生成者 |
| 对称双流 | 双向联合、实现规整 | 可能给简单模态过度分配容量 |
| **不对称双流** | 双向联合且容量按需分配 | 参数更多、跨流同步和部署更复杂 |

## 链接

- [[ltx-2]] · 14B/5B 双流实例
- [[audiovisual-cross-attention]] · 两条流逐层通信的接口
- [[diffusion-transformer]] · 每条流的生成骨架

