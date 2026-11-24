# 数学公式(KaTeX)

`<head>` 片段见 `assets/head-snippets.html`;公式容器样式在 `assets/base.css`(`.formula`);放不下时缩放用 `assets/fit-math.js`。

```html
<div class="formula">$$\theta_{t+1} = \theta_t - \underline{\eta}\,\nabla_\theta L(\theta_t)$$<span class="no">(1)</span></div>
```

规则:
- **不要启用单个 `$` 作为行内分隔符。** 只用 `\( … \)` 行内、`$$ … $$` 或 `\[ … \]` 块级。否则金额 `$138.20` 这类文字会被误当成公式(已实测)。
- 块公式用上下两条细线夹住,不要框、不要底色;编号靠右,窄体数字。
- 缩到 70% 仍放不下的公式(在 360px 手机上尤其容易),用 `\\` 或 `aligned` 手动断行。
- 公式里的强调用 `\underline{…}`(和"下方画线"一致),不要彩色字;陶土色不当文字色。
- KaTeX 自带的数学衬线字体是本风格唯一允许的衬线;公式里尽量不放中文,中文写在正文里。
- `throwOnError:false` 保证单个公式写错不会让整页挂掉。
- 无网络或沙箱不允许外链时:用 `npx katex` 预渲染成静态 HTML,或把 css / js / fonts 本地化。
- 自检:页面可见文本里不应残留 `$$` 或 `\(`;`.katex-error` 数量应为 0(`scripts/check_viewports.py` 会检查)。
