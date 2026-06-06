---
name: structured-caption-conditioning
type: concept
sources: [ideogram-4]
updated: 2026-06-04
---

# 结构化 Caption 条件 · Structured JSON Caption

## 一句话
不喂模型一句话，喂它一份 JSON —— 把画面的每个元素、位置、颜色、文字都显式列出来，训练和推理都用这套结构。

## 直觉
普通 T2I 用自然语言 prompt："夕阳下湖面一艘帆船"。模型得自己猜：帆船多大？放哪？什么色调？—— **模糊语言里藏着大量没说清的关系**，模型只能瞎蒙，所以版面和文字经常翻车。

Ideogram 4 的赌注：与其让模型猜，不如**把结构显式写进 caption**。每条训练 caption 是一份 JSON，穷举画面里每个元素：

- `high_level_description`：整体一句话
- `style_description`：风格 + `color_palette`（最多 16 个 hex 色）
- `compositional_deconstruction.elements[]`：每个元素的描述 + 可选 `bbox`（位置）

关键洞察："**the more relationships each caption pins down, the more grounded supervision the model extracts per training pair**" —— caption 把越多关系钉死，每对训练样本给的监督就越扎实。这跟 fish-speech 把对齐做进权重、dMel 把预处理塌缩是同一条主线：**把结构做进训练，而不是推理时拼 prompt**。

## 怎么做的
训练和推理共用一套格式，推理前按 schema 校验、不合法直接拒：

```json
{
  "high_level_description": "夕阳下湖面一艘木帆船, 冷蓝调",
  "style_description": {
    "lighting": "冷色暮光, 低对比",
    "color_palette": ["#1B3A5C", "#5B8FB9"]
  },
  "compositional_deconstruction": {
    "elements": [
      { "type": "obj", "bbox": [380, 590, 660, 720],
        "desc": "右三分线上的木帆船, 单桅" }
    ]
  }
}
```

三样普通 prompt 给不了的：
- **调色板条件**：直接用 hex 色控主色调（每图 16 色、每元素 5 色），不靠形容词
- **bbox 布局**：`[y_min, x_min, y_max, x_max]` 归一化到 0–1000，模型靠共享的 MRoPE 位置系把元素放到框里
- **文字元素**：一个字段放"要渲染的字面文字"，另一个字段放"它长什么样" → 多行多字体的图内文字

普通用户写一句话也行：一个 "magic prompt" LLM 先把它扩成这套 JSON。

## 链接
- [[ideogram-4]] · 只用结构化 JSON caption 训练
- [[diffusion-transformer]] · bbox 靠 DiT 的 MRoPE 位置系落地
- [[rope]] · 多模态 RoPE 承载 bbox 的空间位置
