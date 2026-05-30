---
name: gpt-3
type: paper
source: https://arxiv.org/abs/2005.14165
upstream: https://arxiv.org/abs/2005.14165
ingested: 2026-05-21
authors: Brown, Mann, Ryder, Subbiah ... Amodei (OpenAI · 31 作者) · NeurIPS 2020
---

# GPT-3 · Language Models are Few-Shot Learners

GPT-2 之后 1 年 4 个月。同样架构再放大 116 倍（1.5B → 175B），发现一件之前没人预见到的事：**模型大到这个程度后，在 prompt 里给几个例子（few-shot），它就能现学新任务 —— 不用 finetune**。这就是 in-context learning，整个 ChatGPT 时代由此开始。

## 一句话
**模型 scale 到 175B 后，prompt 里塞几个例子就能让模型现学任务 —— in-context learning 是 emergent ability**。GPT 系列从 "pretrain + finetune" 演化到 "pretrain + prompt"，finetune 阶段在前沿模型上从此退场。

## 它要解决的痛点
GPT-2 1.5B 已经展示 zero-shot 触发任务，但准确度不够：
- zero-shot 翻译 BLEU 5-10 分 vs finetune SOTA 30-40 分
- 多数 benchmark 离 SOTA finetune 模型还有显著距离
- prompt sensitive，工程上不可靠

OpenAI 押更大的注：**scale 继续推 100× 到 175B，外加在 prompt 里给几个示例（few-shot），看看会发生什么**。如果 GPT-2 的趋势延续，应该能接近甚至超过 finetune SOTA。

## 核心贡献
1. **架构基本不变** —— 同 decoder-only Transformer + causal LM。少数 efficiency 改动：[[sparse-attention]] · 部分层用 strided/local attention 替代 full attention
2. **Scale 推到 175B** —— 96 层 / 12288 dim / 96 head · 8 个 size 系列从 125M 到 175B 系统验证 scaling 行为
3. **In-context learning** —— [[in-context-learning]] · 同一个模型 + 不同 prompt 设计就能做不同任务：zero-shot / one-shot / few-shot
4. **Emergence** —— [[emergent-abilities]] · 算术 / 常识推理 / 三段论这些任务在小模型上 ≈ 0 分，到 13B+ 才突然跳起来。论文第一次系统记录这种"涌现"
5. **训练规模化** —— Common Crawl 过滤 + Books + Wikipedia + 自家清洗 = ~300B token。$4.6M 单次训练成本。"普通研究者训不动" 时代正式开始

## 关键概念
- [[in-context-learning]] · ICL · prompt 里给例子模型现学
- [[emergent-abilities]] · 小模型 ≈ 0 大模型突然能
- [[few-shot-learning]] · ICL 的具体形态之一
- [[sparse-attention]] · 部分层换成稀疏 attention 节省算力
- [[causal-language-model]] · 没变
- [[decoder-only-paradigm]] · 没变
- [[scaling-laws]] · GPT-3 是其经验验证

## 我的批注
- **GPT-3 的论文当时没引爆，是 2 年后 ChatGPT 引爆了它**。2020 年发布时大家觉得"挺大但好像没什么用"，因为 in-context learning 在工程上不可控（prompt 敏感、输出不稳定）。直到 2022 ChatGPT 把 GPT-3.5 + RLHF + chat template 包装成产品，普通用户才意识到这事的威力
- **Few-shot vs finetune 的判断**：GPT-3 自己也没全面赢 finetune SOTA（很多任务仍输）。但<strong>开发成本</strong>差异巨大：finetune 要标几千条 + 训练 + 部署 = 工程一周；few-shot 写几个例子塞 prompt = 5 分钟。<strong>"够好 + 极快"赢了"最好 + 极慢"</strong>，这是 LLM 时代的真正颠覆点
- **Emergence 这点很微妙**：论文用线性 x 轴看 capability 突变像神迹；后来 Anthropic 2023 "Are Emergent Abilities of Large Language Models a Mirage?" 提出，换成 log scale + 更合适的 metric，"涌现"会变成平滑曲线。但<strong>实践上确实有"小于这个 size 跑不动 / 大于这个 size 跑得动"的相变</strong>
- **In-context learning 怎么 work 至今没完全理解**。一个假设：attention 在 prompt 里看到 "(x, y) (x, y) (x, ?)" 这种模式后，相当于在 attention layer 内部做小规模 gradient descent。这是个还在被研究的开放问题
- **真正改变历史的不是 175B 这个数字，是 ICL 这个能力**。ChatGPT 的所有交互（system prompt / user / assistant）本质上都是 in-context learning。Claude / Llama / Qwen 全在这个范式里
- **跟 GPT-2 一样，paper 当时被低估**。GPT-2 当时被低估，因为 zero-shot 不准；GPT-3 被低估，因为 few-shot 仍不及 finetune SOTA。两次都<strong>看 benchmark 看不出 thesis 的重要性</strong>。trajectory 视角 > snapshot 视角

## 跟 wiki 里其他 paper 的关系
- [[gpt-1]] · 同 thesis 的起点
- [[gpt-2]] · 同 thesis 的中段，给了 scaling 趋势的实证
- [[bert]] · 完全被 GPT 路线挤出前沿，BERT 系退到 RAG embedding
- [[attention-is-all-you-need]] · 仍是它的 decoder
- [[resnet]] · 仍带残差连接，深度才训得动 96 层
- 后续：InstructGPT (2022) → ChatGPT (2022-11) → GPT-4 (2023-03)

## 历史定位
- 2018-06 GPT-1 · 117M · pretrain+finetune 范式
- 2018-10 BERT · 340M · encoder-only · 当年明星
- 2019-02 GPT-2 · 1.5B · zero-shot 浮现
- 2020-01 Scaling Laws · 经验公式
- 2020-06 **GPT-3** · 175B · in-context learning 浮现 · paper 当时被低估
- 2022-03 InstructGPT · GPT-3 + RLHF
- 2022-11 ChatGPT · GPT-3.5 + chat template · 产品化引爆全球
- 2023-03 GPT-4 · 多模态 + reasoning
- 2024+ · Claude / Llama / Qwen 等所有现代 LLM 都建立在 GPT-3 立的 ICL 范式上
