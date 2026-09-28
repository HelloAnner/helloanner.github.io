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
│   └── partials/
│       ├── head.html
│       ├── hero.html
│       ├── timeline.html       # 作品画廊与经历
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

- 纯静态站点：HTML + CSS；标题使用 Google Fonts 提供的 La Belle Aurore。
- 所有数据与外部笔记库隔离，全部保存在本仓库内。
