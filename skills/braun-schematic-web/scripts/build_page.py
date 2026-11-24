#!/usr/bin/env python3
"""把 src.html 构建成单文件页面:CSS/JS 内联、字体子集化后 base64 嵌入、KaTeX 预渲染。
页面不依赖任何外部资源,在任何环境下外观一致。

用法:python build_page.py src.html out.html [--assets DIR] [--work DIR]
src.html 里用占位符:
  <!--@CSS-->  tokens.css + base.css + schematic.css + 字体 + KaTeX 样式
  <!--@JS-->   fit-tables.js + fit-math.js + schematic.js
依赖:fonttools、brotli、node + npm 包 katex @fontsource/barlow @fontsource/barlow-semi-condensed @fontsource/ibm-plex-mono
      以及一个含简体中文的 Noto Sans CJK(.ttc)。路径可用环境变量 NODE_MODULES、CJK_TTC 覆盖。
构建会报告缺字(任何字体都没有的字符),必须为空。
"""
import argparse, base64, io, os, pathlib, re, subprocess, sys
from fontTools import subset
from fontTools.ttLib import TTFont, TTCollection

HERE = pathlib.Path(__file__).resolve().parent
NM = pathlib.Path(os.environ.get('NODE_MODULES', '/tmp/bld/node_modules'))
CJK = os.environ.get('CJK_TTC', '/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc')

def b64(b): return base64.b64encode(b).decode()

def subset_bytes(font_bytes, text, flavor='woff2', face=None):
    opt = subset.Options(); opt.flavor = flavor; opt.layout_features = ['*']; opt.notdef_outline = True; opt.name_IDs = []
    f = TTFont(io.BytesIO(font_bytes), fontNumber=face if face is not None else -1, lazy=True)
    s = subset.Subsetter(opt); s.populate(text=text); s.subset(f)
    out = io.BytesIO(); f.flavor = flavor; f.save(out); return out.getvalue()

def cjk_face(path):
    c = TTCollection(path)
    for i, f in enumerate(c.fonts):
        if 'SC' in f['name'].getDebugName(1): return i
    return 0

def cover(path, ch, face=None):
    f = TTFont(path, fontNumber=face) if face is not None else TTFont(path)
    return set(f.getBestCmap().keys())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--assets', default=str(HERE.parent / 'assets')); ap.add_argument('--work', default='/tmp/bld')
    a = ap.parse_args(); assets = pathlib.Path(a.assets); work = pathlib.Path(a.work); work.mkdir(exist_ok=True, parents=True)

    # 1. KaTeX 预渲染
    pre = work / 'prerender.html'
    subprocess.run(['node', str(HERE / 'katex_render.mjs'), a.src, str(pre)], check=True, cwd=str(NM.parent))
    html = pre.read_text(encoding='utf8')

    # 2. 收集页面实际用到的字符(KaTeX 内部的字符用 KaTeX 自己的字体,不计入)
    from html.parser import HTMLParser
    import json as _json
    class P(HTMLParser):
        def __init__(s): super().__init__(); s.out = []; s.stack = []; s.skip = 0
        def handle_starttag(s, tag, attrs):
            cls = dict(attrs).get('class', '') or ''
            if tag in ('script', 'style') and not s.skip: s.stack.append(('x', tag)); s.skip += 1; return
            if 'katex' in cls.split() and tag in ('span',): s.stack.append(('k', tag)); s.skip += 1; return
            if s.skip and tag not in ('br', 'img', 'input', 'meta', 'link'): s.stack.append(('n', tag))
        def handle_endtag(s, tag):
            if s.stack and s.stack[-1][1] == tag:
                kind, _ = s.stack.pop()
                if kind in ('x', 'k'): s.skip -= 1
        def handle_data(s, d):
            if not s.skip: s.out.append(d)
    def visible_text(h):
        p = P(); p.feed(h); return ''.join(p.out)
    text = set(visible_text(html))
    m = re.search(r'<script type="application/json" id="sg-data">([\s\S]*?)</script>', html)
    if m:
        def walk(v):
            if isinstance(v, str): text.update(visible_text(v))
            elif isinstance(v, list): [walk(x) for x in v]
            elif isinstance(v, dict): [walk(x) for x in v.values()]
        walk(_json.loads(m.group(1)))
    text |= set('0123456789.,%:;()[]+-=/ ')
    text = ''.join(sorted(text))
    cjk_chars = ''.join(ch for ch in text if ord(ch) > 0x2E7F)

    # 3. 字体
    faces = []
    def fs(family, weight, path, chars, style='normal'):
        data = subset_bytes(pathlib.Path(path).read_bytes(), chars)
        faces.append("@font-face{font-family:'%s';font-weight:%s;font-style:%s;font-display:block;src:url(data:font/woff2;base64,%s) format('woff2')}" % (family, weight, style, b64(data)))
    latin = ''.join(ch for ch in text if ord(ch) <= 0x2E7F)
    for w in (400, 500, 600, 700): fs('Barlow', w, NM / f'@fontsource/barlow/files/barlow-latin-{w}-normal.woff2', latin)
    for w in (400, 500, 600): fs('Barlow Semi Condensed', w, NM / f'@fontsource/barlow-semi-condensed/files/barlow-semi-condensed-latin-{w}-normal.woff2', latin)
    fs('IBM Plex Mono', 400, NM / '@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2', latin)
    missing = set()
    for w, name in ((400, 'Regular'), (500, 'Regular'), (700, 'Bold')):
        p = CJK % name; face = cjk_face(p)
        data = subset_bytes(pathlib.Path(p).read_bytes(), cjk_chars, face=face)
        faces.append("@font-face{font-family:'Noto Sans SC';font-weight:%d;font-display:block;src:url(data:font/woff2;base64,%s) format('woff2')}" % (w, b64(data)))
    cmap_c = cover(CJK % 'Regular', None, cjk_face(CJK % 'Regular'))
    missing = [ch for ch in cjk_chars if ord(ch) not in cmap_c and not ch.isspace()]
    # 拉丁部分缺字(Barlow 没有的字符会回退到 Noto Sans SC 或 KaTeX)
    bar = cover(str(NM / '@fontsource/barlow/files/barlow-latin-400-normal.woff2'), None)
    latin_missing = [ch for ch in latin if ord(ch) not in bar and ord(ch) not in cmap_c and not ch.isspace() and ch not in '​']

    # 4. KaTeX 样式与字体
    kd = NM / 'katex/dist'; kcss = (kd / 'katex.min.css').read_text(encoding='utf8')
    def kf(m):
        f = kd / 'fonts' / m.group(1)
        return 'url(data:font/woff2;base64,%s)' % b64(f.read_bytes()) if f.exists() else 'none'
    kcss = re.sub(r'url\(fonts/([^)]+\.woff2)\) format\("woff2"\),\s*url\(fonts/[^)]+\.woff\) format\("woff"\),\s*url\(fonts/[^)]+\.ttf\) format\("truetype"\)', lambda m: kf(m) + ' format("woff2")', kcss)
    kcss = re.sub(r'url\(fonts/[^)]+\)', 'none', kcss) if 'url(fonts/' in kcss else kcss

    css = '\n'.join((assets / n).read_text(encoding='utf8') for n in ['tokens.css', 'base.css', 'schematic.css'])
    css = '\n'.join(faces) + '\n' + kcss + '\n' + css
    js = '\n'.join((assets / n).read_text(encoding='utf8') for n in ['fit-tables.js', 'fit-math.js', 'schematic.js'])
    html = html.replace('<!--@CSS-->', '<style>' + css + '</style>').replace('<!--@JS-->', '<script>' + js + '</script>')
    pathlib.Path(a.out).write_text(html, encoding='utf8')
    print('wrote', a.out, '%.0f KB' % (len(html) / 1024))
    print('missing glyphs (CJK):', ''.join(missing) or 'none')
    print('missing glyphs (latin):', ''.join(sorted(set(latin_missing))) or 'none')
    if re.search(r'url\(fonts/', html): print('WARNING: KaTeX font url not inlined'); sys.exit(3)
    if missing: sys.exit(4)

if __name__ == '__main__': main()
