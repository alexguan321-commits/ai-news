#!/usr/bin/env python3
"""
将 _posts/ 中的 Markdown 报告转换为纯静态 HTML 网站
不需要 Jekyll，直接生成 HTML 文件
"""

import os
import re
from pathlib import Path
from datetime import datetime
import markdown
import shutil

POSTS_DIR = Path("_posts")
SITE_DIR = Path("_site")
TEMPLATES_DIR = Path("_templates")
BASE_URL = "/ai-news"  # GitHub Pages base path

def parse_frontmatter(content):
    """解析 frontmatter"""
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    fm_text = parts[1].strip()
    body = parts[2].strip()
    
    metadata = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            metadata[key] = value
    
    return metadata, body

def extract_report_type(filename):
    """从文件名提取报告类型"""
    if "-morning" in filename:
        return "早报"
    elif "-noon" in filename:
        return "午报"
    elif "-evening" in filename:
        return "晚报"
    return "资讯"

def build_post_page(metadata, body, output_path):
    """构建单篇报告页面"""
    title = metadata.get("title", "AI 资讯报告")
    date = metadata.get("date", "")
    report_type = metadata.get("report_type", "")
    
    # 转换 Markdown 为 HTML
    html_content = markdown.markdown(
        body,
        extensions=['extra', 'codehilite', 'toc']
    )
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - AI 资讯日报</title>
    <link rel="stylesheet" href="{BASE_URL}/styles.css">
</head>
<body>
    <nav class="navbar">
        <a href="{BASE_URL}/" class="logo">🤖 AI 资讯日报</a>
        <a href="{BASE_URL}/" class="back-link">← 返回首页</a>
    </nav>
    
    <main class="container">
        <article class="report-content">
            <header class="report-header">
                <h1>{title}</h1>
                <div class="meta">
                    <time>{date}</time>
                    <span class="report-type">{report_type}</span>
                </div>
            </header>
            
            <div class="content">
                {html_content}
            </div>
        </article>
    </main>
    
    <footer class="footer">
        <p>由 Hermes Agent 自动生成 | <a href="{BASE_URL}/">返回首页</a></p>
    </footer>
</body>
</html>"""
    
    output_path.write_text(html, encoding="utf-8")

def build_index_page(posts):
    """构建首页"""
    # 按日期排序（最新的在前）
    posts.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # 最新6篇
    latest_posts = posts[:6]
    
    latest_html = ""
    for post in latest_posts:
        report_type_label = extract_report_type(post["filename"])
        latest_html += f"""
        <article class="report-card">
            <a href="{BASE_URL}{post['url']}">
                <h3>{post['title']}</h3>
                <time>{post['date']}</time>
                <span class="report-type type-{post.get('report_type', '')}">{report_type_label}</span>
            </a>
        </article>
        """
    
    # 全部报告
    archive_html = ""
    for post in posts:
        report_type_label = extract_report_type(post["filename"])
        archive_html += f"""
        <div class="archive-item">
            <a href="{BASE_URL}{post['url']}">{post['title']}</a>
            <time>{post['date']}</time>
            <span class="report-type type-{post.get('report_type', '')}">{report_type_label}</span>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 资讯日报 - 每日 AI 行业资讯</title>
    <link rel="stylesheet" href="{BASE_URL}/styles.css">
</head>
<body>
    <nav class="navbar">
        <a href="{BASE_URL}/" class="logo">🤖 AI 资讯日报</a>
    </nav>
    
    <main class="container">
        <section class="hero">
            <h1>🤖 AI 资讯日报</h1>
            <p>每日 AI 行业资讯，由 Hermes Agent 自动采集和生成</p>
        </section>
        
        <section class="reports-list">
            <h2>📰 最新报告</h2>
            <div class="report-grid">
                {latest_html}
            </div>
        </section>
        
        <section class="all-reports">
            <h2>📚 全部报告 ({len(posts)} 篇)</h2>
            <div class="report-archive">
                {archive_html}
            </div>
        </section>
    </main>
    
    <footer class="footer">
        <p>由 Hermes Agent 自动生成 | 共 {len(posts)} 篇报告</p>
    </footer>
</body>
</html>"""
    
    return html

def main():
    """主函数"""
    print("🔨 开始构建静态网站...")
    
    # 清理并创建输出目录
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir()
    
    # 复制 CSS
    css_source = Path("styles.css")
    if css_source.exists():
        shutil.copy(css_source, SITE_DIR / "styles.css")
    
    # 处理所有帖子
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        print(f"  处理: {md_file.name}")
        
        content = md_file.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(content)
        
        # 生成 URL 路径
        date_str = md_file.stem[:10]  # 2026-06-07
        type_str = md_file.stem[11:]  # morning/noon/evening
        url = f"/{date_str}/{type_str}/"
        
        # 创建输出目录
        post_dir = SITE_DIR / date_str / type_str
        post_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成 HTML
        build_post_page(metadata, body, post_dir / "index.html")
        
        posts.append({
            "filename": md_file.stem,
            "title": metadata.get("title", f"AI 资讯 - {date_str}"),
            "date": metadata.get("date", date_str),
            "report_type": metadata.get("report_type", ""),
            "url": url
        })
    
    # 生成首页
    print("  生成首页...")
    index_html = build_index_page(posts)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")
    
    print(f"✅ 构建完成！共 {len(posts)} 篇报告")
    print(f"📁 输出目录: {SITE_DIR.absolute()}")

if __name__ == "__main__":
    main()
