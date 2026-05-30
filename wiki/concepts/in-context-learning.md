---
name: in-context-learning
type: concept
sources: [gpt-3, gpt-2]
updated: 2026-05-21
---

# In-Context Learning · ICL · 在 prompt 里现学

## 一句话
**模型权重一个不动**，在 prompt 里给几个 (input, output) 示例，模型就能从这些示例里"现学"任务规则，然后在新输入上应用。

## 直觉
传统机器学习：要让模型做新任务 → 收集标注数据 → 训练（更新权重）→ 部署。整个循环数周到数月。

In-context learning：要让模型做新任务 → 在 prompt 里给几个例子 → 直接问。整个循环 5 分钟。

类比：传统 ML 是"上岗培训"（改 weights = 改大脑），ICL 是"<strong>给你一份范例文档让你照着办</strong>"（不改大脑，只看示例推断模式）。

**关键洞察**：GPT-3 在预训练时见过<strong>无数次</strong>"几个示例 + 新任务"格式的文本（百科 / 教程 / 翻译对照表 / 问答论坛），它学会了一个通用元能力：**遇到这种"示例 + ?"格式，要从示例里抽规则套到 ?上**。

## 三档形态
**Zero-shot**（GPT-2 已经能做）：
```
Translate to French: "Hello, world."
French:
```
（只描述任务，没给例子）

**One-shot**（GPT-3 提出）：
```
Translate to French.

English: Hello.
French: Bonjour.

English: Hello, world.
French:
```
（给 1 个例子）

**Few-shot**（GPT-3 论文重点）：
```
Translate to French.

English: Hello.
French: Bonjour.

English: Goodbye.
French: Au revoir.

English: Thank you.
French: Merci.

English: Hello, world.
French:
```
（给 K 个例子，K 通常 3-30）

GPT-3 论文 Fig 1.2 用 SuperGLUE 类任务展示：从 zero-shot → few-shot，准确度稳步提升。这是<strong>不改 weights 的"学习"</strong>。

## 为什么不改权重也能"学"
这是 open question，至今没完全理解。主流假设：
1. **Pattern matching**：模型在 attention 里识别 prompt 里的 (x, y) 对，在新 x 出现时去 attend 已有 (x, y) 推断答案
2. **Implicit gradient descent**：attention layer 内部相当于在做小规模的 in-weight optimization（"meta-learning"）。形式上有证明，工程上待验证
3. **Function approximation**：transformer 学到的不是"具体任务"，是"从示例里抽函数"的元能力 —— prompt 触发的是这个元能力的应用

无论哪种解释，<strong>实证现象</strong>都是：scale 上去后 ICL 能力浮现，prompt 里给例子能稳定提升性能。

## 它的局限
- **prompt 敏感**：同一任务用不同例子或者不同顺序，性能可能差 10-20 个点
- **长上下文成本高**：few-shot 把 prompt 撑得很长 → 推理算力变大
- **不可控**：模型经常输出格式不对、忽略部分示例
- **不及 finetune 极致 SOTA**：finetune 能学到更深的任务知识，ICL 只能学浅模式

但<strong>"够好 + 极快"赢了"最好 + 极慢"</strong> —— ICL 工程门槛低到 5 分钟出 demo，finetune 要工程一周。这是 LLM 时代的真正颠覆点。

## 演化线
- **GPT-1** · input transformations (用特殊 token + finetune)
- **GPT-2** · zero-shot prompting (不 finetune，自然语言 prompt)
- **GPT-3** · few-shot in-context learning (prompt 里给几个例子)
- **ChatGPT** · system + user + assistant chat template (角色化的 ICL)
- **Claude / GPT-4** · 长上下文 ICL + 工具使用 + reasoning

一条直接的演化线。ICL 是中间最关键的一步。

## 链接
- [[gpt-3]] · 提出论文
- [[gpt-2]] · zero-shot 前身
- [[input-transformations]] · 更早的祖先
- [[emergent-abilities]] · ICL 本身就是一个 emergent ability
- [[language-modeling-as-multitask]] · ICL 的理论解释
