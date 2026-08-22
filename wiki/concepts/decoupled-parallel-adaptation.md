---
name: decoupled-parallel-adaptation
type: concept
sources: [avatar-forever]
updated: 2026-08-19
---

# 解耦并行适配 · 两门课分开学，部署时再合卷

## 一句话

从同一组基础权重 \(\theta_0\) 出发，用两条互不依赖的训练支路分别学习“少步生成质量”和“长时间抗漂移”，最后把两份参数增量相加。

## Avatar-Forever 的具体形式


\[
\theta^\star=\theta_0+\Delta\theta_{\mathrm{DMD}}+\Delta\theta_{\mathrm{RRT}}.
\]

- \(\Delta\theta_{\mathrm{DMD}}\)：全参数更新，把多步 LTX-2.3 蒸成 4 步；
- \(\Delta\theta_{\mathrm{RRT}}\)：rank 128 的 video-side LoRA，只补长 rollout 时的恢复能力；
- 两条支路都从同一个 \(\theta_0\) 起步，所以更新拥有共同坐标系，论文直接组合后部署。

## 为什么不是先 DMD，再在 DMD 权重上训 RRT

串行训练会让第二阶段继承第一阶段的所有分布偏移；第一阶段一变，后面都要重跑，也难判断最终退化来自哪一段。并行适配让两份目标可以独立调试和扩展。

## 重要边界

“参数增量可以相加”不是普适定理。两条支路如果更新幅度过大、修改同一功能方向，仍可能互相干扰。Avatar-Forever 的设计把稳定性支路限制成 LoRA，并用消融证明组合优于 DMD-only 和 FM-only；论文没有给出不同合并系数或冲突度分析。

## 链接

- [[avatar-forever]] · 原始设计与消融
- [[lora]] · 低秩增量为什么便于合并
- [[dmd-distillation]] · 效率支路
- [[recovery-oriented-rollout-training]] · 稳定性支路
