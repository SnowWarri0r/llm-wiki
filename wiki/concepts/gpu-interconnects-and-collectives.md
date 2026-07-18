---
name: gpu-interconnects-and-collectives
type: concept
sources: [krea-2, cosmos-3]
updated: 2026-07-16
---

# GPU 互联与集合通信 · 多卡训练为什么常卡在“搬”而不是“算”

## 一句话
NVLink、PCIe、InfiniBand 是路；NCCL 是组织车队的通信库；all-gather、reduce-scatter 是具体搬法。

## 四个名字别混

- **PCIe**：CPU、GPU 和设备间的通用总线，覆盖广，GPU 间带宽通常低于 NVLink。
- **NVLink**：同机或特定机柜内的高速 GPU 互联。
- **InfiniBand**：跨服务器的低延迟高速网络；整片交换网络称 fabric。
- **NCCL**：NVIDIA 的 GPU 集合通信库，会在可用的 NVLink、PCIe、InfiniBand 上执行 all-reduce 等操作。

IPoIB 是“让普通 IP 流量跑在 InfiniBand 上”。存储也走这条路时，可能和 GPU 集合通信争同一张网络。

## 数字例子

4 张 GPU 各持有一份参数：

```text
GPU0:[A]  GPU1:[B]  GPU2:[C]  GPU3:[D]

all-gather 后，每张卡都有 [A,B,C,D]

若每张卡各算一份梯度 g0,g1,g2,g3：
all-reduce 后，每张卡都拿到 g0+g1+g2+g3

reduce-scatter 则把总和后的结果再切四份，
每张卡只保留自己负责的 1/4。
```

模型层数越多，FSDP 每层触发 all-gather / reduce-scatter 的次数越多。Krea 2 偏好“更宽、层数更少”，其中一个系统理由就是减少通信轮次和 NCCL 出错机会。

## 指标怎么看

PCIe replay、NVLink CRC / recovery、InfiniBand 端口错误都在回答“链路有没有重传或纠错”。GPU_UTIL 变成 0% 往往只是通信已经卡死后的结果，不是根因。

## 链接

- [[krea-2]] · NCCL、PCIe、NVLink、InfiniBand 与 IPoIB 故障经验
- [[cosmos-3]] · HSDP / CP 的通信底座
- [[distributed-training-parallelism]] · 为什么训练会产生这些集合通信
