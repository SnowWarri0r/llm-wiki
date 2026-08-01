// 用真 KaTeX 校验全仓每一条数学源码。
// 为什么必须有：页面上 data-tex 走的是 throwOnError:false，非法命令只会渲染成
// 红字，不报错、不留痕迹（genception 的 v^\* 就这么活了很久）。正则猜不出
// "这条 LaTeX 合不合法"，只有真编译器说了算。
const fs = require('fs'), path = require('path');
const katex = require(path.join(__dirname, 'docs/vendor/katex/katex.min.js'));
const dec = s => s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"')
                  .replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const files = [];
(function walk(d){ for (const e of fs.readdirSync(d,{withFileTypes:true})) {
  const p = path.join(d, e.name);
  e.isDirectory() ? walk(p) : p.endsWith('.html') && files.push(p); } })(path.join(__dirname,'docs'));

let n = 0; const bad = [];
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8');
  const i = s.indexOf('<!-- mathify:start -->');   // 注入块里是脚本模板，不是内容
  if (i > 0) s = s.slice(0, i);
  const srcs = [...s.matchAll(/data-(?:tex|expr)="([^"]*)"/g)].map(m => dec(m[1]))
    .concat([...s.matchAll(/<code class="m">([\s\S]*?)<\/code>/g)]
              .map(m => dec(m[1].replace(/<[^>]+>/g, '')).trim()));
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
