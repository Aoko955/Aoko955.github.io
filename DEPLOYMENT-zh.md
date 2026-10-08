# GitHub Pages 发布

本项目通过 `.github/workflows/jekyll-pages.yml` 运行 Python 静态构建，
将 `_pages/about.md`、`_config.yml` 和静态资源生成到 `_site/` 后发布。

## 仓库设置（首次配置）

1. 打开 https://github.com/Aoko955/Aoko955.github.io/settings/pages 。
2. 在 **Build and deployment → Source** 中选择 **GitHub Actions**。
3. 在 Actions 中打开 **Deploy site to GitHub Pages**，需要重发时点击
   **Run workflow**，选择 `main`。
4. 等待 `build` 和 `deploy` 成功后访问 https://aoko955.github.io/ 。

不要选择 **Deploy from a branch**：它会额外触发默认的
`pages build and deployment` Jekyll 工作流。本项目的旧 Jekyll 样式缺少
`vendor/breakpoint/breakpoint`，该流程会失败，即使 Python 发布已成功。
切换来源不会清除历史失败记录；检查最新的自定义工作流即可。

## 更新主页

修改正文、配置或图片后，先验证：

```sh
python3 build_preview.py --site
```

推送修改到 `main` 后会自动发布。`_site/` 是生成目录，不需要提交。
线上内容以 Python 构建结果为准，无需安装 Ruby 或运行 Jekyll。
