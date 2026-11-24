# 算符级计算图

用来讲一个计算过程(模型的一层、一个算法、一条数据通路)。每个框是一个量或一步运算,框里写算式,线是真实的数据流。不画"谁连谁"的关系图。

和 `theorem-schematic.md` 的区别:那里的图是手写坐标的定理关系图,适合带证明的系统。这里的图由 `assets/schematic.js` 按框的实际位置自动布线,适合论文里的架构、公式推导、数据通路。两者可以放在同一页。

## 什么算一张合格的计算图

1. 每个框内有算式,不是只有名字。名字放在框的第一行(14px 灰字),算式放在第二行,用 KaTeX 排。
2. 每个运算一个框:归一化、打分、softmax、乘、求和各占一个。不把"注意力"这种复合名词画成一个框。
3. 每条线是一个量真的流过去。程序不读的输入不连。参数用灰色实线,框用虚线,和数据区分。
4. 线交叉不表示连接。只有黑色小方块表示分叉。
5. 同一个符号全图只指一个量。
6. 图和图之间的差别要能一眼看出:同一个页面用标签页切换"做法",各做法共用同一套车道和阶段,位置一致。

## 数据格式

页面里放一个 `<script type="application/json" id="sg-data">`,内容是 `{modes: [...]}`。每个 mode:

```
{ id, name, hero,                    // hero:页首主算式(KaTeX 行间公式)
  cols,                              // CSS grid-template-columns,每个阶段一列
  lanes,                             // 车道数(行数)
  stages: ['来源', '归一化', ...],    // 列标题,同时是窄屏清单的分组名
  nodes: [{id, kind, s, l, ls?, tag, fx, read}],
  wires: [{a, b, pa?, pb?, kind?, route?, label?}],
  notes: [{tag, text}],              // 图下方的虚线框:论文论断、代价
  read0: {k, t, fm, p} }             // 未选中时读数栏显示的内容
```

- 节点 `kind`:`in` 来源,`op` 运算(灰底粗线),`out` 结果,`par` 参数(虚线),`note` 不可点的说明。
- `s` 是阶段(列号,从 1 起),`l` 是车道(行号,从 1 起),`ls` 是跨几条车道。
- `tag` 是第一行的类别名,`fx` 是 KaTeX 算式。`read` 是点开后读数栏的 `{k 种类, t 标题, fm 算式, p 说明}`,说明一两句。
- 连线端口:`pa`、`pb` 写 `R`、`L`、`T`、`B` 加可选的位置。`L=u2` 表示接在 L 边、高度对齐到节点 u2;`L:0.8` 表示 L 边 80% 高度。默认 `pa=R`、`pb=L`。
- `route`:默认走"水平、竖直、水平"(`hv`);`vh` 先竖后横;`drop` 从来源右侧分出,走行间缝隙,从下方进入目标,用来画"这个量绕过中间运算,直接送到后面"的线。
- `kind: 'param'` 画成灰色线(参数)。`label` 是线上的文字,最多 8 个字。

## 折叠重复结构

多条车道结构相同时(例如对每个来源各做一遍的归一化、打分、softmax),给这个 mode 加 `fold`:

```
fold: {from: 1, to: 4, rep: '4 条'}
```

页首出现按钮"合并重复结构"。点一下,车道 2 到 4 向车道 1 汇合并淡出(约 0.5 秒,缓入缓出,不回弹),车道 1 的文字换成通式。再点一下展开。

- 要换成通式的节点,给它加 `fxf`(通式算式)、`tagf`(通式类别名)、可选 `readf`(合并后点开读数栏显示的内容)。没有 `fxf`、`tagf` 的节点保持原样。
- `from` 车道本身保留。跨车道的节点(`ls`)不参与折叠,留在原处,所以求和框要在 `fxf` 里写成 `\sum_{i=0}^{3}`。
- 参数和只出现一次的运算(分母 Z、查询向量 w)不在 `from..to` 里,折叠后自动上移填空。
- 尊重 `prefers-reduced-motion`:用户设了减少动效,直接切换,不播动画。
- 动画只由点击触发,不自动播放,符合"响应用户操作的小变化"。

## 页面骨架

`scripts/build_page.py` 的输入是一个带占位符的 HTML:

```
<head>... <!--@CSS--></head>
<body><div class="page wide">
  <div class="crumb">导读 / <b id="sg-crumb"></b></div><h1>标题</h1><p class="lede">一句话</p>
  <div class="sg-head"><div class="sg-tabs" id="sg-tabs" role="tablist"></div><div class="sg-hero" id="sg-hero"></div></div>
  <div class="sg" id="sg"></div><div class="sg-notes" id="sg-notes"></div><div class="sg-read" id="sg-read"></div>
  <div class="lec" id="lec"> ...讲义条目... </div>
</div>
<script type="application/json" id="sg-data">{...}</script>
<!--@JS--></body>
```

`examples/attention-residuals/src/make.py` 是完整例子。用 Python 生成数据和讲义,比手写 JSON 不容易出错。注意:Python 3.10 的 f 字符串花括号里不能有反斜杠,公式用 `<名字>` 占位后替换。

## 讲义条目

```
<div class="li" data-n="节点id 节点id" data-m="模式id 模式id">
  <div class="lh"><span class="no">2.1</span><span class="ty">定义</span><span class="nm">名字</span><span class="src">出处</span></div>
  <div class="fm">\[ 公式 \]</div><p>一到三句。</p></div>
```

- `data-n`:点这一条时,图上保留的节点。写错的 id 会被 `check_schematic.py` 报出来。
- `data-m`:只在这些模式下显示。省略表示所有模式都显示。
- `ty` 的取值:记号、定义、注、论断、他人结果。论断是论文自己的结论,本页没有验证;他人结果是别人复现的数。这样读者分得清哪些是定义、哪些是证据。
- 术语写成 `<span class="term" data-def="定义">词</span>`,点一下原地展开。

## 论文导读的写法

- 先写出论文自己的记号,图里的符号和论文式子一一对应。图里的 `l=4` 这类具体数字,要在讲义 0.2 里说明。
- 论文的结论(损失降了多少、开销多少)放在讲义里,用表,每条标出处和页码。结论没有对应的图,所以不画灰色"论断框"冒充图的一部分;只有直接说明图里某个量的论断(如"内存 O(Ld)")才放进 `notes`。
- 没读到的部分在页脚写明。引用二手材料要写明哪一条来自二手。
- 他人复现的结果单列一条,标"评价"区分哪是对方论断、哪是自己判断。

## 构建与检查

```
python scripts/build_page.py src.html out.html      # 内联 CSS/JS,字体子集化后嵌入,KaTeX 预渲染
python scripts/check_schematic.py out.html          # 线不穿框、箭头贴框、文字不溢出、读数栏非空、窄屏清单
python scripts/check_viewports.py out.html          # 7 个宽度:溢出、圆角、小字、公式
```

构建的依赖:fonttools、brotli、node,以及 `npm i katex @fontsource/barlow @fontsource/barlow-semi-condensed @fontsource/ibm-plex-mono`;含简体中文的 Noto Sans CJK 的 `.ttc`。路径用环境变量 `NODE_MODULES`、`CJK_TTC` 指。构建会报告缺字,必须为 none。构建出的页面不引用任何外部资源,断网也是同一个样子。

## 窄屏

宽度不超过 1000px 时,图隐藏,改成按阶段分组的清单。清单里每项仍然带算式,点击行为不变。图在窄屏缩小后文字会低于 12px,违反反小字准则,所以不缩小。

## 已知的限制

- 线是自动布的,只有 `hv`、`vh`、`drop` 三种走法。复杂的回环要拆成两个框。
- 一张图建议不超过 25 个框,不超过 7 个阶段。再多就拆成两个模式。
- 折叠只支持一段连续的车道。
- 没有真实读者验证过这套图的可读性;冷读只验证过文字部分。
