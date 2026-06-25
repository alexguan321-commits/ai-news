#!/usr/bin/env python3
"""
AI 资讯报告发布脚本
1. 读取报告文件
2. 保存到 _posts/ 目录
3. 构建静态网站
4. Git push 触发 Vercel 部署
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re

WEBSITE_DIR = Path.home() / "projects" / "ai-news-website"
POSTS_DIR = WEBSITE_DIR / "_posts"

def extract_metadata(report_content, report_path):
    """从报告内容中提取元数据"""
    # 从文件名提取日期和类型
    filename = report_path.stem
    
    # 尝试匹配日期格式
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if date_match:
        date_str = date_match.group(1)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 确定报告类型
    if "morning" in filename or "早报" in report_content[:200]:
        report_type = "morning"
        title = f"AI 早报 - {date_str}"
    elif "noon" in filename or "午报" in report_content[:200]:
        report_type = "noon"
        title = f"AI 午报 - {date_str}"
    elif "evening" in filename or "晚报" in report_content[:200]:
        report_type = "evening"
        title = f"AI 晚报 - {date_str}"
    else:
        report_type = "morning"
        title = f"AI 资讯 - {date_str}"
    
    # 提取时间
    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', report_content)
    time_str = time_match.group(1) if time_match else "08:00:00"
    
    return {
        "title": title,
        "date": f"{date_str} {time_str} +0800",
        "report_type": report_type,
        "filename": f"{date_str}-{report_type}.md"
    }

def save_to_posts(report_content, metadata):
    """保存报告到 _posts 目录"""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成 frontmatter
    frontmatter = f"""---
layout: report
title: "{metadata['title']}"
date: {metadata['date']}
report_type: {metadata['report_type']}
---

"""
    
    # 写入文件
    post_file = POSTS_DIR / metadata["filename"]
    post_file.write_text(frontmatter + report_content, encoding="utf-8")
    
    print(f"✅ 已保存: {post_file.name}")
    return post_file

def build_site():
    """构建静态网站"""
    print("\n🔨 构建静态网站...")
    result = subprocess.run(
        ["python3", "build_static_site.py"],
        cwd=WEBSITE_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ 构建失败: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def git_push(commit_msg):
    """Git 提交并推送"""
    print("\n📤 推送到 GitHub...")
    
    os.chdir(WEBSITE_DIR)
    
    # Git add
    subprocess.run(["git", "add", "."], check=True)
    
    # Git commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            print("⚠️  没有变化需要提交")
            return True
        else:
            print(f"❌ 提交失败: {result.stderr}")
            return False
    
    print(f"✅ 已提交: {commit_msg}")
    
    # Git push
    result = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ 推送失败: {result.stderr}")
        return False
    
    print("✅ 已推送到 GitHub")
    print("🚀 Vercel 将自动部署...")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python3 publish_to_website.py <报告文件路径>")
        sys.exit(1)
    
    report_path = Path(sys.argv[1])
    
    if not report_path.exists():
        print(f"❌ 文件不存在: {report_path}")
        sys.exit(1)
    
    # 读取报告
    print(f"📄 读取报告: {report_path.name}")
    report_content = report_path.read_text(encoding="utf-8")
    
    # 提取元数据
    metadata = extract_metadata(report_content, report_path)
    print(f"📊 元数据: {metadata}")
    
    # 保存到 _posts
    post_file = save_to_posts(report_content, metadata)
    
    # 构建网站
    if not build_site():
        sys.exit(1)
    
    # Git push
    commit_msg = f"Add {metadata['title']}"
    if not git_push(commit_msg):
        sys.exit(1)
    
    print("\n✅ 发布完成！")
    print("🌐 网站: https://ai-news-olive-tau.vercel.app")

if __name__ == "__main__":
    main()
