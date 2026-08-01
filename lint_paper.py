#!/usr/bin/env python3
"""bespoke paper 页的机械体检。

用法:
    python3 lint_paper.py                 # 扫 docs/papers/ 全部
    python3 lint_paper.py <slug> [<slug>] # 只扫指定页
    python3 lint_paper.py --warn          # 连 WARN 一起当失败

退出码非零 = 有 ERROR。

为什么要有这个脚本
------------------
SKILL.md 里那些"交付前自检"条目，靠回忆是过不掉的。写的人知道自己定义过
某个符号，于是把「定义过吗」当成「定义在使用之前吗」来答，就漏了——
solaris §07 的 Lₛ/Lₜ 就是这么两次躲过人工 review 的。凡是能被回忆绕过的
规则，都搬到这里变成位置比较、计数比较这类机械判定。

ERROR = 机械可判、没有解释空间，必须清零。
WARN  = 启发式，可能误报，要人眼看一下再决定。
"""
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent / "docs" / "papers"

# render.py 注入的整块内容，体检前摘掉（用等长空格替换以保持偏移量）
INJECTED = [
    ("<!-- wiki-nav:start -->", "<!-- wiki-nav:end -->"),
    ("<!-- gloss-popover:start -->", "<!-- gloss-popover:end -->"),
    ("<!-- mathify:start -->", "<!-- mathify:end -->"),
]

# 历史上出现过 5 种符号格子写法(.sym/.symbol/.var + 容器 .vars/.symbol-grid)，都要认
SYMBOL_CELL = re.compile(
    r'<(?:div|span|li) class="(?:sym|symbol|var)"\s*>(.*?)</(?:div|span|li)>', re.S)

SUBMAP = "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u209c\u2093\u209b\u209a\u2099\u2096\u2090\u2091\u2092"
ASCIIMAP = "0123456789txspnkaeo"
SUB = str.maketrans(SUBMAP, ASCIIMAP)
TO_SUB = dict(zip(ASCIIMAP, SUBMAP))
GREEK = {
    "theta": "\u03b8", "sigma": "\u03c3", "epsilon": "\u03b5", "alpha": "\u03b1",
    "beta": "\u03b2", "gamma": "\u03b3", "delta": "\u03b4", "mu": "\u03bc",
    "lambda": "\u03bb", "phi": "\u03c6", "psi": "\u03c8", "rho": "\u03c1",
    "tau": "\u03c4", "omega": "\u03c9", "eta": "\u03b7",
}
# 首次使用与符号格子相隔多少字符以内算"就地定义"（约一两句话）
INPLACE_TOLERANCE = 500

CJK = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
SMART_QUOTE_ATTR = re.compile("\\w+=[\u201c\u201d\u2018\u2019]")


def strip_injected(html):
    for a, b in INJECTED:
        while a in html and b in html:
            i, j = html.index(a), html.index(b) + len(b)
            html = html[:i] + " " * (j - i) + html[j:]
    return html


def blank_tag(html, tag):
    return re.sub(rf"<{tag}\b.*?</{tag}>", lambda m: " " * len(m.group(0)), html, flags=re.S)


def visible(html):
    """抹掉 style/script 内容，偏移量保持不变。"""
    return blank_tag(blank_tag(html, "style"), "script")


def canon(sym):
    """符号可能写成 LaTeX(L_s / \\sigma)、unicode(L_s 下标 / sigma)、或裸写。
    返回所有等价写法，任一出现都算用到了。"""
    s = sym.strip()
    forms = {s}
    for name, ch in GREEK.items():
        s = s.replace("\\" + name, ch)
    forms.add(s)
    forms.add(s.translate(SUB))                    # unicode 下标 → ASCII
    forms.add(re.sub(r"[{}\\]", "", s))            # 去花括号反斜杠
    m = re.fullmatch(r"([A-Za-z\u0370-\u03ff])_\{?([a-z0-9])\}?", s)
    if m and m.group(2) in TO_SUB:                 # L_s → unicode 下标写法
        forms.add(m.group(1) + TO_SUB[m.group(2)])
    return {f for f in forms if f}


def symbol_defs(body):
    """→ [(位置, 原始符号串, 等价写法集合)]，按位置排序。"""
    out = []
    for m in SYMBOL_CELL.finditer(body):
        inner = m.group(1)
        hit = re.search(r"<(?:code|b)>(.*?)</(?:code|b)>", inner, re.S)
        raw = hit.group(1) if hit else inner
        sym = re.sub(r"<[^>]+>", "", raw).strip()
        # 「目标」「① 换记号」这类中文标签不是符号
        if not sym or CJK.search(sym) or " " in sym:
            continue
        # 单字母(B/P/T/x)在正文里到处都是，误报会淹掉信号，且本来不易出问题
        if len(sym.translate(SUB).replace("\\", "")) < 2:
            continue
        # 格子里塞的是整条等式(x=Gθ(z) / softplus(u)=log(1+eᵘ))，不是一个符号
        if "=" in sym:
            continue
        # 全大写缩写(MLP / LPIPS)和纯英文单词(log / score / stopgrad)不是数学符号，
        # 它们在正文里当普通词用，按符号查必然满页误报
        if re.fullmatch(r"[A-Z]{2,}", sym) or re.fullmatch(r"[a-z]{3,}", sym):
            continue
        out.append((m.start(), sym, canon(sym)))
    return sorted(out)


def find_use(body, forms, skip_ranges):
    """第一次"使用"的位置。前后不能是 ASCII 字母数字，避免 log2N 里切出 g2 这种碎片。"""
    best = None
    for f in forms:
        for m in re.finditer(re.escape(f), body):
            i, j = m.start(), m.end()
            if any(a <= i < b for a, b in skip_ranges):
                continue
            before = body[i - 1] if i else " "
            after = body[j] if j < len(body) else " "
            if before.isascii() and before.isalnum():
                continue
            if after.isascii() and after.isalnum():
                continue
            if best is None or i < best:
                best = i
            break
    return best


def check_define_before_use(html, name, issues):
    body = visible(html)
    defs = symbol_defs(body)
    if not defs:
        return
    cell_ranges = [(m.start(), m.end()) for m in SYMBOL_CELL.finditer(body)]
    # 同一符号可能被多张表定义，只跟最早那次比
    earliest = {}
    for pos, sym, forms in defs:
        key = frozenset(forms)
        if key not in earliest or pos < earliest[key][0]:
            earliest[key] = (pos, sym)
    for key, (pos, sym) in sorted(earliest.items(), key=lambda kv: kv[1][0]):
        use = find_use(body, key, cell_ranges)
        if use is None or use >= pos:
            continue
        # 首次使用就紧挨着定义(同一句/同一段)，属于"就地定义"，不算断链
        if pos - use < INPLACE_TOLERANCE:
            continue
        line = body[:use].count("\n") + 1
        ctx = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body[max(0, use - 60):use + 40])).strip()
        issues.append(("WARN", name,
                       f"define-before-use: 符号 {sym} 第 {line} 行就用上了，符号格子在 {pos - use} 字符之后。"
                       f"要么把格子挪到首次使用之前，要么首次使用处已在散文里讲清、那张格子是冗余的 … {ctx}"))


def check_figcaption_symbols(html, name, issues):
    """figcaption 也是正文，不许出现本页尚未定义的下标符号（solaris 的原始翻车点）。
    启发式，列 WARN。"""
    body = visible(html)
    defs = symbol_defs(body)
    pat = re.compile(rf"(?<![0-9A-Za-z])[A-Za-z\u0370-\u03ff][{SUBMAP}]+")
    for m in re.finditer(r"<figcaption>(.*?)</figcaption>", body, re.S):
        text = re.sub(r"<[^>]+>", " ", m.group(1))
        for tok in sorted(set(pat.findall(text))):
            if any(pos < m.start() and tok in forms for pos, _s, forms in defs):
                continue
            flat = re.sub(r"\s+", " ", text).strip()[:60]
            issues.append(("WARN", name, f"figcaption 出现符号 {tok!r}，此前无符号格子定义: {flat}"))


def check_glossary(html, name, issues):
    refs = set(re.findall(r'href="#(g-\d+)"', html))
    ids = set(re.findall(r'id="(g-\d+)"', html))
    orphans = sorted(ids - refs)
    if orphans:
        issues.append(("ERROR", name,
                       f"glossary {len(orphans)}/{len(ids)} 条没有 .jr 入口: {', '.join(orphans)}"))
    for r in sorted(refs - ids):
        issues.append(("ERROR", name, f"glossary 死链 {r}：正文引用了但没这条"))


def check_markup(html, name, issues):
    body = visible(html)
    for attr in sorted(set(SMART_QUOTE_ATTR.findall(html))):
        issues.append(("ERROR", name, f"属性用了中文引号（样式会静默失效）: {attr}"))
    # 注意 <li[ >] 天然不匹配 <link，别再去减 link 的数量
    for tag in ("code", "p", "div", "ol", "ul", "h2", "h3", "figure", "li", "table", "section"):
        o = len(re.findall(rf"<{tag}[ >]", body))
        c = body.count(f"</{tag}>")
        if o != c:
            issues.append(("ERROR", name, f"<{tag}> 开合不平衡: {o} 开 / {c} 合"))
    n = body.count("`")
    if n:
        issues.append(("ERROR", name, f"残留 {n} 个 markdown 反引号（应写成 <code>）"))
    for slip in sorted(set(re.findall(r"[\u4e00-\u9fff][a-z]{3,}[\u4e00-\u9fff]", body))):
        issues.append(("WARN", name, f"中文里夹了没空格的英文，疑似手滑: {slip}"))


def check_chat_context(html, name, issues):
    """§3.7：不许指回聊天、不许预设读者读过别的页。会误报，列 WARN。"""
    text = re.sub(r"<[^>]+>", " ", visible(html))
    for pat in ("用户问", "你问的", "刚才说", "前面聊到", "我们上面", "你学的", "你已经懂"):
        for m in re.finditer(pat, text):
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 30):m.start() + 40]).strip()
            issues.append(("WARN", name, f"§3.7 疑似聊天语境「{pat}」: …{ctx}…"))


def lint(path):
    html = strip_injected(path.read_text(encoding="utf-8"))
    issues = []
    for fn in (check_define_before_use, check_figcaption_symbols,
               check_glossary, check_markup, check_chat_context):
        fn(html, path.name, issues)
    return issues


def main():
    argv = sys.argv[1:]
    strict = "--warn" in argv
    args = [a for a in argv if a != "--warn"]
    if args:
        paths = []
        for a in args:
            p = DOCS / (a if a.endswith(".html") else a + ".html")
            if not p.exists():
                print(f"找不到 {p}")
                return 2
            paths.append(p)
    else:
        paths = sorted(DOCS.glob("*.html"))

    issues = [i for p in paths for i in lint(p)]
    errors = [i for i in issues if i[0] == "ERROR"]
    warns = [i for i in issues if i[0] == "WARN"]
    for lvl, name, msg in errors + warns:
        print(f"[{lvl}] {name}: {msg}")
    print(f"\n扫了 {len(paths)} 页 · {len(errors)} ERROR · {len(warns)} WARN")
    return 1 if errors or (strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
