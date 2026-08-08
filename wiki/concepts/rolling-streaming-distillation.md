---
name: rolling-streaming-distillation
type: concept
sources: [wan-streamer-v01]
updated: 2026-08-06
---

# 滚动式流媒体蒸馏 · 让少步学生练习读取自己的历史

## 一句话

教师用更多去噪步给方向，学生用更少步连续生成多段，并在自己已经出现误差的历史上继续练。

## 为什么逐段蒸馏还不够

若每次训练都给学生真实的干净历史，它只会处理“完美过去”。部署时前一段却是学生自己生成的，轻微色偏、口型误差或姿态漂移都会进入下一段，形成训练—推理分布差距。

## 一个三段例子

假设学生每段都把脸部位置向右偏 0.1：

```text
只做单段训练：每次都从真实位置 0 开始，只看见误差 0.1
连续 rollout：第 1 段 0.1 → 第 2 段 0.2 → 第 3 段 0.3
```

滚动训练让学生真的看到 0.1、0.2 这类自己制造的历史，再由教师或分布匹配信号教它往回修。这样优化的不是孤立一帧，而是整条长期轨迹。

## Wan-Streamer 公开到哪

v0.1 说明强教师带 CFG 和更多 flow-matching solver 步，学生用 self-forcing 与 distribution matching 做 rolling distillation。论文没有给完整损失、教师与学生步数、CFG scale、rollout 长度或误差权重，因此不能据此写出一条“官方蒸馏公式”。

## 链接

- [[wan-streamer-v01]] · 三阶段训练和长会话的落点
- [[teacher-forcing-video-diffusion]] · 为什么真实历史会制造 exposure bias
- [[classifier-free-guidance]] · 教师额外使用的条件引导
- [[dmd-distillation]] · distribution matching 的基础思路
