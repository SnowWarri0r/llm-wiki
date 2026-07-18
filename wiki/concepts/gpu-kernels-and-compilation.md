---
name: gpu-kernels-and-compilation
type: concept
sources: [krea-2, cosmos-3]
updated: 2026-07-16
---

# GPU Kernel 与编译 · 为什么同一个公式能快很多

## 一句话
Kernel 是 GPU 一次执行的一小段程序；编译优化的目标，是少启动、少搬数据、选对专用实现。

## 从 PyTorch 表达式到 GPU

模型代码写的是 `归一化 → 乘法 → 激活 → attention`。GPU 实际执行的却是一串 kernel。每启动一个 kernel，CPU 都要下发任务；kernel 之间还可能把中间结果写回显存再读出。

- `torch.compile` 会观察整段计算图，融合能合并的操作，并为实际形状选择实现。
- CUDA Graph 把一串已经稳定的 GPU 启动顺序录下来，后续直接整段重放，减少 CPU 逐个发令。
- AOT 是提前编译；JIT 是运行到某种形状时再编译。形状很多时，AOT 缓存能避免每台机器重复“热身”。

## 数字例子

假设三个小操作各算 10 微秒，每次 kernel 启动还要 8 微秒：

```text
三个独立 kernel：3 × (10 + 8) = 54 微秒
融合成一个 kernel：30 + 8 = 38 微秒
少掉：54 - 38 = 16 微秒，约 29.6%
```

真实收益还取决于内存搬运、形状和硬件，不能把这个玩具比例当成报告数字。Cosmos 3 实测 `torch.compile` 给 Nano Generator 带来约 41% 训练吞吐提升；视频 tokenizer 编译后编码延迟降低约 52%。

## cuDNN、FlashAttention、FlexAttention、NATTEN 是什么关系

它们都是“底层怎么执行”的选择，不是四套模型：

- **cuDNN**：NVIDIA 的通用深度学习算子库。
- **FlashAttention**：针对标准密集 attention，重点减少 HBM 搬运。
- **FlexAttention**：更容易表达特殊 mask，但通用性可能带来额外开销。
- **NATTEN**：擅长局部 / 邻域 attention；Cosmos 3 在 Blackwell 上把它作为后端之一。

## 链接

- [[krea-2]] · torch.compile、cuDNN、FlexAttention 与 FlashAttention 3
- [[cosmos-3]] · 两路变长 kernel、AOT 缓存与 CUDA Graph
- [[flash-attention]] · FlashAttention 为什么省搬运
- [[batch-invariant-kernel]] · kernel 选择还可能影响逐位可复现性
