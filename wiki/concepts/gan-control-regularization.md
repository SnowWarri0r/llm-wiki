---
name: gan-control-regularization
type: concept
sources: [wonder-video-world-model]
updated: 2026-07-29
---

# GAN Control Regularization · 让判别器专门盯住相机有没有走偏

## 一句话

DMD 主要修局部纹理，Wonder 再用冻结 teacher 的低频特征比较真实轨迹与学生 rollout，给相机布局单独补一股梯度。

## 直觉

四步因果 student 每次只偏一点，滚几十个 chunk 后相机可能飞得过快、方向跑偏，最后整幅图糊掉。标准 DMD 的 score 差更容易盯到边缘和纹理；逐像素 L2 虽能拽回轨迹，却会把未知区域平均得模糊。

Wonder 把真实 latent 和 student latent 加同一份高噪声，送进同一个冻结 camera-conditioned teacher。它不直接判“哪张图更真”，而是比较 teacher 从浅层到中层的低频特征变化是否像一条听话的相机轨迹。

## 怎么做的

同噪声扰动：

\[
z_\tau^r=\alpha_\tau z_0+\sigma_\tau\epsilon,\qquad
z_\tau^f=\alpha_\tau\hat z_0+\sigma_\tau\epsilon.
\]

- \(z_0\)：真实视频 latent。
- \(\hat z_0\)：student rollout latent。
- \(r/f\)：real / fake 标签，不是指数。
- \(\epsilon\)：两支共享的高斯噪声。

冻结 teacher 取第 1 层和三个中层特征；线性投影到同空间后相减，再用 stride convolution 压低高频：

\[
\Delta F_{M_i}^x=
\psi_i\big(\eta_i(F_{M_i}^x)-\eta_1(F_1^x)\big).
\]

register token cross-attend 这些低频图，汇总成相机一致性 logit \(d^x\)。最后用相对 softplus：

\[
L_D=\operatorname{softplus}(d^f-d^r),\qquad
L_G=\operatorname{softplus}(d^r-d^f).
\]

\(\operatorname{softplus}(x)=\log(1+e^x)\)。判别器希望 real 分数高于 fake；生成器希望 fake 追上 real。

## 数字例子

先看共享噪声为什么重要。取 \(\alpha=.2,\sigma=.98,\epsilon=.5,z_0=2,\hat z_0=1\)：

```text
z_r = .2×2 + .98×.5 = .89
z_f = .2×1 + .98×.5 = .69
差值 = .20

直接代数：
z_r−z_f = α(z_0−z_hat_0) + σ(ε−ε)
        = .2×(2−1) + 0
        = .20
```

同一份噪声会在差值里抵消，比较仍落在 real/fake 的信号差上。

再算生成器损失。若 \(d^r=1.2,d^f=.3\)：

```text
L_G = log(1+exp(1.2−.3))
    = log(1+exp(.9))
    ≈ 1.241
```

student 改好后 \(d^f\) 升到 1.0：

```text
L_G = log(1+exp(.2)) ≈ .798
```

损失下降，说明 fake 的相机一致性分数追近 real。自检：\(d^f=d^r\) 时 \(L_G=\log 2\approx.693\)，相对差为 0。

## 边界

“低频 = 相机”是有针对性的工程代理，不是定理。高噪声、跨层差与 stride conv 共同压纹理，但也可能保留与物体大运动相关的低频变化。论文没有单独消融这项损失，也没公开高噪声范围、层号、卷积配置和权重。

## 链接

- [[wonder-video-world-model]] · 提出这项控制正则
- [[dmd-distillation]] · 主分布匹配损失
- [[dmd2]] · 对照：DMD2 的 GAN 更偏高频真实感
- [[gradient-backprop]] · 生成器与判别器怎样收到相反目标
