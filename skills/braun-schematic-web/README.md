# braun-schematic-web(skill 包说明)

Braun 说明书风格的网页视觉规范,加上把复杂系统和论文讲清楚的讲解层。由 braun-lofi-web(视觉)和 theorem-schematic(形式化系统讲解)合并而来,并新增了算符级计算图和单文件构建管线。

不含任何具体产品的品牌资产,可以直接给任何站点用。

## 目录

```
braun-schematic-web/
├── SKILL.md                       主文件:何时使用、核心规则、工作流、响应式、反小字准则、禁止清单、自检
├── README.md                      本文件
├── AGENTS.snippet.md              备用:agent 不支持 SKILL.md 目录时并入 AGENTS.md
├── assets/
│   ├── tokens.css  base.css       设计令牌与基础组件(表格、刻度条、按钮、公式、代码块)
│   ├── schematic.css/.js          计算图、读数栏、讲义、术语展开(讲解层组件)
│   ├── fit-tables.js fit-math.js  表格堆叠、公式缩放,保证无横向滚动条
│   ├── head-snippets.html         简单页面的 <head> 片段(联网字体与 KaTeX)
│   └── example.html               学习页示例
├── references/
│   ├── compute-graphs.md          算符级计算图:数据格式、写法、构建与检查
│   ├── theorem-schematic.md       定理原理图、LADR 讲义、子代理复核流程
│   ├── learning-pages.md  charts-and-icons.md  katex.md  migrating-legacy-pages.md
└── scripts/
    ├── build_page.py              内联 CSS/JS,字体子集化后嵌入,KaTeX 预渲染,输出单文件
    ├── katex_render.mjs           build_page.py 调用的 KaTeX 预渲染
    ├── check_viewports.py         360–2560 七种宽度:溢出、圆角、小字、公式
    └── check_schematic.py         计算图:线穿框、箭头贴框、文字溢出、读数栏、窄屏清单
```

## 迁移到 Codex agent

这个目录本身就是标准的 Agent Skills 格式(一个带 YAML frontmatter 的 `SKILL.md`,加可选的 `scripts/`、`references/`、`assets/`),可以原样拷贝。

1. **安装位置**(按 OpenAI 当前文档;我整理时没能直接打开官方页面,是通过检索结果得出的,请以官方文档为准 —— https://developers.openai.com/codex/skills):
   - 项目级:`<仓库>/.agents/skills/braun-schematic-web/SKILL.md`
   - 用户级:`$HOME/.agents/skills/braun-schematic-web/SKILL.md`
   - 较旧的资料里还提到 `~/.codex/skills/` 与 `.codex/skills/`,可能是旧路径;如果你们的 Codex 版本较老,可以两处都试。
   - 注意:文件夹必须**直接**位于 skills 目录下(`skills/<name>/SKILL.md`),不要多包一层。
2. **验证**:重启 Codex(或开新会话),让它列出可用 skill,或直接提一个触发场景,例如"帮我做一个梯度下降的学习页面",看它是否按本风格输出。
3. **如果你们的 agent 不支持 SKILL.md 目录**:把 `AGENTS.snippet.md` 的内容并入项目的 `AGENTS.md`,并把 `assets/`、`references/`、`scripts/` 放进仓库,按实际路径调整引用。
4. **依赖**:
   - 用 `build_page.py` 构建的页面不引用任何外部资源。构建需要 Python 3、fonttools、brotli、node,`npm i katex @fontsource/barlow @fontsource/barlow-semi-condensed @fontsource/ibm-plex-mono`,以及含简体中文的 Noto Sans CJK(`.ttc`),路径用环境变量 `NODE_MODULES`、`CJK_TTC` 指。
   - 用 `head-snippets.html` 的简单页面需要能访问 Google Fonts 和 cdn.jsdelivr.net。
   - 检查脚本需要 Python 3 + `pip install playwright` + `python -m playwright install chromium`。
5. **与 Claude 版本的差异**:`SKILL.md` 里没有依赖任何某个产品专有的工具名;"保存到用户的工作目录并告诉用户路径"这一步按你们 agent 自己的文件输出方式处理即可。

## 快速试用

```bash
# 在包目录下
python scripts/check_viewports.py assets/example.html          # 7 个常见宽度,应全部 OK
python scripts/check_schematic.py 带计算图的页面.html           # 计算图的几何和窄屏检查
python scripts/check_viewports.py 你的页面.html --shot out/    # 同时保存截图
```

## 版本

2026-11-17。风格经多轮设计试错确定,"禁止清单"里的每一条都是试过且效果不好的做法。
