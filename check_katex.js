// 用真 KaTeX 校验全仓每一条数学源码。
// 为什么必须有：页面脚本一律 throwOnError:false，非法命令只会渲染成红字，
// 不报错、不进任何计数（v^\* 就这么活了很久）。正则猜不出"这条 LaTeX 合不
// 合法"，只有真编译器说了算。
//
// 承载形式必须全覆盖 —— 第一版只认 data-tex/data-expr/code.m，漏掉了自动页
// 用的 .tex，于是 concept 页上同一个 v^\* 一直没被抓到。当前四种壳是从
// 全仓「内容里含 \命令」的元素反查出来的，不是猜的：
//   code.m        mathify（bespoke 页行内）
//   .tex          render.py 的 KATEX_PAGE_SCRIPT（自动页 + 部分 bespoke）
//   [data-expr]   少数 bespoke 页自带脚本
//   .math         另几页 bespoke 自带脚本
const fs = require('fs'), path = require('path');
const katex = require(path.join(__dirname, 'docs/vendor/katex/katex.min.js'));
// 数字实体要一起解：markdown 把撇号输出成 &#x27;，只解命名实体会把 h&#x27;=…
// 当成非法源码报错（我第一版就这么误报了两条）。
const dec = s => s.replace(/&#x([0-9a-f]+);/gi, (_,h)=>String.fromCodePoint(parseInt(h,16)))
                  .replace(/&#(\d+);/g, (_,d)=>String.fromCodePoint(+d))
                  .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"')
                  .replace(/&apos;/g,"'").replace(/&amp;/g,'&');
const files = [];
(function walk(d){ for (const e of fs.readdirSync(d,{withFileTypes:true})) {
  const p = path.join(d, e.name);
  e.isDirectory() ? walk(p) : p.endsWith('.html') && files.push(p); } })(path.join(__dirname,'docs'));

const CARRIER = /<(\w+)((?=[^>]*(?:class="[^"]*\b(?:tex|math)\b[^"]*"|data-expr=))[^>]*)>([\s\S]*?)<\/\1>/g;
const CODE_M  = /<code class="m">([\s\S]*?)<\/code>/g;

let n = 0; const bad = [];
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8');
  const i = s.indexOf('<!-- mathify:start -->');    // 注入块里是脚本模板，不是内容
  if (i > 0) s = s.slice(0, i);
  s = s.replace(/<(style|script)\b[\s\S]*?<\/\1>/g, ' ');
  const srcs = new Set();
  for (const m of s.matchAll(CARRIER)) {
    const raw = m[3];
    if (/<(?:div|span|p|code|li)\b/.test(raw)) continue;   // 外层容器，取里面的
    const expr = /data-expr="([^"]*)"/.exec(m[2]);
    srcs.add(dec(expr ? expr[1] : raw.replace(/<[^>]+>/g,'')).trim());
  }
  for (const m of s.matchAll(CODE_M)) srcs.add(dec(m[1].replace(/<[^>]+>/g,'')).trim());
  for (const t of srcs) {
    if (!t) continue;
    n++;
    try { katex.renderToString(t, { throwOnError: true }); }
    catch (e) { bad.push([path.relative(__dirname, f), t.slice(0, 60), e.message.slice(0, 90)]); }
  }
}
for (const [f, t, m] of bad) console.log(`[ERROR] ${f}\n        源码: ${t}\n        ${m}`);
console.log(`KaTeX 校验 ${n} 条 · ${bad.length} 条编译失败`);
process.exit(bad.length ? 1 : 0);
