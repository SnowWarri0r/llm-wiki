---
name: solarwm
type: paper
source: raw/solarwm.txt
upstream: https://arxiv.org/abs/2609.02886
ingested: 2026-09-14
authors: Junchao Huang et al. · CUHK-SZ × SLAI × NUS × CUHK × HKUST × NVIDIA × UCLA × MSRA · arXiv 2609.02886 (2026-09)
year: 2026
---

# SolarWM · 世界模型的公共地基：数据引擎 + 四条骨干一套配方

交互式视频世界模型的全开源基建：1.43M canonical clip 的可重构数据引擎 + 四个 5B–33B 异构骨干模型（Wan2.2-5B/14B、LTX-2.5、MiniMax-H3）+ 统一三阶段训练配方。数据、管线、配方、权重、框架全放。

## 一句话

**把"多源数据怎么混"和"异构骨干怎么适配"这对耦合问题拆开：数据侧先全量标注、选择只是元数据运算（拒收样本带 reasons 留档）；模型侧共享相机条件/训练/推理接口、保留各骨干原生表示；配方 = 双向适配 → TF-AnyFlow 自回归初始化 → DMD 因果训练，只训 5 秒序列就能小时级 rollout。**

## 它要解决的痛点

- 数据源在时间尺度、相机几何、画质、运动、caption 风格上全不一样,朴素混训产生不一致监督——单源表现好的模型多源反而退化;
- 骨干在 latent 表示、注意力结构、条件机制上互不相同:统一适配会伤预训练能力,逐骨干定制又没法系统比较;
- 现有开源栈要么缺数据、缺选择记录、缺可执行管线、缺精确配方,要么只覆盖一两个骨干家族。

## 核心设计

1. **数据引擎（先全量标注,后做决定）**:10 源 → 14 个 dataset owner,1,425,694 条 canonical clip,25.85TB;每条统一七元组契约 (V,P,K,C,m,q,π)——视频、度量制 c2w 位姿、逐帧内参 (fx,fy,cx,cy)、dense caption、元数据、全量指标、谱系。三命名空间分离:物理语料 / 逻辑配方(split、tier、源权重、repeat)/ 模型视图(窗口、latent),改配方不动底层。**拒收的 549,101 条照样全套标注入库**,带机器可读 reject reasons。
2. **相机标注双路**:video-only 源走 Pi3X(结构)+MoGe-2(度量深度锚)融合 → 改造版 VIPE SLAM,逐帧可独立优化内参(为 zoom),GeoCalib 初始化;有真值/COLMAP 位姿的源保留原轨迹,Pi3X 只用来接度量 gauge(Umeyama Sim(3),最低残差 80% 帧重估)。全部输出度量制、不做全语料平移归一化。
3. **Clean Plate 衍生 owner**:LTX-2.3 IC-LoRA 去人车(8 步、strength 1.0、1248×704 → 1280×720@16fps),产出 543k 干净 clip;指标全部重算、尺度重建 fail-closed,是独立 owner 不是替换。
4. **Kimi-K2.6 标注契约**:严格六字段 JSON;caption 只写持久环境、硬性排除人/动作/相机运动/镜头术语——**防文本条件泄漏相机控制信息**。指标向量五轴(相机完整性/视觉/运动/时间一致性/语义),没用于筛选的也全存。
5. **分层策略逐源冻结**:xhigh/high/rejected 三互斥标签;门限按源不对称(Sekai-Game 不设几何/饱和门以保高速游戏轨迹);规则引用的指标缺失/非有限 = fail-closed 拒。
6. **三阶段配方**:①双向适配(原生 flow/velocity 目标 + fused-PRoPE 相机注入);②TF-AnyFlow:因果注意力 + teacher forcing + AnyFlow flow-map 损失,直接产出少步自回归初始化,**替代 Causal Forcing 的 Causal ODE 和 Causal Forcing++ 的 Causal CD 两个专门阶段**;③DMD:detached rollout-and-replay 让 KV cache 可传梯度,冻结双向老师 + 可训 fake 模型。发现:优化大头放双向阶段,AR 适配快收敛,DMD 步数更少。
7. **fused-PRoPE**:相机位姿+内参决定的投影旋转直接作用在 Q/K/V 上(V 转完在输出投影前配套逆变换),不加控制分支不加额外注意力。H3 路线保留预训练头维切分:[0:96) 原生内容 MM-RoPE,只有 [96:128) 吃相机 PRoPE。

## 关键数字

- 语料:1,425,694 全量 = 471,798 high + 404,795 xhigh + 549,101 rejected(kept 876,593);29k shard / 25.85TB;<81 帧的 78k 全在拒收区。
- 81f 短配方:600,320 物理行,ABOT/MiraData/Sekai-Game 重复因子 6 → 870,210 虚拟出现(反解:被加倍三源在配方内合计 (870,210−600,320)/5 = 53,978 条)。
- 四路线 VAE 压缩:Wan5B 4×/16×(48ch)、Wan14B 4×/8×(y=4ch mask+16ch 图 latent)、LTX 8×/32×(22B 砍掉 3.69B 音频流+2.58B AV 交叉注意力,保留 14.74B=13.13 视频核+1.61 冻结 Gemma)、H3 时间 17n+5↦5n+2(n=9: 158 帧→47 latent)/空间 16×。
- 推理:16fps、4 步、无 attention sink;单图+固定 prompt,相机轨迹是唯一时变控制;60 分钟 rollout 端点仍可识别。

## 关键概念 → 概念页链接

- [[annotate-once-select-by-metadata]] — 数据引擎的核心原则(新)
- [[teacher-forced-anyflow]] — 少步 AR 初始化,替代 Causal ODE/CD(新)
- [[projective-rope]] — fused-PRoPE 的本体
- [[dmd-distillation]] — 第三阶段
- [[teacher-forcing-video-diffusion]] — 第二阶段的 TF 端与 exposure bias
- [[causal-consistency-distillation]] — 被 TF-AnyFlow 绕开的路线
- [[world-foundation-model]] — 所处的物种

## 我的批注 / 疑问

- **实验全是定性图,一张数值基准表都没有**——没有基线对比、没有消融,"SOTA"与"三阶段各贡献多少"只有叙述。这是 release/基建论文,不是 benchmark 论文,读的时候要按这个定位打折。
- 发布对照矩阵(Table 1)在 arXiv HTML 里只剩表头,各家系统的行没渲染出来;比较轴本身(权重/推理/训练/数据/全记录/管线/精确配方/多骨干)是这篇的自我定位依据。
- 最值钱的工程思想是"先全量标注、后做决定"+拒收留档:改门限=索引一遍,不再跑 GPU;和"门限逐源不对称、不跨语料迁移"一起,是多源数据工程的成文范本。
- 训练超参、步数、算力在正文缺席(承诺随 release 给 exact recipes);LTX 参数账 22−6.27≈15.7 vs 保留 14.74 有约 1B 口径差,论文未解释。
