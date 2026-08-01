#!/usr/bin/env python3
"""把 <pre> 里的 ASCII 数学记号换成 unicode 等价写法。

用法:
    python3 fix_pre_math.py                # 全仓 dry-run，只报告不改
    python3 fix_pre_math.py --write        # 全仓实际写入
    python3 fix_pre_math.py --write <slug> # 只改指定页

为什么存在
----------
mathify 明确跳过 <pre>（run() 里 `if(el.closest('pre')) return`），所以 pre 里的
k_n / e^H / V_l 会原样显示成源码——被读者连着指了三次。pre 里的记号规范是：

  - 下标走 unicode：kₙ pₗ dₕ xₜ（只在整个下标都有 unicode 形式时才转）
  - e 的幂一律写 exp(·)：小数上标（e^1.4142）unicode 排不出来
  - 其他底数的幂：指数每个字符都有 unicode 上标形式才转（N² wᵏ 10⁴）

转不了的（W_f 这类 f 没有 unicode 下标、x_{t−1} 这类花括号）只报告不硬转——
那些往往说明这块本该是 KaTeX aligned 而不是 pre（见 SKILL 的载体判据）。

跟 lint_paper.check_pre_ascii_math 配套：linter 负责报，这里负责修。
"""
import html as html_mod
import re
import sys
import unicodedata
from pathlib import Path

DOCS = Path(__file__).parent / "docs" / "papers"

SUBS = dict(zip("0123456789aehijklmnoprstuvx+-",
                "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ₊₋"))
SUBS["−"] = "₋"        # − 号
SUPS = dict(zip("0123456789abcdefghijklmnoprstuvwxyz+-()",
                "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ⁺⁻⁽⁾"))
SUPS["−"] = "⁻"
SUPS.update(dict(zip("ABDEGHIJKLMNOPRTUVW", "ᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ")))  # 无 CFQSXYZ

# 下标是希腊字母时（π_θ / u_θ / v_θ）unicode 没有对应形式，且这种写法本身读起来
# 不歧义，约定为允许保留 —— 不转也不报。
GREEK = "α-ωΑ-Ω"
ACCEPTED_SUB = re.compile(rf"^[{GREEK}]+$")

# 真代码块不动：里面的 x_t 当变量名读是成立的，转成 xₜ 反而不能照抄运行
CODE_MARKERS = re.compile(
    r"torch\.|np\.|nn\.|\.detach\(|\.backward\(|import |def |self\.|"
    r"\.shape|\.norm\(|@ |encoder\(|embedding\(")

# 底数含希腊字母（ρ_t / Σ_t）；下标含希腊（π_θ）→ ACCEPTED_SUB 放行
SUB_TOKEN = re.compile(rf"(?<![A-Za-z0-9_])([A-Za-z{GREEK}∑])_([A-Za-z0-9{GREEK}]{{1,2}})(?![A-Za-z0-9_])")
# 花括号下标（m_{t−1}）：整个内容都能映射就转成 mₜ₋₁，否则报人工
SUB_BRACED = re.compile(rf"(?<![A-Za-z0-9_])([A-Za-z{GREEK}∑])_\{{([^{{}}]+)\}}")
E_POW = re.compile(r"(?<![A-Za-z0-9_])e\^(\{[^}]+\}|[-+−]?[\w.]+)")
# 底数四类：单字母（前面不能是标识符字符）、多位数字（10^4）、右括号（(params)^α）、
# 已转成 unicode 下标的（Aᵢ^Dr 里 ^ 前面是 ᵢ）
POW = re.compile(r"(?:(?<![A-Za-z0-9_])([A-Za-z])|(?<![A-Za-z0-9_.])(\d+)|([)\]])"
                 r"|([₀-ₜᵢ-ᵪⱼ]))"
                 r"\^([-+−]?[\w]+|\{[^}]+\})")
BRACED = re.compile(r"[A-Za-z][_^]\{[^}]*\}")

PRE = re.compile(r"(<pre\b[^>]*>)(.*?)(</pre>)", re.S)
TAG = re.compile(r"(<[^>]+>)")


def convert_text(text, report):
    """转一段 pre 里的纯文本（不含标签）。转不动的塞进 report。"""
    def sub_repl(m):
        base, sub = m.group(1), m.group(2)
        if ACCEPTED_SUB.match(sub):          # π_θ：允许保留，不转不报
            return m.group(0)
        if all(c in SUBS for c in sub):
            return base + "".join(SUBS[c] for c in sub)
        report.append(m.group(0))
        return m.group(0)

    def e_repl(m):
        exp = m.group(1)
        if exp.startswith("{"):
            exp = exp[1:-1]
        return f"exp({exp.replace(chr(0x2212), '-')})"

    def sub_braced_repl(m):
        base, sub = m.group(1), m.group(2)
        if ACCEPTED_SUB.match(sub):
            return f"{base}_{sub}"           # 去掉花括号，π_{θ} → π_θ
        if all(c in SUBS for c in sub):
            return base + "".join(SUBS[c] for c in sub)
        report.append(m.group(0))
        return m.group(0)

    def pow_repl(m):
        base = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        exp = m.group(5)
        inner = exp[1:-1] if exp.startswith("{") else exp
        if all(c in SUPS for c in inner):
            return base + "".join(SUPS[c] for c in inner)
        report.append(m.group(0))
        return m.group(0)

    text = E_POW.sub(e_repl, text)
    text = SUB_BRACED.sub(sub_braced_repl, text)
    text = SUB_TOKEN.sub(sub_repl, text)
    text = POW.sub(pow_repl, text)
    report.extend(BRACED.findall(text))
    return text


def dwidth(s):
    """终端显示宽度：CJK/全角 2 列，组合字符 0 列，其余 1 列。"""
    return sum(0 if unicodedata.combining(c)
               else 2 if unicodedata.east_asian_width(c) in "FW"
               else 1 for c in s)


GAP = re.compile(r" {2,}")


def realign(orig, conv):
    """token 变短/变长会打歪手工对齐的列。按原行的 2+ 空格分段，
    把转换后各段 pad 回原来的起始显示列。转换只动 token 不动空格，
    所以两边分段数必然一致；不一致就原样返回不硬来。"""
    if orig == conv or "\n" in orig:
        return conv
    osegs, csegs = GAP.split(orig), GAP.split(conv)
    ogaps = GAP.findall(orig)
    if len(osegs) != len(csegs) or len(osegs) < 2:
        return conv
    out = csegs[0]
    ocol = dwidth(osegs[0])
    for i, gap in enumerate(ogaps):
        ocol += len(gap)                      # 原行下一段的起始列
        pad = max(2, ocol - dwidth(out))      # 至少留住 2 空格的间隔感
        out += " " * pad + csegs[i + 1]
        ocol += dwidth(osegs[i + 1])
    return out


def process(path, write):
    s = path.read_text(encoding="utf-8")
    changed, manual = 0, []

    def pre_repl(m):
        nonlocal changed
        body = m.group(2)
        if CODE_MARKERS.search(html_mod.unescape(body)):
            return m.group(0)
        out = []
        for seg in TAG.split(body):
            if seg.startswith("<"):
                out.append(seg)
                continue
            # 逐行转换 + 逐行按原列宽重排，跨行的对齐关系就不会被字宽变化打歪
            lines = seg.split("\n")
            new_lines = []
            for ln in lines:
                cv = convert_text(ln, manual)
                if cv != ln:
                    changed += 1
                    cv = realign(ln, cv)
                new_lines.append(cv)
            out.append("\n".join(new_lines))
        return m.group(1) + "".join(out) + m.group(3)

    new = PRE.sub(pre_repl, s)
    if new != s:
        n_tok = sum(1 for a, b in zip(s, new) if a != b)  # 粗略
        if write:
            path.write_text(new, encoding="utf-8")
        print(f"{'[写入]' if write else '[dry ]'} {path.name}: 改动 {changed} 段")
    for tok in sorted(set(manual)):
        print(f"    ⚠ 转不了，需人工（改 KaTeX 或换名）: {tok}   ({path.name})")
    return new != s


def main():
    write = "--write" in sys.argv
    slugs = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = [DOCS / f"{s.removesuffix('.html')}.html" for s in slugs] if slugs \
        else sorted(DOCS.glob("*.html"))
    touched = sum(process(f, write) for f in files if f.exists())
    print(f"—— {touched} 页有改动{'（已写入）' if write else '（dry-run，加 --write 生效）'}")


if __name__ == "__main__":
    main()
