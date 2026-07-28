---
name: sana-video-2
type: paper
source: https://arxiv.org/abs/2607.21553
upstream: https://nvlabs.github.io/Sana/Video2/
code: https://github.com/NVlabs/Sana
ingested: 2026-07-28
authors: Junsong Chen, Jincheng Yu, Yitong Li, Shuchen Xue, Haozhe Liu, Jingyu Xin, Yuyang Zhao, Tian Ye, Zhangjie Wu, Zian Wang, Daquan Zhou, Ping Luo, Song Han, Enze Xie · NVIDIA · arXiv v1
year: 2026
---

# SANA-Video 2.0 · 用三层“速写”加一层“精查”生成长视频

长视频生成最贵的地方之一，是每层 softmax attention 都让所有视频 token 两两比较。视频变长、分辨率变高后，token 数量 \(N\) 上升，比较表从 \(N\times N\) 膨胀。纯线性注意力把全部 token 先压进固定大小的状态，成本接近 \(O(N)\)，却也可能把本来不同的时空关系揉在一起。

SANA-Video 2.0 没在两端二选一：连续三层用便宜的线性注意力，第四层用 softmax 做一次全局“精查”；再让 Block AttnRes 从更早的 8 层摘要里按 token 取回需要的信息。它还补齐了从数据筛选、时间步采样、偏好后训练到内核、缓存、稀疏注意力和量化的生产链路。

## 一句话

大多数层用近似线性成本的 attention 跑得快，每四层插一层 softmax 恢复精确的 token-to-token 关系，再用分块残差路由把这些高质量特征带到更深层。

## 推荐阅读顺序

```text
为什么视频 softmax 越来越贵
→ 纯线性注意力省掉了什么，又丢掉了什么
→ 3:1 混合注意力怎样折中
→ Block AttnRes 怎样跨 8 层块取回旧特征
→ flow matching 与时间步采样怎样训练
→ 数据、SFT、DPO、在线 RL
→ 实验到底证明了什么
→ Sol-Engine / QAT 的部署收益与边界
```

## 完整模型拼图

1. **输入压缩**：LTX-VAE 2.3 把像素视频压成时空 latent token；Gemma-2-2B-IT 把提示词编码成文本特征。
2. **主干**：5B 版 32 层、宽度 2,560；14B 版 40 层、宽度 4,096。每层有自注意力、文本 cross-attention 和 SwiGLU FFN。
3. **混合自注意力**：按 `Linear → Linear → Linear → Softmax` 循环。5B 有 24 层线性 + 8 个 softmax anchor；14B 有 30 + 10。
4. **跨深度取回**：每 8 层保存一份完成块摘要；后续 token 在 attention 与 FFN 前分别对旧块做加权汇总。
5. **训练目标**：flow matching 预测从干净视频 latent 指向噪声的速度；训练再叠加阶段性的 TQD、Self-Flow、DPO 与 ReFL。
6. **输出**：flow solver 迭代约 40 步，把噪声 latent 走回视频 latent，再由 VAE decoder 还原像素视频。

## 论文覆盖地图

| 原文章节 | 本页怎样重排 |
|---|---|
| 1 Introduction | 先讲视频长度为何把全注意力推到瓶颈 |
| 2 Preliminaries | 拆成 flow matching、softmax、gated linear attention、残差四个前置概念 |
| 3.1–3.2 Architecture / Hybrid Attention | 放进完整总览和 3:1 主机制 |
| 3.3 Block AttnRes | 用 8 层积木、逐 token 路由和数字例完整推一遍 |
| 4.1 Data | 还原六段数据漏斗、阶段性数据池和 caption |
| 4.2 Objectives | 解释 TQD、token-aware flow shift、EMA 与 Self-Flow |
| 4.3 Validation | 解释为什么随机 \(t\) 均值会遮住局部退化 |
| 4.4 Post-training | 区分离线 Diffusion-DPO 和在线 ReFL |
| 5 Experiments | 主结果、注意力比例、AttnRes、秩与路由、效率分口径解读 |
| 6 Deployment | Sol-Engine、MXFP4/8 QAT 与 Physical AI |
| Appendix B–G | 吸收模型配置、阈值、评测口径、机制干预与系统分析 |

## 1. 痛点：视频 token 两两见面，账单按平方涨

普通 softmax self-attention 先算：

\[
A=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_h}}\right),\qquad O=AV.
\]

- \(N\)：视频 latent token 数；每个 token 对应一小段时空区域。
- \(Q,K,V\in\mathbb R^{N\times d_h}\)：每个 token 投影出的 query、key、value。
- \(d_h\)：一个 attention head 的维度。
- \(A\in\mathbb R^{N\times N}\)：第 \(j\) 个 token 应该从第 \(n\) 个 token 取多少信息。
- \(O\)：加权后的输出 token。

当 \(N=1{,}000\) 时，\(A\) 有一百万格；\(N=10{,}000\) 时变成一亿格。分辨率、帧数和时长会一起推高 \(N\)。论文实测在 1080p、121 帧形状上，全 softmax 主干比 25% softmax 的混合主干慢 \(2.01\times\)；固定 720p、24fps，把时长拉到 60 秒时差距达到 \(3.17\times\)。

[[flash-attention]] 能避免把完整 \(N\times N\) 中间矩阵反复写回显存，但它算的仍是同一套两两关系；当序列继续变长，计算量本身仍接近平方增长。

## 2. 线性注意力：先做一份公共摘要，再让每个 token 来查

SANA-Video 2.0 的 gated linear attention 先把所有 key/value 累进固定大小状态：

\[
S=\sum_{n=1}^{N}v_n\left(\beta_n k_n^r\right)^\top.
\]

- \(n\)：被写进状态的 token 编号。
- \(v_n\in\mathbb R^{d_h}\)：第 \(n\) 个 token 的 value。
- \(k_n^r\in\mathbb R^{d_h}\)：经过 RoPE 的 key。
- \(\beta_n\)：写入门；决定这个 token 对公共状态贡献多少。
- \(S\in\mathbb R^{d_h\times d_h}\)：所有 token 共享的固定大小摘要。

第 \(j\) 个 token 再用自己的 query 读取：

\[
o_j=W_o\!\left[
\operatorname{RMSNorm}\!\left(
\frac{Sq_j^r}
{\sum_{n=1}^{N}\phi(k_n)^\top\phi(q_j)+\varepsilon}
\right)
\odot\sigma(g_j)
\right].
\]

- \(q_j^r\)：第 \(j\) 个 token 经 RoPE 的 query。
- \(\phi(\cdot)=\operatorname{ReLU}(\cdot)\)：把 query/key 映射成非负特征。
- 分母：归一化因子，使输出不会随 token 数量无界放大。
- \(\varepsilon\)：防止分母为零的小常数。
- \(g_j\)：输出门；\(\sigma\) 是 sigmoid，把门压到 \(0\) 到 \(1\)。
- \(\odot\)：逐元素相乘。
- \(W_o\)：attention 输出投影。

它快在先交换乘法顺序：

\[
\underbrace{\phi(Q)\phi(K)^\top}_{N\times N}V
\quad\Longrightarrow\quad
\phi(Q)\underbrace{\left(\phi(K)^\top V\right)}_{d_h\times d_h}.
\]

不再保存 \(N\times N\) 的关系表，而是先得到 \(d_h\times d_h\) 的状态，因此长序列成本主要随 \(N\) 线性增长。

代价也正来自这一步：不同 token 的关系先被压进同一个 \(S\)。当 \(N\gg d_h\) 时，\(S\) 的秩最高只有 \(d_h\)，不可能保留一张最多秩为 \(N\) 的完整关系表。它像把一场几千人的会议压成一页纪要：主题还在，但“第 417 人的左手在第 23 帧碰到杯沿”这类精确关系容易被揉掉。

## 3. 3:1 混合：三层做摘要，第四层重新逐一核对

32 层 5B 模型的布局是：

```text
L L L S | L L L S || L L L S | L L L S || ...
线性层 L：便宜地传播大范围信息
锚点层 S：重新显式计算所有 token-to-token 关系
每 8 层：恰好两个 3:1 周期，并保存一个块摘要
```

这里的 softmax anchor 不是“修正上一层算错的一个框”，也不是另加一条旁路；它就是完整的 softmax attention 层。它让当前 token 再次直接决定“我具体看哪一个时空位置”，输出随后继续流入后面的三层线性注意力。

论文从头训练 0%、14.3%、25%、50%、100% softmax 五个固定宽深代理模型：

| softmax 比例 | 验证损失 | 怎样读 |
|---:|---:|---|
| 0% | 0.955 | 纯线性最差，缺少周期性精查 |
| 14.3% | 0.914 | 少量 anchor 已明显补回质量 |
| 25% | 0.905 | 质量接近 50%，成本更低 |
| 50% | 0.897 | 损失最低，但 1080p 延迟比 25% 高 1.29 倍 |
| 100% | 0.945 | 在这组固定配置的短实验里也不如混合端点 |

因此 25% 是测出来的质量—速度“拐点”，不是验证损失最低点。这个结论来自 256p、81 帧、10K steps 的架构搜索代理实验，不能直接理解成“任何视频模型都该固定 25%”。

## 4. Block AttnRes：别只接上一层，让 token 自己翻旧笔记

普通残差流是：

\[
h_l=h_{l-1}+f_l(h_{l-1}).
\]

第 \(l\) 层只能在上一层已经揉合好的 \(h_{l-1}\) 上继续加工。若早先 softmax anchor 得到的精确关系在连续线性层里逐渐变淡，深层没有直接回看旧表示的入口。

Block AttnRes 每 8 层打包一份摘要：

- \(b_0\)：最初的输入 embedding。
- \(b_1,b_2,\ldots\)：已经完成的 8 层块摘要；写完后冻结，不再被当前块改写。
- \(p_l\)：当前 8 层块尚未完成的部分和；每来一个 attention / cross-attention / FFN 输出就继续相加。
- \(V_l=\{b_0,b_1,\ldots,p_l\}\)：第 \(l\) 层可以读取的来源集合。

路由公式是：

\[
h_l(x)=\sum_{v_i\in V_l}\alpha_{i\to l}^{(\tau)}(x)v_i(x),
\]

\[
\alpha_{i\to l}^{(\tau)}(x)=
\operatorname{softmax}_i\!\left[
\left(w^{(\tau)}\right)^\top
\operatorname{RMSNorm}\!\left(v_i(x)\right)
\right],
\qquad \tau\in\{\text{attn},\text{ffn}\}.
\]

- \(x\)：某一个时空 token；路由不是整段视频共用一组权重。
- \(v_i(x)\)：来源 \(i\) 在这个 token 位置的特征。
- \(i\)：来源编号，不是层内 token 编号。
- \(w^{(\tau)}\)：共享路由 query；attention 与 FFN 各有一份，但同一分支跨所有深度共享。
- \(\tau\)：当前是在 attention 前取旧特征，还是 FFN 前取。
- \(\alpha_{i\to l}^{(\tau)}(x)\)：来源 \(i\) 对第 \(l\) 层、token \(x\) 的权重；对所有 \(i\) 求和为 1。
- \(h_l(x)\)：路由后的输入，交给当前子层继续处理。

### 一个完整数字例

假设某个 token 到第 17 层时可读三份来源：

```text
b0=2：最初输入
b1=5：第 1 个八层块摘要
b2=8：第 2 个八层块摘要
```

共享 query 给它们的 logits 是 \([0,1,2]\)。softmax 后：

\[
\alpha\approx[0.090,\;0.245,\;0.665].
\]

于是当前 token 读出的表示是：

\[
h_{17}=0.090\times2+0.245\times5+0.665\times8\approx6.73.
\]

这不是固定 skip connection。另一个 token 的 \(b_i(x)\) 不同，即使用同一个 \(w\)，点积结果和权重也会不同：杯沿 token 可以偏向最近块，背景 token 可以多保留输入构图。

论文曾给 router 额外输入时间步，但去掉后短实验损失反而从 0.962 降到 0.920。原因不是模型“不需要时间”：每个 DiT block 的 AdaLN 仍已把 \(t\) 写进来源特征；显式 router 时间偏置跨时间的平均余弦相似度为 0.979，变化部分只有常量部分范数的 13%，基本学成了常量。

### 为什么按 8 层存，而不是每层都存

若保存每一层，历史特征内存约为 \(O(NLd)\)。每 \(S=8\) 层存一份，变成 \(O(N\lceil L/S\rceil d)\)，约省 8 倍历史存储。实验里 \(S=4/8/16\) 的损失几乎相同；选 8 主要是工程折中：每块恰好容纳两个 3:1 周期，又比 16 层块保留更多中间深度来源。

## 5. 训练目标：给一段带噪视频，预测它沿哪条直线变化

论文沿用 flow matching。令干净视频 latent 为 \(z\)，高斯噪声为 \(\epsilon\)，抽一个 \(t\in[0,1]\)：

\[
z_t=(1-t)z+t\epsilon,\qquad v^\star=\epsilon-z.
\]

- \(t=0\)：\(z_t=z\)，完全干净。
- \(t=1\)：\(z_t=\epsilon\)，完全是噪声。
- \(v^\star\)：这条直线路径的恒定目标速度。
- \(v_\theta(z_t,t,c)\)：模型在文本条件 \(c\) 下预测的速度。

损失：

\[
\mathcal L_{\mathrm{FM}}
=
\mathbb E_{z,\epsilon,t,c}
\left[
\left\|v_\theta(z_t,t,c)-(\epsilon-z)\right\|_2^2
\right].
\]

这里 \(\|\cdot\|_2^2\) 是把预测张量每个元素的误差平方后求和或按实现取平均；\(\mathbb E\) 表示换不同视频、噪声、时间步和文本后取平均。

数字例：取 \(z=2,\epsilon=-1,t=0.25\)：

\[
z_t=0.75\times2+0.25\times(-1)=1.25,\qquad v^\star=-1-2=-3.
\]

若模型预测 \(-2.4\)，单个标量的平方误差是：

\[
(-2.4-(-3))^2=0.36.
\]

推理方向与论文训练插值方向相反：从 \(t=1\) 的噪声出发，数值求解器沿模型速度的反方向逐步走向 \(t=0\) 的干净视频。

## 6. 时间步不是均匀抽：把不同素材安排到更有用的练习题

### 6.1 预训练 TQD：动得好与画得好，练不同噪声段

作者把视频质量和运动分开打分：

- **高运动、但画质未过高阈值**：在 logit 上加 \(+1.1\)，中位 \(t\approx0.75\)，多练高噪声下的全局运动与结构。
- **高画质、但运动未过高阈值**：减 \(1.1\)，中位 \(t\approx0.25\)，多练低噪声下的纹理和细节。
- **两者都高或都不高**：不偏移。

“高运动只练高噪、高清只练低噪”只是采样倾向，不是把其他时间步删掉。TQD 仅用于预训练；continual training 与 SFT 都关闭。

### 6.2 flow shift 到底怎样把 .5 变成 .75

若原时间步是 \(t\)，shift 为 \(s>0\)，对 logit 加 \(\log s\)：

\[
\operatorname{logit}(t_s)
=
\operatorname{logit}(t)+\log s.
\]

把 logit 展开并解回概率：

\[
t_s=\frac{st}{1+(s-1)t}.
\]

取 \(t=0.5,s=3\)：

\[
t_s=\frac{3\times0.5}{1+2\times0.5}=0.75.
\]

取 \(s=\frac13\) 则得到 \(t_s=0.25\)。这就是附录里“shift 3 / \(1/3\) 的中位数约为 .75 / .25”的来历。

continual training 起，作者根据 latent token 数把 shift 从 3 对数线性增到 6：更长、更高分辨率的视频含更多 token，训练更多偏向高噪声段。它是 batch size 1 时逐样本算的，不是一批视频共用一个长度。

### 6.3 EMA 与 Self-Flow

- [[ema]]：持续保存一份平滑权重，SFT 也开启。
- Self-Flow：预训练与 continual training 的辅助特征蒸馏。浅层 student readout 对齐更深层或 EMA teacher；10% token 使用第二个时间步，但所有 token 仍参与 flow-matching loss。它改变条件与监督，不是靠丢掉 10% token 来省主干计算。SFT 时关闭。

## 7. 数据与课程：不是一个美学分从头筛到尾

数据经过六类操作：解码与尺寸检查、镜头切分、黑边/字幕清理、画质与曝光检测、运动与一致性打分、逐阶段收紧阈值。

作者明确分开多个轴：

| 轴 | 代表信号 | 防止什么 |
|---|---|---|
| 视觉质量 | DOVER、模糊/曝光统计 | 低清、过曝、明显瑕疵 |
| 运动 | optical flow、VMAF motion | 数据池被干净但静止的视频占满 |
| 色彩 | 饱和度、亮度 | 不自然颜色 |
| 文图/时序一致性 | SigLIP 等 | caption 与视频不对应 |
| 镜头完整性 | 切镜、伪影检测 | 一段 clip 内突然跳场景 |

训练课程：

| 阶段 | 过滤后 clips | 分辨率 / 时长 | LR | 额外目标 |
|---|---:|---|---:|---|
| Pre-train | 约 3000 万 | 480p / 5s | \(10^{-4}\) | TQD + Self-Flow |
| Continual | 约 1000 万 | 480→720p / 5→8s | \(10^{-4}\) | token-aware shift + Self-Flow |
| SFT | 约 \(10^4\) | 720p / 8s | \(5\times10^{-5}\) | 标准 flow matching |

caption 也逐步增强到主体、动作、相机运动、场景、光照、交互和时间演化。图像 batch 以固定频率插入视频训练，给偏运动的视频池补外观质量。

## 8. 验证：一个随机时间步均值会把进步与退步抵消

论文发现 loss 沿噪声轴相差约 3 倍。如果 100 个验证样本都随机抽 \(t\)，某次恰好多抽到高损失段，checkpoint 比较就会抖；把所有时间步混成一个均值，也看不出低噪声变好、高噪声变差。

他们把 1000 个离散噪声步分成 10 桶，每桶固定 10 个样本，并让不同 checkpoint 重用相同视频、文本、噪声和时间步。

四个 checkpoint 从早到晚：

- 十桶宏平均 MSE 下降 6.42%；
- 低噪声段最多改善 11.44%；
- 高噪声段反而退化 1.16%；
- 固定 100 次评估预算时，变化估计的标准差比 IID 随机抽样低 2.27 倍；
- VBench 从 82.68 到 83.29，但只有四个点，只能作描述，不能声称强相关。

这个分桶均值只是训练监控工具，不是新的优化损失。

## 9. 后训练：离线偏好对与在线奖励是两件事

### 9.1 Diffusion-DPO

Gemini 离线比较同一 prompt 的多条视频，选出 preferred \(x^+\) 和 rejected \(x^-\)。训练策略 \(\theta\) 与冻结参考模型 \(\theta_{\mathrm{ref}}\) 都从 SFT checkpoint 初始化。

两条视频共享同一 \(t\) 和高斯噪声，单条 flow error 为：

\[
e_\phi^\pm
=
\frac1D
\left\|
v_\phi(x_t^\pm,t,c)-(\epsilon-x^\pm)
\right\|_2^2.
\]

- \(\phi\)：泛指当前策略或参考模型。
- \(D\)：latent 元素数，用来取平均。
- \(+\) / \(-\)：preferred / rejected。
- \(\Delta_\phi=e_\phi^- - e_\phi^+\)：模型对坏视频的误差比好视频大多少。

最终损失：

\[
\mathcal L_{\mathrm{DPO}}
=-\mathbb E\!\left[
w\log\sigma\!\left(
\beta(\Delta_\theta-\Delta_{\theta_{\mathrm{ref}}})
\right)
\right]
+\lambda\mathbb E[e_\theta^+].
\]

第一项要求当前策略比参考模型更偏爱 preferred；\(w\) 来自裁判分差，\(\beta\) 控制偏好强度。第二项继续把 preferred 当普通 flow 样本训练，防止只顾拉开差距而忘掉生成。

### 9.2 在线 ReFL

ReFL 真正用当前模型 rollout：无梯度走到随机去噪步，预测干净 latent \(\hat x_0\)，解码视频的首帧、中帧、尾帧，再让冻结的 HPSv3++、DeQA-Score、UniPercept 以 4:4:1 合成奖励。梯度只穿过当前模型评估与 decoder，不反传整条采样轨迹；另用速度 MSE 约束模型别偏离冻结基座。

400 次迭代里三条记录奖励都上升，但这是训练 reward，不等于独立人评全面胜出。附录只给四组 matched-prompt 定性样例。

## 10. 实验：把“好”“快”和“为何有效”分开看

### 10.1 最终质量

5B、480×832、81 帧、40 步：

- VBench Total 84.30；
- Quality 85.61，是主表最高；
- Semantic 79.05，低于 Bernini-R 的 82.49；
- Bernini-R Total 84.64 更高，但相同 shape、步数、H100 下是 421s，对比本模型 13.2s。

121 帧和 193 帧 operating point 的 Total 分别为 85.29 与 84.48。它们使用另一 late-stage checkpoint、不同 CFG / flow-shift，不能只凭帧数解释分数变化。

### 10.2 AttnRes 没有被实验成“显著涨分按钮”

晚期对照 MSE 是 0.48547→0.48506，20 个噪声桶里 17 个略好。作者自己也不从这个窄差距声称画质提升。

更扎实的机制证据是：

- 同 checkpoint 开/关聚合，深层线性状态有效秩平均 +11.7%，24 个线性层中 22 个不下降；
- 最深块里，旧完成块获得 attention/FFN 路由质量的 56%/50%；
- 最近完成块权重约 26%，更早两块约 15% 与 14%，呈现近因梯度；
- 在第 9/17/25 层块入口删除旧块来源，有效秩下降 82%–91%；块内 partial sum 重建后，删除影响很小。

有效秩定义：

\[
r_{\mathrm{eff}}(S)
=
\exp\!\left(
-\sum_i p_i\log p_i
\right),
\qquad
p_i=\frac{\sigma_i(S)}{\sum_j\sigma_j(S)}.
\]

- \(\sigma_i(S)\)：状态矩阵 \(S\) 的第 \(i\) 个奇异值。
- \(p_i\)：奇异值归一化后的“信息占比”。
- \(r_{\mathrm{eff}}\)：若信息只挤在一个方向，接近 1；若均匀分布在 \(k\) 个方向，等于 \(k\)。

例如奇异值 \([3,1]\) 给出 \(p=[.75,.25]\)，有效秩约 \(1.75\)，不是机械地数“非零奇异值有 2 个”，而是反映第二个方向实际贡献较少。

## 11. 部署：模型设计、内核优化、近似加速不要混成一个数字

### 11.1 Sol-Engine 三段栈

在一张 B200、720p、8s：

| 阶段 | NFE | 延迟 | 相对本机 baseline |
|---|---:|---:|---:|
| 基线 | 50 | 62.65s | 1.00× |
| kernel / execution 优化 | 50 | 30.74s | 2.04× |
| diffusion cache | 33 | 20.89s | 3.00× |
| softmax anchor 稀疏注意力 | 33 | 17.52s | 3.58× |

第一段保持数学计算不变；cache 少算 17 次模型评估，稀疏 attention 也引入近似。它们是部署优化，不是 3:1 架构本身的训练贡献。

论文项目页还报告 5B 在单 H100、720p、5s 的完整生成是 13.06s；这与表中的 B200、8s、50-step 起点不是一个测量条件，不能互相除或直接拼倍数。

### 11.2 QAT：存储大降，延迟只小降

MXFP4 权重 + MXFP8 激活：

- BF16 VBench Total 83.22，QAT 83.25，PTQ 82.87；
- 模型静态存储 8.94→2.87GB，下降 67.9%；
- peak memory 10.74→4.63GB，下降 56.9%；
- GB200 单次 backbone forward 203.08→191.30ms，只快 5.8%。

因为当前只量化 linear GEMM，而这部分只占 BF16 runtime 的 16.2%；两种 attention kernel 仍是 BF16。省很多存储但只快一点并不矛盾。

## 12. Physical AI 与局限

作者用约 5000 小时公开机器人/第一视角视频微调 10 万步，并给出与 Cosmos3-Edge、Cosmos3-Nano、Lingbot-Video 的定性对比。它说明同一高效 backbone 可以迁移到机器人视频，但没有量化机器人控制成功率，也没有证明生成得“像真的”就能直接用于闭环决策。

需要保留的边界：

1. 25% 比例来自特定代理模型和训练预算，不是理论最优。
2. AttnRes 的最终质量增益很窄；论文主要证明跨深度复用和秩恢复。
3. 主 VBench 表混有官方报告与作者复测，模型帧数、CFG 和 checkpoint 也不同。
4. Sol-Engine 的 cache 与稀疏 attention 是近似，不能与纯架构 speedup 无条件相乘。
5. 在线 RL 只报告训练 reward 和少量定性样例。
6. 14B 的核心质量主表没有像 5B 一样完整展开；它主要出现在速度与硬件 scaling。
7. 数据是 in-house，虽公开筛选信号和阈值，仍无法完整复现数据分布。

## 13. 真正值得带走的三点

1. **线性与 softmax 的差别不是“近似公式 vs 精确公式”这么简单**：前者把所有 token 先写进固定状态，后者保留当前 query 对每个 token 的独立关系。
2. **周期性精查与跨深度取回是互补的**：softmax anchor 产生更丰富的关系，Block AttnRes 让深层 token 不必只靠上一层间接继承它。
3. **生产速度必须按口径拆开**：主干算法、编译 kernel、少算步数、稀疏 attention、量化各自改变的对象不同，只有完整同条件计时才能写在同一条加速链上。

## 关键概念

- [[gated-linear-attention]] · 固定大小状态怎样把 \(O(N^2)\) token mixing 改成接近 \(O(N)\)。
- [[hybrid-linear-softmax-attention]] · 为什么周期性 softmax anchor 能补线性状态的表示瓶颈。
- [[block-attention-residuals]] · 每 8 层保存摘要并逐 token 路由旧特征。
- [[content-aware-flow-shift]] · 用视频质量、运动和 token 数改变时间步训练密度。
- [[flow-matching]] · 从干净 latent 到噪声的直线速度回归。
- [[diffusion-timestep-conditioning]] · router 不直接吃 \(t\)，不等于 DiT block 没有时间条件。
- [[quantization]] · PTQ、QAT、权重/激活位宽与实际延迟。

## 来源

- [论文摘要](https://arxiv.org/abs/2607.21553)
- [论文 PDF](https://arxiv.org/pdf/2607.21553)
- [官方项目页](https://nvlabs.github.io/Sana/Video2/)
- [官方代码仓库](https://github.com/NVlabs/Sana)
