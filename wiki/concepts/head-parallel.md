---
name: head-parallel
type: concept
sources: [magi-2]
updated: 2026-11-24
---

# Head Parallel · 按头分片交换激活，通信形状开训前就定死

## 一句话

多头 MoE 里每张卡负责几个固定的头：跨卡只搬"这几个头的那段维度"，路由的不规则全关在卡内。

## 直觉

标准专家并行像快递按收件人分拣：每个 token 被复制 k 份、寄到 k 个专家所在的卡，哪张卡收多少件取决于今天大家选了谁——有的卡爆仓、有的卡闲着，全队等最慢的那张；接收缓冲大小每步都不一样，还得 CPU 先同步一下数量才能分配。

Head Parallel 改成按工位分拣：第 1–2 个头永远归 0 号卡、第 3–4 个头永远归 1 号卡……每个 token 只是把对应维度那一截交过去，每张卡收到的形状永远是"token 数 × 自己负责的头数 × 头维度"。路由仍然随数据变，但只在卡内部决定"这截向量进哪个本地专家"。

## 怎么做的

```
x_heads = x.view(N, M, head_dim)
x_heads = head_dispatch_over_ib(x_heads)   # 按头归属交换，形状固定
routes  = route_per_local_head(x_heads)    # 卡内路由，随数据变
y_heads = grouped_expert_ffn(x_heads, routes)
y = head_combine_over_ib(y_heads).view(N, M * head_dim)
```

通信量对比（忽略常数和回程）：

\[ C_{\text{standard}}\propto N\,k\,H,\qquad C_{\text{head}}\propto N\,M\,H_{\mathrm{head}}=N\,H \]

- \(N\)：序列 token 数；\(k\)：每 token 激活专家数；\(H\)：隐藏维。
- \(M\)：头数；\(H_{\mathrm{head}}\)：每头维度，\(H=M\,H_{\mathrm{head}}\)。

**分层（Hierarchical）**：一个头的全部 256 个专家放不进一张卡。MAGI-2 把两件事交给两层网络——跨节点 InfiniBand 只做上面那种固定形状的头交换；节点内 NVLink 用 ZeRO/FSDP 把专家权重、梯度、优化器状态全分片，算到哪层再 gather 出来，算完 reshard。

## 数字例子

MAGI-2 preview 一条 10 秒视频：57,344 个视频 token，H=3,072，BF16 每数 2 字节。

- 如果整 token 按 top-6 寄出去：\(57{,}344\times6\times3{,}072\times2\approx2.11\) GB（单程、单层）。
- 按头分片：\(57{,}344\times3{,}072\times2\approx0.35\) GB，正好少 k=6 倍。

更要紧的是形状。8 张卡、12 个头：12 除不尽 8，推理代码把头补到 16 个，每卡 2 个——0–5 号卡持有真头，6、7 号卡持有补出来的空头，在 MoE 层收发照做但算的是零。每张卡收到的永远是 \(N\times2\times256\)，可以预先分配；代价是推理时 MoE 层 8 张卡里有 2 张空转。

## 链接

- [[multi-head-latent-moe]] · 它服务的架构
- [[distributed-training-parallelism]] · ZeRO/FSDP、上下文并行等基础切法
- [[moe]] · 标准专家并行的通信问题
- [[magi-2]] · 114B 视频 MoE 的实际做法
