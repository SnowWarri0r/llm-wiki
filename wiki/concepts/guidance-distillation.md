---
name: guidance-distillation
type: concept
sources: [flux-1, krea-2]
updated: 2026-06-17
---

# 引导蒸馏 · guidance distillation · 把 CFG 的两遍前向压成一遍

## 一句话
把 [[classifier-free-guidance]](CFG)那个"每步算两遍再外推"的过程**蒸进模型**:让模型把**引导强度当输入**,**一遍前向**就直接吐出"已经引导好"的结果 → 省掉每步那一半算力,质量不掉。

## 直觉 · 别每步都算两遍

[[classifier-free-guidance]] 提质量靠"两遍":一遍带 prompt 出 `v_cond`、一遍空 prompt 出 `v_uncond`,再按引导强度 `w` 外推 `v = v_uncond + w·(v_cond − v_uncond)`。问题:**每一步采样都要前向两次** → 推理算力直接 2×。

引导蒸馏的想法:**这个外推结果是确定的,能不能让模型直接学会输出它?** 训练时:
- **老师**:跑完整 CFG(两遍 + 外推),在各种 `w` 下生成"标准答案"。
- **学生**:输入里**多塞一个引导强度 `w`**,被训成**一遍前向**就复现老师那个带 CFG 的结果。

蒸完之后,学生模型把 `w` 当普通条件吃进去,一次前向出图——**两遍变一遍**。[[flux-1]] 的 dev 版就是这么训的(老师是闭源的 pro)。

类比:CFG 像每道菜都"做一份正常的、做一份不放料的,再按比例兑";引导蒸馏是**直接训一个厨师,你告诉他要多大味儿(w),他一锅就给你那个味儿**,不用做两份再兑。

## 注意:跟"步数蒸馏"是两回事(正交)
- **引导蒸馏**:省的是**每一步的 2× 前向**(两遍→一遍)。步数不变。
- **步数蒸馏**([[dmd-distillation]] 那类):省的是**采样步数**(几十步→4 步)。每步几遍不管。
- 两者**正交**,可叠加:[[flux-1]] 的 schnell = dev(引导蒸馏)再 + 步数蒸馏。

dev 里那个 `guidance` 参数是**喂进模型的输入**,跟标准 CFG 的外推系数 `w` 不是一回事(虽然都叫引导强度)。

## 怎么做的
```
# 老师：完整 CFG（两遍）
v* = uncond + w·(cond − uncond)
# 学生：把 w 当输入，一遍前向逼近 v*
minimize  ‖ model(z_t, t, prompt, w) − v* ‖
# 推理时：一次前向，无需再跑无条件支
```

## 代码出处 / 来源
- [[flux-1]] · FLUX.1-dev 用引导蒸馏(老师=pro),一遍前向出 CFG 质量
- 思想源:CFG distillation(Meng et al. 2023,把 CFG 蒸进单模型)

## 链接
- [[classifier-free-guidance]] · 被蒸的那个"两遍外推"
- [[flux-1]] · dev 的训练方式
- [[dmd-distillation]] · 正交的另一种蒸馏(省步数)
- [[flow-matching]] · 引导作用在速度场上
