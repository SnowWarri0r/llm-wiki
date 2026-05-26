# llm-wiki

个人 LLM 学习 wiki。按 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式组织。

**Live**: https://snowwarri0r.github.io/llm-wiki/

## 工作分层

- `wiki/` — Markdown 笔记，做内部 ER + 链接 + 协作脚手架（人不直接看）
- `docs/` — 静态 HTML 站点（GitHub Pages 服务）
  - `index.html` 由 `render.py` 自动生成
  - `docs/concepts|topics|threads/*.html` 由 Markdown 自动渲染，保证链接可走
  - `docs/papers/*.html` 主要手工打磨，自带动画/图表
- `raw/` — 原始源（论文 PDF、博客 HTML、外部 repo 软链）
- `CLAUDE.md` — schema + 工作流约定（给 LLM agent 看的）

## 渲染目录页

```
python3 render.py
```

扫 `wiki/*.md` frontmatter，重新生成 `docs/index.html`、概念/主题/thread 页面，并刷新 bespoke 页面顶部导航与 `[[wikilink]]`。

## 当前快照

- 起步日期：2026-05-20
- 公开站点：<https://snowwarri0r.github.io/llm-wiki/>
- 当前主线：从 ResNet → Transformer → BERT/GPT 系 → Flow Matching / dMel → TML interaction model / fish-speech
- 仓库协作重点：Markdown 做知识图谱和 agent 脚手架，HTML 做人读的交互讲解
