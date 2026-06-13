---
name: multi-token-prediction
type: concept
sources: [minimind-o]
updated: 2026-06-08
---

# Multi-Token Prediction · MTP · 一步预测好几个

## 一句话
一个位置上**同时预测多个 token**，而不是一次一个 —— minimind-o 的 Talker 用它在每帧一次性吐出 8 层 Mimi codebook，避免把 8 层拆成 8 条长链路。

## 直觉 · RVQ 的 8 层不该排成 8 倍长队

[[rvq-codec]] 把每帧音频量化成**多层 code**（Mimi 是 8 层：第 1 层粗轮廓，往后逐层补残差细节）。一秒 12.5 帧、每帧 8 层 → 如果像普通自回归那样一个 code 一个 code 地吐，序列瞬间变 8 倍长，又慢又难训。

MTP 的办法：**在同一个时间步，一次把这 8 层都预测出来**。模型在每帧位置有 8 个输出头（或一个能出 8 路的结构），并行给出第 1..8 层的 code。序列长度回到"每帧一个位置"，不膨胀。

类比：写八行诗，不是写完第一行再想第二行，而是**一眼把八行的骨架同时落下**——因为这八层描述的是同一帧声音的不同精度，本就该一起出。

## 怎么做的 · 共享主体 + 轻量 codebook adapter

8 层 codebook 分布不一样（粗层 vs 残差层），但给每层都配一整套 embedding + 输出头，参数会爆，0.1B 装不下。minimind-o 的折中：

- **共享主体**：8 层共用大部分 Talker 参数
- **轻量 adapter**：每层只挂一个小 codebook adapter，吸收该层的分布差异

```
Talker hidden ─┬─ adapter_1 → head → codebook layer 1 (粗)
               ├─ adapter_2 → head → codebook layer 2
               │      ⋮                    ⋮
               └─ adapter_8 → head → codebook layer 8 (细残差)
        （同一帧，8 路并行出 code）
```

既保留各层分布差异，又不用为每层复制一整套参数。

## 跟流式的关系 · 边想边补

流式生成时，Thinker 一边吐文本 token，Talker 一边用 MTP + 延迟调度**补齐这一帧的 8 层 codes**，Mimi 解码器增量还原 24kHz 波形 → 不用等整句说完就能播。MTP 是"每帧并行出多层"，让这种边想边说成为可能。

## 一个区分 · 跟"投机解码的 MTP"同名不同用
DeepSeek 等用 MTP 指"训练时多预测几个未来 token 当辅助目标 / 加速"。这里 minimind-o 的 MTP 是**同一帧的多层 codebook 并行预测**——同名，但解决的是 RVQ 多层的序列膨胀问题，别混。

## 代码出处
- minimind-o Talker 的 MTP audio head（`model/model_omni.py`）
- 思路谱系：RVQ 多码本的并行/延迟预测（fish-speech 的 dual-AR、MusicGen 的 delay pattern 同源问题）

## 链接
- [[rvq-codec]] · 多层 codebook 就是 MTP 要并行预测的对象
- [[thinker-talker]] · Talker 用 MTP 渲染 codes
- [[dual-ar]] · fish-speech 处理多码本的另一种结构
- [[minimind-o]] · 用 MTP 的 0.1B Omni
