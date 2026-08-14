---
name: input-guidance
type: concept
sources: [asyncpatch-diffusion]
updated: 2026-08-14
---

# Input Guidance · 放大已知图像真正带来的修改方向

## 一句话

对同一个待更新状态算两次 score：一次使用较干净的输入条件，一次故意把输入再加噪；两者之差就是“清晰输入多带来的细节方向”。

## 公式

\[
\begin{aligned}
\Delta s_i&=s_{\mathrm{clean},i}-s_{\mathrm{noisy},i},\\
s_{\mathrm{guided},i}&=s_{\mathrm{clean},i}+\omega_i\Delta s_i
\end{aligned}
\]

- \(i\)：当前要更新的空间 token。
- \(s_{\mathrm{clean},i}\)：输入参考区域较干净时，网络给位置 \(i\) 的 score 向量。
- \(s_{\mathrm{noisy},i}\)：参考输入被额外加噪后，同一位置的 score。
- \(\omega_i\ge 0\)：引导强度；0 表示不放大。
- \(\Delta s_i=s_{\mathrm{clean},i}-s_{\mathrm{noisy},i}\)：清晰输入相对模糊输入额外提供的修改方向。

## 一个标量手算

真实 score 是与 latent 同形的张量，这里只拿其中一个数说明算法。设：

~~~text
清晰输入时的 score = 0.8
输入加噪后的 score = 0.5
guidance 强度 omega = 2
~~~

则：

~~~text
差向量 = 0.8 - 0.5 = 0.3
放大后   = 0.8 + 2×0.3 = 1.4
等价写法 = 3×0.8 - 2×0.5 = 1.4
~~~

它没有把去噪方向随便乘三；只放大“清晰输入相比模糊输入多出来的 0.3”。

## 与 CFG 的关系

[[classifier-free-guidance]] 用“有文本条件 − 无文本条件”的差提高 prompt 遵循；Input Guidance 用“清晰空间输入 − 加噪空间输入”的差提高细节忠实度。AsyncPatch 在实现中先在每个噪声水平完成 CFG，再对两个空间输入分支做 Input Guidance。

## 边界

引导是外推，强度过大会夸大错误。论文主要用定性样例和附录曲线展示纹理 / 输入忠实度的变化，没有证明它对所有任务都单调变好。

## 链接

- [[asyncpatch-diffusion]] · Input Guidance 的来源
- [[classifier-free-guidance]] · 同一种“放大两次前向之差”的思路
- [[score-function]] · 上式里的 score 究竟是什么
