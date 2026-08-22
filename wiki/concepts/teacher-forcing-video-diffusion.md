---
name: teacher-forcing-video-diffusion
type: concept
sources: [minwm, solaris-multiplayer-world-model, wan-streamer-v01, wan-animate-2, uniswap-av]
updated: 2026-08-18
---

# 视频扩散里的 Teacher Forcing · 训练时喂真历史

## 一句话

训练因果视频模型时，第 `i` 段只生成当前 noisy chunk，但把此前的真实干净视频段当历史条件；这样容易学会下一段，却会造成训练看真历史、推理看自己历史的 exposure bias。

## 用四段视频看懂

假设视频 latent 被切成 `A、B、C、D` 四段，当前训练目标是 `C`：

```text
训练：真实 A + 真实 B + noisy C → 还原真实 C
推理：生成 A + 生成 B + noisy C → 生成 C
```

因果 mask 保证 `C` 看不到未来的 `D`。但训练时的 `A、B` 没有任何生成误差，推理时则可能已经漂色、变形或偏离相机轨迹。模型从没在这种有瑕疵的历史上练过，误差便会一段段放大。

## 为什么还要先这样训

如果一开始就让未训练好的模型反复读取自己的烂输出，后续每段的输入分布会不断变化，学习很不稳定。Teacher forcing 先把“只看过去、续写下一段”的基本能力教会，再由 self-rollout / self forcing 阶段让模型适应自己的历史。

## 它和文字自回归的关系

LLM 训练时用真实前词预测下一个词，推理时读取自己刚生成的词；视频版本的矛盾相同，只是一个 token 换成了一小段 noisy latent，而且每段内部还要进行多步或少步去噪。

## 链接

- [[minwm]] · Stage 1 用 teacher forcing 获得因果能力，Stage 3 用 self-rollout 修正分布错位
- [[solaris-multiplayer-world-model]] · Diffusion Forcing 与 Checkpointed Self Forcing
- [[autoregressive-vs-bidirectional-video-diffusion]] · 因果生成与整段双向去噪的取舍
- [[wan-streamer-v01]] · rolling distillation 让少步学生连续读取自己的生成历史
- [[wan-animate-2]] · 用 Error Buffer 先污染干净历史，再用分块 Self-Forcing 真正读取自身输出
- [[uniswap-av]] · Stage 2 喂真实目标历史，Stage 3 再改成读取自己的历史
