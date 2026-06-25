#!/bin/bash
# AI News 自动发布脚本
# 用法: ./publish_report.sh <report_file> <report_type>

set -e

REPORT_FILE="$1"
REPORT_TYPE="$2"
WEBSITE_DIR="$HOME/projects/ai-news-website"
POSTS_DIR="$WEBSITE_DIR/_posts"

if [ -z "$REPORT_FILE" ] || [ -z "$REPORT_TYPE" ]; then
    echo "用法: $0 <report_file> <report_type>"
    echo "report_type: morning | noon | evening"
    exit 1
fi

if [ ! -f "$REPORT_FILE" ]; then
    echo "错误: 报告文件不存在: $REPORT_FILE"
    exit 1
fi

# 生成文件名
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H-%M)
FILENAME="${DATE}-${REPORT_TYPE}.md"

# 创建 Jekyll front matter
cat > "$POSTS_DIR/$FILENAME" << EOF
---
layout: report
title: "AI ${REPORT_TYPE^} - $(date +%Y年%m月%d日)"
date: $(date +"%Y-%m-%d %H:%M:%S +0800")
report_type: ${REPORT_TYPE}
---

EOF

# 追加报告内容（跳过可能的原始 front matter）
cat "$REPORT_FILE" >> "$POSTS_DIR/$FILENAME"

# Git 操作
cd "$WEBSITE_DIR"
git add "_posts/$FILENAME"
git commit -m "Add AI ${REPORT_TYPE^} report - $(date +%Y-%m-%d\ %H:%M)"
git push

echo "✅ 报告已发布: $FILENAME"
echo "🌐 网站将在 1-2 分钟后更新"
