#!/usr/bin/env python3
"""Generate index.html from _posts/ directory.

Scans all markdown files in _posts/ and generates a static index.html
with search/filter support. Run this after adding new reports.

Usage:
    python3 generate_index.py              # Generate index.html
    python3 generate_index.py --dry-run    # Preview without writing
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

WEBSITE_DIR = Path(__file__).parent
POSTS_DIR = WEBSITE_DIR / "_posts"
OUTPUT_FILE = WEBSITE_DIR / "index.html"


def parse_post(filepath):
    """Extract metadata from a post file."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    
    # Parse Jekyll front matter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not fm_match:
        return None
    
    fm = fm_match.group(1)
    title_m = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    date_m = re.search(r'^date:\s*(.+)$', fm, re.MULTILINE)
    type_m = re.search(r'^report_type:\s*(\w+)', fm, re.MULTILINE)
    
    if not title_m or not date_m:
        return None
    
    title = title_m.group(1).strip()
    date_str = date_m.group(1).strip()
    report_type = type_m.group(1).strip() if type_m else "morning"
    
    # Extract date from filename as fallback for URL
    fname = filepath.stem  # e.g. "2026-06-27-morning"
    date_prefix = fname[:10]  # "2026-06-27"
    
    # Build URL path
    url = f"/ai-news/{date_prefix}/{report_type}/"
    
    return {
        "title": title,
        "date": date_str,
        "report_type": report_type,
        "url": url,
        "date_prefix": date_prefix,
    }


def generate_html(posts):
    """Generate the full index.html content."""
    # Sort posts by date descending
    posts.sort(key=lambda p: p["date"], reverse=True)
    
    total = len(posts)
    latest = posts[:6]
    
    type_labels = {"morning": "早报", "noon": "午报", "evening": "晚报"}
    
    def render_card(p):
        label = type_labels.get(p["report_type"], p["report_type"])
        # Add emoji based on report type for visual interest
        emoji = "🌅" if p["report_type"] == "morning" else "☀️" if p["report_type"] == "noon" else "🌙"
        return f"""        <article class="report-card">
            <a href="{p['url']}">
                <div class="card-image">{emoji}</div>
                <div class="card-content">
                    <h3>{p['title']}</h3>
                    <time>{p['date']}</time>
                    <span class="report-type type-{p['report_type']}">{label}</span>
                </div>
            </a>
        </article>"""
    
    def render_archive(p):
        label = type_labels.get(p["report_type"], p["report_type"])
        return f"""        <div class="archive-item">
            <a href="{p['url']}">{p['title']}</a>
            <time>{p['date']}</time>
            <span class="report-type type-{p['report_type']}">{label}</span>
        </div>"""
    
    cards = "\n".join(render_card(p) for p in latest)
    archive = "\n".join(render_archive(p) for p in posts)
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 资讯日报</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar">
        <a href="/ai-news/" class="logo">AI 资讯日报</a>
        <div class="nav-stats">
            <div><span class="stat-value">{total}</span> reports</div>
            <div><span class="stat-value">35</span> sources</div>
            <div><span class="stat-value">24/7</span> monitoring</div>
        </div>
    </nav>
    
    <main class="container">
        <section class="hero">
            <h1>AI 资讯日报</h1>
            <p>每日 AI 行业深度情报，由 AI 自动采集、分析、生成</p>
        </section>
        
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">Reports Published</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">35+</div>
                <div class="stat-label">Data Sources</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">3</div>
                <div class="stat-label">Daily Editions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Auto Collection</div>
            </div>
        </div>
        
        <section class="search-section">
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="搜索报告..." autocomplete="off">
                <span id="searchCount" class="search-count"></span>
            </div>
            <div class="filter-tags">
                <button class="filter-tag active" data-filter="all">全部</button>
                <button class="filter-tag" data-filter="morning">早报</button>
                <button class="filter-tag" data-filter="noon">午报</button>
                <button class="filter-tag" data-filter="evening">晚报</button>
            </div>
        </section>
        
        <section class="reports-list">
            <div class="section-header">
                <h2>Latest</h2>
                <span class="count">{min(6, total)} most recent</span>
            </div>
            <div class="report-grid">
{cards}
            </div>
        </section>
        
        <section class="all-reports">
            <div class="section-header">
                <h2>Archive</h2>
                <span class="count">{total} reports</span>
            </div>
            <div class="report-archive">
{archive}
            </div>
        </section>
    </main>
    
    <footer class="footer">
        <p>AI 资讯日报 — 由 Hermes Agent 自动采集、分析、生成</p>
        <p class="footer-brand">COLLECTOR V3 · PIPELINE ARCHITECTURE · {total} REPORTS</p>
    </footer>
    
    <script>
    (function() {{
        const searchInput = document.getElementById('searchInput');
        const searchCount = document.getElementById('searchCount');
        const filterTags = document.querySelectorAll('.filter-tag');
        const archiveItems = document.querySelectorAll('.archive-item');
        const reportCards = document.querySelectorAll('.report-card');
        let activeFilter = 'all';
        
        function filterReports() {{
            const query = searchInput.value.toLowerCase().trim();
            let visibleCount = 0;
            
            archiveItems.forEach(item => {{
                const text = item.textContent.toLowerCase();
                const type = item.querySelector('.report-type');
                const typeClass = type ? type.className : '';
                const matchesSearch = !query || text.includes(query);
                const matchesFilter = activeFilter === 'all' || typeClass.includes('type-' + activeFilter);
                if (matchesSearch && matchesFilter) {{
                    item.style.display = '';
                    visibleCount++;
                }} else {{
                    item.style.display = 'none';
                }}
            }});
            
            reportCards.forEach(card => {{
                const text = card.textContent.toLowerCase();
                const type = card.querySelector('.report-type');
                const typeClass = type ? type.className : '';
                const matchesSearch = !query || text.includes(query);
                const matchesFilter = activeFilter === 'all' || typeClass.includes('type-' + activeFilter);
                card.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
            }});
            
            if (query || activeFilter !== 'all') {{
                searchCount.textContent = visibleCount + ' 条结果';
            }} else {{
                searchCount.textContent = '';
            }}
        }}
        
        searchInput.addEventListener('input', filterReports);
        filterTags.forEach(tag => {{
            tag.addEventListener('click', function() {{
                filterTags.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                activeFilter = this.dataset.filter;
                filterReports();
            }});
        }});
        document.addEventListener('keydown', function(e) {{
            if (e.key === '/' && document.activeElement !== searchInput) {{
                e.preventDefault();
                searchInput.focus();
            }}
            if (e.key === 'Escape') {{
                searchInput.value = '';
                searchInput.blur();
                filterReports();
            }}
        }});
    }})();
    </script>
</body>
</html>"""


def simple_md_to_html(md_text):
    """Convert markdown to HTML (basic support for headers, lists, links, bold, etc.)."""
    lines = md_text.split('\n')
    html_lines = []
    in_list = False
    in_paragraph = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            continue
        
        # Headers
        if stripped.startswith('#### '):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            text = stripped[5:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            html_lines.append(f'<h4>{text}</h4>')
            continue
        if stripped.startswith('### '):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            text = stripped[4:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            html_lines.append(f'<h3>{text}</h3>')
            continue
        if stripped.startswith('## '):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            text = stripped[3:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            html_lines.append(f'<h2>{text}</h2>')
            continue
        if stripped.startswith('# '):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            text = stripped[2:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            html_lines.append(f'<h1>{text}</h1>')
            continue
        
        # Horizontal rule
        if stripped == '---' or stripped == '***':
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            html_lines.append('<hr>')
            continue
        
        # Blockquote
        if stripped.startswith('> '):
            if in_list: html_lines.append('</ul>'); in_list = False
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            text = stripped[2:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            html_lines.append(f'<blockquote><p>{text}</p></blockquote>')
            continue
        
        # Unordered list
        if stripped.startswith('- '):
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            text = stripped[2:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
            html_lines.append(f'<li>{text}</li>')
            continue
        
        # Regular paragraph
        if in_list:
            html_lines.append('</ul>')
            in_list = False
        if not in_paragraph:
            html_lines.append('<p>')
            in_paragraph = True
        
        text = stripped
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        html_lines.append(text)
    
    if in_list:
        html_lines.append('</ul>')
    if in_paragraph:
        html_lines.append('</p>')
    
    return '\n'.join(html_lines)


def generate_report_page(post, all_posts_count):
    """Generate an individual report HTML page from a post."""
    # Read the full markdown content
    md_file = POSTS_DIR / f"{post['date_prefix']}-{post['report_type']}.md"
    if not md_file.exists():
        return None
    
    md_text = md_file.read_text(encoding="utf-8", errors="replace")
    
    # Remove front matter
    md_text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", md_text, count=1, flags=re.DOTALL)
    
    # Convert markdown to HTML
    content_html = simple_md_to_html(md_text)
    
    type_labels = {"morning": "早报", "noon": "午报", "evening": "晚报", "weekly": "周报"}
    label = type_labels.get(post["report_type"], post["report_type"])
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - AI 资讯日报</title>
    <link rel="stylesheet" href="../../styles.css">
</head>
<body>
    <nav class="navbar">
        <a href="../../" class="logo">AI 资讯日报</a>
        <div class="nav-stats">
            <div><span class="stat-value">{all_posts_count}</span> reports</div>
            <div><span class="stat-value">35</span> sources</div>
            <div><span class="stat-value">24/7</span> monitoring</div>
        </div>
    </nav>
    
    <main class="container">
        <article class="report-content">
            <header class="report-header">
                <h1>{post['title']}</h1>
                <div class="meta">
                    <time>{post['date']}</time>
                    <span class="report-type type-{post['report_type']}">{label}</span>
                </div>
            </header>
            
            <div class="content">
                {content_html}
            </div>
        </article>
        
        <footer class="footer">
            <p><a href="../../">← 返回所有报告</a></p>
            <p>AI 资讯日报 — 由 Hermes Agent 自动采集、分析、生成</p>
        </footer>
    </main>
</body>
</html>"""


def main():
    dry_run = "--dry-run" in sys.argv
    
    if not POSTS_DIR.exists():
        print(f"Error: {POSTS_DIR} does not exist", file=sys.stderr)
        sys.exit(1)
    
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md")):
        post = parse_post(f)
        if post:
            posts.append(post)
    
    print(f"Found {len(posts)} posts", file=sys.stderr)
    
    total = len(posts)
    
    if dry_run:
        html = generate_html(posts)
        print(f"Would write {len(html)} bytes to {OUTPUT_FILE}")
        # Count report pages that would be generated
        missing = 0
        for p in posts:
            report_dir = WEBSITE_DIR / p["date_prefix"] / p["report_type"]
            report_file = report_dir / "index.html"
            if not report_file.exists():
                missing += 1
        print(f"Would generate {missing} missing report pages")
    else:
        # Generate index.html
        html = generate_html(posts)
        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print(f"✅ Generated index.html ({total} reports)")
        
        # Generate individual report pages
        generated = 0
        for p in posts:
            report_dir = WEBSITE_DIR / p["date_prefix"] / p["report_type"]
            report_file = report_dir / "index.html"
            
            # Always regenerate to keep style consistent
            report_html = generate_report_page(p, total)
            if report_html:
                report_dir.mkdir(parents=True, exist_ok=True)
                report_file.write_text(report_html, encoding="utf-8")
                generated += 1
        
        print(f"✅ Generated {generated} report pages")


if __name__ == "__main__":
    main()
