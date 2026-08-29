# helloanner.github.io

Anner 的个人作品集站点。

## 访问地址

<https://helloanner.github.io/>

## 项目结构

```
.
├── src/
│   ├── index.template.html    # 页面模板
│   ├── styles.css             # 全局样式
│   └── partials/              # HTML 片段
│       ├── head.html
│       ├── header.html
│       ├── hero.html
│       ├── links.html
│       ├── timeline.html
│       ├── portfolio.html
│       └── footer.html
├── build.py                   # 本地构建脚本
├── .github/workflows/deploy.yml  # GitHub Actions 自动部署
└── dist/                      # 构建输出（由 build.py 生成，不提交）
```

## 本地构建

```bash
python3 build.py
```

构建结果在 `dist/` 目录，可直接打开 `dist/index.html` 预览。

## 自动部署

推送代码到 `main` 分支后，GitHub Actions 会自动运行 `build.py` 并将 `dist/` 部署到 GitHub Pages。

## 说明

- 纯静态站点：HTML + CSS + 内联 SVG。
- 不依赖任何 UI 库或外部字体 CDN。
- 所有数据与外部笔记库隔离，全部保存在本仓库内。
