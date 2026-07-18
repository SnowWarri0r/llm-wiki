#!/usr/bin/env python3
"""
LLM Wiki renderer — index + auto-page generator.

Scans wiki/*.md (papers / topics / concepts / threads) for frontmatter, then
generates docs/index.html and auto-rendered docs pages for concepts, topics,
and threads. Bespoke paper pages are hand-crafted under docs/<cat>/.

Paper pages that don't have a bespoke HTML yet are listed as TODO so you can
see what's pending.

Also writes docs/style.css (a shared baseline; bespoke pages don't have to
use it).
"""

from __future__ import annotations

import html
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml
import markdown

ROOT = Path(__file__).resolve().parent
WIKI = ROOT / "wiki"
HTML_OUT = ROOT / "docs"
CATEGORIES = ["papers", "books", "topics", "concepts", "threads"]
CATEGORY_LABELS = {
    "papers": "精读页 · Deep Dives",
    "books": "Books · 书籍精讲",
    "topics": "Topics · 综合",
    "concepts": "Concepts · 概念",
    "threads": "Threads · 思考",
}

# 领域标签：frontmatter 里写 tags: [系统] / [金融] / [史] ... 覆盖默认
DOMAIN_ORDER = ["ML", "系统", "金融", "史", "理财"]
# 精读页段内按领域分的小标题
DOMAIN_SUBLABEL = {
    "ML": "ML · 论文",
    "系统": "系统 · Systems",
    "金融": "金融 · Trading & Macro",
    "史": "史 · Classics",
    "理财": "理财 · Personal Finance",
}


def entry_domains(e) -> list:
    """页面的领域标签。显式 tags 优先，否则按 category 推断默认。"""
    tags = e.meta.get("tags")
    if tags:
        return [str(t) for t in (tags if isinstance(tags, list) else [tags])]
    if e.category == "books":
        return ["理财"]
    return ["ML"]


def _strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def entry_search_text(e) -> str:
    """搜索索引文本：标题 + 一句话 + slug + 领域 + 章节标题 + glossary 术语。"""
    parts = [e.title, e.hook, e.slug, str(e.meta.get("type", ""))]
    parts += entry_domains(e)
    page = HTML_OUT / e.category / f"{e.slug}.html"
    if page.exists():
        h = page.read_text()
        for pat in (r"<h2[^>]*>(.*?)</h2>", r"<h3[^>]*>(.*?)</h3>", r'class="term">(.*?)</span>'):
            parts += [_strip_html(m) for m in re.findall(pat, h, re.S)]
    return re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip().lower()


@dataclass
class Entry:
    slug: str
    category: str
    title: str
    meta: dict
    hook: str           # one-line hook from index.md, optional
    bespoke_path: Path | None  # docs/<cat>/<slug>.html if exists


def parse_frontmatter(text: str):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = yaml.safe_load(text[4:end]) or {}
            return fm, text[end + 5 :]
    return {}, text


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback


def extract_one_line(body: str) -> str:
    """First '## 一句话' block content, or first paragraph."""
    m = re.search(r"##\s*一句话\s*\n+([^\n]+)", body)
    if m:
        return m.group(1).strip()
    # fallback: first non-empty non-heading paragraph
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("---"):
            return s
    return ""


def scan_entries() -> list[Entry]:
    entries = []
    for cat in CATEGORIES:
        d = WIKI / cat
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            text = f.read_text()
            meta, body = parse_frontmatter(text)
            slug = meta.get("name", f.stem)
            title = extract_title(body, slug)
            hook = extract_one_line(body)
            page = HTML_OUT / cat / f"{slug}.html"
            auto_rendered = cat in ("concepts", "topics", "threads", "books")
            entries.append(Entry(
                slug=slug,
                category=cat,
                title=title,
                meta=meta,
                hook=hook,
                bespoke_path=page if auto_rendered or page.exists() else None,
            ))
    return entries


CSS = r"""
:root {
  --paper: #f0e9d6;
  --paper-2: #e8e0c8;
  --paper-3: #faf4e1;
  --paper-card: #f7f1de;
  --ink: #181410;
  --ink-2: #3a3128;
  --muted: #7a6f5d;
  --rule: #bfb398;
  --brick: #9b2c2c;
  --brick-soft: #efd6c8;
  --ochre: #b8841c;
  --ochre-soft: #f0e0a8;
  --moss: #4a6b3a;
  --moss-soft: #d8e6ce;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--paper); color: var(--ink); }
body {
  font-family: 'Newsreader', 'Noto Serif SC', Georgia, serif;
  font-size: 18px;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(155,44,44,0.025) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(74,107,58,0.025) 0%, transparent 40%);
}
body::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 100;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.035 0'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>");
  mix-blend-mode: multiply; opacity: 0.5;
}

.page { max-width: 1080px; margin: 0 auto; padding: 56px 32px 120px; }

.masthead {
  border-top: 4px double var(--ink);
  border-bottom: 1px solid var(--rule);
  padding: 14px 0;
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--ink-2);
  margin-bottom: 48px;
}
.masthead .l { font-weight: 700; }
.masthead .r { color: var(--muted); }

.hero { margin-bottom: 64px; }
.hero .issue {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--brick); font-weight: 700;
  margin-bottom: 18px;
  display: flex; align-items: center; gap: 12px;
}
.hero .issue::after { content: ""; flex: 1; height: 1px; background: var(--rule); }
h1.title {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-variation-settings: "opsz" 144, "SOFT" 30, "WONK" 1;
  font-weight: 700;
  font-size: clamp(56px, 9vw, 104px);
  line-height: 0.92;
  letter-spacing: -0.035em;
  margin: 0 0 8px;
}
h1.title .em {
  font-style: italic;
  font-variation-settings: "opsz" 144, "SOFT" 100, "WONK" 1;
  color: var(--brick);
}
.hero .dek {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-variation-settings: "opsz" 36;
  font-style: italic;
  font-weight: 300;
  font-size: clamp(20px, 2.2vw, 26px);
  line-height: 1.4;
  color: var(--ink-2);
  max-width: 720px;
  margin: 20px 0 16px;
}
.hero .meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 1.5px;
  display: flex; gap: 16px;
}

h2 {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-variation-settings: "opsz" 96, "SOFT" 30, "WONK" 1;
  font-weight: 700;
  font-size: 38px;
  letter-spacing: -0.02em;
  margin: 56px 0 20px;
  display: flex; align-items: baseline; gap: 18px;
}
h2 .num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--brick); font-weight: 700;
}

.entries { display: grid; gap: 14px; }
.entry {
  padding: 16px 20px;
  background: var(--paper-card);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--brick);
  border-radius: 0 4px 4px 0;
  transition: transform 0.12s, box-shadow 0.12s;
}
.entry:hover { transform: translateX(2px); box-shadow: 2px 2px 0 var(--ink); }
.entry.todo { border-left-color: var(--muted); opacity: 0.7; background: var(--paper-2); }
.entry.topic { border-left-color: var(--ochre); }
.entry.concept { border-left-color: var(--moss); }
.entry.thread { border-left-color: #6b4a8a; }
.entry.book { border-left-color: var(--brick); }
.entry h3 {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 6px;
  letter-spacing: -0.01em;
}
.entry h3 a {
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px dotted transparent;
}
.entry h3 a:hover { color: var(--brick); border-bottom-color: var(--brick); }
.entry .hook {
  font-size: 16px;
  color: var(--ink-2);
  margin: 0 0 8px;
}
.entry .pills {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--muted);
  text-transform: uppercase;
  display: flex; gap: 10px; flex-wrap: wrap;
  align-items: center;
}
.pill {
  background: var(--paper-3);
  padding: 2px 8px;
  border-radius: 2px;
  border: 1px solid var(--rule);
}
.pill.todo {
  background: transparent;
  border-color: var(--muted);
  color: var(--muted);
}
.pill.ready {
  background: var(--moss-soft);
  color: var(--moss);
  border-color: var(--moss);
  font-weight: 700;
}

.intro {
  background: var(--paper-card);
  border-left: 3px solid var(--ochre);
  padding: 18px 24px;
  border-radius: 0 4px 4px 0;
  margin: 40px 0;
}
.intro p { margin: 8px 0; }
.intro .label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ochre);
  font-weight: 700;
  display: block;
  margin-bottom: 6px;
}

.colophon {
  margin-top: 80px;
  padding-top: 18px;
  border-top: 1px solid var(--rule);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 1px;
}
.colophon a { color: var(--brick); }

/* ============================================================ */
/* Concept / Topic / Thread pages · auto-rendered from md       */
/* ============================================================ */

.page.concept {
  max-width: 760px;
  padding-top: 40px;
}

/* === Header (badge + h1) === */
.concept-header {
  margin: 0 0 48px;
  padding: 0 0 28px;
  border-bottom: 4px double var(--ink);
}
.concept-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  padding: 5px 14px;
  border-radius: 2px;
  font-weight: 700;
  margin-bottom: 20px;
}
.concept-badge.cat-concept {
  background: var(--moss-soft);
  color: var(--moss);
  border: 1px solid var(--moss);
}
.concept-badge.cat-topic {
  background: var(--ochre-soft);
  color: var(--ochre);
  border: 1px solid var(--ochre);
}
.concept-badge.cat-thread {
  background: #e8dcec;
  color: #6b4a8a;
  border: 1px solid #6b4a8a;
}
.concept-badge.cat-book {
  background: var(--brick-soft);
  color: var(--brick);
  border: 1px solid var(--brick);
}

.page.concept h1 {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-variation-settings: "opsz" 144, "SOFT" 30, "WONK" 1;
  font-weight: 700;
  font-size: clamp(34px, 5vw, 52px);
  line-height: 1.05;
  letter-spacing: -0.025em;
  margin: 0;
  color: var(--ink);
}

/* === Body typography === */
.concept-body {
  font-family: 'Newsreader', 'Noto Serif SC', Georgia, serif;
  font-size: 18px;
  line-height: 1.75;
  color: var(--ink-2);
}
.concept-body h2 {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-variation-settings: "opsz" 72, "SOFT" 30;
  font-weight: 700;
  font-size: 26px;
  letter-spacing: -0.015em;
  margin: 44px 0 12px;
  color: var(--ink);
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.concept-body h2::before {
  content: "§";
  font-style: italic;
  font-size: 18px;
  color: var(--moss);
  font-weight: 700;
}
.page.concept[data-cat="topics"] .concept-body h2::before { color: var(--ochre); }
.page.concept[data-cat="threads"] .concept-body h2::before { color: #6b4a8a; }
.concept-body h3 {
  font-family: 'Fraunces', 'Noto Serif SC', serif;
  font-weight: 600;
  font-size: 19px;
  margin: 26px 0 8px;
  color: var(--ink);
}
.concept-body p { margin: 12px 0; }
.concept-body ul, .concept-body ol {
  margin: 12px 0;
  padding-left: 28px;
}
.concept-body li { margin: 6px 0; }
.concept-body li > ul, .concept-body li > ol { margin: 6px 0; }
.concept-body strong { font-weight: 700; color: var(--ink); }
.concept-body em { font-style: italic; color: var(--ink); }
.concept-body code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.86em;
  background: var(--paper-3);
  padding: 1px 6px;
  border-radius: 2px;
  border: 1px solid var(--rule);
  color: var(--ink);
}
.concept-body pre {
  font-family: 'JetBrains Mono', monospace;
  background: var(--paper-3);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--moss);
  padding: 16px 20px;
  border-radius: 3px;
  font-size: 13px;
  overflow-x: auto;
  line-height: 1.65;
  margin: 20px 0;
  color: var(--ink-2);
}
.page.concept[data-cat="topics"] .concept-body pre { border-left-color: var(--ochre); }
.page.concept[data-cat="threads"] .concept-body pre { border-left-color: #6b4a8a; }
.concept-body pre code {
  background: transparent;
  border: none;
  padding: 0;
  font-size: inherit;
  color: inherit;
}

/* === Links (核心修复 · 多组 selector 确保不漏) === */
.concept-body a,
.concept-body a:link,
.concept-body a:visited {
  color: var(--moss);
  text-decoration: underline;
  text-decoration-thickness: 1.2px;
  text-underline-offset: 3px;
  text-decoration-color: var(--moss-soft);
  transition: color 0.15s, text-decoration-color 0.15s;
}
.page.concept[data-cat="topics"] .concept-body a {
  color: var(--ochre);
  text-decoration-color: var(--ochre-soft);
}
.page.concept[data-cat="threads"] .concept-body a {
  color: #6b4a8a;
  text-decoration-color: #e8dcec;
}
.concept-body a:hover {
  color: var(--brick);
  text-decoration-color: var(--brick);
}

/* === Tables === */
.concept-body table {
  border-collapse: collapse;
  margin: 22px 0;
  font-size: 15px;
  width: 100%;
}
.concept-body th, .concept-body td {
  border: 1px solid var(--rule);
  padding: 10px 14px;
  text-align: left;
  vertical-align: top;
}
.concept-body th {
  background: var(--paper-3);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-weight: 700;
  color: var(--ink-2);
}
.concept-body tbody tr:nth-child(even) td {
  background: var(--paper-card);
}

/* === Blockquote === */
.concept-body blockquote {
  border-left: 3px solid var(--rule);
  padding: 4px 18px;
  margin: 18px 0;
  color: var(--muted);
  font-style: italic;
}

/* === Horizontal rule === */
.concept-body hr {
  border: none;
  border-top: 1px dashed var(--rule);
  margin: 36px 0;
}

/* === Backlinks footer === */
.concept-backlinks {
  margin-top: 56px;
  padding: 20px 24px;
  background: var(--paper-card);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--ochre);
  border-radius: 0 4px 4px 0;
}
.concept-backlinks .label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ochre);
  font-weight: 700;
  display: block;
  margin-bottom: 12px;
}
.concept-backlinks ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.concept-backlinks li a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--paper);
  color: var(--ink-2);
  padding: 6px 12px;
  border: 1px solid var(--rule);
  border-radius: 3px;
  text-decoration: none;
  font-family: 'Newsreader', 'Noto Serif SC', serif;
  font-size: 13px;
  transition: all 0.15s;
}
.concept-backlinks li a:hover {
  background: var(--ochre-soft);
  border-color: var(--ochre);
  color: var(--ink);
  transform: translateY(-1px);
}
.concept-backlinks li a .cat {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 1px 5px;
  background: var(--paper-3);
  border-radius: 2px;
}

/* === Missing wikilink === */
a.wikilink-missing {
  color: var(--muted);
  text-decoration: line-through;
  text-decoration-color: var(--brick);
  pointer-events: none;
  cursor: not-allowed;
}

/* === Concept page colophon (slimmer than paper) === */
.page.concept .colophon {
  margin-top: 56px;
  padding-top: 18px;
  border-top: 1px solid var(--rule);
}
.page.concept .colophon a {
  color: var(--brick);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
.page.concept .colophon a:hover { color: var(--ochre); }

/* === Figure animation harness (scroll-triggered, play once) ===
   同 bespoke paper 页的观感：滚动进视口 → figure 加 .play → 子元素分阶段揭示 / 描线。
   概念页 SVG 用 class="reveal d1..d6" / "draw" 即可，JS 在 CONCEPT_PAGE_TEMPLATE 注入。 */
figure svg .reveal { opacity: 0; transition: opacity .55s ease; }
figure.play svg .reveal { opacity: 1; }
figure.play svg .reveal.d1 { transition-delay: .15s; }
figure.play svg .reveal.d2 { transition-delay: .40s; }
figure.play svg .reveal.d3 { transition-delay: .65s; }
figure.play svg .reveal.d4 { transition-delay: .90s; }
figure.play svg .reveal.d5 { transition-delay: 1.15s; }
figure.play svg .reveal.d6 { transition-delay: 1.40s; }
figure.play svg .reveal.d7 { transition-delay: 1.65s; }
figure.play svg .reveal.d8 { transition-delay: 1.90s; }
/* 描线：路径从无到有画出来（需在元素上设 pathLength="1000"） */
figure svg .draw { stroke-dasharray: 1000; stroke-dashoffset: 1000; transition: stroke-dashoffset 1.4s ease; }
figure.play svg .draw { stroke-dashoffset: 0; }
figure svg .draw.d2 { transition-delay: .40s; }
figure svg .draw.d3 { transition-delay: .65s; }
figure svg .draw.d4 { transition-delay: .90s; }
figure svg .draw.d5 { transition-delay: 1.15s; }
/* 高亮脉冲：命中元素轻微放大+亮一下（一次性） */
figure svg .pulse { opacity: 0; transition: opacity .5s ease; }
figure.play svg .pulse { opacity: 1; animation: figPulse 1.1s ease-out .9s; }
@keyframes figPulse { 0%,100% { opacity: .85; } 45% { opacity: .35; } }
/* 横向生长：条形从左长出（概率条/量柱）。配合 .reveal.dN 可错峰 */
figure svg .grow-x { transform: scaleX(0); transform-box: fill-box; transform-origin: left center; transition: transform .7s ease; }
figure.play svg .grow-x { transform: scaleX(1); }
@media (prefers-reduced-motion: reduce) {
  figure svg .reveal, figure svg .draw, figure svg .pulse, figure svg .grow-x { transition: none; opacity: 1; stroke-dashoffset: 0; transform: none; animation: none; }
}
"""


def entry_date(e) -> str:
    """排序/时间线用：ingested 优先，否则 updated。"""
    return str(e.meta.get("ingested") or e.meta.get("updated") or "")


def make_card(e) -> str:
    href = f"{e.category}/{e.slug}.html" if e.bespoke_path else None
    ready = bool(e.bespoke_path)
    doms = entry_domains(e)
    stext = entry_search_text(e)
    pills = [f'<span class="pill dom dom-{html.escape(d)}">{html.escape(d)}</span>' for d in doms]
    pills.append(f'<span class="pill">{e.meta.get("type", e.category[:-1] if e.category.endswith("s") else e.category)}</span>')
    if e.meta.get("_chapters"):
        pills.append(f'<span class="pill">{e.meta["_chapters"]} 章</span>')
    if "updated" in e.meta:
        pills.append(f'<span class="pill">updated {html.escape(str(e.meta["updated"]))}</span>')
    if "ingested" in e.meta:
        pills.append(f'<span class="pill">ingested {html.escape(str(e.meta["ingested"]))}</span>')
    if "upstream" in e.meta:
        pills.append(f'<a class="pill" href="{html.escape(e.meta["upstream"])}" target="_blank" style="text-decoration:none;color:var(--muted);">↗ upstream</a>')
    if ready and e.category == "papers":
        pills.append('<span class="pill ready">bespoke HTML ✓</span>')
    elif ready:
        pills.append('<span class="pill ready">auto HTML ✓</span>')
    else:
        pills.append('<span class="pill todo">md only · 待做 bespoke HTML</span>')
    title_link = f'<a href="{href}">{html.escape(e.title)}</a>' if href else html.escape(e.title)
    entry_class = f"entry {e.category[:-1] if e.category.endswith('s') else e.category}"
    if not ready:
        entry_class += " todo"
    hook_html = ('<p class="hook">' + html.escape(e.hook) + '</p>') if e.hook else ''
    return (f'<div class="{entry_class}" data-domains="{html.escape(" ".join(doms))}" data-s="{html.escape(stext, quote=True)}">\n'
            f'  <h3>{title_link}</h3>\n'
            f'  {hook_html}\n'
            f'  <div class="pills">{"".join(pills)}</div>\n'
            f'</div>')


CATEGORY_DESC = {
    "papers": "手工打磨的论文 / 源码精读页",
    "books": "非 ML 书籍的章节精讲",
    "topics": "跨多个源的横向综合",
    "concepts": "跨论文复用的概念颗粒",
    "threads": "个人思考线 / 开放问题",
}

LIST_CSS = """
.search { margin: 28px 0 8px; }
.search input { width: 100%; box-sizing: border-box; font-family: 'JetBrains Mono', monospace; font-size: 15px; padding: 14px 16px; border: 1px solid var(--rule); border-radius: 6px; background: var(--paper-card); color: var(--ink); }
.search input:focus { outline: none; border-color: var(--brick); }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.chip { font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 1px; padding: 5px 13px; border: 1px solid var(--rule); border-radius: 20px; background: transparent; color: var(--ink-2); cursor: pointer; transition: all 0.15s; }
.chip:hover { border-color: var(--brick); }
.chip.active { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.chip .c { opacity: 0.55; font-size: 10px; }
.pill.dom { font-weight: 700; border-color: var(--ink-2); }
.nores { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--muted); padding: 36px 0; text-align: center; }
.entries { margin-top: 18px; }
"""

LANDING_CSS = """
.catcards { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; margin: 18px 0 8px; }
.catcard { display: block; border: 1px solid var(--rule); border-radius: 8px; padding: 18px 20px; background: var(--paper-card); text-decoration: none; color: var(--ink); transition: all 0.15s; }
.catcard:hover { border-color: var(--brick); transform: translateY(-2px); }
.catcard .n { font-family: 'JetBrains Mono', monospace; font-size: 30px; font-weight: 700; color: var(--brick); line-height: 1; }
.catcard .lbl { display: block; font-family: 'Fraunces', serif; font-weight: 700; font-size: 17px; margin-top: 6px; }
.catcard .d { display: block; font-size: 13px; color: var(--muted); margin-top: 4px; }
.timeline { margin: 12px 0; }
.tl-row { display: flex; align-items: baseline; gap: 14px; padding: 11px 4px; border-bottom: 1px dashed var(--rule); text-decoration: none; color: var(--ink); }
.tl-row:hover { background: var(--paper-3); }
.tl-date { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); min-width: 80px; flex-shrink: 0; }
.tl-cat { font-family: 'JetBrains Mono', monospace; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--brick); min-width: 64px; flex-shrink: 0; }
.tl-title { font-weight: 700; flex-shrink: 0; }
.tl-hook { color: var(--muted); font-size: 14px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 700px) { .tl-hook { display: none; } }
"""

FILTER_JS = """
(function(){
  var q = document.getElementById('q');
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var entries = [].slice.call(document.querySelectorAll('.entry'));
  var nores = document.getElementById('nores');
  var dom = '';
  function apply(){
    var term = q.value.trim().toLowerCase();
    var shown = 0;
    entries.forEach(function(el){
      var okT = !term || (el.getAttribute('data-s') || '').indexOf(term) !== -1;
      var okD = !dom || (el.getAttribute('data-domains') || '').split(' ').indexOf(dom) !== -1;
      var vis = okT && okD;
      el.style.display = vis ? '' : 'none';
      if (vis) shown++;
    });
    nores.hidden = shown !== 0;
  }
  q.addEventListener('input', apply);
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      chips.forEach(function(x){ x.classList.remove('active'); });
      c.classList.add('active');
      dom = c.getAttribute('data-dom') || '';
      apply();
    });
  });
})();
"""

FONTS_LINK = '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&family=Newsreader:opsz,wght@6..72,300..700&family=Noto+Serif+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">'


def _doc_head(title_tag: str, extra_css: str = "") -> str:
    return (
        '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8" />\n'
        f'<title>{title_tag}</title>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        + FONTS_LINK + '\n'
        '<link rel="stylesheet" href="style.css" />\n'
        f'<style>\n{extra_css}\n</style>\n</head>\n<body>\n<div class="page">\n'
    )


def _masthead(right: str) -> str:
    return ('<div class="masthead">\n'
            '  <span class="l">Connectionism · Personal Wiki</span>\n'
            f'  <span class="r">{html.escape(right)}</span>\n</div>\n')


COLOPHON = ('<div class="colophon">\n'
            '  Renderer / <code>render.py</code> · Pattern / '
            '<a href="https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f" target="_blank">Karpathy LLM Wiki</a> · '
            'Source / <a href="https://github.com/SnowWarri0r/llm-wiki" target="_blank">github.com/SnowWarri0r/llm-wiki</a>\n</div>\n')


def render_category_page(cat: str, items: list) -> str:
    items = sorted(items, key=entry_date, reverse=True)
    book_note = ""
    if cat == "books":
        # 书架视图：只把"书"当卡片，章节收进各自书页的目录里。
        chap_count: dict = {}
        for e in items:
            if e.meta.get("type") == "chapter":
                b = e.meta.get("book")
                chap_count[b] = chap_count.get(b, 0) + 1
        overviews = [e for e in items if e.meta.get("type") == "book"]
        for e in overviews:
            e.meta["_chapters"] = chap_count.get(e.slug, 0)
        n_chapters = sum(chap_count.values())
        items = overviews
        book_note = f"{len(items)} 本书 · {n_chapters} 章精讲"
    cards = "\n".join(make_card(e) for e in items)
    dom_count: dict = {}
    for e in items:
        for d in entry_domains(e):
            dom_count[d] = dom_count.get(d, 0) + 1
    ordered = [d for d in DOMAIN_ORDER if d in dom_count] + sorted(d for d in dom_count if d not in DOMAIN_ORDER)
    chips = [f'<button class="chip active" data-dom="">全部 <span class="c">{len(items)}</span></button>']
    for d in ordered:
        chips.append(f'<button class="chip" data-dom="{html.escape(d)}">{html.escape(d)} <span class="c">{dom_count[d]}</span></button>')
    chips_html = "".join(chips)
    label = CATEGORY_LABELS[cat]
    return (
        _doc_head(f"个人 wiki · {label}", LIST_CSS)
        + _masthead(f"{label} · {book_note or str(len(items)) + ' 条目'}")
        + '\n<section class="hero">\n'
          '  <div class="issue"><a href="index.html" style="color:var(--brick);text-decoration:none;">← index</a> · 按时间倒序</div>\n'
          f'  <h1 class="title">{html.escape(label)}</h1>\n'
          f'  <p class="dek">{html.escape(book_note) + "，每本点进书页看章节目录。" if book_note else "共 " + str(len(items)) + " 条，最新在上。"}</p>\n</section>\n'
        + '\n<div class="search">\n'
          '  <input id="q" type="search" placeholder="搜索 标题 / 概念 / 术语…" autocomplete="off" spellcheck="false" />\n'
          f'  <div class="chips">{chips_html}</div>\n</div>\n'
          '<div id="nores" class="nores" hidden>没有匹配的条目 — 换个词试试</div>\n'
        + f'<div class="entries">\n{cards}\n</div>\n'
        + COLOPHON
        + f'\n</div>\n<script>\n{FILTER_JS}\n</script>\n</body>\n</html>\n'
    )


def render_index(entries: list) -> str:
    by_cat = {c: [] for c in CATEGORIES}
    for e in entries:
        by_cat[e.category].append(e)
    cards = []
    for cat in CATEGORIES:
        its = by_cat[cat]
        if not its:
            continue
        count = len(its)
        desc = CATEGORY_DESC.get(cat, "")
        if cat == "books":
            # 书按"本"计数，章节数放进描述，别把 N 本书显示成 N 条
            count = sum(1 for e in its if e.meta.get("type") == "book")
            n_chap = sum(1 for e in its if e.meta.get("type") == "chapter")
            desc = f"{count} 本书 · {n_chap} 章精讲"
        cards.append(
            f'<a class="catcard" href="{cat}.html">'
            f'<span class="n">{count}</span>'
            f'<span class="lbl">{html.escape(CATEGORY_LABELS[cat])}</span>'
            f'<span class="d">{html.escape(desc)}</span></a>'
        )
    cards_html = "\n".join(cards)
    # "最近更新"里书只显示书本身，不让一本书的几十章刷屏
    recent = sorted(
        [e for e in entries if e.meta.get("type") != "chapter"],
        key=entry_date, reverse=True,
    )[:14]
    rows = []
    for e in recent:
        href = f"{e.category}/{e.slug}.html" if e.bespoke_path else f"{e.category}.html"
        catname = e.category[:-1] if e.category.endswith("s") else e.category
        rows.append(
            f'<a class="tl-row" href="{href}">'
            f'<span class="tl-date">{html.escape(entry_date(e) or "—")}</span>'
            f'<span class="tl-cat">{html.escape(catname)}</span>'
            f'<span class="tl-title">{html.escape(e.title)}</span>'
            f'<span class="tl-hook">{html.escape(e.hook)}</span></a>'
        )
    rows_html = "\n".join(rows)
    return (
        _doc_head("个人 wiki · index", LANDING_CSS)
        + _masthead(f"索引 · {len(entries)} 条目")
        + '\n<section class="hero">\n'
          '  <div class="issue">FIELD NOTES · 个人学习 / 多领域</div>\n'
          '  <h1 class="title">Study<br /><span class="em">Index.</span></h1>\n'
          '  <p class="dek">按 Karpathy <a href="https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f" target="_blank" style="color:var(--brick);">LLM Wiki</a> 模式：每个主题一份独立静态 HTML。这页只做目录 —— 按类型进子页，或看最近更新。</p>\n</section>\n'
        + '\n<h2><span class="num">§ 01</span>浏览 · Browse by type</h2>\n'
          f'<div class="catcards">\n{cards_html}\n</div>\n'
        + '\n<h2><span class="num">§ 02</span>最近更新 · Recent</h2>\n'
          f'<div class="timeline">\n{rows_html}\n</div>\n'
        + COLOPHON
        + '\n</div>\n</body>\n</html>\n'
    )


NAV_START = "<!-- wiki-nav:start -->"
NAV_END = "<!-- wiki-nav:end -->"


def build_nav_strip(category: str, slug: str) -> str:
    """The dark thin bar injected at top of every bespoke page."""
    return f"""{NAV_START}
<style>
.wiki-nav {{
  background: #181410; color: #e8e0c8;
  padding: 8px 22px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #3a3128;
  position: sticky; top: 0; z-index: 1001;
}}
.wiki-nav a {{ color: #e8e0c8; text-decoration: none; border-bottom: none; }}
.wiki-nav a:hover {{ color: #efd6c8; }}
.wiki-nav .ws-r {{ color: #b8841c; }}
</style>
<div class="wiki-nav">
  <span><a href="../index.html">← 个人 wiki / index</a></span>
  <span class="ws-r"><a href="../{html.escape(category)}.html" style="color:#b8841c;">{html.escape(category)}</a> · {html.escape(slug)}</span>
</div>
{NAV_END}
"""


def inject_nav_strip(path: Path, category: str, slug: str) -> bool:
    """Inject (or refresh) the wiki nav strip in a bespoke HTML page.

    Idempotent: if a strip already exists (marked by NAV_START/NAV_END),
    it's removed first, then the fresh one is written. Returns True if
    the file was changed."""
    text = path.read_text()
    original = text

    # strip existing (if any) — consume any trailing newlines so we don't accrete blank lines
    if NAV_START in text:
        text = re.sub(
            re.escape(NAV_START) + r".*?" + re.escape(NAV_END) + r"\n*",
            "",
            text,
            flags=re.DOTALL,
        )

    # normalize strip to end with exactly one \n
    strip = build_nav_strip(category, slug).rstrip("\n") + "\n"
    # consume any newlines right after <body> so we don't double them
    new_text, n = re.subn(r"(<body[^>]*>)\n*", r"\1\n" + strip, text, count=1)
    if n == 0:
        return False
    if new_text == original:
        return False
    path.write_text(new_text)
    return True


# ============================================================
# Glossary popover (点术语 → 右侧浮卡，不跳页)
# ============================================================

GLOSS_POP_START = "<!-- gloss-popover:start -->"
GLOSS_POP_END = "<!-- gloss-popover:end -->"

GLOSS_POP_BLOCK = GLOSS_POP_START + """
<style>
.jr-pop{position:fixed;z-index:1002;right:20px;top:50%;transform:translateY(-50%);width:min(330px,86vw);max-height:78vh;overflow:auto;background:var(--paper-card,#f7f1de);color:var(--ink,#181410);border:1px solid var(--rule,#bfb398);border-left:4px solid var(--accent,#9b2c2c);border-radius:6px;box-shadow:0 10px 34px rgba(24,20,16,.20);padding:16px 20px 16px 18px;font-family:'Newsreader','Noto Serif SC',Georgia,serif;font-size:15px;line-height:1.62;display:none;}
.jr-pop.show{display:block;animation:jrPopIn .18s ease;}
@keyframes jrPopIn{from{opacity:0;}to{opacity:1;}}
.jr-pop .jr-pop-num{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accent,#9b2c2c);font-weight:700;letter-spacing:1px;margin-right:4px;}
.jr-pop .jr-pop-close{position:absolute;top:6px;right:9px;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--muted,#7a6f5d);border:none;background:none;line-height:1;}
.jr-pop .jr-pop-close:hover{color:var(--ink,#181410);}
.jr-pop .term{font-family:'Fraunces',serif;font-weight:700;font-style:italic;}
.jr-pop a{color:var(--accent,#9b2c2c);}
a.jr.jr-active{background:var(--accent,#9b2c2c);color:var(--paper,#f0e9d6);}
@media(max-width:820px){.jr-pop{right:0;left:0;bottom:0;top:auto;transform:none;width:auto;max-height:55vh;border-radius:12px 12px 0 0;border-left:1px solid var(--rule,#bfb398);border-top:4px solid var(--accent,#9b2c2c);}}
@media print{.jr-pop{display:none!important;}}
</style>
<script>
(function(){
  var items={};
  document.querySelectorAll('.gloss ol li[id^="g-"]').forEach(function(li){items[li.id]=li.innerHTML;});
  if(!Object.keys(items).length)return;
  var pop=document.createElement('div');pop.className='jr-pop';
  pop.innerHTML='<button class="jr-pop-close" aria-label="close">✕</button><div class="jr-pop-body"></div>';
  document.body.appendChild(pop);
  var body=pop.querySelector('.jr-pop-body');var active=null;
  function hide(){pop.classList.remove('show');if(active){active.classList.remove('jr-active');active=null;}}
  pop.querySelector('.jr-pop-close').addEventListener('click',hide);
  document.querySelectorAll('a.jr[href^="#g-"]').forEach(function(a){
    a.addEventListener('click',function(e){
      var id=a.getAttribute('href').slice(1);
      if(!items[id])return;
      e.preventDefault();
      body.innerHTML='<span class="jr-pop-num">'+id.replace('g-','')+'</span> '+items[id];
      pop.classList.add('show');
      if(active)active.classList.remove('jr-active');active=a;a.classList.add('jr-active');
    });
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape')hide();});
  document.addEventListener('click',function(e){
    if(pop.classList.contains('show')&&!pop.contains(e.target)&&!(e.target.closest&&e.target.closest('a.jr')))hide();
  });
})();
</script>
""" + GLOSS_POP_END + "\n"


def inject_glossary_popover(path: Path) -> bool:
    """Inject (or refresh) the click-to-float glossary popover before </body>.

    Idempotent (marker-bounded). Progressive enhancement: the bottom <ol>
    glossary + #g-NN anchors stay as a no-JS / print fallback. Returns True
    if the file changed."""
    text = path.read_text()
    original = text
    # strip any existing block first (idempotent)
    if GLOSS_POP_START in text:
        text = re.sub(
            re.escape(GLOSS_POP_START) + r".*?" + re.escape(GLOSS_POP_END) + r"\n*",
            "",
            text,
            flags=re.DOTALL,
        )
    # only pages with an actual bottom glossary need the popover
    if 'class="gloss"' not in text:
        if text != original:           # we stripped a now-stale block (page lost its glossary)
            path.write_text(text)
            return True
        return False
    block = GLOSS_POP_BLOCK.rstrip("\n") + "\n"
    new_text, n = re.subn(r"</body>", lambda m: block + m.group(0), text, count=1)
    if n == 0 or new_text == original:
        return False
    path.write_text(new_text)
    return True


# ============================================================
# Slug index + wikilink resolution
# ============================================================

SLUG_INDEX: dict = {}  # slug -> {category, title}
WIKILINK_RE = re.compile(r"\[\[([a-z][a-z0-9-]*)\]\]")


def build_slug_index(entries: list[Entry]) -> dict:
    return {
        e.slug: {"category": e.category, "title": e.title}
        for e in entries
    }


def scan_missing_slugs() -> dict[str, list[str]]:
    """Walk every wiki/*.md, return {missing_slug: [source_md_path, ...]}."""
    missing: dict[str, list[str]] = defaultdict(list)
    for cat in CATEGORIES:
        cat_dir = WIKI / cat
        if not cat_dir.exists():
            continue
        for f in sorted(cat_dir.glob("*.md")):
            text = f.read_text()
            for slug in WIKILINK_RE.findall(text):
                if slug not in SLUG_INDEX:
                    missing[slug].append(f"{cat}/{f.stem}")
    return missing


def resolve_wikilinks(text: str, from_dir: str = "papers") -> str:
    """Replace [[slug]] with <a> linking to the resolved category page.

    from_dir is the dir of the file containing the [[slug]] (e.g. 'papers',
    'concepts', 'topics'). Used to compute relative path.
    """
    def repl(m):
        slug = m.group(1)
        info = SLUG_INDEX.get(slug)
        if info is None:
            return f'<a class="wikilink-missing" title="missing slug">{slug}</a>'
        # Both from_dir and target are inside docs/<cat>/, so use ../<cat>/
        return f'<a href="../{info["category"]}/{slug}.html">{slug}</a>'
    return WIKILINK_RE.sub(repl, text)


def find_backlinks(target_slug: str) -> list[tuple]:
    """Find all md files in papers/topics/concepts/threads that contain [[target_slug]]."""
    pat = re.compile(rf"\[\[{re.escape(target_slug)}\]\]")
    out = []
    for cat in CATEGORIES:
        d = WIKI / cat
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.stem == target_slug:
                continue
            text = f.read_text()
            if pat.search(text):
                info = SLUG_INDEX.get(f.stem)
                title = info["title"] if info else f.stem
                out.append((cat, f.stem, title))
    return out


# ============================================================
# Concept / topic / thread page renderer
# ============================================================

CONCEPT_PAGE_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>{title} · {cat_label}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&family=Newsreader:opsz,wght@6..72,300..700&family=Noto+Serif+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../style.css" />
</head>
<body>
<div class="page concept" data-cat="{category}">

<header class="concept-header">
  <span class="concept-badge cat-{cat_singular}">{cat_label}</span>
  <h1>{title}</h1>
</header>

<article class="concept-body">
{body_html}
</article>

{backlinks_html}

<div class="colophon">
  <span>Auto-rendered from <code>wiki/{category}/{slug}.md</code></span>
  <span>← <a href="../index.html">个人 wiki / index</a></span>
</div>

</div>
<script>
// 滚动进视口 → 给 figure 加 .play（播一次就 disconnect），驱动 .reveal/.draw/.pulse
(function () {{
  var figs = document.querySelectorAll('figure');
  if (!('IntersectionObserver' in window) || !figs.length) {{
    figs.forEach(function (f) {{ f.classList.add('play'); }});
    return;
  }}
  var obs = new IntersectionObserver(function (es) {{
    es.forEach(function (e) {{
      if (e.isIntersecting) {{ e.target.classList.add('play'); obs.unobserve(e.target); }}
    }});
  }}, {{ threshold: 0.25 }});
  figs.forEach(function (f) {{ obs.observe(f); }});
}})();
</script>
</body>
</html>
"""


def normalize_md(text: str) -> str:
    """Pre-process markdown so python-markdown renders it sanely.

    Bug being fixed:
      "段落:\n- bullet" → python-markdown 把 - bullet 当成段落延续。
    Fix: 在 list item 前缺空行时自动插入。

    也处理 ordered list (1. 2. ...) 同样的问题。
    """
    list_re = re.compile(r"^(\s*)([-*+]|\d+\.)\s")
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if list_re.match(line):
            prev = out[-1] if out else ""
            prev_stripped = prev.rstrip()
            # If previous line is non-empty and non-list → inject blank line
            if prev_stripped and not list_re.match(prev_stripped):
                out.append("")
        out.append(line)
    return "\n".join(out)


def render_concept_page(entry: Entry) -> str:
    md_path = WIKI / entry.category / f"{entry.slug}.md"
    text = md_path.read_text()
    _, body = parse_frontmatter(text)

    # Strip leading blank lines, then the "# Title" heading (we render it in the template)
    body = body.lstrip()
    body = re.sub(r"^#\s+.+?(?:\n|$)", "", body, count=1).lstrip()

    # Resolve [[wikilinks]] BEFORE markdown so they become <a> tags pre-conversion
    body = resolve_wikilinks(body, from_dir=entry.category)

    # Rewrite [text](foo.md) → [text](foo.html) so md cross-links resolve in served HTML
    body = re.sub(r"\]\(([^)]+)\.md\)", r"](\1.html)", body)

    # Normalize list spacing so python-markdown actually renders them
    body = normalize_md(body)

    # md → html
    body_html = markdown.markdown(
        body,
        extensions=["fenced_code", "tables", "sane_lists", "attr_list"],
    )

    # Build backlinks block
    backlinks = find_backlinks(entry.slug)
    if backlinks:
        items = "".join(
            f'<li><a href="../{cat}/{slug}.html"><span class="cat">{cat[:-1] if cat.endswith("s") else cat}</span>{html.escape(title)}</a></li>'
            for cat, slug, title in backlinks
        )
        backlinks_html = (
            f'<div class="concept-backlinks">\n'
            f'  <span class="label">引用此页的内容 · {len(backlinks)} 处</span>\n'
            f'  <ul>{items}</ul>\n'
            f'</div>'
        )
    else:
        backlinks_html = ""

    cat_singular = entry.category[:-1] if entry.category.endswith("s") else entry.category
    cat_label = {
        "concepts": "Concept",
        "topics": "Topic",
        "threads": "Thread",
        "papers": "Paper",
        "books": "Book",
    }.get(entry.category, entry.category)

    return CONCEPT_PAGE_TEMPLATE.format(
        title=html.escape(entry.title),
        slug=entry.slug,
        category=entry.category,
        cat_singular=cat_singular,
        cat_label=cat_label,
        body_html=body_html,
        backlinks_html=backlinks_html,
    )


# ============================================================
# Bespoke HTML post-processing: replace [[slug]] with <a>
# ============================================================

def repair_missing_wikilink_anchors(text: str) -> str:
    """If a slug used to be missing but now exists, turn the placeholder into a link."""

    def repl(m: re.Match) -> str:
        slug = m.group(1)
        target = SLUG_INDEX.get(slug)
        if not target:
            return m.group(0)
        return f'<a href="../{target["category"]}/{slug}.html">{html.escape(slug)}</a>'

    return re.sub(
        r'<a class="wikilink-missing" title="missing slug">([^<]+)</a>',
        repl,
        text,
    )


def inject_wikilinks(path: Path, from_dir: str) -> bool:
    """In bespoke HTML, replace [[slug]] and repair old missing-link placeholders.

    Idempotent — re-running keeps existing resolved links stable.
    """
    text = path.read_text()
    if "[[" not in text and "wikilink-missing" not in text:
        return False
    new_text = resolve_wikilinks(text, from_dir=from_dir)
    new_text = repair_missing_wikilink_anchors(new_text)
    if new_text == text:
        return False
    path.write_text(new_text)
    return True


# ============================================================
# Main
# ============================================================

def main():
    global SLUG_INDEX
    HTML_OUT.mkdir(exist_ok=True)
    (HTML_OUT / "style.css").write_text(CSS)
    entries = scan_entries()

    SLUG_INDEX = build_slug_index(entries)

    # 1. Render auto pages for concepts / topics / threads / books
    #    Skip if a bespoke HTML already exists (allows hand-crafted topic pages)
    auto_rendered = 0
    for e in entries:
        if e.category in ("concepts", "topics", "threads", "books"):
            out_dir = HTML_OUT / e.category
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / f"{e.slug}.html"
            if out_path.exists() and "<!-- bespoke -->" in out_path.read_text()[:200]:
                continue
            out_path.write_text(render_concept_page(e))
            inject_nav_strip(out_path, e.category, e.slug)
            auto_rendered += 1

    # 2. Inject nav strip + resolve [[wikilinks]] in bespoke HTML
    injected = 0
    linked = 0
    popped = 0
    for e in entries:
        if e.bespoke_path and e.bespoke_path.exists():
            if inject_nav_strip(e.bespoke_path, e.category, e.slug):
                injected += 1
            if inject_wikilinks(e.bespoke_path, e.category):
                linked += 1
            if inject_glossary_popover(e.bespoke_path):
                popped += 1

    # 3. Render landing index + per-category sub-pages（按时间倒序）
    (HTML_OUT / "index.html").write_text(render_index(entries))
    by_cat_pages = defaultdict(list)
    for e in entries:
        by_cat_pages[e.category].append(e)
    cat_pages = 0
    for cat in CATEGORIES:
        if by_cat_pages[cat]:
            (HTML_OUT / f"{cat}.html").write_text(render_category_page(cat, by_cat_pages[cat]))
            cat_pages += 1
    print(f"index.html + {cat_pages} category pages rendered with {len(entries)} entries")
    ready = sum(1 for e in entries if e.bespoke_path)
    print(f"  HTML pages ready: {ready}")
    print(f"  待做: {len(entries) - ready}")
    print(f"  nav strip refreshed in {injected} bespoke pages")
    print(f"  glossary popover injected in {popped} bespoke pages")
    print(f"  wikilinks resolved in {linked} bespoke pages")
    print(f"  auto-rendered concept/topic/thread pages: {auto_rendered}")

    # 4. Missing-slug gate
    missing = scan_missing_slugs()
    if missing:
        print()
        print(f"✗ {len(missing)} missing [[slug]] target(s) — fix before commit:")
        for slug in sorted(missing):
            sources = ", ".join(missing[slug])
            print(f"    [[{slug}]]  ← referenced by {sources}")
        print()
        print("  补法: 在 wiki/concepts/<slug>.md 写一份 stub (5 段模板)，或修正错别字。")
        sys.exit(1)


if __name__ == "__main__":
    main()
