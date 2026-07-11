#!/usr/bin/env python3
"""批量发布历史报告到网站"""

import os
import subprocess
from pathlib import Path
from datetime import datetime

WEBSITE_DIR = Path.home() / "projects" / "ai-news-website"
POSTS_DIR = WEBSITE_DIR / "_posts"

# 报告目录映射
REPORT_DIRS = {
    "morning": Path.home() / ".hermes/cron/output/20eeacb765e6",
    "noon": Path.home() / ".hermes/cron/output/79c3eecbed89",
    "evening": Path.home() / ".hermes/cron/output/26da9ef864ba",
}

# 需要排除的测试文件
EXCLUDE_FILES = {
    "2026-06-25_23-32-25.md",  # 测试早报
    "2026-06-21_14-02-37.md",  # 测试午报
    "2026-06-21_14-17-35.md",  # 测试午报
    "2026-06-21_14-26-12.md",  # 测试午报
    "2026-06-21_14-29-24.md",  # 测试午报
    "2026-06-21_15-06-25.md",  # 测试午报
    "2026-06-21_15-08-31.md",  # 测试午报
    "2026-06-21_15-10-13.md",  # 测试午报
}

def get_date_from_filename(filename: str) -> str:
    """从文件名提取日期"""
    # 格式: 2026-06-12_08-32-35.md
    return filename.split("_")[0]

def get_time_from_filename(filename: str) -> str:
    """从文件名提取时间"""
    # 格式: 2026-06-12_08-32-35.md
    time_part = filename.split("_")[1].replace(".md", "")
    return time_part.replace("-", ":")

def create_jekyll_post(report_file: Path, report_type: str) -> str:
    """创建 Jekyll 帖子"""
    filename = report_file.name
    date_str = get_date_from_filename(filename)
    time_str = get_time_from_filename(filename)
    
    type_names = {
        "morning": "早报",
        "noon": "午报",
        "evening": "晚报"
    }
    type_name = type_names[report_type]
    
    # 读取报告内容
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 生成 Jekyll front matter
    front_matter = f"""---
layout: report
title: "AI {type_name} - {date_str}"
date: {date_str} {time_str} +0800
report_type: {report_type}
---

"""
    
    # 生成目标文件名
    target_filename = f"{date_str}-{report_type}.md"
    target_path = POSTS_DIR / target_filename
    
    # 写入文件
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)
    
    return str(target_path)

def main():
    os.chdir(WEBSITE_DIR)
    
    created_files = []
    
    # 遍历所有报告类型
    for report_type, report_dir in REPORT_DIRS.items():
        if not report_dir.exists():
            print(f"⚠️  目录不存在: {report_dir}")
            continue
        
        # 获取所有报告文件
        files = sorted([f for f in report_dir.iterdir() if f.suffix == '.md'])
        
        for report_file in files:
            # 排除测试文件
            if report_file.name in EXCLUDE_FILES:
                print(f"⏭️  跳过测试文件: {report_file.name}")
                continue
            
            # 创建 Jekyll 帖子
            target_path = create_jekyll_post(report_file, report_type)
            created_files.append(target_path)
            print(f"✅ 创建: {Path(target_path).name}")
    
    if not created_files:
        print("❌ 没有文件需要发布")
        return
    
    # Git 操作
    print(f"\n📦 准备发布 {len(created_files)} 个文件...")
    
    # Git add
    subprocess.run(['git', 'add', '_posts/'], check=True)
    
    # Git commit
    commit_msg = f"Add {len(created_files)} historical reports"
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    
    # Git push
    subprocess.run(['git', 'push'], check=True)
    
    print(f"\n✅ 成功发布 {len(created_files)} 个报告到网站")
    print(f"🌐 网站将在 1-2 分钟后更新: https://alexguan321-commits.github.io/ai-news/")

if __name__ == "__main__":
    main()
