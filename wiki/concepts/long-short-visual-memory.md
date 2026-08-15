---
name: long-short-visual-memory
type: concept
sources: [interactive-avatar]
updated: 2026-08-12
---

# 长短期视觉记忆 · 近处逐帧留，远处只留代表画面

## 一句话

最近几秒完整保存，久远历史压成少量代表 token，让流式视频既能接稳上一拍，也不忘早先的身份、衣服和物体。

## 直觉

长时间视频像一场没有结束时间的直播。把所有旧帧都塞进 attention，显存和计算会一直增长；只留最近几帧，人物戴过的手表、换过的坐姿又会被忘掉。

InteractiveAvatar 因而保留两个固定容量的池：

- 短期池像剪辑软件的最近窗口，密集保存最近 5 秒；
- 长期池像直播回放的关键截图，只保存语义上互不重复的旧状态。

两者都先经轻量压缩器 \(\mathcal C\) 变成 memory token，再与当前块一起送进视频 DiT。

## 怎么做的

当前视频 latent 为 \(z_t\)，压缩结果为

\[
m_t=\mathcal C(z_t).
\]

短期池保存最近 \(K\) 个压缩 latent，长期池固定保存 \(N\) 个代表项：

\[
\mathcal M_s=\{m_{t-K+1},\ldots,m_t\},\qquad
\mathcal M_l=\{\tilde m_1,\ldots,\tilde m_N\}.
\]

模型实际读取的是两池拼接后的历史 \(\Phi(H)=\operatorname{Concat}(\mathcal M_l,\mathcal M_s)\)。这里的“长 / 短”不是 LSTM 的两个门，也不是把帧分成高低频；它只表示时间跨度与保存密度不同。

## 数字例子

论文在 1024×576 下先经 VAE 做 16 倍空间压缩，再让 memory compressor 在高、宽上各压 4 倍：

```text
宽方向：1024 ÷ 16 ÷ 4 = 16
高方向： 576 ÷ 16 ÷ 4 =  9
每个 memory latent：16 × 9 = 144 token
```

5 秒视频有 120 帧，对应 30 个 video latent，因此一个短期池有

```text
30 latent × 144 token = 4320 token
```

长期池容量与短期池相同，又是 4320 token；总 memory 上限约 8640 token，不随直播时长继续增长。论文保留时间维不压缩，所以仍能逐 latent 更新，而不是把相邻时刻混成一个平均画面。

## 边界

固定容量只把成本封顶，没有让记忆无限无损。被移出长期池的早期状态无法恢复；论文也承认长视频、大动作和新物体会出现退化或消失。

## 链接

- [[interactive-avatar]] · 提出这套长短期视觉记忆
- [[ai-memory-hierarchy]] · 近、中、远记忆分层的通用思路
- [[kv-cache]] · KV cache 省重算，memory token 负责挑选和压缩内容，两者不是一回事
