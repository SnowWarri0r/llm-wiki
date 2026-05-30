# LLM Wiki — 个人学习笔记

这是 Karpathy "LLM Wiki" 模式（https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f）在我自己机器上的实例。**LLM 维护，人类导航**。

## 目录约定

```
study/
├── CLAUDE.md      # 本文件，schema + 工作流
├── index.md       # 目录：所有 wiki 页按类别列出
├── log.md         # 时间线：每次 ingest/query/lint 追加一行
├── raw/           # 原始源（PDF、HTML、txt、repo 引用）。只读，LLM 不改。
├── wiki/
│   ├── concepts/  # 跨论文的概念页：RVQ、GRPO、micro-turn、early fusion ...
│   ├── papers/    # 一篇 ML 论文/HTML/repo 一页：摘要 + 我自己的批注
│   ├── books/     # 一本书一组页：书概览 + 每章精讲（非 ML / 跨领域）
│   ├── topics/    # 综合页：跨多个源的横向比较
│   └── threads/   # 个人思考线索 / open questions
└── docs/          # GitHub Pages 服务的静态站点
                #   - index.html (由 render.py 渲染的目录页)
                #   - papers/<slug>.html 是 bespoke 手工打磨
                #   - books/concepts/topics/threads 自动渲染
```

## 用户偏好（不可省略）

用户的 ML 背景：跑过 fish-speech、做过 LoRA、懂 Transformer 概念但抗拒数学。

**讲解风格硬规则**：
- 直觉先行，数学符号尽量替换成代码或类比
- 类比要落到熟悉的领域（编程、工程系统、日常物件）
- 必给"为什么这么干"——背后的痛点 / 替代方案 / trade-off
- 不写空泛的"x 是一种 y" 定义句

## 页面模板

每个 `wiki/concepts/<name>.md` 页固定五段：

```markdown
---
name: <kebab-case-slug>
type: concept
sources: [<paper-name>, <paper-name>]   # 哪些 papers/ 页引用了它
updated: 2026-05-20
---

# <概念名>

## 一句话
<不超过 30 字的精炼描述>

## 直觉
<类比、为什么需要它、它替代了什么>

## 怎么做的
<机制描述。可以放伪代码或简化公式，但不要纯数学推导>

## 代码出处
<指向 raw/ 或外部 repo 的具体文件:行号>

## 链接
- [[<related-concept>]] — 关系一句话
- [[<paper-name>]] — 在哪用到
```

每个 `wiki/papers/<name>.md` 固定结构：

```markdown
---
name: <slug>
type: paper
source: raw/<filename>
ingested: 2026-05-20
---

# <标题>

## 一句话
## 它要解决的痛点
## 核心贡献（2-5 个 bullet）
## 关键概念 → 概念页链接
## 我的批注 / 疑问
```

## 工作流

### Ingest（吃源）
1. 用户告知新源（路径或 URL）→ 放入 `raw/`（或在 raw/ 写一个 stub 指针）
2. LLM 读源 → 跟用户简短讨论关键点
3. 写 `wiki/papers/<name>.md`
4. 抽出新概念，写 `wiki/concepts/<concept>.md`；已有的页面更新 sources 字段 + 增量内容
5. 更新 `index.md`：按类别加新条目
6. 追加 `log.md` 一行：`## [YYYY-MM-DD] ingest | <name>`
7. 重新生成 `docs/index.html`

### Query（提问 / 复习）
1. LLM 读 `index.md` 找相关页
2. 答完后判断：这个答案值得归档吗？值得 → 写成 `wiki/topics/<name>.md` 或 `wiki/threads/<name>.md`
3. 追加 `log.md`：`## [YYYY-MM-DD] query | <topic>`

### Lint（体检）
- 查矛盾、孤儿页、缺交叉引用、stale 断言
- 建议补什么源 / 问什么新问题

## HTML 输出 / 部署

**papers 面向人的版本主要是 bespoke HTML**。每篇 paper 在 `docs/papers/<slug>.html` 手工打磨，自带动画、配图、独立排版。md 做内部 ER + scaffold。

**concepts / topics / threads 由 `render.py` 自动渲染**。`render.py` 扫 wiki/ 所有 md frontmatter，生成 `docs/index.html`、概念/主题/thread 页面，并给 bespoke 页面注入 wiki nav、解析 `[[wikilink]]`。每次 ingest / lint 后跑一次：

```
python3 render.py
```

部署 GitHub Pages：Settings → Pages → Source = main branch / `/docs` 文件夹。commit + push 后自动上线。

URL: https://snowwarri0r.github.io/llm-wiki/

## Claude Code 补强规则

Claude Code 容易犯的不是"不会写"，而是**忘记当前仓库已经演化过**。每次改这个 repo：

1. **看 `log.md` 最近几条**，对齐到当前演化状态再动手。
2. **改 Markdown 后必须跑 `python3 render.py`**，因为 `docs/` 是发布源；只改 `wiki/` 不渲染等于没上线。
3. **render 在有 `[[missing-slug]]` 时退出非零** —— 写新 wikilink 前先检查 `wiki/concepts/` 有没有同名页，没有就顺手补一份 stub，避免读者点到死链。

## 当前快照

- 起步日期：2026-05-20
- 已 ingest 源：
  - ResNet / Attention / BERT / GPT-1 / GPT-2 / GPT-3
  - Flow Matching / dMel
  - Thinking Machines · Interaction Models（HTML 中文版）
  - fish-speech（GitHub repo）
- 渲染策略：paper bespoke 优先；concept/topic/thread 自动 HTML 兜底
