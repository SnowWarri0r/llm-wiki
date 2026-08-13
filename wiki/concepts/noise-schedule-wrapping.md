---
name: noise-schedule-wrapping
type: concept
sources: [rcm]
updated: 2026-08-12
---

# 噪声日程包装 · 给不同老师换一只统一的时间表

## 一句话

不改老师学到的信噪比，只把原时间坐标改写成 TrigFlow 时间坐标。

## 直觉

两只钟表一个用 0–1000 刻度，一个用 0–90 度。包装不是让时间倒流，而是找到两只表上“同样嘈杂”的刻度，再把老师的输入缩放到对应幅度。

## 怎么做的

原老师的加噪式为 \(x_s=\alpha_s x_0+\sigma_s\epsilon\)。TrigFlow 使用 \(x_t=\cos t\,x_0+\sin t\,\epsilon\)。先匹配噪声与信号之比：

\[
\frac{\sigma_{\phi(t)}}{\alpha_{\phi(t)}}=\tan t.
\]

- \(s=\phi(t)\)：TrigFlow 时间 \(t\) 对应的原老师时间。
- \(\alpha_s\)：原日程的信号系数。
- \(\sigma_s\)：原日程的噪声系数。
- \(\tan t=\sin t/\cos t\)：TrigFlow 的噪声/信号比。

两边比例相同但总幅度可能不同，所以调用老师前再乘：

\[
k(t)=\sqrt{\alpha_{\phi(t)}^2+\sigma_{\phi(t)}^2},\qquad
x^{\mathrm{raw}}=k(t)x_t.
\]

## 数字例子

某原日程在 \(s=400\) 时，\(\alpha_s=0.6,\ \sigma_s=0.8\)。

```text
噪声/信号比 = .8/.6 = 1.333
t = arctan(1.333) ≈ .927 rad

TrigFlow 系数：cos(t)≈.6，sin(t)≈.8
k = sqrt(.6²+.8²)=1
```

此例总幅度正好为 1，所以无需缩放。若原系数是 \(0.3,0.4\)，比例仍是 \(1.333\)，对应同一个 \(t\)，但 \(k=\sqrt{0.3^2+0.4^2}=0.5\)，老师应读取 \(0.5x_t\)。比例保住“噪多少”，缩放补回“整体多大”。

## 链接

- [[rcm]] · 用包装把 Cosmos / Wan 老师接进统一 TrigFlow sCM 目标。
- [[probability-path]] · 加噪系数怎样定义整条概率路径。
- [[velocity-field]] · 包装后的老师输出再换成统一速度表示。
