---
name: vfm-discriminator
type: concept
sources: [senseflow]
updated: 2026-07-24
---

# VFM 判别器 · 冻结视觉骨干，只训练轻量真假头

## 一句话

VFM 判别器把 DINOv2 这类视觉基础模型当作冻结的“特征显微镜”，再训练小型判别头判断生成图是否逼真、是否符合文字以及是否接近真实参考图。

## 为什么不用从零训练判别器

普通 GAN 判别器要一边学习“图片里有什么”，一边学习“哪里像假图”。大模型蒸馏时，生成器变化快、图像语义复杂，从零训练的判别器可能先学会低级纹理捷径，给不出稳定的语义反馈。

SenseFlow 把职责拆开：

- 冻结 DINOv2：提取多层空间视觉特征；
- 冻结 CLIP 文本编码器：把 prompt 变成文字条件；
- 真实参考图也过 DINOv2：提供真实图特征；
- 只训练每一层后面的轻量卷积判别头。

## 数据流

\[
D(x,c,r)=h\!\left(f_{\mathrm{VFM}}(x),c,r\right)
\]

- `x`：待判断的生成图或真实图；
- `f_VFM(x)`：冻结 DINOv2 提取的多层特征；
- `c=f_CLIP(text)`：冻结 CLIP 生成的文字条件；
- `r=f_VFM(x_ref)`：真实参考图经过同一 DINOv2 得到的特征；
- `h`：可训练的判别头；
- `D`：输出的真假 logit；数值越高越偏向“真实且匹配”。

SenseFlow v2 附录专门更正：参考图特征 `r` 来自 DINOv2，不是正文早先写的 CLIP 图像编码器。

## Hinge loss 怎么工作

判别器目标：

\[
\mathcal L_D
=\mathbb E_{\mathrm{real}}\!\left[\max(0,1-D(x_{\mathrm{real}}))\right]
+\mathbb E_{\mathrm{fake}}\!\left[\max(0,1+D(x_{\mathrm{fake}}))\right].
\]

真实图希望 `D≥1`，假图希望 `D≤-1`。已经越过安全边界的样本损失为 0，不再继续把 logit 推到无穷大。

若 `D(real)=.4、D(fake)=-.2`：

```text
真实项 = max(0,1-.4)  = .6
假图项 = max(0,1-.2)  = .8
总损失 = 1.4
```

生成器则最小化 `-D(x_fake)`，也就是努力把假图 logit 调高。

## SenseFlow 的时间权重

带噪图在高噪声时刻不可靠，GAN 信号不能压过 DMD。SenseFlow 使用：

\[
\omega(t)=(1-\sigma_t)^2=\alpha_t^2,\qquad
\mathcal L_G^{\mathrm{adv}}=-\omega(t)\,\mathbb E[D(x_{\mathrm{fake}})].
\]

若 `σ=.8`，权重只有 `.04`；若 `σ=.2`，权重为 `.64`。越接近干净图，判别器越值得信；越接近纯噪声，主要依靠 DMD 方向。

## 工程边界

官方 SD 3.5 Large 实现使用 DINOv2 ViT-L/14 的 7 层特征和可微颜色、平移、cutout 增强，只优化判别头。更大的 VFM 并不单调更好：论文附录中 ViT-B 的 FID-T 最好，ViT-S 的 CLIP / ImageReward 更高，ViT-L 只在部分人偏好指标略强。

## 链接

- [[senseflow]] · VFM 判别器与 DMD、IDA、ISG 的组合
- [[dmd2]] · DMD2 原来的扩散骨干判别头
- [[dino]] · DINO 系列如何用自监督学视觉表征
- [[hinge-loss]] · margin 与生成器/判别器两个方向
