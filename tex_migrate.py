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
       "ₙ": "n", "ₖ": "k", "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₚ": "p", "ₛ": "s",
       "₊": "+", "₋": "-", "ᵥ": "v", "ᵣ": "r", "ᵤ": "u", "ₘ": "m", "ₗ": "l", "ₕ": "h"}
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6",
       "⁷": "7", "⁸": "8", "⁹": "9", "ⁿ": "n", "ᵀ": "T", "ⁱ": "i", "⁻": "-", "⁺": "+"}
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
# KaTeX 自带的函数命令
FUNCS = ("exp", "log", "ln", "max", "min", "sin", "cos", "det", "dim")
# KaTeX 没有对应命令的，要包 \operatorname
OPNAMES = ("softmax", "softplus", "sigmoid", "argmax", "argmin", "stopgrad", "sg")

MATHY = re.compile("[" + "".join(map(re.escape, list(SUB) + list(SUP) + list(GREEK) + list(OPS))) + "]")
CJK = re.compile(r"[一-鿿　-〿＀-￯]")


# 形状像数学、实际是英文短语 / 图例 / 代码 / 配置，机器分不出来，人工钉死"不是数学"。
# （典型：里面有个 − 或 → 就被 is_math 放行了，但整体是一句话。）
NOT_MATH = {
    '"golden_retriever"',
    '0.5×Quality + 0.5×Domain',
    'PSNR_merged',
    'car-1 → red',
    'car-2 → cyan',
    'fake score − real score',
    'fake ‖ real',
    'fake − real',
    'fake−real',
    'ignore_thresh=.7',
    'linear → ReLU → linear',
    'noise - clean_latent',
    'person-1→pink',
    'real−fake',
    'requires_grad=false',
    'road→cyan',
    'sfake−sreal',
    'stride=kernel_size=16',
    'ε-best response',
}


# 机器判不了的少数记号，人工钉死。空值 = 判定为"不是数学，别碰"。
MANUAL = {
    "x_tⱼ": r"x_{t_j}",          # 到底是 x_{t_j} 还是 (x_t)_j，按上下文取前者
    "fᵥⁱᵀ_l": r"f^{v,i,T}_{l}",  # 三个上标挤在一起，拆成逗号分隔
}


def to_tex(s: str) -> str:
    if s in MANUAL:
        return MANUAL[s]
    t = s
    # unicode 上下标 → LaTeX。连续的合成一组：xₜ₊₁ → x_{t+1}
    t = re.sub("([" + "".join(SUB) + "]+)", lambda m: "_{" + "".join(SUB[c] for c in m.group(1)) + "}", t)
    t = re.sub("([" + "".join(SUP) + "]+)", lambda m: "^{" + "".join(SUP[c] for c in m.group(1)) + "}", t)
    # 希腊字母与运算符
    t = re.sub("[" + "".join(map(re.escape, GREEK)) + "]", lambda m: GREEK[m.group(0)] + " ", t)
    t = re.sub("[" + "".join(map(re.escape, OPS)) + "]", lambda m: OPS[m.group(0)] + " ", t)
    # 多字母下标/上标 → \mathrm{}。先处理已带花括号的，再处理裸的，
    # 否则 x_{t_mid} 会被当成 "_mid}" 匹配掉，吐出括号不配对的 x_{t_{\mathrm{mid}}
    t = re.sub(r"([_^])\{([A-Za-z]{2,})\}", lambda m: m.group(1) + "{\\mathrm{" + m.group(2) + "}}", t)
    t = re.sub(r"([_^])([A-Za-z]{2,})(?![A-Za-z}])", lambda m: m.group(1) + "{\\mathrm{" + m.group(2) + "}}", t)
    # 希腊命令后"紧贴"一个词（θbase）→ 下标；只吃希腊替换自己加的那一个空格
    t = re.sub(r"(\\[a-zA-Z]+) ([a-z]{2,})\b",
               lambda m: m.group(1) + "_{\\mathrm{" + m.group(2) + "}}" if m.group(2) in WORDS else m.group(0), t)
    # 拉丁字母紧跟希腊字母（fθ / Gθ / qφ）→ 论文里几乎总是下标：f_\theta
    t = re.sub(r"(?<![\\A-Za-z])([A-Za-z])(\\(?:theta|phi|psi|sigma|mu|lambda|omega|eta|beta|alpha|gamma|delta|rho|tau|pi|nu|kappa|chi|epsilon|zeta)) ",
               lambda m: m.group(1) + "_" + m.group(2) + " ", t)
    # 组合变音符号：x̂ → \hat{x}。希腊字母此时已变成 "\epsilon "，所以要连命令一起吃
    for comb, cmd in (("\u0302", "hat"), ("\u0303", "tilde"), ("\u0304", "bar"), ("\u0307", "dot")):
        t = re.sub(r"(\\[a-zA-Z]+) ?" + comb, lambda m, c=cmd: "\\" + c + "{" + m.group(1) + "}", t)
        t = re.sub(r"([A-Za-z])" + comb, lambda m, c=cmd: "\\" + c + "{" + m.group(1) + "}", t)
    # 函数名直立
    t = re.sub(r"(?<!\\)\b(" + "|".join(FUNCS) + r")\b", lambda m: "\\" + m.group(1) + " ", t)
    t = re.sub(r"(?<![\\A-Za-z])(" + "|".join(OPNAMES) + r")\b",
               lambda m: "\\operatorname{" + m.group(1) + "}", t)
    # 函数名后紧跟希腊字母（minθ maxφ）→ 那是取极值的变量，写成下标
    t = re.sub(r"(\\(?:" + "|".join(FUNCS) + r")) (\\[a-zA-Z]+) (?![_^])",
               lambda m: m.group(1) + "_" + m.group(2) + " ", t)
    # 多字母的函数式名字（Beta(…) / Uniform(…)）直立
    t = re.sub(r"(?<![\\A-Za-z])([A-Z][a-z]{2,})\(", lambda m: "\\mathrm{" + m.group(1) + "}(", t)
    # 收尾：运算符后不留多余空格，命令与下标之间也不留
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"(?<=[-+=,(\[]) (?=[\\A-Za-z0-9])", "", t)
    t = re.sub(r"(\\[a-zA-Z]+) (?=[_^])", r"\1", t)
    # \sqrt 后面必须跟一个组：\sqrt (2\pi ) → \sqrt{2\pi}；\sqrt \hat{v} → \sqrt{\hat{v}}
    t = re.sub(r"\\sqrt\s*\(([^()]*)\)", lambda m: "\\sqrt{" + m.group(1).strip() + "}", t)
    t = re.sub(r"\\sqrt\s+(\\[a-zA-Z]+\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z0-9])", lambda m: "\\sqrt{" + m.group(1) + "}", t)
    t = re.sub(r"\\sqrt(?![{\\A-Za-z0-9])", lambda m: "\\surd", t)
    t = re.sub(r"(?<!\\\\)#", lambda m: "\\#", t)
    return t


def is_math(s: str) -> bool:
    """这串 <code> 是数学，还是代码/普通文本？"""
    if s in NOT_MATH:
        return False
    if not s or len(s) > 60 or CJK.search(s):
        return False
    if re.fullmatch(r"[a-z][a-z0-9]+(_[a-z0-9]+)+", s):      # loss_dm 这类 snake_case
        return False
    # 真代码：属性访问、赋值、两段以上的多字母 snake_case、末尾下划线
    if "." in s and re.search(r"[A-Za-z]\.[A-Za-z_]", s):    # skimage.metrics.xxx
        return False
    if "=True" in s or "=False" in s or "=None" in s:
        return False
    if s.endswith("_"):                                       # clip_grad_norm_
        return False
    if len(re.findall(r"_[A-Za-z]{2,}", s)) >= 2:             # a_memory_search / _get_init_query
        return False
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(", s) and re.search(r"_[A-Za-z]{2,}", s):
        return False                                          # 带下划线的函数调用
    # CONST_NAME，但首段得有 2 个以上字符——D_KL / L_CLIP 是数学不是常量名
    if re.fullmatch(r"[A-Z]{2,}[A-Z0-9_]*", s) and "_" in s:
        return False
    if re.fullmatch(r"[A-Z][A-Z0-9]{3,}", s):
        return False
    if re.fullmatch(r"[A-Z][A-Za-z0-9]*(_[A-Za-z0-9]+){2,}", s):   # V4_QUALITY_48
        return False
    if re.match(r"^(https?:|/|\./|--)", s):                   # 路径 / URL / 命令行开关
        return False
    if re.fullmatch(r"[0-9a-f]{7,40}", s):                    # commit hash
        return False
    if re.fullmatch(r"\d+(\.\d+)?[eE][-+]?\d+", s):           # 1e-4
        return False
    if re.fullmatch(r"<.*>", s):                              # <eos> / <|zh|>
        return False
    # 明摆着的 LaTeX：花括号下标/上标、反斜杠命令。x_{<t} 这种以前会漏，
    # 因为下面那条只认"下划线后面紧跟字母数字"。
    if re.search(r"[_^]\{", s) or re.search(r"\\[A-Za-z]", s):
        return True
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
    elif cmd == "apply":
        targets = [a for a in sys.argv[2:] if not a.startswith("-")]
        n_files = n_hits = 0
        for path in sorted(DOCS.rglob("*.html")):
            rel = str(path.relative_to(DOCS))
            if targets and not any(t in rel for t in targets):
                continue
            text = path.read_text(encoding="utf-8")
            cut = text.find("<!-- mathify:start -->")
            head, tail = (text[:cut], text[cut:]) if cut > 0 else (text, "")
            # <pre> 里的代码块整段不碰
            pre = [(m.start(), m.end()) for m in re.finditer(r"<pre\b.*?</pre>", head, re.S)]
            edits = []
            for m in re.finditer(r"<code>(.*?)</code>", head, re.S):
                if any(a <= m.start() < b for a, b in pre):
                    continue
                inner = m.group(1)
                raw = H.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if "\\" in raw or not is_math(raw):
                    continue
                tex = to_tex(raw)
                # 即便转换后文本没变（p_g / A_i 本来就是合法 LaTeX），也要打标记：
                # Phase C 会删掉运行时那层"猜哪个 code 是数学"，没标记就不再渲染。
                edits.append((m.start(), m.end(),
                              '<code class="m">' + H.escape(tex, quote=False) + "</code>"))
            if not edits:
                continue
            for a, b, v in sorted(edits, reverse=True):
                head = head[:a] + v + head[b:]
            path.write_text(head + tail, encoding="utf-8")
            n_files += 1
            n_hits += len(edits)
            print(f"  {rel:52s} {len(edits):3d} 处")
        print(f"\n改了 {n_files} 个文件 / {n_hits} 处")
    else:
        print("用法: table | table --full | apply [页名片段…]")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
