---
name: training-time-test
type: concept
sources: [raven]
updated: 2026-09-28
---

# 训练时测试 Training-Time Test · 在自己推理时会遇到的上下文上训练

## 一句话

推理时模型看到的上下文是它自己产出的，训练就也用它自己产出的上下文，并且让这段上下文留在计算图里吃梯度。

## 直觉

学开车，教练坐副驾时车总在正道上（真历史）；自己上路后每个弯都是上一个弯的后果（自生成历史）。Self Forcing 已经让学员在自己开出来的路况上练，但把"前面怎么开的"当成录像回放，不改；training-time test 更进一步：练后面的弯时，前面的弯也在打分表里——后面出事，前面的处置也要挨批。

它跟"测试时训练"（[[test-time-training]]）是反的：TTT 是推理时临时改参数；training-time test 是训练时模拟推理的上下文，参数照常更新，推理时什么都不多做。

## 怎么做的（RAVEN 的做法）

```
1. fake-score 步：冻结学生做 self rollout（复用 KV cache）
   每块 t 得到去噪轨迹 ẑ_t^(τ_1) → … → ẑ_t^(τ_K)=x̂_t（干净端点）
2. 选一个采样层级 u ∈ {τ_1..τ_{K−1}}
3. 拍平成交错序列（长 2T−1）：
   I_u = (ẑ_1^(u), x̂_1, ẑ_2^(u), x̂_2, …, ẑ_{T−1}^(u), x̂_{T−1}, ẑ_T^(u))
4. 因果 mask 下一次前向：
   带噪块 ẑ_t^(u) = 被监督的去噪输入
   前面的干净块 x̂_{<t} = 它的历史 h_t = H(x̂_{<t})，这次在图里
5. 输出加噪到 s，老师和 fake critic 各给一个端点，算 DMD 损失，按块加权反传
```

关键是第 4 步：Self Forcing 写的是 \(h_t=\mathrm{sg}(\mathcal H(\hat x_{<t}))\)，RAVEN 把 \(\mathrm{sg}\) 拿掉。梯度到不了 \(\hat x_{<t}\) 的数值（它们是采出来的常数），但能到**模型把它们编成 KV 的那套参数**——历史的"读法"被后面块的损失修了。

出处是 EAGLE-3（[[speculative-decoding]]）：草稿模型训练时喂自己上一步的草稿表示，而不是目标模型的真表示。视频里麻烦在每块是多步去噪的终点，真展开要穿过自回归递归 + 采样器两层反传；RAVEN 的省法是复用 fake-score 步已经采出来的 rollout，只做一次重排 + 一次前向。

## 数字例子

T=3 块，交错序列长 2×3−1=5：

```
位置   1        2     3        4     5
内容   ẑ_1^(u)  x̂_1  ẑ_2^(u)  x̂_2  ẑ_3^(u)
```

因果 mask 下谁看谁（√ 可见；按正文「历史 = 干净端点」画，精确 mask 以论文图 1(d) 为准）：

| 查询 \ 键 | ẑ_1 | x̂_1 | ẑ_2 | x̂_2 | ẑ_3 |
|---|---|---|---|---|---|
| ẑ_1 | √ | | | | |
| x̂_1 | | √ | | | |
| ẑ_2 | | √ | √ | | |
| x̂_2 | | √ | | √ | |
| ẑ_3 | | √ | | √ | √ |

- ẑ_3 的历史 = {x̂_1, x̂_2}，正是推理时第三块接龙看的东西；
- ẑ_3 的 DMD 损失反传时穿过 x̂_1、x̂_2 的 KV 投影 → 这两块"怎么被读"被第三块的错误修正；
- Self Forcing 同样的图里 x̂_1、x̂_2 的 KV 是 detach 的，第三块的损失到位置 3 就停。

代价：5 个位置的因果注意力 vs Self Forcing 的 3 个位置，注意力 pair 数 15 vs 6（论文没报这笔账）。

## 跟相近做法的对照

| 做法 | 历史来源 | 历史吃梯度？ |
|---|---|---|
| Teacher Forcing | 真视频块 | 否 |
| Diffusion Forcing / CausVid | 真视频块各自加噪 | 否 |
| Self Forcing | 自己 rollout，\(\mathrm{sg}\) | 否 |
| DF w/ self rollout（RAVEN 消融） | 自己 rollout，不反传 | 否（83.30，比 DF 还低） |
| RAVEN | 自己 rollout，在图里 | 是（85.15） |

消融最有意思的一行：只把历史换成自生成、不给梯度，分数反而掉——分布对了不等于有监督。

## 链接

- [[raven]] · 提出并用于因果视频蒸馏
- [[chunk-wise-self-forcing]] · Self Forcing 分块反传的另一种省显存切法
- [[teacher-forcing-video-diffusion]] · 被替代的范式
- [[stop-gradient]] · 被拿掉的那个 \(\mathrm{sg}\)
- [[kv-cache]] · 历史表示 \(\mathcal H(\cdot)\) 的载体
- [[future-participation-loss-scaling]] · 交错序列上各块损失怎么加权
