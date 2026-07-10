# YOLO v1 Page Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the YOLO v1 page into a self-contained review that accurately explains the full method, training recipe, inference path, experimental error profile, model complementarity, VOC 2012 results, and artwork generalization.

**Architecture:** Keep the existing bespoke HTML shell and tangerine visual identity. Rewrite the content around one dog-detection example, retain and correct the six existing figures, add two evidence-driven experiment figures, then synchronize the Markdown scaffold and generated indexes. Treat the whole revamp as one semantic unit and create one implementation commit after all content and visual checks pass.

**Tech Stack:** Markdown, hand-authored HTML/CSS, inline SVG, vanilla JavaScript, Python 3, `render.py`, Git.

## Global Constraints

- Use arXiv v5 of `1506.02640` as the source of truth for paper structure, claims, and numbers.
- Cover YOLO v1 only. Mention later versions in one closing sentence without teaching their mechanisms.
- Preserve the paper/ink palette and tangerine accent; change individual layouts when clarity improves.
- Use the same dog example from grid assignment through class score and NMS.
- SVG body labels must be at least 11px; figure titles must be 13-14px.
- Redraw mechanisms and quantitative comparisons as inline SVG. Do not embed or copy paper figures.
- Do not add personal information, chat context, internal service names, credentials, or absolute local paths to public wiki content.
- Keep the implementation in one revamp commit, following the repository's paper-revamp rule.
- Do not push. Present the local commit and diff summary for user approval.

## File Map

- Modify `docs/papers/yolo.html`: reader-facing narrative, corrected figures, two new experiment figures, glossary, animation registry.
- Modify `wiki/papers/yolo.md`: internal scaffold with corrected mechanism and experiment summary.
- Modify `index.md`: expanded YOLO entry that reflects the new experiment coverage.
- Modify `log.md`: one `expand+fix` entry describing this revamp.
- Regenerate `docs/index.html` and `docs/papers.html` with `python3 render.py`; retain other generated changes only when `render.py` produces them from the four source edits above.
- Do not create or expand concept pages unless a directly conflicting statement is discovered during implementation.

---

### Task 1: Re-establish the baseline and evidence map

**Files:**
- Read: `docs/superpowers/specs/2026-07-10-yolo-v1-rewrite-design.md`
- Read: `wiki/papers/yolo.md`
- Read: `docs/papers/yolo.html`
- Read: `index.md`
- Read: `log.md`

**Interfaces:**
- Consumes: arXiv v5 paper facts and the approved design spec.
- Produces: a verified clean baseline and exact expected values for later assertions.

- [ ] **Step 1: Confirm branch, identity, remotes, and worktree state**

Run:

```bash
git branch --show-current
git status --short --branch
git remote -v
git config --local --get user.name
git config --local --get user.email
```

Expected: branch `main`; only the committed spec and plan are ahead of `origin/main`; identity `SnowWarri0r <gerrytranchina@gmail.com>`; no unstaged user changes.

- [ ] **Step 2: Refresh and compare the production branch without resetting local commits**

Run:

```bash
git fetch origin main
git rev-parse origin/main
git log --oneline --decorate -5
git diff --stat origin/main..HEAD
```

Expected: the local design/plan commits remain intact. If `origin/main` advanced, inspect `git diff HEAD..origin/main` and reconcile deliberately; never reset or overwrite local commits.

- [ ] **Step 3: Record the paper outline as the coverage gate**

Verify the implementation covers these headings from the paper:

```text
1 Introduction
2 Unified Detection
  2.1 Network Design
  2.2 Training
  2.3 Inference
  2.4 Limitations of YOLO
3 Comparison to Other Detection Systems
4 Experiments
  4.1 Comparison to Other Real-Time Systems
  4.2 VOC 2007 Error Analysis
  4.3 Combining Fast R-CNN and YOLO
  4.4 VOC 2012 Results
  4.5 Generalizability: Person Detection in Artwork
5 Real-Time Detection In The Wild
6 Conclusion
```

Expected: every line maps to one planned page section or paragraph; section 3 maps to the detector-landscape opening, and sections 5-6 map to the experiments close and legacy close.

- [ ] **Step 4: Verify the corrected square-root example before editing copy**

Run:

```bash
python3 -c "import math; small=math.sqrt(.02)-math.sqrt(.01); large=math.sqrt(.11)-math.sqrt(.10); print(f'{small:.8f} {large:.8f} {small/large:.6f} {(small*small)/(large*large):.6f}')"
```

Expected:

```text
0.04142136 0.01543471 2.683649 7.201973
```

- [ ] **Step 5: Capture baseline page audits**

Run:

```bash
diff <(rg -o 'href="#g-[0-9]+"' docs/papers/yolo.html | sort -u) <(rg -o 'id="g-[0-9]+"' docs/papers/yolo.html | sort -u)
rg -n '<figure id=|const figs' docs/papers/yolo.html
python3 -c "import re; from pathlib import Path; s=Path('docs/papers/yolo.html').read_text(); print(sorted({float(x) for x in re.findall(r'<(?:text|tspan)[^>]*font-size=\"([0-9.]+)\"', s) if float(x)<11}))"
```

Expected: glossary diff is empty; six current figure IDs are registered; the final command lists the current sub-11px SVG sizes that must be removed.

---

### Task 2: Rewrite the detector landscape and the end-to-end mechanism

**Files:**
- Modify: `docs/papers/yolo.html`
- Modify: `wiki/papers/yolo.md`

**Interfaces:**
- Consumes: current bespoke page shell, existing FIG 01-05, and the running-example values from the design spec.
- Produces: accurate sections for detector history, output semantics, responsibility assignment, loss, training, and NMS.

- [ ] **Step 1: Correct the opening comparison**

Replace the blanket “R-CNN family runs about 2000 CNN evaluations” claim with this distinction in both the HTML narrative and Markdown scaffold:

```text
DPM 把分类器滑过整张图；原始 R-CNN 先用 Selective Search 提约 2000 个候选框，再逐框提 CNN 特征。Fast R-CNN 已把整图卷积共享起来，但仍要等 Selective Search；Faster R-CNN 再用 RPN 生成候选。YOLO 真正砍掉的不是某一个慢算子，而是“先提候选、再逐候选判断”的分段流水线。
```

Update FIG 01 so its upper row is labelled `原始 R-CNN · ~2000 候选逐框提特征`, and add a separate 11px note below it:

```text
Fast/Faster R-CNN 后来共享卷积、改进提议，但仍保留候选阶段
```

Keep the YOLO lower row as a single full-image network evaluation followed by thresholding and NMS.

- [ ] **Step 2: Make coordinate semantics explicit**

Immediately after `7×7×30=1470`, add:

```html
<p><code>x,y</code> 不是整图像素坐标，而是框中心相对当前格子的偏移；<code>w,h</code> 则按整张图宽高归一化。两个框各有自己的几何和置信度，但同一格只共享一套 20 类概率——这也是一格挤进多个不同类别小物体时容易漏的根源。</p>
```

Update FIG 02 and FIG 03 labels to show `x,y · 相对格子` and `w,h · 相对整图` without adding a second visual point.

- [ ] **Step 3: Carry one dog example through responsibility and scoring**

Use these exact values everywhere:

```text
框 A 与真值 IOU = 0.70
框 B 与真值 IOU = 0.30
框 A 成为责任框
Pr(狗 | 有物体) = 0.80
框 A 置信度目标 = 0.70
狗的类专属分数 = 0.80 × 0.70 = 0.56
```

FIG 03 must show the `0.56` class score. FIG 04 must reuse boxes A/B and IOU 0.70/0.30 rather than introducing differently named boxes.

- [ ] **Step 4: Correct and deepen the five-part loss explanation**

Use this exact five-line structure in prose and FIG 04:

```text
① 责任框中心 x,y：× λcoord=5
② 责任框尺寸 √w,√h：× λcoord=5
③ 责任框置信度：目标 = 当前 IOU
④ 非责任框与空格框置信度：目标 = 0，× λnoobj=0.5
⑤ 有物体网格的一套 20 类条件概率
```

After the list, state that sum-squared error is easy to optimize but does not directly optimize mAP and weights localization/classification errors imperfectly.

- [ ] **Step 5: Replace the incorrect width example with normalized values**

Use this exact block:

```html
<pre class="eq">同样相差整图宽度的 0.01：
小框 0.01 → 0.02：√0.02 - √0.01 = 0.0414
大框 0.10 → 0.11：√0.11 - √0.10 = 0.0154

平方根残差比：0.0414 / 0.0154 ≈ 2.68
真正进入损失的是残差平方：2.68² ≈ 7.20

✓ 同样偏 1% 图宽，小框收到的尺寸损失约是大框的 7.2 倍。</pre>
```

Do not retain the old `100→110 / 10→20` pixel example or the `罚约 2.7 倍` conclusion.

- [ ] **Step 6: Add the complete training recipe**

Keep the two-stage pretraining explanation and add a compact table containing:

| Item | Value |
|---|---|
| Detection training | about 135 epochs |
| Batch | 64 |
| Momentum | 0.9 |
| Weight decay | 0.0005 |
| Learning rate | warm from `1e-3` to `1e-2`; then `1e-2` for 75 epochs, `1e-3` for 30, `1e-4` for 30 |
| Regularization | dropout 0.5 after the first fully connected layer |
| Augmentation | scale/translation up to 20%; exposure/saturation up to 1.5× |

Do not invent a warmup epoch count; the prose should say `训练开头缓慢升到 1e-2`.

- [ ] **Step 7: Clarify inference and quantify NMS**

Keep `7×7×2=98` and class-specific scoring. Change the NMS threshold sentence to `例如 0.5` and explicitly label it as a hand-worked example rather than a paper-fixed hyperparameter. Add:

```text
论文还给了一个容易漏掉的量化结果：YOLO 的网格本身已经减少重复框，NMS 不像在 R-CNN/DPM 里那么关键，但仍能增加约 2-3 mAP。
```

- [ ] **Step 8: Run focused mechanism checks**

Run:

```bash
rg -n '约 2000|Fast R-CNN|Faster R-CNN|相对当前格子|相对整张图|0\.70|0\.30|0\.56|7\.20|135|dropout 0\.5|2-3 mAP' docs/papers/yolo.html wiki/papers/yolo.md
rg -n '100→110|10 →20|罚约 2\.7|R-CNN 家族.*上千次网络评估' docs/papers/yolo.html wiki/papers/yolo.md
```

Expected: the first command finds evidence in the detector opening, coordinate explanation, running example, loss example, training table, and NMS paragraph; the second command returns no matches.

---

### Task 3: Build the complete experiment story and two new figures

**Files:**
- Modify: `docs/papers/yolo.html`
- Modify: `wiki/papers/yolo.md`

**Interfaces:**
- Consumes: paper Table 1, Figure 4, Table 2, Table 3, and Figure 5 values.
- Produces: one complete experiments section, FIG 07 error profile, FIG 08 artwork generalization, and a concise limitations/legacy close.

- [ ] **Step 1: Retitle and structure the experiments section**

Use the section title:

```html
<h2><span class="num">§ 06</span>实验：快只是半个答案，关键是它错得不一样</h2>
```

Keep FIG 06 as the speed-accuracy opening. Follow it with four subsections in this order:

```text
错误画像 · 定位差，背景误检少
模型互补 · 不是普通集成
VOC 2012 · 小物体短板坐实
跨域泛化 · 从照片迁到艺术画
```

- [ ] **Step 2: Add FIG 07 as two exact 100% stacked bars**

Use a `720×300` SVG. Each bar starts at `x=70`, has width `600`, and uses these segment widths:

| Model | Correct | Localization | Similar | Other | Background |
|---|---:|---:|---:|---:|---:|
| Fast R-CNN | 429.6 | 51.6 | 25.8 | 11.4 | 81.6 |
| YOLO | 393.0 | 114.0 | 40.5 | 24.0 | 28.5 |

Use one consistent color per error type across both rows. Put values in a separate legend/callout area when a segment is too narrow; do not force text inside 11.4px or 24px segments. The two primary callouts must read:

```text
YOLO 定位错误：19.0% vs 8.6%
YOLO 背景误检：4.75% vs 13.6%（约三分之一）
```

The caption must state that values are the top-N VOC 2007 detections averaged across 20 classes.

- [ ] **Step 3: Add the model-complement table**

Add this exact table below FIG 07:

| Added model | Added model mAP | Combined with best Fast R-CNN | Gain |
|---|---:|---:|---:|
| Fast R-CNN (2007 data) | 66.9 | 72.4 | +0.6 |
| Fast R-CNN (VGG-M) | 59.2 | 72.4 | +0.6 |
| Fast R-CNN (CaffeNet) | 57.1 | 72.1 | +0.3 |
| YOLO | 63.4 | 75.0 | +3.2 |

The prose must anchor the baseline: `最佳 Fast R-CNN 单独为 71.8 mAP` and conclude that YOLO helps because its background/localization tradeoff differs, not merely because another model was added.

- [ ] **Step 4: Add the VOC 2012 evidence**

State all three facts together:

```text
YOLO：57.9 mAP
Fast R-CNN：68.4 mAP
Fast R-CNN + YOLO：70.7 mAP（+2.3）
```

Then state that bottle, sheep, and tv/monitor trail nearby methods by 8-10 points, while cat and train are stronger. Keep this as evidence for the small-object limitation rather than a full 20-class leaderboard.

- [ ] **Step 5: Add FIG 08 as a two-panel grouped bar chart**

Use a `720×330` SVG with a shared vertical scale from 0 to 60 AP. The left panel is Picasso; the right panel is People-Art. Plot:

| Model | Picasso | People-Art |
|---|---:|---:|
| YOLO | 53.3 | 45 |
| R-CNN | 10.4 | 26 |
| DPM | 37.8 | 32 |

Each bar must show its exact value above it. Add one bottom annotation:

```text
只说明这两个人体艺术数据集上的迁移结果，不外推成普遍域泛化保证
```

Link readers to the official paper for qualitative artwork examples instead of embedding Figure 6.

- [ ] **Step 6: Add the real-time demo and limitations close**

Add one short sentence that the authors connected YOLO to a webcam and included frame acquisition/display while verifying real-time behavior. Then close with four mechanism-linked limitations:

```text
每格只有两个框和一套类别概率 → 成群小目标容易漏
框形状从训练数据中学 → 罕见长宽比和布局不稳
多次下采样 → 定位特征偏粗
误差平方和不等于 mAP → 主要错误仍是定位
```

End with one sentence that the enduring contribution is reframing general-purpose detection as a single jointly trained regression system.

- [ ] **Step 7: Register and audit all figures**

Update the JavaScript array to:

```javascript
const figs = ['fig-oneshot','fig-grid','fig-cell','fig-loss','fig-nms','fig-tradeoff','fig-errors','fig-art'];
```

Run:

```bash
python3 -c "import re; from pathlib import Path; s=Path('docs/papers/yolo.html').read_text(); ids=re.findall(r'<figure id=\"([^\"]+)\"',s); reg=re.search(r'const figs = \[(.*?)\];',s,re.S).group(1); js=re.findall(r\"'([^']+)'\",reg); print(ids); print(js); assert ids==js; assert len(ids)==len(set(ids))==8"
```

Expected: both printed lists are identical and contain eight unique IDs.

---

### Task 4: Polish typography, sync metadata, render, and verify

**Files:**
- Modify: `docs/papers/yolo.html`
- Modify: `wiki/papers/yolo.md`
- Modify: `index.md`
- Modify: `log.md`
- Regenerate: `docs/index.html`
- Regenerate: `docs/papers.html`

**Interfaces:**
- Consumes: completed reader page and Markdown scaffold.
- Produces: one coherent published diff, passing audits, and one local revamp commit.

- [ ] **Step 1: Raise all SVG label sizes and clean overlaps statically**

Raise every SVG `<text>`/`<tspan>` below 11px to at least 11px; figure titles should be 13-14px. Reflow boxes, legends, and viewBoxes rather than shrinking text to make it fit.

Run:

```bash
python3 -c "import re; from pathlib import Path; s=Path('docs/papers/yolo.html').read_text(); bad=[float(x) for x in re.findall(r'<(?:text|tspan)[^>]*font-size=\"([0-9.]+)\"',s) if float(x)<11]; print(bad); assert not bad"
rg -n '<text[^>]*>.*<strong>|<tspan[^>]*>.*<strong>' docs/papers/yolo.html
```

Expected: `[]` from the first command; no matches from the second.

- [ ] **Step 2: Synchronize the Markdown scaffold**

Ensure `wiki/papers/yolo.md` contains:

```text
R-CNN/Fast R-CNN/Faster R-CNN distinction
x,y relative to grid cell; w,h relative to image
five-part loss and corrected 7.20× square-loss example
complete training recipe
VOC 2007 speed table
VOC 2007 error profile
Fast R-CNN + YOLO complementarity
VOC 2012 result
Picasso and People-Art data
four mechanism-linked limitations
```

Keep the Markdown concise; the bespoke HTML remains the reader-facing full explanation.

- [ ] **Step 3: Update the index and log**

Replace the YOLO line in `index.md` with a summary that includes the corrected detector comparison, `7×7×30`, five-part loss, `7.20×` small-box example, 19.0% localization vs 4.75% background error, Fast R-CNN combination `71.8→75.0`, and artwork generalization.

Append this semantic record to `log.md`:

```text
## [2026-07-10] expand+fix | yolo 深改为完整 YOLO v1 复习页: 区分原始 R-CNN/Fast/Faster R-CNN; 用同一只狗贯通责任格→双框竞争→0.56类分数→NMS; 修正√w,h示例(残差2.68×,平方损失7.20×); 补135epoch训练配方与SSE局限; 新增VOC2007错误画像(Fast R-CNN loc8.6/bg13.6 vs YOLO loc19.0/bg4.75)、模型互补(71.8→75.0,+3.2)、VOC2012 57.9与小物体短板、Picasso/People-Art跨域数据; 新增fig-errors与fig-art,全页SVG标签≥11px
```

- [ ] **Step 4: Render generated pages**

Run:

```bash
python3 render.py
```

Expected: exit code 0; no missing wikilinks; bespoke nav and glossary popover injection remain idempotent.

- [ ] **Step 5: Run structural audits**

Run:

```bash
diff <(rg -o 'href="#g-[0-9]+"' docs/papers/yolo.html | sort -u) <(rg -o 'id="g-[0-9]+"' docs/papers/yolo.html | sort -u)
python3 -c "import re; from pathlib import Path; s=Path('docs/papers/yolo.html').read_text(); ids=re.findall(r'<figure id=\"([^\"]+)\"',s); reg=re.search(r'const figs = \[(.*?)\];',s,re.S).group(1); js=re.findall(r\"'([^']+)'\",reg); assert ids==js; assert len(ids)==len(set(ids))==8; print('figure audit ok')"
python3 -c "from html.parser import HTMLParser; from pathlib import Path; p=HTMLParser(); p.feed(Path('docs/papers/yolo.html').read_text()); p.close(); print('html parser ok')"
git diff --check
```

Expected: glossary diff empty; `figure audit ok`; `html parser ok`; `git diff --check` empty.

- [ ] **Step 6: Run content-safety audits**

Run:

```bash
rg -n '用户问|你问的|刚才说|前面聊|你已经懂|你学的|放进你学的|点回来|一路点|终点就是这' wiki/papers/yolo.md docs/papers/yolo.html
rg -n 'agent-scheduler|agent-generator|tool-svc|cashier|canda|ToolPreStart|\bLovart\b|/Users/lovart' wiki/papers/yolo.md docs/papers/yolo.html index.md log.md
rg -n '[0-9]+k|测开|字节.*LD|buffer.*攒|你的朋友|你朋友|你选.*不选|你跟.*不对付' wiki/papers/yolo.md docs/papers/yolo.html index.md log.md
```

Expected: no matches. Review any match manually before proceeding.

- [ ] **Step 7: Perform desktop and narrow-screen visual review**

Start a local server only after checking the port owner:

```bash
lsof -nP -iTCP:4173 -sTCP:LISTEN
python3 -m http.server 4173 -d docs
```

Use the Browser skill to inspect `http://127.0.0.1:4173/papers/yolo.html` at desktop width and a narrow viewport. Check all eight figures, table overflow, glossary popover, animation reveal order, label/line collisions, and minimum readable type. Before stopping the server, confirm the exact listener with `lsof`; stop only the single server session started for this review.

If no browser backend is available, do not substitute static inspection for visual review. Record the missing desktop/narrow-screen check explicitly in the handoff.

- [ ] **Step 8: Review the complete diff**

Run:

```bash
git status --short
git diff --stat
git diff -- wiki/papers/yolo.md index.md log.md
git diff -- docs/papers/yolo.html
```

Expected: only the YOLO source page, Markdown scaffold, index/log, and render-produced publication files changed. No unrelated user edits are included.

- [ ] **Step 9: Create the single implementation commit**

Stage only verified files and commit:

```bash
git add wiki/papers/yolo.md docs/papers/yolo.html index.md log.md docs/index.html docs/papers.html
git commit -m "yolo: 补全实验与误差画像" -m "区分原始 R-CNN、Fast R-CNN 与 Faster R-CNN；修正平方根尺寸损失为 7.20×。新增 VOC 2007 错误画像与 Picasso/People-Art 泛化图，并补齐训练配方、模型互补、VOC 2012 和局限。"
```

If `render.py` changed another generated file solely because the edited YOLO metadata feeds it, inspect and add that exact file before committing. Never use `git add -A`.

- [ ] **Step 10: Verify the committed result and stop before push**

Run:

```bash
git status --short --branch
git show --stat --oneline --decorate HEAD
git diff HEAD^ --check
```

Expected: clean worktree; one YOLO implementation commit containing the complete revamp; no push performed.
