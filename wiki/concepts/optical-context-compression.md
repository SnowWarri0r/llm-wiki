---
name: optical-context-compression
type: concept
sources: [unlimited-ocr]
updated: 2026-06-22
---

# Optical Context Compression · 光学上下文压缩

## 一句话
把整页文字"拍成图"再用视觉编码器压成几百个 token，比一个字一个 token 省得多——一张图顶上千个文本 token。

## 直觉
反直觉但很硬的观察：**一页密密麻麻的文字，当成图像编码，比当成文本编码更省 token**。一页论文上千个文字 token，但渲染成一张 1024×1024 的图、过一个高压缩视觉编码器，能压到 ~256 个视觉 token。约 **1:10** 的视觉:文本比——一个视觉 token 解码出来约 10 个文本 token。

这套是 DeepSeek-OCR 的 DeepEncoder 带火的。为什么对长程 OCR 这么关键？因为视觉 token 进了模型就当**前缀 prefix**，编码一次后**全程不变**（不随输出做状态转移）。前缀压得越小，[[kv-cache]] 里那段固定开销越小，留给输出的空间越多。输入侧先把账压下来，解码侧再用 [[reference-sliding-window-attention]] 兜住，两头一夹才有"几十页一次过"。

## 怎么做的
DeepEncoder = 两段 ViT 串起来 + 中间 16× 压缩：
```
高分辨率图
  → SAM-ViT  (窗口注意力, 只看局部)   ← 处理原始大量图像 token, 激活值低省显存
  → 16× 压缩 (桥接处把 token 数砍到 1/16)
  → CLIP-ViT (全局注意力)            ← 只在压缩后的少量 token 上做全局, 才划算
  → 少量视觉 token
```
关键设计：**全局注意力只留给压缩后的 token**。前半段用窗口注意力扛住原图的海量 token（局部、便宜），等砍到 1/16 了，才上全局注意力（贵但 token 少）。这样编码高分辨率图时激活值低、省 GPU。

模式：Base（1024×1024，多页用）、Gundam（动态分辨率，单页用）。

## 数字例子
一张 1024×1024 的 PDF 图：

```
按 16×16 patch 切     → (1024/16)² = 64×64 = 4096 个图像 token
桥接处 16× 压缩       → 4096 / 16 = 256 个视觉 token
```

按 1:10 解码：`256 视觉 token → ~2560 文本 token`，约等于一整页密集文档 ✓。

反过来推长程：要解析 20-30 页 → 约 `10000` 个视觉 token 当前缀 → 全解码出来要 **100000+** 文本 token。✓ 自检：这就是为什么"输入侧已经压得很好，真正的瓶颈在解码侧"——前缀 256~10000 不算大，但输出动辄十万，标准注意力的 KV cache 在这步爆掉。光学压缩解决了输入，[[reference-sliding-window-attention]] 才接着解决输出。

## 链接
- [[unlimited-ocr]] · 沿用 DeepEncoder 这套压缩
- [[reference-sliding-window-attention]] · 配套的输出侧省法，两头一夹
- [[kv-cache]] · 前缀压得小 = KV cache 固定开销小
- [[vit]] · DeepEncoder 是 SAM-ViT 串 CLIP-ViT
- [[clip]] · 后半段全局注意力那截就是 CLIP-ViT
