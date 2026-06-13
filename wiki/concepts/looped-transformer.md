---
name: looped-transformer
type: concept
sources: [elt]
updated: 2026-06-10
---

# Looped Transformer · 把同一个 block 循环套用

## 一句话
不堆很多**不同**的层，而是把**同一个** transformer block 反复套 L 圈 —— 在深度上共享权重，把"算多深"和"用多少参数"解耦。

## 直觉 · 深度上的 RNN / 工程上的 for 循环

标准 transformer 是 N 个**各不相同**的层叠起来，参数 = N × 每层。但很多任务（迭代算法、多跳推理）的本质是"**把同一步操作重复做很多遍**"——这种结构用"很多不同层"去拟合是浪费。

Looped transformer 的办法：留**一个**（或一小组 N 个）block，把它**循环套 L 圈**。

```
标准:  x → L1 → L2 → L3 → … → L_D    （D 个不同层，参数随 D 涨）
循环:  x → [block] → [block] → … → [block]   （同一个 block 套 L 圈）
            ↑___________循环 L 次___________↑
       有效深度 = N×L，但参数只看 N
```

类比：标准 transformer 是把一段代码**复制粘贴 100 遍**；looped 是写一个 **for 循环跑 100 次**。同样的"计算深度"，代码（参数）少一个数量级。这跟 [[convolution]] 的权重共享是同一招，只是共享的轴从"空间位置"换成了"深度/迭代"。

## 怎么做的 · N 层 block × L 圈

- **N**：循环体里有几个 unique 层（决定参数量）。
- **L**：循环几圈（决定计算量 / 有效深度）。
- **有效深度 = N × L**。比如 8N×4L = 8 个 unique 层套 4 圈 = 等效 32 层深，但只存 8 层的参数。
- 关键红利：**L 可以在推理时调**——多套几圈 = 多算 = 通常更准。算力变成一个"旋钮"，不必重训。

## 谱系 · 从推理到视觉生成
- **Universal Transformer**（2018）：始祖，同一层反复套 + ACT 自适应停。
- **Looped Transformers as Programmable Computers**（2023）：理论，13 层循环能模拟一台小型指令集计算机、跑迭代算法。
- **Looped for Length Generalization**（2024）：自适应步数让算术/算法任务能泛化到没见过的长度。
- **Recurrent-Depth 潜在推理**（2025，Geiping 等）：推理时多循环几圈、在**隐空间**里"想"，当成 CoT 的替代、scale test-time compute。
- **ELT**（2026）：把循环带进**视觉生成**（DiT），一次训练出一族深度（[[elastic-inference]]），4× 参数缩减。详见 [[elt]]。

## 为什么 work
- **很多问题要的是"有效深度"不是参数量**：迭代算法、多跳推理天生是"重复同一步"，循环正好对上这个归纳偏置。
- **算力可在推理时加**：标准网络深度训死了，循环网络能"想久一点"——这是它跟 test-time compute / reasoning 那条线的接口。

## 代码出处
- ELT：arXiv 2604.09168（视觉生成的循环 DiT）
- Universal Transformer arXiv 1807.03819 / Programmable Computers arXiv 2301.13196

## 链接
- [[convolution]] · 同样是权重共享，轴是空间；这里轴是深度
- [[transformer-architecture]] · 被循环的就是它的标准 block
- [[diffusion-transformer]] · ELT 循环的是 DiT
- [[elastic-inference]] · 循环圈数当算力旋钮，一族深度
- [[elt]] · 把循环带进视觉生成的论文
