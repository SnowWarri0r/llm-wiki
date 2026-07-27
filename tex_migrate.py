#!/usr/bin/env python3
"""把散落在 <code> 里的 unicode 数学记号一次性转成 LaTeX，固化进源码。

背景：mathify 的 toTex() 是个"运行时猜测层"——每次页面加载都把松散记号猜成 LaTeX。
猜错了没有任何提示（`minθ maxφ` 被吞成 `θ_max`、`^adv` 被读成 `^a`+`dv`），
而且它跟 .formula 那条"手写 LaTeX 原样渲染"的路径行为不一致。

这个脚本把同一套转换搬到离线：跑一次 → 人工审 diff → 写回源码 → 运行时那层删掉。
错误从此出现在 diff 里，而不是藏在渲染结果里。

    python3 tex_migrate.py table          # 产出转换表给人审（不改文件）
    python3 tex_migrate.py table --full   # 连"无需改动"的也列出来
    python3 tex_migrate.py apply          # 写回源码（先审过表再跑）
"""
import html as H
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DOCS = Path(__file__).parent / "docs"

SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6",
       "₇": "7", "₈": "8", "₉": "9", "ₜ": "t", "ₓ": "x", "ᵢ": "i", "ⱼ": "j",
       "ₙ": "n", "ₖ": "k", "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₚ": "p", "ₛ": "s"}
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "ⁿ": "n",
       "ᵀ": "T", "⁻": "-", "⁺": "+"}
GREEK = {"θ": r"\theta", "σ": r"\sigma", "α": r"\alpha", "μ": r"\mu",
         "ε": r"\epsilon", "φ": r"\phi", "ψ": r"\psi", "γ": r"\gamma",
         "λ": r"\lambda", "ω": r"\omega", "τ": r"\tau", "β": r"\beta",
         "δ": r"\delta", "ρ": r"\rho", "π": r"\pi", "η": r"\eta", "ζ": r"\zeta",
         "χ": r"\chi", "ν": r"\nu", "κ": r"\kappa",
         "Ω": r"\Omega", "Δ": r"\Delta", "Φ": r"\Phi", "Ψ": r"\Psi",
         "Θ": r"\Theta", "Σ": r"\Sigma", "Λ": r"\Lambda", "Γ": r"\Gamma"}
OPS = {"∑": r"\sum", "∫": r"\int", "∂": r"\partial", "√": r"\sqrt",
       "∞": r"\infty", "≈": r"\approx", "≠": r"\neq", "≤": r"\le", "≥": r"\ge",
       "×": r"\times", "·": r"\cdot", "−": "-", "∼": r"\sim", "→": r"\to",
       "⟺": r"\iff", "⇒": r"\Rightarrow", "‖": r"\|", "∈": r"\in",
       "∇": r"\nabla", "⊕": r"\oplus", "∝": r"\propto", "≡": r"\equiv",
       "∥": r"\parallel", "⊙": r"\odot", "∀": r"\forall", "∃": r"\exists"}
# 这些词当下标时应当直立（\mathrm），不是变量名相乘
WORDS = {"fake", "real", "base", "cfg", "cond", "uncond", "data", "reg", "pseudo",
         "denoise", "train", "infer", "new", "old", "out", "tot", "avg", "ref",
         "max", "min", "tar", "mid", "direct", "adv", "gt", "lin", "text", "dur",
         "clip", "KL", "GAN", "DMD", "DM", "MSE", "LPIPS", "FID", "CE", "ISG"}
FUNCS = ("exp", "log", "ln", "max", "min", "sin", "cos", "det", "dim", "softmax",
         "sigmoid", "softplus", "argmax", "argmin")

MATHY = re.compile("[" + "".join(map(re.escape, list(SUB) + list(SUP) + list(GREEK) + list(OPS))) + "]")
CJK = re.compile(r"[一-鿿　-〿＀-￯]")


def to_tex(s: str) -> str:
    t = s
    # unicode 上下标 → LaTeX。连续的合成一组：xₜ₊₁ → x_{t+1}
    t = re.sub("([" + "".join(SUB) + "]+)", lambda m: "_{" + "".join(SUB[c] for c in m.group(1)) + "}", t)
    t = re.sub("([" + "".join(SUP) + "]+)", lambda m: "^{" + "".join(SUP[c] for c in m.group(1)) + "}", t)
    # 希腊字母与运算符
    t = re.sub("[" + "".join(map(re.escape, GREEK)) + "]", lambda m: GREEK[m.group(0)] + " ", t)
    t = re.sub("[" + "".join(map(re.escape, OPS)) + "]", lambda m: OPS[m.group(0)] + " ", t)
    # 多字母下标/上标 → \mathrm{}
    t = re.sub(r"([_^])\{?([A-Za-z]{2,})\}?", lambda m: m.group(1) + "{\\mathrm{" + m.group(2) + "}}", t)
    # 希腊命令后"紧贴"一个词（θbase）→ 下标；只吃希腊替换自己加的那一个空格
    t = re.sub(r"(\\[a-zA-Z]+) ([a-z]{2,})\b",
               lambda m: m.group(1) + "_{\\mathrm{" + m.group(2) + "}}" if m.group(2) in WORDS else m.group(0), t)
    # 拉丁字母紧跟希腊字母（fθ / Gθ / qφ）→ 论文里几乎总是下标：f_\theta
    t = re.sub(r"(?<![\\A-Za-z])([A-Za-z])(\\(?:theta|phi|psi|sigma|mu|lambda|omega|eta|beta|alpha|gamma|delta|rho|tau|pi|nu|kappa|chi|epsilon|zeta)) ",
               lambda m: m.group(1) + "_" + m.group(2) + " ", t)
    # 组合变音符号：x̂ → \hat{x}，x̃ → \tilde{x}，x̄ → \bar{x}
    for comb, cmd in (("\u0302", "hat"), ("\u0303", "tilde"), ("\u0304", "bar"), ("\u0307", "dot")):
        t = re.sub(r"([A-Za-z])" + comb, lambda m, c=cmd: "\\" + c + "{" + m.group(1) + "}", t)
    # 函数名直立
    t = re.sub(r"(?<!\\)\b(" + "|".join(FUNCS) + r")\b", lambda m: "\\" + m.group(1) + " ", t)
    # 函数名后紧跟希腊字母（minθ maxφ）→ 那是取极值的变量，写成下标
    t = re.sub(r"(\\(?:" + "|".join(FUNCS) + r")) (\\[a-zA-Z]+) ",
               lambda m: m.group(1) + "_" + m.group(2) + " ", t)
    # 多字母的函数式名字（Beta(…) / Uniform(…)）直立
    t = re.sub(r"(?<![\\A-Za-z])([A-Z][a-z]{2,})\(", lambda m: "\\mathrm{" + m.group(1) + "}(", t)
    # 收尾：运算符后不留多余空格，命令与下标之间也不留
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"(?<=[-+=,(\[]) (?=[\\A-Za-z0-9])", "", t)
    t = re.sub(r"(\\[a-zA-Z]+) (?=[_^])", r"\1", t)
    return t


def is_math(s: str) -> bool:
    """这串 <code> 是数学，还是代码/普通文本？"""
    if not s or len(s) > 60 or CJK.search(s):
        return False
    if re.fullmatch(r"[a-z][a-z0-9]+(_[a-z0-9]+)+", s):      # loss_dm 这类 snake_case
        return False
    if re.fullmatch(r"[A-Z][A-Z0-9_]{3,}", s):                # CONST_NAME
        return False
    if re.match(r"^(https?:|/|\./|--)", s):                   # 路径 / URL / 命令行开关
        return False
    if re.fullmatch(r"[0-9a-f]{7,40}", s):                    # commit hash
        return False
    if re.fullmatch(r"\d+(\.\d+)?[eE][-+]?\d+", s):           # 1e-4
        return False
    if re.fullmatch(r"<.*>", s):                              # <eos> / <|zh|>
        return False
    if MATHY.search(s):
        return True
    return bool(re.search(r"[A-Za-z]_[A-Za-z0-9]", s))        # p_g / x_t


def scan():
    """→ {原串: {"tex":…, "pages":Counter}}"""
    out = defaultdict(lambda: {"tex": "", "pages": Counter()})
    for p in sorted(DOCS.rglob("*.html")):
        s = p.read_text(encoding="utf-8")
        i = s.find("<!-- mathify:start -->")
        body = s[:i] if i > 0 else s
        for m in re.finditer(r"<code[^>]*>(.*?)</code>", body, re.S):
            raw = H.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
            if "\\" in raw or not is_math(raw):
                continue
            out[raw]["tex"] = to_tex(raw)
            out[raw]["pages"][str(p.relative_to(DOCS))] += 1
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "table"
    full = "--full" in sys.argv
    tbl = scan()
    changed = {k: v for k, v in tbl.items() if v["tex"] != k}
    if cmd == "table":
        items = tbl if full else changed
        for raw in sorted(items, key=lambda k: -sum(tbl[k]["pages"].values())):
            n = sum(tbl[raw]["pages"].values())
            where = ", ".join(list(tbl[raw]["pages"])[:2])
            print(f"{n:4d}  {raw!r:34s} → {tbl[raw]['tex']!r:44s} {where}")
        print(f"\n共 {len(tbl)} 种唯一串 / {sum(sum(v['pages'].values()) for v in tbl.values())} 处；"
              f"其中 {len(changed)} 种需要改写")
    else:
        print("apply 尚未启用——先审过 table 再说")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
