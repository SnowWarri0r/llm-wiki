#!/usr/bin/env python3
"""给 glossary 孤儿条目在正文里补 .jr 入口。

用法:
    python3 fix_gloss_orphans.py          # 干跑，只打印会改哪里
    python3 fix_gloss_orphans.py --apply  # 真改

两种 .jr 写法都支持：
  包裹式  <a class="jr" href="#g-01">RNN<sup>1</sup></a>   （attention / fish-speech）
  上标式  术语<a class="jr" href="#g-01">1</a>              （其余页）
按每页已有的 .jr 自动判断用哪种。

已知限制：术语若整个包在 concept 链接里（<a href="../concepts/x.html">score 函数</a>），
脚本为避免嵌套链接会判成"没有挂点"。这种要手工把 .jr 追加到 </a> 之后——本仓惯例就是
概念链接后面紧跟一个 .jr 角标。
"""
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent / "docs" / "papers"
TERM = re.compile(r'<span class="(?:gloss-)?term">(.*?)</span>', re.S)


def blank_tag(html, tag):
    return re.sub(rf"<{tag}\b.*?</{tag}>", lambda m: " " * len(m.group(0)), html, flags=re.S)


def glossary_terms(html):
    out = {}
    for m in re.finditer(r'id="(g-\d+)"', html):
        t = TERM.search(html[m.end():m.end() + 400])
        if t:
            out[m.group(1)] = re.sub(r"<[^>]+>", "", t.group(1)).replace("&nbsp;", " ").strip()
    return out


def style_of(html):
    """→ ('wrap'|'sup', 是否补零)"""
    m = re.search(r'<a class="jr" href="#g-\d+">(.*?)</a>', html, re.S)
    if not m:
        return "sup", False
    inner = m.group(1)
    kind = "wrap" if "<sup>" in inner else "sup"
    digits = re.search(r"\d+", inner)
    pad = bool(digits and digits.group(0).startswith("0") and len(digits.group(0)) > 1)
    return kind, pad


def safe_positions(html, needle, limit):
    """term 在正文里可以安全挂链接的位置（limit 之前）。"""
    # 抹掉不能碰的区域，但保持偏移量
    masked = blank_tag(blank_tag(html, "style"), "script")
    masked = re.sub(r"<a\b.*?</a>", lambda m: " " * len(m.group(0)), masked, flags=re.S)   # 别嵌套链接
    masked = re.sub(r"<nav.*?</nav>", lambda m: " " * len(m.group(0)), masked, flags=re.S)  # 目录不算正文
    masked = re.sub(r"<svg\b.*?</svg>", lambda m: " " * len(m.group(0)), masked, flags=re.S)   # SVG 里挂链接会破版
    masked = re.sub(r"<(?:h1|h2|figcaption)\b.*?</(?:h1|h2|figcaption)>",
                    lambda m: " " * len(m.group(0)), masked, flags=re.S)                    # 标题里挂着难看
    masked = re.sub(r"<[^>]+>", lambda m: " " * len(m.group(0)), masked)                    # 标签内部不算

    good = []
    for m in re.finditer(re.escape(needle), masked):
        if m.start() >= limit:
            break
        # 前后不能粘着别的 ASCII 字母（避免 AR 匹配到 ARMS 这种）
        before = masked[m.start() - 1] if m.start() else " "
        after = masked[m.end()] if m.end() < len(masked) else " "
        if (before.isascii() and before.isalnum()) or (after.isascii() and after.isalnum()):
            continue
        # 优先落在 <p> 里
        seg = html.rfind("<p", 0, m.start())
        in_p = seg != -1 and html.rfind("</p>", 0, m.start()) < seg
        good.append((not in_p, m.start(), m.end()))
    good.sort()
    return good


def pick_term(term_text, html, limit):
    """一条词条可能列了好几个名字（SGD / 动量 / RMSprop）。
    挑正文里出现次数最少的那个——越специфic 越是读者真正会卡住的词，
    也避免挂到「动量」这种到处都是的常用词上。"""
    cands = [c.strip() for c in re.split(r"[·/(（)）,，]", term_text) if 2 <= len(c.strip()) <= 26]
    cands = list(dict.fromkeys(cands))
    if not cands:
        return None
    # 主名优先：词条叫「GSPO（RL 阶段）」就该挂在 GSPO 上，不该挂在「RL 阶段」上
    head = cands[0]
    pos = safe_positions(html, head, limit)
    if pos:
        return head, pos[0]
    # 主名在正文里没有安全落点，才退而挑出现次数最少（= 最具体）的别名
    scored = []
    for c in cands[1:]:
        pos = safe_positions(html, c, limit)
        if pos:
            scored.append((len(pos), -len(c), c, pos[0]))
    if not scored:
        return None
    scored.sort()
    return scored[0][2], scored[0][3]


def main():
    apply = "--apply" in sys.argv
    changed = 0
    for p in sorted(DOCS.glob("*.html")):
        html = p.read_text(encoding="utf-8")
        refs = set(re.findall(r'href="#(g-\d+)"', html))
        ids = set(re.findall(r'id="(g-\d+)"', html))
        orphans = sorted(ids - refs)
        if not orphans:
            continue
        limit = min(m.start() for m in re.finditer(r'id="g-\d+"', html))
        kind, pad = style_of(html)
        terms = glossary_terms(html)
        edits = []
        for g in orphans:
            t = terms.get(g)
            if not t:
                print(f"  [跳过] {p.stem} {g}: 取不到术语名")
                continue
            got = pick_term(t, html, limit)
            if not got:
                print(f"  [人工] {p.stem} {g}「{t}」: 正文里没有可挂的词，需要自己加一句")
                continue
            word, (_pref, a, b) = got
            n = g.split("-")[1]
            num = n if pad else str(int(n))
            if kind == "wrap":
                new = f'<a class="jr" href="#{g}">{word}<sup>{num}</sup></a>'
                edits.append((a, b, new, word, g))
            else:
                new = f'{word}<a class="jr" href="#{g}">{num}</a>'
                edits.append((a, b, new, word, g))

        if not edits:
            continue
        print(f"\n### {p.stem}")
        for a, b, new, word, g in sorted(edits, reverse=True):
            ctx = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html[max(0, a - 45):b + 25])).strip()
            print(f"  {g} 挂到「{word}」 … {ctx}")
        if apply:
            for a, b, new, _w, _g in sorted(edits, reverse=True):   # 从后往前改，偏移量不乱
                html = html[:a] + new + html[b:]
            p.write_text(html, encoding="utf-8")
            changed += len(edits)
    print(f"\n{'已写入' if apply else '干跑'} {changed if apply else ''} 处")


if __name__ == "__main__":
    main()
