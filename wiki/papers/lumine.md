---
name: lumine
type: paper
source: https://arxiv.org/abs/2511.08892
ingested: 2026-06-16
authors: [Tan et al., ByteDance Seed]
year: 2025
---

# Lumine · 从像素直接玩 3D 开放世界的通用 agent

## 一句话
一个 VLM(Qwen2-VL-7B)当大脑,直接吃游戏画面像素、吐键盘鼠标操作,端到端打通《原神》5 小时蒙德主线,零样本迁移《鸣潮》《崩铁》。三招:动作即文本 token、看一眼预测多步([[action-chunking]])、该想才想(hybrid thinking)。**纯模仿人类录像,零 RL**。

## 它要解决的痛点
3D 开放世界任务长达数小时、要探索+战斗+解谜+对话+实时键鼠操作。纯 RL 在这里失灵(reward 太稀疏、状态空间太大),所以走 [[imitation-learning]] 抄人类作业。

## 核心贡献
- **动作即文本**:不加专门动作头,键鼠操作编码成 token 串(鼠标位移 [-1000,1000] + 分号隔开的 33ms 按键片),VLM 自回归吐出来 → 复用语言/视觉先验。
- **[[action-chunking]]**:5Hz 看、30Hz 动 —— 一次推理预测 6 个动作块(每 33ms),慢感知喂快控制。
- **Hybrid thinking**:只在关键转折点触发 `<|thought|>` 推理,平时反射出招;卡 100 步强制思考自救。
- **纯模仿三阶段**:2424h 人类原神录像 —— 预训练 1731h 行为克隆 → 指令跟随 200h(小 Qwen2-VL-2B 分类器 + GPT-4.1 自动打标) → 推理 15h(人工标内心独白)。零 RL。
- **记忆 = context**:滑窗 20 帧图像-动作对 + 长期保留推理([[memory-stream]] 思路)。
- **25.3× 延迟优化**:流式输出 + 投机解码 + KV-cache 复用(StreamingLLM) + [[quantization]] W8A8(SmoothQuant) + 4 卡张量并行;无推理一帧 ~114ms。

## 关键概念 → 概念页
- [[action-chunking]] · 看慢动快,一次预测多步
- [[imitation-learning]] · 替代 RL 的纯模仿三阶段
- [[quantization]] · W8A8 让推理塞进 200ms
- [[qwen3-vl]] · VLM 当大脑(用 Qwen2-VL)
- [[memory-stream]] · context 当记忆

## 我的批注 / 疑问
- 一句话记牢:**把游戏操作翻译成"语言",让 VLM 看图说"话"(话=键鼠),抄人类录像学会,该想才想**。跟纯 RL 的 Mario 是两条路:RL 从零试错练手感,Lumine 站 VLM 先验上抄作业。
- 来源:abstract + ar5iv 全文镜像;机制(Qwen2-VL-7B/动作即文本/6块chunk/hybrid thinking/2424h三阶段/W8A8)已确证。
- 待查:迁移到鸣潮/崩铁时哪些是真零样本、哪些靠通用先验;hybrid thinking 触发的精确判据;chunk 长度对反应灵敏度的实测影响。
