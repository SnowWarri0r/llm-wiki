---
name: gpu-cluster-scheduling
type: concept
sources: [krea-2]
updated: 2026-07-16
---

# GPU 集群调度 · 为什么 128 卡任务不能先给 120 卡

## 一句话
分布式训练要整组资源一起到位；只启动一半，已经拿到卡的进程也只能空等。

## Kubernetes、Kueue 和 gang scheduling 各管哪一层

- **Kubernetes scheduler** 决定单个 Pod 放到哪台节点。
- **Kueue** 先看队列、优先级和配额，决定整个 Workload 有没有资格入场。
- **Gang scheduling** 要求同一任务需要的 Pod 成组启动；凑不齐就都不启动。

## 数字例子

一个训练任务有 16 个 Pod，每个 Pod 要 8 张 GPU，总共 128 张：

```text
集群只剩 120 张卡 = 只能放 15 个 Pod
没有 gang scheduling：15 个 Pod 已占 120 卡，却一直等第 16 个
有 gang scheduling：16 个都先排队，等 128 卡齐了再一起启动
```

后者看似让任务晚一点开跑，却避免 120 张卡在等待中白烧。

## Virtual Kubelet 和 HPA

Virtual Kubelet 把外部算力伪装成 Kubernetes 节点：上层仍提交普通 Pod，它把规格翻译给外部供应商。HPA 根据负载增减 Pod。Krea 的适配层不自己重试失败实例，而是把 Pod 标成失败，让 Kubernetes / HPA 沿原有控制逻辑补一个新的。

## 链接

- [[krea-2]] · Kueue、配额借还、推理外溢与 Virtual Kubelet
- [[training-checkpointing-and-recovery]] · 调度解决“资源何时到位”，checkpoint 解决“任务坏了丢多少”
