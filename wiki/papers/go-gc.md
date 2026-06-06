---
name: go-gc
type: paper
source: https://go.dev/blog/greenteagc
upstream: https://go.dev/doc/go1.26
ingested: 2026-06-01
authors: [Go Runtime Team, Michael Knyszek]
year: 2026
---

# Go GC · 从三色 mark-sweep 到 Green Tea

> 系统/runtime 深度页（非 ML），跟着自己的 Go 后端工作做的。bespoke HTML 在 `docs/papers/go-gc.html`，deep 蓝 accent。

## 一句话
Go 的 GC 是**三色并发 mark-sweep + write barrier**，靠 GOGC/GOMEMLIMIT 控触发节奏；Go 1.26 默认开的 **Green Tea** 把 mark 的工作单元从"对象"换成"8 KiB page"，把指针追逐的随机访存改成按页顺序扫，GC-heavy 程序 GC overhead 降 10–40%。

## 它要解决的痛点
传统 mark 阶段是 **graph flood**：从灰色队列取一个对象 → 扫它的指针 → 把引用对象染灰 → 再取下一个。本质是**指针追逐**，在堆里乱跳，cache/TLB miss 满天飞 —— 官方测出 mark 时间里**至少 35% 纯粹 stall 在等堆内存**。堆越大、对象越小越碎越严重，加核也救不了（核都卡在等内存）。mark 从 CPU-bound 退化成 memory-latency-bound。

## 核心贡献
- **三色不变式 + 并发标记**：黑对象不能直接指白对象；mark 跟 mutator 并发跑，不长时间 STW。
- **write barrier**：并发标记时，mutator 改指针可能制造"黑→白"漏标；barrier 在写指针时顺手把对象染灰救回，保证不误删活对象。
- **GOGC / GOMEMLIMIT pacing**：GOGC=100 → 堆涨到 2× live 触发 GC；GOMEMLIMIT 设硬上限，逼近时提前触发（代价 GC CPU 上升）。
- **Green Tea（1.26 默认）**：工作单元从对象换成 **8 KiB page**；每页用 seen/scanned 两个 bitmap，page 在 FIFO 队列里攒一批 seen 对象，再按地址顺序一次扫完 → 随机访存变顺序访存。work list 更小、竞争更少。现代 CPU（Ice Lake / Zen 4+）用 **AVX-512 GFNI（`VGF2P8AFFINEQB`）** 把整页 metadata 装进 2 个 512-bit 寄存器，几条直线指令扫一页，再多省 ~10%。

## 关键概念
三色标记 / mark-sweep / STW / write barrier / mutator / GC roots / GOGC / GOMEMLIMIT / GC pacing / size class（span）/ page（8 KiB）/ graph flood / Green Tea / seen-scanned bitmap / AVX-512 GFNI。术语表收在 bespoke 页。

## 我的批注 / 疑问
- Green Tea 是**纯 locality 优化**，语义不变、不用改代码；可观察到的就是 GC CPU% 掉。JSON 重、小对象 churn 大的 Go 服务受益最大，升 1.26 后值得用 `runtime/metrics` + pprof 量前后 GC CPU。
- 反直觉的发现：官方说**一次只扫一页 2% 的对象就已经比 graph flood 快** —— locality 收益比"批量"本身还关键。
- 关 GC：`GOEXPERIMENT=nogreenteagc`（build 时），出问题官方让提 issue。
- 类比锚点：graph flood = 在城市街道乱开（看不见下个路口）；Green Tea = 上高速顺着扫（CPU 能预取）。
