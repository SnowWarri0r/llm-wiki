---
name: time-aligned-speech-motion-rope
type: concept
sources: [dyaplex]
updated: 2026-08-11
---

# Time-Aligned Speech-Motion RoPE · 语音动作时间对齐旋转编码

## 一句话

动作 token 虽被摊成长序列，做语音 cross-attention 时仍按它们所属的真实帧编号位置。

## 直觉

DyaPlex 一帧塞进 46 个动作 token。若直接用扁平序号，第一帧最后一个动作和第二帧第一个动作看起来相差 1，而同一帧第一个和最后一个动作反而相差 45，时间关系被“部位数量”污染了。

时间对齐 RoPE 给同一帧的 46 个 token 同一只时间戳。它替代“拿扁平 token 下标冒充时间”的做法，使动作 Query 与同为 12.5 Hz 的语音 Key 能按真实帧差比较。

## 怎么做的


若每个运动帧占 (L_{step}) 个 token，扁平位置 (n) 对应的运动时间是


\[
q_{pos}(n)=\left\lfloor\frac{n}{L_{step}}\right\rfloor.
\]


- (n)：动作序列里的扁平 token 下标；
- (L_{step})：每帧 token 数，DyaPlex 为 46；
- (q_{pos})：真正送入 cross-attention RoPE 的帧编号；
- (lfloor\cdot\rfloor)：向下取整。

动作 Query 按 (q_{pos}) 旋转，语音 Key 按自己的 12.5 Hz 帧编号 (s) 旋转。两者点积里出现的是相对时间差 (q_{pos}-s)。因果 mask 还要求 (s\le q_{pos})，防止看见未来语音。

## 数字例子

取 (L_{step}=46)。扁平下标 92、100、137 分别属于：


\[
\lfloor92/46\rfloor=2,\quad
\lfloor100/46\rfloor=2,\quad
\lfloor137/46\rfloor=2.
\]


所以它们虽相隔 45 个 token，时间位置都为第 2 帧。查询第 2 帧动作时，语音帧 0、1、2 的相对距离分别为 2、1、0；语音帧 3 属于未来，会被遮住。

## 跟普通 RoPE 的对照

- 普通扁平 RoPE：位置差混进了人物、身体部位和 codebook 顺序。
- 时间对齐 RoPE：先还原真实帧，再比较语音与动作相隔几帧。

## 链接

- [[dyaplex]] · 首次用于双人流式语音—动作对齐
- [[rotary-position-embedding]] · RoPE 为什么能表达相对位置
- [[dyadic-motion-interleaving]] · 为什么一帧会膨胀成 46 个 token
