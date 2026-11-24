#!/usr/bin/env python3
"""计算图页面(schematic.js 生成)的机械检查。用法:python check_schematic.py 页面.html [--width 1440]
对每个模式检查:
  1. 连线的线段不穿过非端点的框
  2. 箭头终点离目标框边不超过 6px
  3. 框内文字不溢出框
  4. 连线标签不压在框上
  5. 点开每个框,读数栏都有内容
  6. 讲义 data-n 里的 id 至少在一个模式里存在
  7. 窄屏(<=1000px)按步骤清单显示,且没有横向溢出
任何一项失败退出码为 1。"""
import argparse, json, pathlib, sys
from playwright.sync_api import sync_playwright

JS = r"""() => {
  const out = [], root = document.getElementById('sg'), o = root.getBoundingClientRect();
  const R = {}; document.querySelectorAll('.sg-grid [data-id]').forEach(b => { const r = b.getBoundingClientRect(); R[b.dataset.id] = [r.left - o.left, r.top - o.top, r.width, r.height]; });
  const ids = Object.keys(R), E = 1;
  document.querySelectorAll('.sg-wires > path').forEach(p => {
    const nums = p.getAttribute('d').match(/-?[0-9.]+/g).map(Number), pts = [];
    for (let i = 0; i < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
    const end = pts[pts.length - 1], start = pts[0];
    const near = (pt, r) => Math.min(Math.abs(pt[0] - r[0]), Math.abs(pt[0] - r[0] - r[2]), Math.abs(pt[1] - r[1]), Math.abs(pt[1] - r[1] - r[3]));
    const inside = (pt, r, t) => pt[0] >= r[0] - t && pt[0] <= r[0] + r[2] + t && pt[1] >= r[1] - t && pt[1] <= r[1] + r[3] + t;
    const endBox = ids.filter(id => inside(end, R[id], 6)), startBox = ids.filter(id => inside(start, R[id], 6));
    if (!endBox.length) out.push('arrow end not on a box: ' + end.map(Math.round));
    if (!startBox.length) out.push('wire start not on a box: ' + start.map(Math.round));
    for (let k = 0; k < pts.length - 1; k++) {
      const [x1, y1] = pts[k], [x2, y2] = pts[k + 1], lx = Math.min(x1, x2), hx = Math.max(x1, x2), ly = Math.min(y1, y2), hy = Math.max(y1, y2);
      for (const id of ids) {
        if (endBox.includes(id) || startBox.includes(id)) continue;
        const [x, y, w, h] = R[id];
        if (hx > x + E && lx < x + w - E && hy > y + E && ly < y + h - E) out.push('wire ' + Math.round(start[0]) + ',' + Math.round(start[1]) + ' crosses box ' + id);
      }
    }
  });
  document.querySelectorAll('.sg-grid .sg-n').forEach(b => {
    b.querySelectorAll('.tag, .fx').forEach(s => { if (s.scrollWidth > b.clientWidth + 1) out.push('text overflows box ' + b.dataset.id + ' by ' + (s.scrollWidth - b.clientWidth)); });
  });
  document.querySelectorAll('.sg-lab').forEach(l => {
    const r = l.getBoundingClientRect(), a = [r.left - o.left, r.top - o.top, r.width, r.height];
    for (const id of ids) { const [x, y, w, h] = R[id]; if (!(a[0] + a[2] <= x || x + w <= a[0] || a[1] + a[3] <= y || y + h <= a[1])) out.push('label ' + l.textContent + ' on box ' + id); }
  });
  return out; }"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('page'); ap.add_argument('--width', type=int, default=1440); a = ap.parse_args()
    url = pathlib.Path(a.page).resolve().as_uri(); bad = 0
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--no-sandbox']); pg = b.new_page(viewport={'width': a.width, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
        pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(800)
        data = json.loads(pg.evaluate("document.getElementById('sg-data').textContent"))
        all_ids = {n['id'] for m in data['modes'] for n in m['nodes']}
        for m in data['modes']:
            pg.click('#sg-tabs [data-m=%s]' % m['id']); pg.wait_for_timeout(250)
            res = pg.evaluate(JS)
            for n in m['nodes']:
                pg.evaluate("id => document.querySelector('.sg-grid [data-id=\"'+id+'\"]').click()", n['id'])
                if not pg.inner_text('#sg-read').strip(): res.append('empty read-out for ' + n['id'])
                pg.evaluate("id => document.querySelector('.sg-grid [data-id=\"'+id+'\"]').click()", n['id'])
            print(('OK ' if not res else '!! ') + m['id'].ljust(6), len(m['nodes']), 'nodes', len(m['wires']), 'wires', res[:6]); bad += bool(res)
        li_ids = set(pg.evaluate("[...document.querySelectorAll('#lec .li')].flatMap(l => (l.dataset.n||'').split(/\\s+/)).filter(Boolean)"))
        miss = sorted(li_ids - all_ids); print(('OK ' if not miss else '!! ') + 'lecture data-n ids', miss); bad += bool(miss)
        for w in (390, 768):
            q = b.new_page(viewport={'width': w, 'height': 844}); q.goto(url, wait_until='networkidle'); q.wait_for_timeout(600)
            ov = q.evaluate("document.documentElement.scrollWidth - innerWidth"); steps = q.evaluate("getComputedStyle(document.getElementById('sg-steps')).display")
            ok = ov <= 0 and steps == 'block'; bad += not ok
            print(('OK ' if ok else '!! ') + 'narrow', w, 'overflow', ov, 'steps display', steps)
        print('page errors:', errs or 'none'); bad += bool(errs)
    sys.exit(1 if bad else 0)
main()
