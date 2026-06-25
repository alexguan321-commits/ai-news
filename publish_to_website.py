#!/usr/bin/env python3
"""
AI News 网站自动发布脚本
用于将 Hermes Agent 生成的报告发布到 Jekyll 网站
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

WEBSITE_DIR = Path.home() / "projects" / "ai-news-website"
POSTS_DIR = WEBSITE_DIR / "_posts"

def get_report_type_from_schedule():
    """根据当前时间判断报告类型"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 18:
        return "noon"
    else:
        return "evening"

def create_jekyll_post(report_content: str, report_type: str) -> str:
    """创建 Jekyll 格式的 Markdown 文件"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # 生成中文标题
    type_names = {
        "morning": "早报",
        "noon": "午报",
        "evening": "晚报"
    }
    type_name = type_names.get(report_type, "资讯")
    
    # Jekyll front matter
    front_matter = f"""---
layout: report
title: "AI {type_name} - {now.strftime('%Y年%m月%d日')}"
date: {date_str} {time_str} +0800
report_type: {report_type}
---

"""
    
    # 组合内容
    full_content = front_matter + report_content
    
    # 生成文件名
    filename = f"{date_str}-{report_type}.md"
    filepath = POSTS_DIR / filename
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    return str(filepath)

def git_commit_and_push(filepath: str, report_type: str):
    """Git commit 和 push"""
    os.chdir(WEBSITE_DIR)
    
    # Git add
    subprocess.run(['git', 'add', filepath], check=True)
    
    # Git commit
    now = datetime.now()
    commit_msg = f"Add AI {report_type.capitalize()} report - {now.strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    
    # Git push
    subprocess.run(['git', 'push'], check=True)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python publish_to_website.py <report_file> [report_type]")
        print("report_type: morning | noon | evening (默认根据时间自动判断)")
        sys.exit(1)
    
    report_file = sys.argv[1]
    report_type = sys.argv[2] if len(sys.argv) > 2 else get_report_type_from_schedule()
    
    # 读取报告内容
    with open(report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # 创建 Jekyll 帖子
    filepath = create_jekyll_post(report_content, report_type)
    print(f"✅ 创建帖子: {filepath}")
    
    # Git commit 和 push
    try:
        git_commit_and_push(filepath, report_type)
        print(f"✅ 已推送到 GitHub")
        print(f"🌐 网站将在 1-2 分钟后自动更新")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
