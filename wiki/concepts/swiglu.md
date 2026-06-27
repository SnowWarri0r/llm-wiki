---
name: swiglu
type: concept
sources: [dit]
updated: 2026-06-24
---

# SwiGLU · 带门的 FFN

## 一句话
把 transformer 的 FFN 改成"一条算内容、一条当门，两条逐元素相乘"——让网络自己决定哪些特征放过去。

## 直觉
普通 FFN：`x → 升维(d→4d) → 激活(GELU) → 降维(4d→d)`，一条路、一个激活函数。

SwiGLU 加了个**门**：开两条并行投影，一条当"内容"，另一条过一个平滑激活(Swish)当"开关"，两条**逐元素相乘**——门接近 0 的位置内容被掐掉，门大的地方放过。直觉上比"算一遍激活一遍"多了一层**自己给自己开关**的能力，实测同算力下更强，所以 LLaMA、PaLM、现代 [[diffusion-transformer]] 家族(SD3/FLUX)都用它。

注意：**原版 [[dit]](2022) 用的是 GELU，不是 SwiGLU**——SwiGLU 是后来给 DiT 家族的现代化升级，别记串了。

## 怎么做的
```
FFN_SwiGLU(x) = ( Swish(x·W_gate)  ⊙  x·W_up ) · W_down

Swish(z) = z · sigmoid(z)   (也叫 SiLU，一条平滑、负区不全为 0 的曲线)
⊙ = 逐元素相乘
```
三个矩阵(W_gate / W_up / W_down)而非两个，为保持参数量，中间维度从 4d 缩到约 2.67d(×2/3)。

## 数字例子
设某 token 算出两条投影：门 `g = x·W_gate = [2, -1]`，内容 `u = x·W_up = [3, 4]`。

**第一步 · 门过 Swish**(Swish(z)=z·σ(z))：
```
σ(2) ≈ 0.88 → Swish(2)  = 2·0.88  =  1.76
σ(-1)≈ 0.27 → Swish(-1) = -1·0.27 = -0.27
```

**第二步 · 门 ⊙ 内容**：
```
gated = [1.76, -0.27] ⊙ [3, 4] = [1.76·3, -0.27·4] = [5.28, -1.08]
```
再过 `W_down` 降维。✓ 自检：第二维门的输入是 −1(负)→ Swish 压到 −0.27(接近 0)→ 把内容 4 几乎掐灭(−1.08)；第一维门输入 2(正)→ 放大内容到 5.28。**门在挑哪些内容通过**，这是普通 GELU FFN(单路、无门)给不了的。

## 跟普通 FFN 的对比
| | 普通 FFN | SwiGLU |
|---|---|---|
| 投影矩阵 | 2 个 | 3 个(gate/up/down) |
| 激活 | GELU 单路 | Swish 当门 ⊙ 内容 |
| 中间维度 | 4d | ≈2.67d(补回参数量) |
| 谁用 | 原版 DiT、早期 Transformer | LLaMA / PaLM / SD3 / FLUX |

## 链接
- [[dit]] · DiT 家族的 FFN；原版用 GELU，现代换 SwiGLU
- [[diffusion-transformer]] · 现代 DiT 主干的 FFN 就是它
- [[normalization]] · 同属"transformer 块内部零件"
