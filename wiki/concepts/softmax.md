---
name: softmax
type: concept
sources: [unet]
updated: 2026-07-24
---

# Softmax · 一组实数压成概率分布 · 温度调软硬

## 一句话
把一组实数(logits)变成**和为 1 的概率**:每个先取 `exp` 再除以总和。指数让"大的更大",但小的也留一点(不像 argmax 一刀切)。**温度 T** 是软硬旋钮:T 小→尖锐(接近 argmax)、T 大→平(接近均匀)。

## 直觉 · 可导的"软 argmax"

模型最后常要从一堆分数里"选"一个——直接 argmax 取最大?**不可导**(挪一点分数,选择要么不变要么突跳),没法反向传播训练。softmax 是 argmax 的**可导软化版**:
```
pᵢ = exp(zᵢ) / Σⱼ exp(zⱼ)
```
- **exp**:把分数指数放大,大的拉得更开 → 倾向于"最大那个占大头"。
- **除以总和**:归一化成概率(都正、加起来 1)。

为什么用 `exp` 而不是直接归一化?因为指数能**拉开差距 + 永远为正**,且配 [[cross-entropy]] 损失时梯度特别干净(`p − onehot`)。

## 温度 T · 尖锐 ↔ 平滑的旋钮
把 logits 先除以温度 `T` 再 softmax:`pᵢ = softmax(zᵢ / T)`。
- **T → 小(<1)**:差距被放大 → 分布**尖锐**,几乎把全部概率给最大那个(接近 argmax、更确定、更死板)。
- **T → 大(>1)**:差距被压平 → 分布**平滑**,各选项概率拉近(更随机、更有创造性/多样)。
- **T = 1**:原样。

这就是 LLM 采样里的 "temperature":调高更天马行空、调低更稳重保守。

## 怎么做的 · 数字例子
logits `z = [2, 1, 0]`:
```
T=1:   exp=[7.389, 2.718, 1.000]，总和=11.107
       softmax=[0.665, 0.245, 0.090]
       自检：0.665+0.245+0.090=1.000

T=0.5: 等于把 z 翻倍 [4,2,0]
       softmax=[0.867, 0.117, 0.016]  更尖

T=2:   等于把 z 减半 [1,0.5,0]
       softmax=[0.506, 0.307, 0.186]  更平
```
(还有个工程细节:实现时先减去最大值 `exp(zᵢ − max z)` 防 `exp` 溢出,结果不变。)

## 落点
- **[[self-attention]]**:`softmax(Q·Kᵀ/√d)` 把注意力分数变成"分配给每个位置的权重",和为 1。那个 `√d` 就是防分数过大、softmax 太尖(同 [[qk-rmsnorm]] 一类稳定动机)。
- **分类输出 / [[cross-entropy]]**:最后一层 logits 过 softmax 得类别概率。
- **采样**:温度 + top-k/top-p 控制生成的随机性。

## 链接
- [[self-attention]] · 注意力权重 = softmax(点积分数)
- [[sampling-decoding]] · softmax 出分布后,怎么从里面挑 token(温度/top-k/top-p)
- [[dot-product]] · softmax 的输入 logits 常来自点积
- [[cross-entropy]] · softmax 的天生搭档损失,梯度 = p − onehot
- [[qk-rmsnorm]] · 都为"别让 softmax 太尖/炸"服务
- [[flash-attention]] · 在线 softmax 用的就是这页"减最大值"那套,改成 running
- [[gspo]] · RL 里序列概率也走 softmax/对数概率
- [[unet]] · 每个像素的类别 logits 独立做 softmax
