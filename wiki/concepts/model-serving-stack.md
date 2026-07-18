---
name: model-serving-stack
type: concept
sources: [cosmos-3]
updated: 2026-07-16
---

# 模型服务栈 · PyTorch、TensorRT、vLLM 和 vLLM-Omni 各管什么

## 一句话
模型服务不是换一个“更快框架”就结束：运行时、请求调度、跨卡并行、缓存和解码各管一层。

## 把名字放回各自位置

- **PyTorch**：最接近训练代码的参考运行时，方便改模型、查数值。
- **TensorRT**：为 NVIDIA GPU 做图优化、算子选择与低精度执行，更偏稳定部署。
- **vLLM**：先以大语言模型服务见长，核心工作包括请求批处理、显存管理和高吞吐调度。
- **vLLM-Omni**：把调度扩到扩散与多模态模型，加入 Cache-DiT、CFG parallel、VAE patch parallel 等生成路径。
- **CPU offload**：暂时不用的权重或状态挪到 CPU 内存，省 GPU 显存，但会增加 PCIe 搬运。
- **FP8**：用 8 位浮点表示部分权重或激活，省显存和带宽；必须验证质量是否可接受。

## 数字例子

一次 50 步 CFG 视频生成，普通做法每步各跑一次有条件和无条件 denoiser：

```text
Generator 前向次数 = 50 × 2 = 100 次
Reasoner 条件编码若每步重算 = 50 次
把 Reasoner 输出缓存后 = 1 次
```

CFG parallel 用两张 GPU 同时算两路，可以缩短每步等待时间，但总前向次数仍是 100，算力没有凭空消失。Cache-DiT 则尝试复用相邻去噪步里变化不大的中间结果，收益取决于缓存命中与误差容忍。

## latency 和 throughput

单请求延迟问“这一个视频多久出”；吞吐问“整个集群每小时出多少视频”。增大 batch 常能提高吞吐，却可能让单个请求排队更久。部署调优必须先说清目标。

## 链接

- [[cosmos-3]] · Reasoner / Generator 分层服务、CFG parallel 与 vLLM-Omni
- [[gpu-kernels-and-compilation]] · CUDA Graph、编译和底层 kernel
- [[distributed-training-parallelism]] · HSDP / CP 在推理中也能复用
