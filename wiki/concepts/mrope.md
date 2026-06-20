---
name: mrope
type: concept
sources: [ideogram-4, qwen3-vl-report, qwen-image-2]
updated: 2026-06-15
---

# M-RoPE · 多模态旋转位置编码

## 一句话
把 RoPE 的"一个位置数字"升级成**三元组 (时间, 行, 列)** —— 让同一套 attention 既能数文字的先后，又能知道图像 patch 在画面的第几行第几列。

## 直觉 · 一维的尺子量不了二维的画

[[rotary-position-embedding]]（RoPE）给每个 token 一个**位置 = 一个整数**：第 0 个、第 1 个、第 2 个……这对纯文本够用，文字本来就是一条直线排下来的。

但图像不是一条线。你把一张图切成 patch 喂进 transformer，如果只给它们排成 `0,1,2,...,255` 的一维序号，模型就只知道"这是第 137 块",**不知道它在画面的左上还是右下**。第 137 块和第 138 块在序号上挨着，可它俩可能一个在画面左边缘、一个在右边缘（只是同一行的头尾）。一维序号把二维空间结构压扁了。

M-RoPE（Multimodal RoPE，Qwen2-VL 提出）的办法：**别用一个数字，用三个**——
- **t**：时间轴（第几帧 / 文字的第几个 token）
- **h**：高度轴（在画面第几行）
- **w**：宽度轴（在画面第几列）

一个 patch 的位置变成 `(t=10, h=4, w=7)` = "第 10 个时刻、第 4 行、第 7 列"。位置编码第一次**带上了画面坐标**。

## 怎么做的 · 把旋转维度劈成三份

RoPE 的本体是"按位置旋转 Q/K"，旋转角 = 位置 × 一组频率。M-RoPE 只改一件事：**把那组旋转维度切成三段，每段用三元组里的一个分量去转**。

```python
# RoPE: 所有维度都用同一个 position 转
angles = position * freqs            # position 是标量

# M-RoPE: 维度分成 3 段，分别用 t / h / w 转
angles_t = t * freqs[:, group_t]     # 前 1/N 段 → 时间
angles_h = h * freqs[:, group_h]     # 中间段   → 行
angles_w = w * freqs[:, group_w]     # 后段     → 列
# 拼回去，照样做 Q·K^T
```

点积出来后，attention score 里同时含了**时间差、行差、列差**三种相对位置。模型一次就能问出"这两块 patch 隔了几行几列"。

## 关键 · 文字会自动塌回普通 RoPE

最漂亮的设计：**纯文本 token 的三元组三个分量相等** `(t=5, h=5, w=5)`。三段旋转角一样 → M-RoPE 退化成普通一维 RoPE。

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:monospace;">
  <!-- 文本 -->
  <text x="20" y="30" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#1f3a5f">文本 token：三轴相等 → 等价一维 RoPE</text>
  <g font-size="11" fill="#3a3128">
    <rect x="30" y="45" width="60" height="32" fill="#c8d4e2" stroke="#1f3a5f"/>
    <text x="60" y="65" text-anchor="middle">(2,2,2)</text>
    <rect x="100" y="45" width="60" height="32" fill="#c8d4e2" stroke="#1f3a5f"/>
    <text x="130" y="65" text-anchor="middle">(3,3,3)</text>
    <rect x="170" y="45" width="60" height="32" fill="#c8d4e2" stroke="#1f3a5f"/>
    <text x="200" y="65" text-anchor="middle">(4,4,4)</text>
    <text x="245" y="65" fill="#7a6f5d">… 像普通文字一样一个接一个</text>
  </g>
  <!-- 图像 -->
  <text x="20" y="120" font-family="Fraunces,serif" font-style="italic" font-size="14" font-weight="700" fill="#9b2c2c">图像 patch：t 固定，(h,w) = 行列坐标</text>
  <g font-size="10" fill="#3a3128">
    <!-- 3x3 patch grid, t=10 fixed -->
    <rect x="30"  y="135" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="54"  y="156" text-anchor="middle">10,0,0</text>
    <rect x="82"  y="135" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="106" y="156" text-anchor="middle">10,0,1</text>
    <rect x="134" y="135" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="158" y="156" text-anchor="middle">10,0,2</text>
    <rect x="30"  y="171" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="54"  y="192" text-anchor="middle">10,1,0</text>
    <rect x="82"  y="171" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="106" y="192" text-anchor="middle">10,1,1</text>
    <rect x="134" y="171" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="158" y="192" text-anchor="middle">10,1,2</text>
    <rect x="30"  y="207" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="54"  y="228" text-anchor="middle">10,2,0</text>
    <rect x="82"  y="207" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="106" y="228" text-anchor="middle">10,2,1</text>
    <rect x="134" y="207" width="48" height="34" fill="#f3d9d9" stroke="#9b2c2c"/><text x="158" y="228" text-anchor="middle">10,2,2</text>
  </g>
  <text x="200" y="180" font-size="11" fill="#7a6f5d">同一张图 t 都=10（同时出现），</text>
  <text x="200" y="198" font-size="11" fill="#7a6f5d">靠 (h,w) 区分它在画面哪一格。</text>
  <text x="200" y="216" font-size="11" fill="#3a3128">→ 第几行第几列写进了位置本身</text>
</svg>
</figure>

这就是为什么一套 attention 能同时吃文字和图：**文字是退化的图（行列恒等），图是展开的文字**。

## 跟 Ideogram 4 的关系 · bbox 不是外挂

[[ideogram-4]] 让你在 JSON caption 里给元素指定 bounding box，模型还真能 honor。它不靠额外的布局模块，**就是借 M-RoPE 的位置系**：你说"这个文字块在画面右上 (h,w) 区间"，等于直接给生成 token 指定了那片 (h,w) 坐标。布局控制天然长在位置编码里，这是 M-RoPE 给 T2I 的红利。

## Qwen3-VL 的 Interleaved-MRoPE · 别让时间只拿到低频

原版 M-RoPE 把频率**按段切**：时间拿一整段低频、行拿中段、列拿高频。问题是时间轴只分到低频 → 长视频里时间分辨率不够。

Qwen3-VL 的 **Interleaved-MRoPE** 改成**交错分配**：t/h/w 三个轴都横跨从低到高的全频段（像 [[rotary-position-embedding]] 里"低音鼓标大拍、高音钹标小拍"那样，每个轴都拿到完整的多尺度）。代价几乎为零，长视频时序推理明显更稳。

## T-RoPE → 文字时间戳 · 视频时间该不该编进位置

Interleaved 管的是"频率怎么分"，这条管的是另一件事：**视频的"时间"到底要不要塞进位置编码**。

**T-RoPE（Qwen2.5-VL）**：把 M-RoPE 的时间维 **t 绑到"绝对时间(秒)"**——不是帧序号 0,1,2,3，而是"这帧在第 3.0 秒、那帧在第 7.5 秒"。动机好：视频按不同帧率采样，想让模型知道**真实流逝了多久**。但两个毛病：

- **id 又大又稀**：t=绝对时间，长视频(比如 1 小时)的时间 id **数值巨大**，RoPE 对见得少的大旋转角**外推差**；而且帧是**采样**的，时间戳**跳着走**(0→2.3s→5.1s…)，id 在巨大范围里**稀疏散布** → 学不好相对时序。
- **要密集采各种帧率训**：id 绑死绝对时间，得让模型在 30fps/1fps… 各种帧率下都对应好"绝对时间↔位置"，只能**密集均匀采各种 fps** 硬训 → 数据构造又贵又烦。

**Qwen3-VL 的修法**：干脆**不把时间塞进位置编码**，给每组帧**前缀一个文字 token `<3.0 seconds>`**(秒和 HMS 两种格式都训)。于是位置 id 回到**正常 token 位置(小、密)**，时间变成**模型能直接读的文字**、精确，也不用为各种 fps 密集采样。代价只是上下文略长。

> 一句话：**T-RoPE 把"绝对时间"硬编进旋转位置 → 长视频 id 又大又稀、还逼你密集采各种帧率；Qwen3-VL 改用一句文字时间戳，把时间从"位置"挪到"内容"，又小又准。**

<figure style="margin:26px 0; padding:22px; background:#eef2f7; border:1px solid #9fb3c8; border-radius:4px;">
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:JetBrains Mono,monospace;">
  <!-- T-RoPE -->
  <text x="40" y="36" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#9b2c2c">T-RoPE：t = 绝对时间 → id 又大又稀</text>
  <g font-size="9" text-anchor="middle">
    <rect x="60" y="48" width="40" height="28" fill="#f3d9d9" stroke="#9b2c2c"/><text x="80" y="66" fill="#7a2020">帧</text>
    <rect x="210" y="48" width="40" height="28" fill="#f3d9d9" stroke="#9b2c2c"/><text x="230" y="66" fill="#7a2020">帧</text>
    <rect x="430" y="48" width="40" height="28" fill="#f3d9d9" stroke="#9b2c2c"/><text x="450" y="66" fill="#7a2020">帧</text>
    <rect x="600" y="48" width="40" height="28" fill="#f3d9d9" stroke="#9b2c2c"/><text x="620" y="66" fill="#7a2020">帧</text>
  </g>
  <line x1="60" y1="92" x2="660" y2="92" stroke="#bfb398" stroke-width="1"/>
  <g font-size="9" text-anchor="middle" fill="#9b2c2c" font-weight="700">
    <line x1="80" y1="87" x2="80" y2="97" stroke="#9b2c2c"/><text x="80" y="110">t=0</text>
    <line x1="230" y1="87" x2="230" y2="97" stroke="#9b2c2c"/><text x="230" y="110">t=72</text>
    <line x1="450" y1="87" x2="450" y2="97" stroke="#9b2c2c"/><text x="450" y="110">t=305</text>
    <line x1="620" y1="87" x2="620" y2="97" stroke="#9b2c2c"/><text x="620" y="110">t=588 …</text>
  </g>
  <text x="360" y="130" text-anchor="middle" font-size="9" fill="#9b2c2c">数值巨大(长视频) + 跳着走(采样) → RoPE 外推差 · 要密集采各种 fps 训</text>
  <!-- 分隔 -->
  <line x1="40" y1="148" x2="680" y2="148" stroke="#bfb398" stroke-width="1" stroke-dasharray="4 4"/>
  <!-- 文字时间戳 -->
  <text x="40" y="174" font-family="Fraunces,serif" font-style="italic" font-size="13" font-weight="700" fill="#1f7a5c">Qwen3-VL：文字时间戳 → id 小而密</text>
  <g font-size="8" text-anchor="middle">
    <rect x="60" y="184" width="62" height="26" rx="3" fill="#cfe6d8" stroke="#2f6e4a"/><text x="91" y="201" fill="#1f4a30">&lt;0.0s&gt;</text>
    <rect x="126" y="184" width="34" height="26" fill="#f3d9d9" stroke="#9b2c2c"/><text x="143" y="201" fill="#7a2020">帧</text>
    <rect x="164" y="184" width="62" height="26" rx="3" fill="#cfe6d8" stroke="#2f6e4a"/><text x="195" y="201" fill="#1f4a30">&lt;3.0s&gt;</text>
    <rect x="230" y="184" width="34" height="26" fill="#f3d9d9" stroke="#9b2c2c"/><text x="247" y="201" fill="#7a2020">帧</text>
    <rect x="268" y="184" width="62" height="26" rx="3" fill="#cfe6d8" stroke="#2f6e4a"/><text x="299" y="201" fill="#1f4a30">&lt;7.5s&gt;</text>
    <rect x="334" y="184" width="34" height="26" fill="#f3d9d9" stroke="#9b2c2c"/><text x="351" y="201" fill="#7a2020">帧</text>
  </g>
  <g font-size="8.5" text-anchor="middle" fill="#7a6f5d">
    <text x="91" y="224">0</text><text x="143" y="224">1</text><text x="195" y="224">2</text><text x="247" y="224">3</text><text x="299" y="224">4</text><text x="351" y="224">5</text>
  </g>
  <text x="520" y="200" text-anchor="middle" font-size="9" font-weight="700" fill="#1f7a5c">位置 id 回到 0,1,2,3 小而密</text>
  <text x="520" y="216" text-anchor="middle" font-size="9" fill="#1f7a5c">时间当文字读 → 精确 · 不挑 fps</text>
</svg>
</figure>

## 代码出处
- M-RoPE 原始提法：Qwen2-VL 技术报告（2024）
- Interleaved-MRoPE：Qwen3-VL 技术报告 arXiv 2511.21631（2025-11）
- HuggingFace transformers `Qwen2VLRotaryEmbedding` / `Qwen3VL` 是参考实现

## 链接
- [[rotary-position-embedding]] · 一维原版，M-RoPE 的地基
- [[positional-encoding]] · 位置编码家族全景
- [[qwen3-vl]] · Interleaved-MRoPE 就出自这里
- [[ideogram-4]] · 用 M-RoPE 的位置系实现 bbox 布局控制
