# helloanner.github.io

Anner 的个人作品集站点。

## 访问地址

<https://helloanner.github.io/>

## 项目结构

```
.
├── src/
│   ├── index.template.html    # 主页模板
│   ├── styles.css             # 主页样式
│   ├── partials/              # 主页片段（head / hero / timeline / footer）
│   ├── article/               # 文章公共模块（所有书籍页共用）
│   │   ├── article.css        #   设计系统：字体、间距、明暗双主题、目录、代码块、公式…
│   │   └── article.js         #   主题切换、回到顶部、目录滚动高亮、代码复制
│   └── projects/
│       └── moss/              # 一本书 = 一个项目
│           ├── book.json      #   书名与副标题
│           └── 01-*.md …      #   章节（front matter: title / eyebrow / tldr / date）
├── build.py                   # 构建脚本（主页 + 全部书籍）
├── .github/workflows/deploy.yml
└── dist/                      # 构建输出（不提交）
```

## 本地构建

```bash
python3 -m pip install markdown   # 唯一依赖
python3 build.py
```

构建结果在 `dist/`：主页 `dist/index.html`，书籍页 `dist/projects/<book>/`（第 1 章即 `index.html`）。

## 新增一篇文章 / 一本书

1. 在 `src/projects/<book>/` 新建 `book.json` 与 `NN-slug.md` 章节；
2. 章节只写 Markdown（`##` 小节、围栏代码块、`>` 提示块、GFM 表格、`$...$` 公式），样式由公共模块统一渲染，不做页面级定制；
3. `python3 build.py` 验证后 commit & push，GitHub Actions 自动部署。

设计与写作约定见 [AGENTS.md](AGENTS.md)。

## 自动部署

推送代码到 `main` 分支后，GitHub Actions 会自动运行 `build.py` 并将 `dist/` 部署到 GitHub Pages。

## 说明

- 纯静态站点：HTML + CSS + 少量 JS；主页标题使用 Google Fonts 的 La Belle Aurore，文章页使用 Inter/system-ui 字体栈。
- 文章页设计系统 1:1 复刻自 wenwen-d.github.io 的技术博客（亮/暗双主题、阅读列、目录栏、代码块、KaTeX 公式）。
- 所有数据与外部笔记库隔离，全部保存在本仓库内。
