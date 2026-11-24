/* schematic.js  算符级计算图运行时。数据来自 #sg-data(JSON),版式见 schematic.css。
   框按 阶段(列)× 车道(行)放进网格;连线按框的实际位置在 SVG 里正交布线。
   连线种类:data 墨色实线,param 灰色实线(参数)。交叉不表示连接,只有方块结点才表示分叉。
   折叠:mode.fold = {from, to, rep} 时,车道 from..to 结构相同。点按钮,这些车道向第一条车道汇合并淡出,
   第一条车道的文字换成带下标 i 的通式(节点的 fxf、tagf、readf)。动画由用户点击触发,约 0.5 秒,缓入缓出,不回弹。 */
(function () {
  const D = JSON.parse(document.getElementById('sg-data').textContent);
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = $('#sg'), tabs = $('#sg-tabs'), hero = $('#sg-hero'), read = $('#sg-read'), notesEl = $('#sg-notes'), crumb = $('#sg-crumb');
  const NS = 'http://www.w3.org/2000/svg';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  let mode = D.modes[0], sel = null, focus = null, grid, svg, labs = [], wires = [];
  let E = 0, folded = false, rest = null, nat = {}, shift = {}, foldIds = [], anim = 0, swapped = false, foldBtn;

  const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
  const sv = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
  const gyOf = () => parseFloat(getComputedStyle(root).getPropertyValue('--gy')) || 26;
  const nodeHTML = (n, g) => '<span class="tag">' + (g && n.tagf ? n.tagf : n.tag) + '</span><span class="fx">' + (g && n.fxf ? n.fxf : n.fx) + '</span>';

  function tabsInit() {
    D.modes.forEach(m => {
      const b = el('button', '', m.name); b.setAttribute('role', 'tab'); b.dataset.m = m.id;
      b.onclick = () => setMode(m.id); tabs.append(b);
    });
    foldBtn = el('button', 'btn sg-fold', ''); foldBtn.id = 'sg-fold'; foldBtn.onclick = toggleFold; tabs.append(foldBtn);
  }
  function foldLabel() { return mode.fold ? (folded ? '展开 ' + mode.fold.rep : '合并重复结构') : ''; }
  function setMode(id) {
    cancelAnimationFrame(anim); mode = D.modes.find(m => m.id === id); sel = null; focus = null; E = 0; folded = false; swapped = false;
    $$('button[role=tab]', tabs).forEach(b => b.setAttribute('aria-selected', b.dataset.m === id));
    crumb.textContent = mode.name; hero.innerHTML = mode.hero;
    $$('#lec .li').forEach(li => { li.classList.remove('on'); li.hidden = !!li.dataset.m && li.dataset.m.split(' ').indexOf(id) < 0; });
    foldBtn.hidden = !mode.fold; foldBtn.textContent = foldLabel();
    build(); showRead(); paint();
  }

  function build() {
    root.innerHTML = '';
    grid = el('div', 'sg-grid');
    grid.style.setProperty('--cols', mode.cols);
    mode.stages.forEach((s, i) => { const h = el('div', 'sg-sh', s); h.style.gridColumn = i + 1; h.style.gridRow = 1; grid.append(h); });
    mode.nodes.forEach(n => {
      const b = el('button', 'sg-n ' + n.kind, nodeHTML(n, false));
      b.dataset.id = n.id; b.style.gridColumn = n.s; b.style.gridRow = (n.l + 1) + ' / span ' + (n.ls || 1);
      b.style.marginTop = n.l === 1 ? '14px' : 'var(--gy)';
      b.onclick = () => pick(n.id);
      grid.append(b);
    });
    svg = sv('svg', { class: 'sg-wires', 'aria-hidden': 'true' });
    root.append(grid, svg);
    const st = el('div', 'sg-steps'); st.id = 'sg-steps';   // 窄屏:按阶段分组的清单
    mode.stages.forEach((s, i) => {
      const ns = mode.nodes.filter(n => n.s === i + 1); if (!ns.length) return;
      st.append(el('h3', '', s)); const row = el('div', 'row');
      ns.forEach(n => { const b = el('button', 'sg-n ' + n.kind, nodeHTML(n, false)); b.dataset.id = n.id; b.onclick = () => pick(n.id); row.append(b); });
      st.append(row);
    });
    root.append(st);
    notesEl.innerHTML = '';
    (mode.notes || []).forEach(n => notesEl.append(el('div', 'sg-n note', '<span class="tag">' + n.tag + '</span><span class="fx" style="white-space:normal">' + n.text + '</span>')));
    requestAnimationFrame(() => { setupFold(); layout(); });
  }

  /* ---- 折叠 ---- */
  const foldedNode = id => foldIds.indexOf(id) >= 0;
  const laneOf = id => (mode.nodes.find(n => n.id === id) || {}).l;
  function setupFold() {
    nat = {}; foldIds = []; const f = mode.fold; if (!f || getComputedStyle(grid).display === 'none') return;
    mode.nodes.forEach(n => { if (n.l >= f.from && n.l <= f.to && !n.ls) foldIds.push(n.id); });
    foldIds.forEach(id => { const n = mode.nodes.find(x => x.id === id), b = $('[data-id="' + id + '"]', grid); nat[n.l] = Math.max(nat[n.l] || 0, b.getBoundingClientRect().height); });
    foldIds.forEach(id => { const n = mode.nodes.find(x => x.id === id), b = $('[data-id="' + id + '"]', grid); b.style.minHeight = nat[n.l] + 'px'; b.style.alignSelf = 'start'; });
    // 自然位置:各车道的 top 相对第 1 车道的差(此时 transform 还没设,取值干净)
    shift = {}; const laneTop = {}; foldIds.forEach(id => { const n = mode.nodes.find(x => x.id === id), b = $('[data-id="' + id + '"]', grid); laneTop[n.l] = b.offsetTop; });
    foldIds.forEach(id => { const n = mode.nodes.find(x => x.id === id); shift[id] = laneTop[n.l] - laneTop[f.from]; });

    applyFold(E, true);
  }
  function setRows(e) {
    const f = mode.fold, gy = gyOf(), rows = ['auto'];
    for (let r = 1; r <= mode.lanes; r++) rows.push(f && r > f.from && r <= f.to && nat[r] != null ? ((nat[r] + gy) * (1 - e)).toFixed(2) + 'px' : f && r === f.from && nat[r] != null ? (nat[r] + (r === 1 ? 14 : gy)) + 'px' : 'auto');
    grid.style.gridTemplateRows = rows.join(' ');
  }
  function swapText(on) {
    swapped = on;
    mode.nodes.forEach(n => { if (n.fxf || n.tagf) { const b = $('[data-id="' + n.id + '"]', grid); if (b) b.innerHTML = nodeHTML(n, on); } });
    $$('#sg-steps [data-id]').forEach(b => { const n = mode.nodes.find(x => x.id === b.dataset.id); if (n) b.innerHTML = nodeHTML(n, on); });
  }
  function applyFold(e, quiet) {
    E = e; const f = mode.fold; if (!f || !grid) return;
    setRows(e);
    rest = rest || {};
    foldIds.forEach(id => {
      const n = mode.nodes.find(x => x.id === id), b = $('[data-id="' + id + '"]', grid);
      if (n.l === f.from) return;          // 第 1 车道留下,只换成通式文字
      b.style.transform = e > 0 ? 'translateY(' + (-(shift[id] || 0) * e).toFixed(2) + 'px)' : '';
      b.style.opacity = e > 0 ? 1 - e : ''; b.style.visibility = e >= 1 ? 'hidden' : ''; b.style.pointerEvents = e > 0 ? 'none' : '';
    });
    if ((e >= .5) !== swapped) swapText(e >= .5);
    if (!quiet) layout();
  }
  function animate(to) {
    cancelAnimationFrame(anim); const from = E, t0 = performance.now(), dur = 520 * Math.abs(to - from);
    if (reduce.matches || dur === 0) { applyFold(to); return; }
    const ease = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const step = now => { const t = Math.min(1, (now - t0) / dur); applyFold(from + (to - from) * ease(t)); if (t < 1) anim = requestAnimationFrame(step); };
    anim = requestAnimationFrame(step);
  }
  function toggleFold() {
    if (!mode.fold) return; folded = !folded; sel = null; foldBtn.textContent = foldLabel();
    showRead(); animate(folded ? 1 : 0);
  }

  /* ---- 布线 ---- */
  const rect = id => { const e = $('.sg-grid [data-id="' + id + '"]', root), r = e.getBoundingClientRect(), o = root.getBoundingClientRect(); return { x: r.left - o.left, y: r.top - o.top, w: r.width, h: r.height }; };
  function port(id, spec) {
    const m = /^([LRTB])(?:=([\w-]+))?(?::([\d.]+))?$/.exec(spec || 'R'); const r = rect(id), f = m[3] == null ? .5 : +m[3];
    const ry = m[2] ? rect(m[2]) : r, yy = m[2] ? ry.y + f * ry.h : r.y + f * r.h;
    return { L: { x: r.x, y: yy }, R: { x: r.x + r.w, y: yy }, T: { x: r.x + f * r.w, y: r.y }, B: { x: r.x + f * r.w, y: r.y + r.h } }[m[1]];
  }
  function route(w) {
    const A = port(w.a, w.pa || 'R'), B = port(w.b, w.pb || 'L'), gx = parseFloat(getComputedStyle(grid).columnGap), gy = gyOf(), t = w.route || 'hv';
    if (t === 'drop') {                         // 从 A 右侧分出,走行间缝隙,再从下方进入 B
      const ra = rect(w.a), xj = A.x + 14, yg = ra.y + ra.h + gy / 2;
      return [A, { x: xj, y: A.y }, { x: xj, y: yg }, { x: B.x, y: yg }, B];
    }
    if (t === 'vh') { const ym = (A.y + B.y) / 2; return A.x === B.x ? [A, B] : [A, { x: A.x, y: ym }, { x: B.x, y: ym }, B]; }
    if (Math.abs(A.y - B.y) < .6) return [A, B];
    const xm = B.x - gx * (w.mid == null ? .5 : w.mid);
    return [A, { x: xm, y: A.y }, { x: xm, y: B.y }, B];
  }
  function layout() {
    if (!grid || !root.isConnected) return;
    const W = root.clientWidth, H = grid.offsetHeight;
    svg.setAttribute('width', W); svg.setAttribute('height', H); svg.style.height = H + 'px'; svg.style.width = W + 'px';
    svg.innerHTML = '<defs>' + [['ink', '#14171A'], ['acc', '#D97757'], ['gry', '#97A0AA']].map(([k, c]) => '<marker id="mk-' + k + '" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="' + c + '"/></marker>').join('') + '</defs>';
    labs.forEach(l => l.remove()); labs = []; wires = [];
    if (getComputedStyle(grid).display === 'none') return;
    (mode.wires || []).forEach(w => {
      const pts = route(w), d = 'M' + pts.map(p => p.x.toFixed(1) + ' ' + p.y.toFixed(1)).join(' L');
      const p = sv('path', { d, class: 'w-' + (w.kind || 'data'), 'marker-end': 'url(#mk-' + (w.kind === 'param' ? 'gry' : 'ink') + ')' });
      svg.append(p); wires.push({ w, p, pts, fold: (foldedNode(w.a) && laneOf(w.a) !== mode.fold.from) || (foldedNode(w.b) && laneOf(w.b) !== mode.fold.from) });
      if (w.label) {
        let i = 0; while (i < pts.length - 2 && Math.abs(pts[i].x - pts[i + 1].x) < 26) i++;
        const a = pts[i], b = pts[i + 1], lb = el('div', 'sg-lab', w.label);
        lb.style.left = ((a.x + b.x) / 2) + 'px'; lb.style.top = (a.y - 3) + 'px'; root.append(lb); labs.push(lb);
      }
    });
    // 分叉结点:某条线的端点或拐点落在另一条线的线段内部
    const segs = []; wires.forEach(o => { for (let i = 0; i < o.pts.length - 1; i++) segs.push({ o, a: o.pts[i], b: o.pts[i + 1] }); });
    const seen = new Set();
    wires.forEach(o => o.pts.forEach(v => segs.forEach(s => {
      if (s.o === o) return; const horiz = Math.abs(s.a.y - s.b.y) < .6, vert = Math.abs(s.a.x - s.b.x) < .6;
      const on = horiz ? Math.abs(v.y - s.a.y) < .6 && v.x > Math.min(s.a.x, s.b.x) + 1 && v.x < Math.max(s.a.x, s.b.x) - 1
               : vert ? Math.abs(v.x - s.a.x) < .6 && v.y > Math.min(s.a.y, s.b.y) + 1 && v.y < Math.max(s.a.y, s.b.y) - 1 : false;
      const k = Math.round(v.x) + ',' + Math.round(v.y);
      if (on && !seen.has(k)) { seen.add(k); const r = sv('rect', { x: v.x - 3, y: v.y - 3, width: 6, height: 6 }); if ((o.fold || s.o.fold) && E > 0) r.style.opacity = 1 - E; svg.append(r); }
    })));
    paint();
  }

  /* ---- 选中与聚焦 ---- */
  function neighbours(id) { const s = new Set([id]); (mode.wires || []).forEach(w => { if (w.a === id || w.b === id) { s.add(w.a); s.add(w.b); } }); return s; }
  function paint() {
    const keep = sel ? neighbours(sel) : null, f = focus;
    root.classList.toggle('dim', !!(keep || f));
    $$('.sg [data-id]', root).forEach(b => {
      const id = b.dataset.id, hot = (!keep || keep.has(id)) && (!f || f.has(id));
      b.classList.toggle('hot', hot); b.classList.toggle('sel', id === sel);
    });
    wires.forEach(o => {
      const { a, b } = o.w, on = (!sel || a === sel || b === sel) && (!focus || (focus.has(a) && focus.has(b)));
      o.p.classList.toggle('off', !on); o.p.classList.toggle('hot', !!sel && (a === sel || b === sel));
      o.p.setAttribute('marker-end', 'url(#mk-' + (o.p.classList.contains('hot') ? 'acc' : o.w.kind === 'param' ? 'gry' : 'ink') + ')');
      o.p.style.opacity = o.fold && E > 0 ? String((1 - E) * (on ? 1 : .12)) : '';
    });
    labs.forEach(l => l.style.opacity = sel || focus ? .25 : 1);
  }
  function pick(id) { sel = sel === id ? null : id; showRead(); paint(); }
  function showRead() {
    const n = sel && mode.nodes.find(x => x.id === sel), r = n ? (folded && n.readf ? n.readf : n.read) : mode.read0;
    read.innerHTML = '<div><div class="k">' + r.k + '</div><div class="t">' + r.t + '</div></div><div class="fm">' + (r.fm || '') + '</div><div><p>' + (r.p || '') + '</p></div>';
  }

  /* ---- 讲义:点一条,图只留下它说到的框;术语点一下展开 ---- */
  $('#lec').addEventListener('click', e => {
    const t = e.target.closest('.term');
    if (t) {
      const nx = t.nextElementSibling;
      if (nx && nx.classList.contains('tdef')) { nx.remove(); t.classList.remove('open'); return; }
      const d = el('span', 'tdef'); d.textContent = t.dataset.def; t.after(d); t.classList.add('open'); return;
    }
    const li = e.target.closest('.li'); if (!li) return;
    const on = li.classList.contains('on'); $$('#lec .li').forEach(x => x.classList.remove('on'));
    focus = null;
    if (!on) { li.classList.add('on'); const ids = (li.dataset.n || '').split(/\s+/).filter(x => mode.nodes.some(n => n.id === x)); focus = ids.length ? new Set(ids) : null; if (focus) root.scrollIntoView({ block: 'nearest' }); }
    paint();
  });

  tabsInit(); setMode(D.modes[0].id);
  addEventListener('resize', () => { if (grid) { setupFold(); layout(); } window.fitMath && fitMath(); });
  if (document.fonts) document.fonts.ready.then(() => { setupFold(); layout(); });
  // 供检查脚本和截图使用:直接设到某个折叠进度,不播动画
  window.__sg = { layout, get mode() { return mode; }, setFold(e) { cancelAnimationFrame(anim); folded = e > 0; foldBtn.textContent = foldLabel(); applyFold(e); showRead(); } };
})();
