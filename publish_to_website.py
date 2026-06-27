#!/usr/bin/env python3
"""
AI 资讯报告发布脚本
1. 读取报告文件
2. 保存到 _posts/ 目录
3. 构建静态网站
4. Git push 触发 GitHub Pages 部署
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

def extract_report_content(content):
    """从 cron 输出文件中提取实际报告内容"""
    # 查找报告的起始位置（以 "# AI 早报" 或 "# AI 午报" 或 "# AI 晚报" 开头）
    report_start = None
    for pattern in [r'^# AI 早报', r'^# AI 午报', r'^# AI 晚报', r'^# AI 资讯']:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            report_start = match.start()
            break
    
    if report_start is not None:
        # 提取从报告开始到文件末尾的内容
        return content[report_start:]
    else:
        # 如果没有找到报告标记，返回原始内容
        return content

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
    
    # 复制构建结果到根目录
    print("\n📋 复制构建结果到根目录...")
    site_dir = WEBSITE_DIR / "_site"
    for item in site_dir.iterdir():
        dest = WEBSITE_DIR / item.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
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
    print("🚀 GitHub Pages 将自动部署...")
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
    raw_content = report_path.read_text(encoding="utf-8")
    
    # 提取实际报告内容（去除 cron 元数据和原始数据）
    report_content = extract_report_content(raw_content)
    print(f"📝 提取报告内容: {len(report_content)} 字符")
    
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
    print("🌐 网站: https://alexguan321-commits.github.io/ai-news/")

if __name__ == "__main__":
    main()
