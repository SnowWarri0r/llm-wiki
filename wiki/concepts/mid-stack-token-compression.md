---
name: mid-stack-token-compression
type: concept
sources: [lynnreal-omni]
updated: 2026-09-17
---

# Mid-stack Token Compression · 三明治压缩：两头全量，中间四分之一

## 一句话

DiT 前几块和后几块跑全部 token，中间大段只跑空间下采样后的约 1/4 视频 token，残差回填补齐——大头计算省了，输入输出接口没变。

## 直觉

Transformer 的算力大头在中间那几十块重复层，而视频 token 空间上高度冗余。直接全程下采样会丢边缘细节、破坏输入输出接口；只压中间段就两头讨好：前 2 块先让视频/文本/音频在全分辨率上完成早期融合，中间 26 块在 stride-2 子采样（约 1/4 token）上跑，最后 14 块回到全分辨率精修。文本和音频 token 全程不压，所有保留 token 保持原 3D RoPE 坐标——多模态结构没动。

## 怎么做的

- 子采样沿两个空间维 stride 2，并保留边界行列护住边缘；时间维不动。
- 残差回填：\(H_{\mathrm{out}}=H+U(F_{\mathrm{mid}}(PH)-PH)\)——P 选 token，F_mid 是中段，U 把每个被略去的视频 token 赋予同帧最近保留 token 的特征更新；保留 token 用自己的更新。全分辨率特征 H 原样保底，中段只贡献"上下文修正量"。
- 序列长度从 \(N_v+N_t+N_a\) 降到约 \(N_v/4+N_t+N_a\)：投影、FFN、注意力三处都省。
- 受控对照（LynnReal-Omni-Flash，同权重同步数只关压缩）：DiT 时延 263ms → 453ms，压缩贡献约 1.7× 加速。

## 链接

- [[lynnreal-omni]] — Flash 变体的三件加速手段之一（另两件：砍深度 50→42 块、W4A8 量化）
