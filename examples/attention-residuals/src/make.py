#!/usr/bin/env python3
"""生成 Attention Residuals 导读页的 src.html,再调用 build_page.py 构建成单文件。
记号与论文一致:v_0 = h_1(词嵌入),v_i = f_i(h_i),h_l 是第 l 层的输入。
事实来源:arXiv 2603.15031 v1 的 ar5iv 文本,读到摘要至 §5.4 开头。"""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
M = lambda x: '\\(' + x + '\\)'          # 行内公式
D = lambda x: '\\[' + x + '\\]'          # 行间公式
def T(defn, word): return '<span class="term" data-def="%s">%s</span>' % (defn, word)

# ───────────── 图数据 ─────────────
def lane_nodes(n, src_defs, lanes_row):
    """n 条车道,每条:来源 v、k、s、α、u。列 1,2,3,5,6;Z 在列 4 的 lanes_row 行。"""
    nodes, wires = [], []
    return nodes, wires

L = 4  # 图中的 l:第 4 层的输入 h_4
RMS = r'\mathrm{RMSNorm}'

def read(k, t, fm='', p=''): return dict(k=k, t=t, fm=fm, p=p)

def S(tpl, **kw):
    """用 <名字> 做占位符的格式化,避免 f 字符串里的反斜杠。"""
    for k, v in kw.items(): tpl = tpl.replace('<' + k + '>', str(v))
    return tpl

def build_attn(mode_id, name, hero, sources, read0, notes, lanes_total):
    n = len(sources); zrow = n + 1
    sym = 'v' if mode_id == 'full' else 'b'
    nodes, wires = [], []
    for i, (tag, fx, rd, kind) in enumerate(sources):
        r = i + 1
        kw = dict(i=i, L=L, n=n, sym=sym + '_' + str(i))
        if mode_id == 'block' and i == 2: kw['sym'] = r'b_2^{1}'
        nodes.append(dict(id='v%d' % i, kind=kind, s=1, l=r, tag=tag, fx=M(fx), read=rd))
        nodes.append(dict(id='k%d' % i, kind='op', s=2, l=r, tag='归一化', fx=M(S(r'k_<i>=\mathrm{RMSNorm}(<sym>)', **kw)),
            read=read('运算', 'RMSNorm', D(r'\mathrm{RMSNorm}(x)=g\odot\frac{x}{\sqrt{\frac{1}{d}\sum_{m}x_m^{2}+\epsilon}}'),
                      '标准定义,论文未展开。它只用在键上,为的是不让输出幅度大的来源在 softmax 里占优。(§3.1)')))
        nodes.append(dict(id='s%d' % i, kind='op', s=3, l=r, tag='打分', fx=M(S(r's_<i>=w_<L>^{\top}k_<i>', **kw)),
            read=read('运算', '点积打分', D(S(r's_<i>=w_<L>^{\top}k_<i>', **kw)), '得到一个数。w 对这一层固定,k 随输入变,所以分数随内容变。(式 2、3)')))
        nodes.append(dict(id='a%d' % i, kind='op', s=5, l=r, tag='softmax 权重', fx=M(S(r'\alpha_<i>=e^{s_<i>}/Z', **kw)),
            read=read('运算', 'softmax 权重', D(S(r'\alpha_{<i>\to <L>}=\frac{e^{s_<i>}}{Z}', **kw)), '非负,和为 1。式 (2) 里的核函数 φ 取 exp 套在 q 与归一化后的 k 的点积上。')))
        nodes.append(dict(id='u%d' % i, kind='op', s=6, l=r, tag='加权', fx=M(S(r'u_<i>=\alpha_<i><sym>', **kw)),
            read=read('运算', '权重乘回来源', D(S(r'u_<i>=\alpha_{<i>\to <L>}\,<sym>', **kw)), '乘回的是没归一化的来源,不是 k。归一化只发生在打分这一支。(式 4)')))
        wires += [dict(a='v%d' % i, b='k%d' % i), dict(a='k%d' % i, b='s%d' % i), dict(a='s%d' % i, b='a%d' % i),
                  dict(a='a%d' % i, b='u%d' % i),
                  dict(a='v%d' % i, b='u%d' % i, pb='B:0.5', route='drop'),
                  dict(a='u%d' % i, b='h', pb='L=u%d' % i),
                  dict(a='s%d' % i, b='Z', pa='R'),
                  dict(a='Z', b='a%d' % i, pb='L:0.8'),
                  dict(a='w', b='s%d' % i, pb='L:0.8', kind='param')]
    nodes.append(dict(id='w', kind='par', s=2, l=zrow, tag='查询向量(训练得到)', fx=M(S(r'w_<L>', L=L)),
        read=read('参数', S('w_<L>:每层一个的查询向量', L=L), D(S(r'w_<L>\in\mathbb{R}^{d}', L=L)),
                  '每层一个 d 维向量,不依赖当前输入。论文要求全部初始化为 0:这时所有分数相等,权重相等,等于对来源取平均。(§3.1、§5)')))
    nodes.append(dict(id='Z', kind='op', s=4, l=zrow, tag='softmax 分母', fx=M(r'Z=\sum_{j}e^{s_{j}}'),
        read=read('运算', '分母', D(S(r'Z=\sum_{j=0}^{<m>}e^{s_j}', m=n - 1)), '所有来源的分数各取指数再相加。除以它,权重才和为 1。')))
    nodes.append(dict(id='h', kind='out', s=7, l=1, ls=n, tag='求和,得到输入', fx=M(S(r'h_<L>=\sum_i u_i', L=L)), tagf='求和,得到输入', fxf=M(S(r'h_<L>=\sum_{i=0}^{<m>}u_i', L=L, m=n - 1)),
        read=read('结果', S('第 <L> 层的输入', L=L), D(S(r'h_<L>=\sum_{i}u_i', L=L)), S('送进第 <L> 层的函数 f_<L>,得到新的 v_<L>,成为后面各层的来源之一。(式 4)', L=L))))
    # 折叠:前 n 条车道结构相同。第 1 条车道换成通式,其余向它合并
    gen = {'k': (r'k_i=\mathrm{RMSNorm}(<G>_i)', '归一化'), 's': (S(r's_i=w_<L>^{\top}k_i', L=L), '打分'),
           'a': (r'\alpha_i=e^{s_i}/Z', 'softmax 权重'), 'u': (S(r'u_i=\alpha_i<G>_i', G=sym), '加权')}
    gen['k'] = (S(gen['k'][0], G=sym), gen['k'][1])
    for nd in nodes:
        if nd['id'] == 'v0':
            nd['fxf'] = M(r'v_i') if mode_id == 'full' else M(r'b_i'); nd['tagf'] = '来源 i ×' + str(n)
        key = nd['id'][0]
        if nd['id'] in ('k0', 's0', 'a0', 'u0'):
            nd['fxf'] = M(gen[key][0]); nd['tagf'] = gen[key][1] + ' ×' + str(n)
            nd['readf'] = dict(nd['read'], t=nd['read']['t'] + '(i 取遍所有来源)', p='这一步对每个来源 i 各做一次,结构完全相同。' + nd['read']['p'])
    return dict(id=mode_id, name=name, hero=hero, fold=dict(**{'from': 1, 'to': n, 'rep': '%d 条' % n}), cols='minmax(0,1.05fr) minmax(0,1.5fr) minmax(0,1.2fr) minmax(0,1fr) minmax(0,1.2fr) minmax(0,1.2fr) minmax(0,1fr)', lanes=zrow,
                stages=['来源', '归一化', '打分', 'softmax 分母', '权重', '加权', '求和'],
                nodes=nodes, wires=wires, notes=notes, read0=read0)

src_full = [
  ('词嵌入', 'v_0=h_1', read('来源', '词嵌入 v_0', M('v_0=h_1'), '输入词变成的向量,始终是一个来源。(式 3)'), 'in'),
  ('第 1 层输出', 'v_1=f_1(h_1)', read('来源', '第 1 层输出 v_1', M('v_1=f_1(h_1)'), '每一层(注意力子层或前馈子层各算一层)的输出。(式 3)'), 'in'),
  ('第 2 层输出', 'v_2=f_2(h_2)', read('来源', '第 2 层输出 v_2', M('v_2=f_2(h_2)'), '同上。'), 'in'),
  ('第 3 层输出', 'v_3=f_3(h_3)', read('来源', '第 3 层输出 v_3', M('v_3=f_3(h_3)'), '同上。'), 'in'),
]
src_blk = [
  ('词嵌入', 'b_0=v_0', read('来源', '词嵌入 b_0', M('b_0=h_1'), '始终是一个来源。(§3.2)'), 'in'),
  ('块 1 的和', 'b_1=v_1+v_2', read('块的和', '块 1 的和 b_1', D(r'b_1=\sum_{j\in\mathcal{B}_1}f_j(h_j)=v_1+v_2'), '块内各层输出照旧直接相加。块外只看这个和。块大小取 2。(式 5)'), 'op'),
  ('块 2 的部分和', 'b_2^{1}=v_3', read('块的和', '块 2 的部分和', D(r'b_2^{1}=v_3'), '块 2 里已经算完一层(第 3 层),所以部分和只有 v_3。第 4 层是块 2 的第二层,按式 (6) 同时看到它。'), 'op'),
]
hero_std = D(r'h_l=h_{l-1}+f_{l-1}(h_{l-1})=v_0+v_1+\cdots+v_{l-1}')
hero_full = D(r'\begin{aligned}h_l&=\sum_{i=0}^{l-1}\alpha_{i\to l}\,v_i\\[4pt]\alpha_{i\to l}&=\frac{\exp\!\big(w_l^{\top}\mathrm{RMSNorm}(v_i)\big)}{\sum_{j=0}^{l-1}\exp\!\big(w_l^{\top}\mathrm{RMSNorm}(v_j)\big)}\end{aligned}')
hero_blk = D(r'\begin{aligned}h_l&=\sum_{s\in S_l}\alpha_{s\to l}\,s,\qquad S_l=\{b_0,\,b_1,\dots,b_{n-1},\,b_n^{\,i-1}\}\\[4pt]b_n&=\sum_{j\in\mathcal{B}_n}f_j(h_j)\end{aligned}')

MODES = []
# 标准残差
std_nodes, std_wires = [], []
for i, (tag, fx, rd, kind) in enumerate(src_full):
    std_nodes.append(dict(id=f'v{i}', kind='in', s=1, l=i + 1, tag=tag, fx=M(fx.replace('b_', 'v_')), read=rd))
    std_nodes.append(dict(id=f'm{i}', kind='op', s=2, l=i + 1, tag='固定权重 1', fx=M(f'1\\cdot v_{i}'),
        read=read('运算', '乘 1', M(f'1\\cdot v_{i}'), '没有可调的量。每个来源都按同样的权重进入求和。')))
    std_wires += [dict(a=f'v{i}', b=f'm{i}'), dict(a=f'm{i}', b='h', pb=f'L=m{i}')]
std_nodes.append(dict(id='h', kind='out', s=3, l=1, ls=4, tag='直接相加', fx=M(r'h_4=\sum_i v_i'),
    read=read('结果', '第 4 层的输入', D(r'h_4=v_0+v_1+v_2+v_3'), '层之间只有这一种聚合方式,和层的输入、深度都无关。(§2.1)')))
MODES.append(dict(id='std', name='标准残差', hero=hero_std, cols='220px 220px 260px', lanes=4,
    stages=['来源', '权重', '求和'], nodes=std_nodes, wires=std_wires,
    notes=[dict(tag='论文论断', text='PreNorm 下隐藏状态的大小随深度按 ' + M(r'O(L)') + ' 增长,每一层的相对贡献被稀释,早期层的信息被埋住。这是作者提出新方法的动机。(§1)')],
    read0=read('标准残差', '每个来源的权重都是 1', D(r'h_4=v_0+v_1+v_2+v_3'), '没有打分,没有 softmax。')))
MODES.append(build_attn('full', '完整 AttnRes', hero_full, src_full,
    read('完整 AttnRes', '一层的输入怎么算出来', D(r'h_4=\sum_{i=0}^{3}\alpha_{i\to 4}\,v_i'), '每个来源先归一化,再和 ' + M('w_4') + ' 打分,再 softmax 成权重,最后用权重对原来源求和。'),
    [dict(tag='代价(论文)', text='要保存每一层的输出:每个词元内存 ' + M('O(Ld)') + ',算术 ' + M('O(L^{2}d)') + '。普通训练里这些输出本来就为反向传播保留;开销出现在激活重计算和流水线并行下。(§3.1)')], 5))
MODES.append(build_attn('block', '分块 AttnRes', hero_blk, src_blk,
    read('分块 AttnRes', '只在块的和之间做同一套运算', D(r'S_4=\{b_0,\,b_1,\,b_2^{1}\}'), '来源从 4 个减到 3 个。后面的运算和完整 AttnRes 完全相同。'),
    [dict(tag='论文论断', text='块数 ' + M('N\\approx 8') + ' 就能恢复大部分收益。' + M('N=L') + ' 就是完整 AttnRes,' + M('N=1') + ' 退化为标准残差(词嵌入单独作为 ' + M('b_0') + ')。内存与通信从 ' + M('O(Ld)') + ' 降到 ' + M('O(Nd)') + '。(§3.2)')], 4))
# block 模式的 k、a、u 文字改用 b 记号
for n in MODES[2]['nodes']:
    if n['id'].startswith('k'): n['fx'] = M(f"k_{n['id'][1:]}={RMS}(b_{n['id'][1:]})")
    if n['id'].startswith('u'): n['fx'] = M(f"u_{n['id'][1:]}=\\alpha_{n['id'][1:]}b_{n['id'][1:]}")
for n in MODES[2]['nodes']:
    if n['id'] == 'u2': n['fx'] = M(r'u_2=\alpha_2 b_2^{1}')
    if n['id'] == 'Z':  n['read']['fm'] = D(r'Z=\sum_{j=0}^{2}e^{s_j}'); n['read']['p'] = '只对 3 个来源求和。'

# ───────────── 讲义 ─────────────
def li(no, ty, nm, body, n='', m='', src=''):
    return ('<div class="li" data-n="%s" data-m="%s"><div class="lh"><span class="no">%s</span><span class="ty">%s</span><span class="nm">%s</span>%s</div>%s</div>\n'
            % (n, m, no, ty, nm, ('<span class="src">%s</span>' % src) if src else '', body))
def fm(x): return '<div class="fm">' + D(x) + '</div>'
def tbl(head, rows, right=()):
    h = ''.join('<th%s>%s</th>' % (' class="r"' if i in right else '', c) for i, c in enumerate(head))
    b = ''.join('<tr>' + ''.join('<td%s>%s</td>' % (' class="r"' if i in right else '', c) for i, c in enumerate(r)) + '</tr>' for r in rows)
    return '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (h, b)

ALL = 'v0 v1 v2 v3 k0 k1 k2 k3 s0 s1 s2 s3 Z a0 a1 a2 a3 u0 u1 u2 u3 h w'
LEC = ''
LEC += li('0.1', '记号', '符号和术语',
  '<p>' + M('v_i') + ' 是第 i 层算出的输出,' + M('v_0=h_1') + ' 是' + T('把输入的每个词变成一个向量,作为第一层的输入。', '词嵌入') + '。每个 ' + M('v_i') + ' 都是一个' + T('一串长度固定的数,长度记作 d。模型里每个词、每一层的输出,都用这样一串数表示。', '向量') + '。' + M('h_l') + ' 是送进第 l 层的输入。' + M(r'\sum') + ' 把几项加起来,' + M(r'\alpha') + ' 是权重。</p>'
  '<p>' + T('对每个分数先取 e 的分数次方,再除以所有这些次方值之和。分数越高权重越大,全部权重加起来恰好是 1。', 'softmax') + ' 把一组分数变成和为 1 的权重。' + M(r'w^{\top}k') + ' 是 w 和 k 逐位相乘再相加得到的一个数,叫点积。' + T('把一个向量整体缩放,使它各位平方的平均值为 1。只改大小,不改方向。', 'RMSNorm') + ' 把向量的大小调成统一。</p>'
  '<p>每层把自己的输出加到输入上,这叫' + T('每一层不替换输入,而是把自己的输出加到输入上,所以输入里的信息一路保留下来。', '残差连接') + '。每层先对输入做 RMSNorm 再计算,这种排法叫' + T('现代大语言模型的常见排法:每层先对输入做 RMSNorm,再做注意力或前馈计算,结果加回输入。', 'PreNorm') + '。注意力子层和前馈子层各算一层。</p>')
LEC += li('0.2', '定义', '图的读法',
  '<p>方框是一个量或一步运算。实线是数据流向下一个框,灰色实线表示这个量是训练得到的参数。虚线框是参数。线的分叉处有一个黑方块,线交叉没有黑方块,表示不相连。图中 ' + M('l=4') + ',即求第 4 层的输入。</p>'
  '<p>点图上的框,上方读数栏显示它的算式。点讲义的一条,图上只留下它说到的框。带下划线的词点一下展开。</p>')
LEC += li('1.1', '定义', '标准残差', fm(r'h_l=h_{l-1}+f_{l-1}(h_{l-1})=h_1+\sum_{i=1}^{l-1}f_i(h_i)') + '<p>展开后,每个来源的权重都是 1。层只能拿到这一个累加后的总和,取不出其中某一个来源。</p>',
  n='v0 v1 v2 v3 m0 m1 m2 m3 h', m='std', src='论文 §2.1')
LEC += li('1.2', '论断', '作者认为的问题', '<p>这个固定累加在 PreNorm 下让隐藏状态的大小随深度增长,每一层的贡献被稀释。后面的层只好学出越来越大的输出来保持影响力。这是提出新方法的动机,论文没有声称已在所有模型里证实。</p>',
  n='', m='std', src='论文 §1、§2.1')
LEC += li('1.3', '论断', '和序列方向的类比', '<p>论文把深度方向的累加类比成循环网络沿时间的累加,把 AttnRes 类比成用注意力代替循环。它还论证标准残差对应深度方向的线性注意力,AttnRes 对应 softmax 注意力。这个论证在 §6,我没有读到。</p>',
  n='', m='std', src='论文 §1、§3')
LEC += li('2.1', '定义', '完整 AttnRes', fm(r'h_l=\sum_{i=0}^{l-1}\alpha_{i\to l}\,v_i,\qquad \alpha_{i\to l}=\frac{\varphi(w_l,v_i)}{\sum_{j=0}^{l-1}\varphi(w_l,v_j)},\qquad \varphi(q,k)=\exp\!\big(q^{\top}\mathrm{RMSNorm}(k)\big)') + '<p>权重非负,和为 1。每层有自己的 ' + M('w_l') + ',一个训练得到的向量。</p>',
  n=ALL, m='full block', src='论文式 (2)(3)(4)')
LEC += li('2.2', '注', '权重为什么随内容变', '<p>' + M('w_l') + ' 对每层固定,' + M('v_i') + ' 随输入变,所以同一层对不同输入给出不同权重。只有来源随内容变,查询本身不依赖当前输入。论文试过让查询依赖输入,损失更低(1.731 对 1.737),但每层多一个 ' + M(r'd\times d') + ' 投影,解码时要按顺序读内存,所以默认没用。</p>',
  n='w k0 k1 k2 k3 s0 s1 s2 s3', m='full block', src='论文 §3.1、§5.3')
LEC += li('2.3', '注', 'RMSNorm 只用在键上', '<p>打分用的是 ' + M(r'\mathrm{RMSNorm}(v_i)') + ',最后求和的是原来的 ' + M('v_i') + '。归一化防止输出幅度大的层在 softmax 里占优。去掉它,Full 从 1.737 变到 1.743,Block 从 1.746 变到 1.750。</p>',
  n='v0 v1 v2 v3 k0 k1 k2 k3 u0 u1 u2 u3', m='full block', src='论文 §3.1、§5.3')
LEC += li('2.4', '注', '初始化为零', '<p>所有 ' + M('w_l') + ' 必须初始化为 0。此时所有分数为 0,权重相等,AttnRes 起步时等于对来源取平均,避免训练一开始不稳。论文称这一点做过实验验证。</p>',
  n='w s0 s1 s2 s3 a0 a1 a2 a3', m='full block', src='论文 §5')
LEC += li('2.5', '注', '代价', '<p>完整版要保存每一层的输出,内存随层数线性增长,每个词元 ' + M('O(Ld)') + '。大规模训练要' + T('训练时不保存中间结果,需要时重新算一遍,用时间换内存。', '重算激活') + '并在' + T('把模型的不同层放到不同设备上,数据依次流过。', '流水线并行') + '的设备之间传这些输出,开销因此变高。</p>',
  n='v0 v1 v2 v3', m='full', src='论文 §3.1')
LEC += li('3.1', '定义', '分块 AttnRes',
  fm(r'b_n=\sum_{j\in\mathcal{B}_n}f_j(h_j),\qquad \mathbf{V}=\begin{cases}[\,b_0,\dots,b_{n-1}\,]^{\top}&i=1\\ [\,b_0,\dots,b_{n-1},\,b_n^{\,i-1}\,]^{\top}&i\ge 2\end{cases}') +
  '<p>把 L 层分成 N 块,每块 S=L/N 层。块内照旧直接相加成 ' + M('b_n') + ',块之间才做 2.1 的运算。第 n 块的第 i 层的来源是词嵌入、前面各完成块的和,以及本块已算完 i-1 层的部分和 ' + M(r'b_n^{\,i-1}') + '。图中块大小为 2,求第 2 块第 2 层的输入。</p>',
  n='v0 v1 v2 k0 k1 k2 s0 s1 s2 a0 a1 a2 u0 u1 u2 Z h w', m='block', src='论文式 (5)(6)')
LEC += li('3.2', '注', 'N 的两个极端', '<p>' + M('N=L') + ' 时每层自成一块,就是完整 AttnRes。' + M('N=1') + ' 时只剩一块,退化为标准残差,词嵌入单独作为 ' + M('b_0') + '。论文固定 ' + M(r'N\approx 8') + ',每个词元只需存 8 个隐藏状态。块版本看到的是块的和,看不到块内每一层单独的输出。</p>',
  n='v0 v1 v2', m='block', src='论文 §3.2')
LEC += li('3.3', '论断', '块大小', '<p>16 层模型上,块大小 S=2、4、8 的损失都在 1.746 附近,S=16、32 逐步靠近基线。这里 S 是每块的层数,和 N≈8 的块数是两个量。</p>',
  n='', m='block', src='论文 §5.3,图 6')

LEC += li('4.1', '论断', '消融:各部分有没有用', '<p>16 层模型,相同' + T('训练前人为设定、不由训练得出的数,例如学习率。', '超参数') + '和算力预算,表中是' + T('模型在没参与训练的数据上的平均预测误差,越低越好。', '验证损失') + '。</p>' +
  tbl(['做法', '验证损失'], [
    ['PreNorm 基线', '1.766'],
    [T('每层按固定、与输入无关的标量系数加权平均前面各层的输出。', 'DenseFormer'), '1.767'],
    ['mHC(多路并行残差流)', '1.747'],
    ['Full AttnRes', '1.737'],
    ['Full,查询依赖当前输入', '1.731'],
    ['Full,换成与输入无关的标量混合', '1.749'],
    ['Full,softmax 换成 sigmoid', '1.741'],
    ['Full,去掉 RMSNorm', '1.743'],
    ['滑动窗口(只看最近 8 层加词嵌入)', '1.764'],
    ['Block,S=4', '1.746'],
    ['Block,多头(H=16)', '1.752'],
    ['Block,去掉 RMSNorm', '1.750']], right=(1,)) +
  '<p>基线到 Full 降 0.029。换成与输入无关的标量混合后只降 0.017,约保留六成。DenseFormer 同样与输入无关却几乎无改善,它和这一行的差别论文正文没有说明,我没有找到。</p>',
  n='', m='', src='论文表 4,§5.3')
LEC += li('4.2', '论断', '缩放曲线', '<p>五个规模,上下文 8192 个' + T('模型处理文字的最小单位,常是一个词或词的一段。', '词元') + ',每组内所有做法共用为基线选的超参数,作者称这样对基线有利。</p>' +
  tbl(['激活参数', '基线', 'Block', 'Full', 'mHC(-lite)'], [
    ['194M', '1.931', '1.909', '1.899', '1.906'], ['241M', '1.895', '1.875', '1.874', '1.869'],
    ['296M', '1.829', '1.809', '1.804', '1.807'], ['436M', '1.766', '1.746', '1.737', '1.747'],
    ['528M', '1.719', '1.693', '1.692', '1.694']], right=(1, 2, 3, 4)) +
  '<p>拟合曲线 ' + M(r'\mathcal{L}=A\,C^{-\alpha}') + ',基线 ' + M(r'1.891\,C^{-0.057}') + ',Block ' + M(r'1.870\,C^{-0.058}') + ',Full ' + M(r'1.865\,C^{-0.057}') + '。算力 C 的单位是' + T('算力单位:每秒 10 的 15 次方次浮点运算,持续一天。', 'PFLOP/s 天') + '。C=5.6 时 Block 为 1.692,基线 1.714,论文把它说成相当于 1.25 倍算力。这是两条拟合曲线的比较,不是训练时间的实测。最大规模下 Block 与 Full 只差 0.001。</p>',
  n='', m='', src='论文表 2,§5.1')
LEC += li('4.3', '论断', '访存开销', '<p>每个词元每层,残差机制本身的内存读写量(不含层函数内部),典型值 L=128、N=8:</p>' +
  tbl(['做法', '读写量'], [['标准残差', '3d'], ['mHC(4 路)', '34d'], ['Full AttnRes', '24d'], ['Block AttnRes', '5.5d']], right=(1,)) +
  '<p>流水线并行下端到端训练开销低于 4%。典型推理负载下延迟开销低于 2%。两个数分开测,都不说明训练会变快。</p>',
  n='', m='', src='论文表 1,§4')
LEC += li('4.4', '论断', '48B 模型的下游成绩', '<p>Kimi Linear,总参数 48B,' + T('总参数中,处理每个词元时实际用到的部分。', '激活参数') + ' 3B,54 层,每块 6 层,共 9 块加词嵌入,即 10 个来源。预训练 1.4T 词元。</p>' +
  tbl(['基准', '基线', 'AttnRes', '差'], [[a, b, c, f'{round(float(c) - float(b), 1):+.1f}'] for a, b, c in [
    ('MMLU', '73.5', '74.6'), ('MMLU-Pro', '52.2', '52.2'), ('GPQA-Diamond', '36.9', '44.4'), ('BBH', '76.3', '78.0'),
    ('ARC-Challenge', '64.6', '65.7'), ('HellaSwag', '83.2', '83.4'), ('TriviaQA', '69.9', '71.8'), ('GSM8K', '81.7', '82.4'),
    ('MGSM', '64.9', '66.1'), ('Math', '53.5', '57.1'), ('CMath', '84.7', '85.1'), ('HumanEval', '59.1', '62.2'),
    ('MBPP', '72.0', '73.9'), ('CMMLU', '82.0', '82.9'), ('C-Eval', '79.6', '82.5')]], right=(1, 2, 3)) +
  '<p>15 项里 14 项提高,MMLU-Pro 持平。每项只给了一个数,我读到的部分没有误差范围。</p>',
  n='', m='', src='论文表 3,§5.2')
LEC += li('4.5', '论断', '训练过程中的观察', '<p>基线的隐藏状态大小随深度单调增长。论文称 Block AttnRes 把增长限制在块内,输出大小呈有界的周期形状,梯度在各层间也更均匀。这些来自论文的图 5,本页没有重现。</p>',
  n='', m='', src='论文 §5.2,图 5')
LEC += li('4.6', '他人结果', '一次独立复现', '<p>另一组作者按论文描述自己重写了 AttnRes(他们称当时官方代码未公开),在自己的设置下各训练 1 万步,指标是' + T('验证损失取指数,越低越好。', '困惑度') + '。220M 和 533M 参数时 AttnRes 比基线好(37.39 对 38.71,31.75 对 32.00)。1044M 时反而更差:31.76 对 29.70,差 6.9%。7.57B 时 18.58 对 17.43,差 6.6%。他们对原因的解释是来源高度冗余,权重趋于均匀,这是他们的论断。</p>'
  '<p>评价(我的判断):两组实验的模型、数据、训练步数都不同,这与 4.2 不构成矛盾,也不能互相推翻。</p>',
  n='', m='', src='arXiv 2605.18855')

RESULTS = '''
<section class="section"><h2>论文报告的几个数</h2>
<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))">
  <div><div class="label">等效算力优势(拟合曲线)</div><div class="value">1.25×</div><div class="sub">Block,C=5.6 PFLOP/s 天</div></div>
  <div><div class="label">训练开销(流水线并行下)</div><div class="value">&lt;4%</div><div class="sub">端到端</div></div>
  <div><div class="label">推理延迟开销</div><div class="value">&lt;2%</div><div class="sub">典型推理负载</div></div>
  <div><div class="label">GPQA-Diamond 提高</div><div class="value">+7.5</div><div class="sub">48B 模型,15 项里最大</div></div>
</div></section>'''

SRC = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Attention Residuals 导读</title>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<!--@CSS--></head>
<body><div class="page wide">
<div class="crumb">导读 / <b id="sg-crumb"></b></div>
<h1>Attention Residuals</h1>
<p class="lede">让每一层自己挑:前面各层的输出里,读哪几个,各读多少。</p>
<div class="sg-head"><div class="sg-tabs" id="sg-tabs" role="tablist"></div><div class="sg-hero" id="sg-hero"></div></div>
<div class="sg" id="sg"></div>
<div class="sg-notes" id="sg-notes"></div>
<div class="sg-read" id="sg-read"></div>
<div class="lec" id="lec">
%s</div>
%s
<p class="sub" style="margin-top:36px">依据 Kimi Team,Attention Residuals,arXiv 2603.15031 v1(2026-03-16)。读到摘要至 §5.4 开头,§5.4 其余、§6 和附录没读。公式记号与论文一致。标注为论断的条目只转述论文。</p>
</div>
<script type="application/json" id="sg-data">%s</script>
<!--@JS-->
</body></html>'''

def main():
    out = HERE / 'ar.src.html'
    out.write_text(SRC % (LEC, RESULTS, json.dumps(dict(modes=MODES), ensure_ascii=False)), encoding='utf8')
    final = HERE.parent / 'attention-residuals.html'
    subprocess.run([sys.executable, str(ROOT / 'skills/braun-schematic-web/scripts/build_page.py'), str(out), str(final)], check=True)
if __name__ == '__main__': main()
