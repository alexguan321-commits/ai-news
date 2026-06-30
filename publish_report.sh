#!/bin/bash
# AI News 自动发布脚本
# 用法: ./publish_report.sh <report_file> <report_type>
#
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

# 重新生成 index.html（自动扫描 _posts/ 目录）
cd "$WEBSITE_DIR"
python3 generate_index.py

# Git 操作（带重试）
git add "_posts/$FILENAME" index.html 2026-*/ cards/ styles.css
git commit -m "Add AI ${REPORT_TYPE^} - $(date +%Y-%m-%d\ %H:%M)"

# Push with retry (3 attempts, exponential backoff)
for i in 1 2 3; do
    if git push 2>&1; then
        echo "✅ 报告已发布: $FILENAME"
        echo "🌐 网站将在 1-2 分钟后更新"
        exit 0
    fi
    echo "⚠️ Push 失败 (尝试 $i/3)，${i}0s 后重试..."
    sleep $((i * 10))
done

echo "❌ 发布失败: git push 3 次重试均失败"
exit 1
