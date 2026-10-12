# AGENTS.md

## 项目理念
- Anner 的个人作品集站点（https://helloanner.github.io/）：纯静态、无框架，`python3 build.py` 构建到 `dist/`，push 后由 GitHub Actions 自动部署。
- 内容分两类：主页（克制的编辑部式作品集）与项目「书籍」——每个项目当作一本书，按章节递进叙述（背景意义 → 机制 → 实现 → 边界教训）。
- 内容必须忠于真实经历；内部信息（内网链接、客户名、内部单号）一律抽象化后才能发布。

## 布局理念
- 主页：`src/index.template.html` + `src/partials/*` + `src/styles.css`，保持现有风格，不随意改版；项目卡片链接到对应书籍页。
- 书籍：`src/projects/<book>/` 下放 `book.json` 与章节 `NN-slug.md`（front matter：title / eyebrow / tldr / date）；产物在 `dist/projects/<book>/`，第 1 章即 `index.html`。
- 书籍页左侧栏 = 章节列表（Chapters）；右侧栏 = 当前页小节（On This Page，滚动高亮、可收起且状态跨页记忆）；右上角 Home 返回主页、太阳/月亮切换明暗。

## 风格理念
- 全部文章页共用唯一公共模块 `src/article/article.css` + `article.js`，1:1 复刻 wenwen-d.github.io 博客设计系统：Inter/system-ui 字体、16.5px/1.62 正文、780px 阅读列（宽图 1040px）、固定顶栏、回到顶部按钮。主页与文章页均支持亮/暗双主题：默认跟随系统主题（prefers-color-scheme，OS 切换时实时跟随），手动切换后才写入 localStorage "theme" 覆盖，首绘前初始化防闪烁。
- 新文章只写 Markdown，不做任何页面级样式定制，保证每篇文章风格完全一致。组件映射：`##` → Section N 并进入页内目录；围栏代码块 → 带语言标签 + Copy 按钮的卡片；`>` 引用 → 左侧竖线提示块；`![alt](src)` → figure + figcaption；GFM 表格；`$...$` / `$$...$$` → KaTeX；插图放 `src/projects/<book>/images/`。
- 本地构建依赖 `python3 -m pip install markdown`（CI 已含此步骤）。修改后及时 build 验证、commit 并 push。
