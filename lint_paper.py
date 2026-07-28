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
import html as html_mod
import importlib.util
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent / "docs" / "papers"

# 复用迁移脚本里的"这是不是数学"判定，保证 linter 与 tex_migrate 永远同一套规则
_spec = importlib.util.spec_from_file_location("_tm", Path(__file__).parent / "tex_migrate.py")
_tm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tm)
_is_math = _tm.is_math

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

PROSE_TIGHT = re.compile(r"^[A-Za-z\u0370-\u03ff](_\{?[A-Za-z0-9]{1,5}\}?)*(\^\{?[A-Za-z0-9]{1,3}\}?)*(\(.*\))?$")

MATH_UNICODE = re.compile("[\\u2080-\\u209c\\u2070-\\u207f\\u0370-\\u03ff\\u2200-\\u22ff\\u2190-\\u21ff\\u2212\\u2016]")

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
        # 必须容许属性：标签迁到 <code class="m"> 之后，只认裸 <code> 会整片瞎掉，
        # 然后退而把格子里随便一段文字（.45 这种数字）当成符号，满页误报。
        hit = re.search(r"<(?:code|b)\b[^>]*>(.*?)</(?:code|b)>", inner, re.S)
        raw = hit.group(1) if hit else inner
        sym = re.sub(r"<[^>]+>", "", raw).strip()
        # 「目标」「① 换记号」这类中文标签不是符号
        if not sym or CJK.search(sym) or " " in sym:
            continue
        # 纯数字 / 小数不是符号
        if re.fullmatch(r"[-+.\d]+", sym):
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


def check_unmarked_math(html, name, issues):
    """裸 <code> 里出现数学 = 不会被渲染。

    Phase C 之后 mathify 只认 <code class="m">，运行时那层"猜哪个 code 是数学"已删掉，
    没打标记的数学不再有兜底，直接显示成灰底的 p_g / \theta / xₜ。

    判定**直接复用 tex_migrate.is_math**，不在这里另写一份——这个仓库这轮踩过太多次
    "两处各写一套规则然后悄悄分叉"了。<pre> 里的不算。"""
    body = visible(html)
    pre = [(m.start(), m.end()) for m in re.finditer(r"<pre\b.*?</pre>", body, re.S)]
    for m in re.finditer(r"<code>(.*?)</code>", body, re.S):
        if any(a <= m.start() < b for a, b in pre):
            continue
        t = html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if not _is_math(t):
            continue
        issues.append(("ERROR", name,
                       f"裸 <code> 里的数学不会渲染: {t[:40]!r}（改成 <code class=\"m\"> 并写 LaTeX）"))


# 符号格的标签常写成 <b>…</b>。LaTeX 或 unicode 数学摆在 <b> 里同样不会渲染，
# 而上面那条只扫 <code>，整类都漏在外面（survey 的 o_{t+1} 就是这么活下来的）。
SYM_LABEL = re.compile(
    r'<div class="(?:sym|symbol|var|vars)[^"]*">\s*<(b|strong)>(?P<lab>.*?)</\1>', re.S)
UNI_MATH = re.compile("[\u0370-\u03ff\u2080-\u209c\u2070-\u207f\u2211\u220f\u222b\u221a\u2248"
                      "\u2260\u2264\u2265\u2297\u2299\u2207\u2212]")


def check_unmarked_sym_label(html, name, issues):
    """符号格的标签里塞了数学却没套 <code class="m"> = 原样把 LaTeX 源码显示出来。"""
    for m in SYM_LABEL.finditer(visible(html)):
        inner = m.group("lab")
        if "<code" in inner:          # 里面已经有 code，交给 check_unmarked_math 判
            continue
        t = html_mod.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if not t or CJK.search(t):
            continue
        # 「S · state」这类标签里的 · 是分隔符不是乘号，抹掉再判，否则整排误报
        probe = re.sub(r"\s[·|]\s", " ", t)
        if not (_is_math(probe) or UNI_MATH.search(probe)):
            continue
        issues.append(("ERROR", name,
                       f"符号格标签里的数学不会渲染: {t[:40]!r}"
                       "（改成 <code class=\"m\"> 并写 LaTeX）"))


# 早前那轮 unicode→LaTeX 批量迁移会把下标拆错：V_{p},q 渲染成 "V_p , q"，
# Z_{1}:j 渲染成 "Z_1 : j"，还有 LaTeX 串里混进 unicode 下标（n_{x},nᵧ）。
# 这几种都能编译成功，KaTeX 不报错，只是显示成另一个意思——只能靠模式扫。
MATH_SRC = re.compile(r'<code class="m">(.*?)</code>|data-tex="([^"]*)"|data-expr="([^"]*)"', re.S)
# 下标字母散落在三个 Unicode 区：₀-₉ 在 2080 区，ᵢᵥᵣᵤᵧᵦ 在 1d62 区（音标扩展），
# ⱼ 单独在 2c7c。只写 2080 区会漏掉一半——nᵧ 就是这么躲过第一版的。
UNI_IN_TEX = re.compile("[\u0370-\u03ff\u1d62-\u1d6a\u2070-\u207f\u2080-\u209c\u2c7c]")
SUB_THEN_COLON = re.compile(r"_\{[^{}]{1,8}\}\s*:")


def check_broken_subscript(html, name, issues):
    """LaTeX 编得过、但下标拆错或混了 unicode —— KaTeX 不会报错，只会显示成别的意思。"""
    for m in MATH_SRC.finditer(visible(html)):
        t = html_mod.unescape(m.group(1) or m.group(2) or m.group(3) or "").strip()
        if not t:
            continue
        if UNI_IN_TEX.search(t):     # code.m 里就该是 LaTeX，下标写 _x 不写 ₓ
            issues.append(("ERROR", name,
                           f"LaTeX 串里混了 unicode 数学字符: {t[:40]!r}（下标写成 _x，别用 ₓ）"))
        if SUB_THEN_COLON.search(t):
            issues.append(("ERROR", name,
                           f"下标花括号后面跟冒号，多半是拆错了: {t[:40]!r}（Z_{{1}}:j 应为 Z_{{1:j}}）"))


# 符号格的标签是块级的（.sym>code.m:first-child）。要是把标签写成两截
#   <code class="m">A</code> / <code class="m">B</code> · 说明…
# 第一截会独占一行，第二截跟说明文字挤在下一行 —— 撞过两次了，交给脚本盯。
SYM_CELL_2CODE = re.compile(r'<div class="(?:sym|symbol|var)"[^>]*>(.*?)</div>', re.S)


def check_split_sym_label(html, name, issues):
    """符号格标签被拆成两个 code.m，第一个会单独占一行。"""
    for m in SYM_CELL_2CODE.finditer(visible(html)):
        inner = m.group(1)
        if not inner.lstrip().startswith('<code class="m">'):
            continue
        if inner.count('<code class="m">') < 2:
            continue
        after = inner.split("</code>", 1)[1].lstrip()
        if after[:1] in "/,\uff0c\u3001" or after.startswith("<code"):
            flat = html_mod.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            issues.append(("ERROR", name,
                           f"符号格标签被拆成两个 code.m，第一个会单独占一行: {flat[:44]!r}"
                           "（合成一个，用 ,\\; 分隔）"))


# .math-sheet / .calc 里写 τ_global、s_real 这种 ASCII 下划线，读起来就是
# "没渲染的 LaTeX"。正解是包成 <code class="m"> 让它真渲染 —— 曾经以为
# "混 KaTeX 进等宽块会毁掉列对齐"，实测是错的：只要同一列各行插入相同，
# 列位置分毫不动（三行 τ_c 右侧列 x 都是 338）。unicode 下标（x₀ / V⁺）同样可以。
LEDGER = re.compile(r'<div class="(?:math-sheet|calc)"[^>]*>(.*?)</div>', re.S)
FAKE_SUB = re.compile(r"(?<![A-Za-z0-9])[A-Za-z\u0370-\u03ff][A-Za-z0-9]*_[A-Za-z][A-Za-z0-9]*")


def check_ledger_pseudo_latex(html, name, issues):
    """等宽算式块里出现 X_y 形式的假下标。"""
    seen = set()
    for m in LEDGER.finditer(visible(html)):
        inner = m.group(1)
        # 已经包进 <code class="m"> 的会被 KaTeX 渲染，不算假下标——先整段抹掉
        inner = re.sub(r'<code class="m">.*?</code>', " ", inner, flags=re.S)
        txt = html_mod.unescape(re.sub(r"<[^>]+>", "", inner))
        for g in FAKE_SUB.finditer(txt):
            if g.group(0) in seen:
                continue
            seen.add(g.group(0))
            issues.append(("ERROR", name,
                           f"等宽算式块里的假下标不会渲染: {g.group(0)!r}"
                           "（包成 <code class=\"m\"> 写 LaTeX；实测 KaTeX 不会破坏等宽列对齐）"))


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
    for fn in (check_define_before_use, check_figcaption_symbols, check_unmarked_math,
               check_unmarked_sym_label,
               check_broken_subscript,
               check_split_sym_label,
               check_ledger_pseudo_latex,
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
