# AGENTS.md

## 项目理念
- Anner 的个人作品集站点（https://helloanner.github.io/）：纯静态、无框架，`python3 build.py` 构建到 `dist/`，push 后由 GitHub Actions 自动部署。
- 内容分两类：主页（克制的编辑部式作品集）与项目「指南」——每个项目一本书，按章节递进叙述（背景意义 → 机制 → 实现 → 边界教训）。
- 内容必须忠于真实经历；内部信息（内网链接、客户名、内部单号）一律抽象化后才能发布。

## 布局理念
- 主页：`src/index.template.html` + `src/partials/*` + `src/styles.css`，保持现有风格，不随意改版；项目卡片链接到对应指南页。主页自带明暗跟随系统主题（右上角切换按钮）。
- 指南：`src/projects/<book>/` 下放 `book.json`（title / intro）与章节 `NN-slug.md`（front matter：title / eyebrow / tldr / date）。
- 产物在 `dist/projects/<book>/`：`index.html` 是独立的指南目录页（章节列表 + 各章小节锚点，对标 simonwillison.net 的 guide index）；每章一个独立页面，面包屑「作品集 > 书名」，右侧边栏为本书章节列表（当前章加粗），文尾上一章/下一章导航。

## 风格理念
- 全部指南页共用唯一公共模块 `src/article/article.css` + `article.js`，1:1 复刻 simonwillison.net 指南设计系统：Helvetica Neue 16px/1.45、940px 布局（560px 正文 + 280px 侧栏）、紫色渐变 smallhead 与页尾、蓝色下划线链接（悬停变虚线、已访问变紫）、Pygments GitHub 配色代码高亮（codehilite）、内容小节标题为加粗正文大小并带 # 锚点、暗色主题底色 #1a1a2e。
- 主题三态切换（auto → light → dark）：默认 auto 跟随系统 prefers-color-scheme；手动选择写入 localStorage "theme" 并设置 `data-theme` 属性；切换按钮在页尾（与 SW 一致）。必须声明 color-scheme，避免浏览器强制暗色转换的渲染瑕疵。
- 新文章只写 Markdown，不做页面级样式定制：`##` 小节自动带锚点 id 并进入指南目录页；围栏代码块走 Pygments 高亮；`>` 引用为紫色左边条；GFM 表格；`![alt](src)` → figure + figcaption；插图放 `src/projects/<book>/images/`。
- 静态资源 URL 带内容哈希版本号防缓存。本地构建依赖 `python3 -m pip install markdown pygments`（CI 已含）。修改后及时 build 验证、commit 并 push。
