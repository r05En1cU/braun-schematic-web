<!-- 如果你们的 agent 不支持 SKILL.md 目录格式:把这一段并入项目的 AGENTS.md,并把本包的 assets/、references/、scripts/ 目录放进仓库,路径按实际调整。 -->

## 可视化 / 数据看板 / 学习笔记页的视觉规范(Braun Lo-fi)

做可视化网页、看板、学习笔记页、知识讲解页、HTML 报告时,遵守以下规范(完整规则见 skills/braun-schematic-web/SKILL.md):

- 冷白灰纸 `#E8EBEE`、冷黑墨 `#14171A`;没有暖色、高饱和色、渐变、阴影、噪点;分区只靠留白和一条 1px 细线,不用卡片框。
- 字体 DIN 风格:Barlow + 思源黑体,大数字用 Barlow Semi Condensed,数字一律 `tabular-nums`。
- 一个圆角都没有(包括状态点、头像、开关,以及 SVG 的 `rx` 和圆头线帽)。
- 点缀色只有一个:Claude 陶土 `#D97757`。强调 = 文字下方画一条陶土线;强调型按钮 = `#B25A3D` 底 + 白字;每屏 1~3 处,面积 < 1%。
- 选中态 = 加粗 + 下方一条陶土线,不要深色整行填充 + 浅色字;悬停只改底色。
- 任何设备上都不出现横向滚动条:表格放不下就堆叠(`assets/fit-tables.js`),代码块自动换行,网格子项加 `min-width:0`,公式缩放。适配 360–2560 宽、9:16–21:9 比例。
- 反小字:少加补充说明;该讲的用 LADR 风格在讲义里一次讲完,图例和术语只定义一次;需要展开的做成点击展开的解释;图下不放说明小字。可见文字 HTML 不小于 14px、SVG 不小于 12px。
- 论文、模型结构、算法的导读:画算符级计算图,框内写算式,线是真实数据流(见 references/compute-graphs.md)。
- 交付的页面不引用外部资源:用 scripts/build_page.py 内联 CSS/JS、嵌入字体、预渲染 KaTeX。
- 不做页面切换过渡动画;不用荧光笔式高亮底色。
- 交付前运行 `python skills/braun-schematic-web/scripts/check_viewports.py 页面.html`,并截图复查 1440 与 390 两个宽度。
- 讲解形式化项目或复杂技术对象时,另读 skills/braun-schematic-web/references/theorem-schematic.md。
