---
name: peakpatch-ecn
type: concept
sources: [peakpatch]
updated: 2026-08-17
---

# ECN · 从 CLIP 中层捞回否定信号，再补到最终向量

## 一句话
读组合信息最强的中层 token，预测一个偏移向量，轻轻推开坍缩的最终 embedding。

## 直觉
最终层像一张为了“这图里有什么物体”而压缩过的摘要，中层还保留“谁否定谁”的句法。ECN 不重写整份摘要，而是从中层提取遗漏项，算成一张小补丁贴回最终向量。

## 怎么做的

1. 一个可学习 query 对峰值层全部 token 做 cross-attention，自动关注 no / not / without 以及被否定的对象。
2. 把这个摘要与峰值层 EOS、较早 anchor 层 EOS、峰值层 token 均值拼接。
3. MLP 输出偏移 \(\delta\)，以可学习强度 \(\alpha\) 加到最终文本向量，再做 L2 归一化：

\[
\hat f_T=\frac{f_T+\alpha\delta}{\lVert f_T+\alpha\delta\rVert_2}.
\]

## 数字例子

把 512 维缩成二维。最终向量 \(f_T=[0.8,0.6]\)，ECN 给出 \(\delta=[-0.3,0.4]\)，\(\alpha=0.5\)：

\[
f_T+\alpha\delta=[0.65,0.80],\qquad
\lVert[0.65,0.80]\rVert_2=\sqrt{1.0625}\approx1.0308,
\]

所以 \(\hat f_T\approx[0.6306,0.7761]\)。若图片向量是 \([1,0]\)，余弦分数便从 0.8 降到 0.6306：对“图里没有该物体”的句子，这个方向正是在削弱错误的物体匹配。

## 跟微调的对照

微调会改 CLIP 编码器本身；ECN 冻结它，只读三层缓存特征。代价是必须有中间层白盒访问，不能只拿最终 embedding。

## 链接

- [[peakpatch]] · ECN 是能迁移到检索和文生图的 embedding 分支。
- [[cross-attention]] · 学习 query 如何从整段 token 中抽一个任务相关摘要。
