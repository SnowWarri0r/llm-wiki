---
name: large-scale-data-pipelines
type: concept
sources: [krea-2, cosmos-3]
updated: 2026-07-16
---

# 大规模数据管线 · 素材、元数据和任务进度怎么不打架

## 一句话
大文件放数据层，小状态放元数据层；worker 靠租约或行锁领活，处理成功后再原子提交。

## 先分三层

1. **媒体数据层**：图像、视频、音频和 checkpoint 很大，放对象存储或分布式文件系统。
2. **元数据层**：保存文件引用、caption、embedding、质量分、处理状态。Parquet / Lance 适合批量扫描，PostgreSQL 适合并发更新与事务。
3. **执行层**：Ray actor、Kubernetes worker 或普通进程领取任务，跑解码、模型标注与写回。

Lance 是带向量能力的列式数据格式；Parquet 也是列式格式，但通常不直接承担高频任务状态更新。Ray actor 是带状态的远程 worker。背压则是下游忙时让上游减速，避免下载队列把内存撑爆。

## 数字例子

有 12 行待处理任务和 3 个 worker，每个一次领 4 行：

```text
worker A 锁住 1–4
worker B 用 SKIP LOCKED 跳过 1–4，领 5–8
worker C 再跳过前 8 行，领 9–12
```

三者不会重复处理。若 B 在第 7 行崩溃，数据库事务回滚或租约超时后，5–8 可以重新领取。若每处理完一条就直接宣布整批成功，7、8 就可能永远丢失；所以管线通常分段记进度，最后再原子提交整个分片。

## Krea 2 和 Cosmos 3 的两种实现

- **Krea 2**：krablet 用 PostgreSQL 分片保存状态，`FOR UPDATE SKIP LOCKED` 把表直接当工作队列；funnel 把大量小更新合成批量写入。
- **Cosmos 3**：SILA 用 Lance 宽表统一媒体元数据和 embedding；fragment lease + heartbeat 判断 worker 是否还活着，分段 checkpoint，最后 atomic commit。

它们不是谁替代谁：PostgreSQL 强在事务与并发更新，Lance 强在大规模列扫描和向量数据。选择取决于读写模式。

## 链接

- [[krea-2]] · krablet、PostgreSQL、Parquet、Ceph / WEKA
- [[cosmos-3]] · SILA、Lance、Ray actor、租约与原子提交
- [[training-checkpointing-and-recovery]] · 训练进度也遵循“先记录，再恢复”
