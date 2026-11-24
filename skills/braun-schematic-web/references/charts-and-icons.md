# 图表与图标

## 图表(SVG / Chart.js 均适用)

- **只用细线,不填充,没有渐变,不用平滑曲线。** 折线 2px,`stroke-linejoin: miter`,端点 `butt`,点与点之间直线连接。
- 柱状图、环形图:直角(`rx: 0`);环形图用 `stroke-linecap: butt`,段与段之间留 2~3px 直缝。
- 颜色顺序:主序列 `--ink`、次序列 `--series-2`(灰)、需要强调的那一条 `--accent`。三条以内;更多请改成小倍图或表格。
- 网格线:`--chart-grid`,1px 实线,只留横线。坐标文字 12.5px,`--ink-3`,`tabular-nums`。
- 柱状图:历史柱子用灰,当前一根用 `--ink`;不要把大面积柱子涂成点缀色。
- 占比首选"一行一条细线"的横向列表(名称 / 2~3px 细条 / 百分比),环形图能不用就不用。
- 图表宽度取容器实际宽度,窗口变化时重绘;窄屏减少坐标刻度数量。
- 不要图例之外的装饰、不要 3D、不要阴影。

## 图标

- 24×24 栅格,2px 描边(界面里常用 1.75),`stroke-linecap: square`、`stroke-linejoin: miter`,全部直线。
- **圆一律画成斜切八边形**:`M8 3H16L21 8V16L16 21H8L3 16V8Z`。
- 单色(`currentColor`),不填充、不带圆角方块底。当前页的图标不加底色,强调靠下方一条陶土线。
- 不用 emoji 当图标。

用法:

```html
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true"><path d="M4 12L10 18L20 6"/></svg>
```

下表每个 `d` 里以空格加 `M` 分隔的是多个子路径,拆成多个 `<path>`(或一个 `<path>` 里直接写多段 `M`)都可以。

| 名称 | path d |
|---|---|
| `chev` | `M5 9L12 16L19 9` |
| `check` | `M4 12L10 18L20 6` |
| `sun` | `M9 9H15V15H9Z M12 2V5 M12 19V22 M2 12H5 M19 12H22 M5 5L7 7 M17 17L19 19 M19 5L17 7 M7 17L5 19` |
| `moon` | `M16 3L10 4L5 8L4 14L8 19L14 21L20 18L14 16L11 12L11 7Z` |
| `folder` | `M3 5H10L12 8H21V19H3Z` |
| `globe` | `M8 3H16L21 8V16L16 21H8L3 16V8Z M3 12H21 M12 3V21` |
| `card` | `M3 5H21V19H3Z M3 10H21` |
| `tag` | `M3 3H12L21 12L12 21L3 12Z M7 7H10V10H7Z` |
| `plug` | `M9 3V8 M15 3V8 M6 8H18V13L15 17H9L6 13Z M12 17V21` |
| `grid` | `M3 3H10V10H3Z M14 3H21V10H14Z M14 14H21V21H14Z M3 14H10V21H3Z` |
| `layers` | `M12 3L21 8L12 13L3 8Z M3 12L12 17L21 12 M3 16L12 21L21 16` |
| `key` | `M3 8H10V16H3Z M10 12H21 M16 12V17 M20 12V16` |
| `zap` | `M13 2L4 14H11L10 22L20 9H13Z` |
| `chart` | `M4 21H20 M7 21V13 M12 21V5 M17 21V10` |
| `receipt` | `M5 3H19V21L16 18L12 21L8 18L5 21Z M8 8H16 M8 12H16` |
| `gift` | `M4 11V21H20V11 M3 7H21V11H3Z M12 7V21 M12 7L8 3L6 5L9 7 M12 7L16 3L18 5L15 7` |
| `activity` | `M2 12H7L10 4L14 20L17 12H22` |
| `gauge` | `M4 19V15L7 9L12 6L17 9L20 15V19Z M12 19L16 11` |
| `bell` | `M6 17V10L9 5H15L18 10V17L20 19H4Z M10 21H14` |
| `shield` | `M12 3L20 6V13L12 21L4 13V6Z` |
| `ticket` | `M3 6H21V10L19 12L21 14V18H3V14L5 12L3 10Z M14 7V9 M14 11V13 M14 15V17` |
| `percent` | `M19 5L5 19 M5 5H9V9H5Z M15 15H19V19H15Z` |
| `heart` | `M12 20L4 12V7L7 4H10L12 6L14 4H17L20 7V12Z` |
| `list` | `M8 6H21 M8 12H21 M8 18H21 M3 6H5 M3 12H5 M3 18H5` |
| `sliders` | `M4 21V14 M4 10V3 M12 21V12 M12 8V3 M20 21V16 M20 12V3 M1 14H7 M9 8H15 M17 16H23` |
| `server` | `M3 4H21V10H3Z M3 14H21V20H3Z M7 7H8 M7 17H8` |
| `users` | `M5 4H11V10H5Z M3 20V16H13V20 M15 4H19V9H15Z M15 14H21V20` |
| `clock` | `M8 3H16L21 8V16L16 21H8L3 16V8Z M12 7V12L16 14` |
| `mail` | `M3 5H21V19H3Z M3 5L12 13L21 5` |
| `refresh` | `M20 8H8V12 M20 8L17 5 M20 8L17 11 M4 16H16V12 M4 16L7 13 M4 16L7 19` |
| `copy` | `M8 8H20V20H8Z M4 16V4H16` |
| `menu` | `M4 6H20 M4 12H20 M4 18H20` |
| `alert` | `M12 3L22 20H2Z M12 9V14 M12 17V18` |
| `info` | `M8 3H16L21 8V16L16 21H8L3 16V8Z M12 11V17 M12 7V8` |
| `arrows` | `M4 8H20 M16 4L20 8L16 12 M20 16H4 M8 12L4 16L8 20` |
