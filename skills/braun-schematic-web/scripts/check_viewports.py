#!/usr/bin/env python3
"""Braun Lo-fi 页面检查:常见设备尺寸下的横向溢出、圆角(含 SVG 的 rx 与圆头线帽)、KaTeX 渲染错误。

用法:
    python check_viewports.py page.html [more.html ...] [--widths 360,390,768,1024,1440,1920,2560] [--shot outdir] [--wait 1500]

依赖:
    pip install playwright && python -m playwright install chromium

输出每个 页面 × 宽度 一行;以 OK 开头表示通过,以 !! 开头表示有问题。退出码:全部通过为 0,否则为 1。
一次跑太多页面和宽度会超时,可以分批并行跑。
"""
import argparse, pathlib, sys
from playwright.sync_api import sync_playwright

DEFAULTS = {360: 740, 390: 844, 768: 1024, 1024: 768, 1280: 800, 1440: 900, 1920: 1080, 2560: 1080}

CHECK = r"""() => {
  const name = e => ((e.tagName + '.' + (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className)).slice(0, 60));
  const out = { overflow: document.documentElement.scrollWidth - innerWidth, wide: [], radius: [], svgRound: [], small: [],
    katexErr: document.querySelectorAll('.katex-error').length, rawMath: /\$\$|\\\(/.test(document.body.innerText),
    stacked: !!document.querySelector('table.is-stacked') };
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e), b = e.getBoundingClientRect();
    if (b.width > 0 && b.right > innerWidth + 1 && cs.position !== 'fixed') out.wide.push(name(e) + ':' + Math.round(b.right));
    if (cs.display !== 'none' && cs.borderTopLeftRadius !== '0px' && !e.closest('.ring')) out.radius.push(name(e));
    if (e.closest('svg')) {
      if (e.tagName === 'rect' && (parseFloat(cs.rx) > 0 || parseFloat(cs.ry) > 0)) out.svgRound.push('rect rx');
      if (cs.stroke !== 'none' && (cs.strokeLinecap === 'round' || cs.strokeLinejoin === 'round')) out.svgRound.push(name(e) + ' round-cap');
    }
  }
  // 反小字(KaTeX 上下标按 70% 缩放,不计):HTML 文字渲染后不小于 14px;SVG 文字按缩放后的实际像素算,不小于 12px
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode());) {
    if (!n.nodeValue.trim()) continue;
    const e = n.parentElement; if (!e || e.closest('.katex-mathml, script, style, [hidden]') || e.classList.contains('mtight') || e.closest('.mtight') || e.classList.contains('vlist-s') || !e.getClientRects().length) continue;
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const svg = e.closest('svg'); let px = parseFloat(cs.fontSize), min = 14;
    if (svg) { const m = e.getScreenCTM && e.getScreenCTM(); px = px * (m ? Math.hypot(m.a, m.b) : 1); min = 12; }
    if (px < min - 0.01) out.small.push(name(e) + ' ' + px.toFixed(1) + 'px');
  }
  for (const k of ['wide', 'radius', 'svgRound', 'small']) out[k] = [...new Set(out[k])].slice(0, 5);
  return out; }"""

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="+", help="HTML 文件路径或 URL")
    ap.add_argument("--widths", default="360,390,768,1024,1440,1920,2560")
    ap.add_argument("--wait", type=int, default=1500, help="加载后等待毫秒数(等字体与脚本)")
    ap.add_argument("--shot", help="截图输出目录(可选)")
    a = ap.parse_args()
    widths = [int(w) for w in a.widths.split(",")]
    if a.shot: pathlib.Path(a.shot).mkdir(parents=True, exist_ok=True)
    bad = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_arg in a.pages:
            url = page_arg if "://" in page_arg else pathlib.Path(page_arg).resolve().as_uri()
            for w in widths:
                h = DEFAULTS.get(w, 900)
                ctx = browser.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page()
                errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:80]))
                pg.goto(url); pg.wait_for_timeout(a.wait)
                r = pg.evaluate(CHECK)
                ok = r["overflow"] <= 0 and not r["radius"] and not r["svgRound"] and not r["small"] and not r["katexErr"] and not r["rawMath"] and not errs
                bad += 0 if ok else 1
                print(f"{'OK ' if ok else '!! '}{pathlib.Path(page_arg).name:28s} {w:4d}px overflow={r['overflow']:3d} stacked={int(r['stacked'])} "
                      f"radius={r['radius']} svgRound={r['svgRound']} small={r['small']} katexErr={r['katexErr']} rawMath={int(r['rawMath'])} wide={r['wide']} errs={errs[:1]}")
                if a.shot: pg.screenshot(path=str(pathlib.Path(a.shot) / f"{pathlib.Path(page_arg).stem}-{w}.png"), full_page=(w < 600))
                ctx.close()
        browser.close()
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
