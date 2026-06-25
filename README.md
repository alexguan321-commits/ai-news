# AI 资讯日报

每日 AI 行业资讯网站，由 Hermes Agent 自动采集和生成。

## 技术栈

- **静态网站生成器**: Jekyll
- **部署平台**: Vercel
- **自动化**: Hermes Agent Cron Jobs

## 本地开发

```bash
# 安装依赖
bundle install

# 本地运行
bundle exec jekyll serve

# 访问 http://localhost:4000
```

## 自动发布

报告通过 Hermes Agent Cron Job 自动生成并发布：

- 早报：每天 08:00
- 午报：每天 14:00
- 晚报：每天 21:00

## 目录结构

```
ai-news-website/
├── _posts/              # 报告文件
├── _layouts/            # 页面布局
├── assets/              # 静态资源
├── _config.yml          # Jekyll 配置
├── vercel.json          # Vercel 配置
└── publish_report.sh    # 自动发布脚本
```

## License

Private
