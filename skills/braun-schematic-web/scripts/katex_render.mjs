// 把 HTML 里的 \( .. \) 和 \[ .. \] 预渲染成 KaTeX 标记;data-json 里的字符串也一并处理。
// 用法:node katex_render.mjs in.html out.html   (需要 npm i katex;throwOnError 打开,公式写错就失败)
import fs from 'node:fs';
import { createRequire } from 'node:module';
const katex = createRequire(process.cwd() + '/')('katex');   // 从当前目录的 node_modules 找 katex
const [, , inp, out] = process.argv;
let t = fs.readFileSync(inp, 'utf8'), n = 0;
const un = s => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const r = (tex, display) => { n++; return katex.renderToString(un(tex), { displayMode: display, throwOnError: true, output: 'html', strict: 'error' }); };
// JSON 数据块里的字符串:在字符串层面渲染,保持 JSON 合法
t = t.replace(/(<script type="application\/json" id="sg-data">)([\s\S]*?)(<\/script>)/, (m, a, body, c) => {
  const data = JSON.parse(body);
  const walk = v => typeof v === 'string' ? sub(v) : Array.isArray(v) ? v.map(walk) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x)])) : v;
  return a + JSON.stringify(walk(data)).replace(/</g, '\\u003c') + c;
});
function sub(s) {
  return s.replace(/\\\[([\s\S]+?)\\\]/g, (m, x) => r(x, true)).replace(/\\\(([\s\S]+?)\\\)/g, (m, x) => r(x, false));
}
// 页面主体(跳过 script/style)
t = t.split(/(<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>)/).map(p => /^<(script|style)/.test(p) ? p : sub(p)).join('');
fs.writeFileSync(out, t);
console.log('katex rendered:', n);
if (/\\\(|\\\[/.test(t.replace(/<script[\s\S]*?<\/script>/g, ''))) { console.error('UNRENDERED delimiters remain'); process.exit(2); }
