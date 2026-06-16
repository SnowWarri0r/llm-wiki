---
name: mmdit
type: concept
sources: [stable-diffusion-3-5, qwen-image-2, mrt]
updated: 2026-06-16
---

# MMDiT · 多模态扩散 Transformer · 文字图像坐同一张桌子

## 一句话
文字 token 和图像 token **拼成同一条序列、过同一个自注意力**实现双向对齐——但**每种模态各用各的一套权重(QKV 投影 + MLP)**。是 SD3/FLUX 那代文生图的主干，长 prompt 服从和文字排版大涨的根。

## 直觉 · 调料 vs 同桌

老文生图(SD1.5/SDXL，U-Net + **cross-attention**)里**图像是主角**：一条图像特征序列从头走到尾，文字编码后**从旁边**通过 cross-attention "喷"进每层。文字像炒菜时**从锅边淋进去的调料**——能影响味道，但它自己不在锅里翻炒，跟图像不平等。后果是长 prompt 顾此失彼、英文单词拼写缺胳膊少腿。

**MMDiT(SD3，Esser et al. 2024)** 把这关系改成**平起平坐**：把图像 token 和文字 token **拼成一条序列**，一起过**同一个 self-attention**，让两边**双向**互相看、互相改。

为什么不直接共享一套权重就完了？因为**图像和文字的统计规律本就不同**(一个是连续的视觉 patch，一个是离散的语言 token)。MMDiT 的折中是:**注意力里合流(共享对齐)，但 QKV 投影和 MLP 按模态分两套(各自的"母语")**。像两个说不同语言的人**坐到同一张桌子**——各自带自己的笔记本(独立权重)，但能直接对视交流(共享注意力)。

## 怎么做的 · 双套权重，一次 attention

```
# 一个 MMDiT block（双流）
# 输入两路 token：文字 h_text、图像 h_img
q_t,k_t,v_t = W_text_qkv( AdaLN_t(t) · h_text )   # 文字用自己的投影权重
q_i,k_i,v_i = W_img_qkv ( AdaLN_i(t) · h_img  )   # 图像用自己的投影权重

# 拼起来做一次联合注意力（这一步两模态合流、双向看）
Q=[q_t;q_i]  K=[k_t;k_i]  V=[v_t;v_i]
attn = softmax(QKNorm(Q)·QKNorm(K)ᵀ/√d) · V       # QK-Norm 防 logit 爆炸

h_text += W_text_o(attn_text);  h_text += MLP_text(h_text)   # 各自的 MLP
h_img  += W_img_o (attn_img );  h_img  += MLP_img (h_img )
# 时间步 t 通过 AdaLN 调制每个 block 的残差路径
```

要点:**两路 token 各走各的投影/MLP(两套权重)，只在算 attention 时拼成一条共享序列**。这就是"双流"。

## 单流 vs 双流(关键分歧)
- **双流 / MMDiT**(SD3、FLUX):文字图像各一套投影，只在 attention 合流。表达强、参数多。
- **单流**([[ideogram-4]]、Z-Image):文字图像**共享同一套投影**，每层就一条 self-attention 序列。更简、更省参数。

SD3.5 还把 MMDiT 块里的单注意力换成**双注意力层**(Medium 版叫 **MMDiT-X**:前 13 层额外加自注意力)，进一步改多分辨率一致性。

## 代码出处 / 来源
- SD3 arXiv 2403.03206《Scaling Rectified Flow Transformers》—— MMDiT 提出处
- [[stable-diffusion-3-5]] · 开源权重实现；[[qwen-image-2]] · 把 MMDiT 推广到生成+编辑统一

## 链接
- [[diffusion-transformer]] · MMDiT 是 DiT 的双流多模态形态(父概念)
- [[stable-diffusion-3-5]] · MMDiT 的招牌落地
- [[qwen-image-2]] · 同吃 MMDiT，做条件→目标统一生成编辑
- [[mrt]] · 把"任意子集图层当条件"推广，仍是 MMDiT 一族
- [[qk-rmsnorm]] · 联合注意力里防 logit 爆炸的 QK-Norm
- [[flow-matching]] · MMDiT 的训练目标(预测速度场)
- [[mrope]] · 给拼起来的文字图像 token 算跨模态联合位置
