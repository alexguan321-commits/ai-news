#!/usr/bin/env python3
"""Generate index.html from _posts/ directory and x-article knowledge cards.

Scans all markdown files in _posts/ and x-article/ and generates a static
index.html with search/filter support. Filters out personal/P&G content
for public sharing.

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
X_ARTICLE_DIR = Path.home() / "AI_News" / "raw" / "sources" / "x-article"
OUTPUT_FILE = WEBSITE_DIR / "index.html"
CARDS_DIR = WEBSITE_DIR / "cards"

# Supabase CDN scripts (injected into all pages)
SUPABASE_HEAD = """
    <!-- Supabase User System -->
    <link rel="stylesheet" href="/ai-news/assets/css/supabase.css?v=20260704f">
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="/ai-news/assets/js/supabase-config.js"></script>
    <script src="/ai-news/assets/js/supabase-auth.js?v=20260704" defer></script>
    <script src="/ai-news/assets/js/supabase-interactions.js?v=20260704" defer></script>
"""

def supabase_nav_auth():
    """Generate auth container HTML for navbar."""
    return '<div id="auth-container"></div>'

def interaction_bar(content_type, content_id):
    """Generate right sidebar for like/bookmark/comment."""
    return f"""
    <!-- Right Sidebar for Interactions -->
    <div class="interaction-sidebar">
        <div class="sidebar-toggle" onclick="toggleInteractionSidebar()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
        </div>
    </div>
    
    <!-- Expanded Panel -->
    <div class="interaction-panel" id="interaction-panel">
        <div class="panel-header">
            <h3>Interactions</h3>
            <button class="panel-close" onclick="toggleInteractionSidebar()">×</button>
        </div>
        <div class="panel-content">
            <div class="interaction-buttons">
                <button class="interaction-btn" id="like-btn" onclick="interactions.toggleLike()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                    <span id="like-count">0</span> Likes
                </button>
                <button class="interaction-btn" id="bookmark-btn" onclick="interactions.toggleBookmark()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
                    Bookmark
                </button>
            </div>
            
            <div class="comments-section">
                <h4>💬 Comments (<span id="comment-count">0</span>)</h4>
                <div class="comment-form">
                    <textarea id="comment-input" placeholder="Leave a comment..." maxlength="2000"></textarea>
                    <button onclick="interactions.submitComment()">Post Comment</button>
                </div>
                <div id="comments-list"></div>
            </div>
        </div>
    </div>
    
    <div class="interaction-overlay" id="interaction-overlay" onclick="toggleInteractionSidebar()"></div>

    <script>
        function toggleInteractionSidebar() {{
            const panel = document.getElementById('interaction-panel');
            const overlay = document.getElementById('interaction-overlay');
            panel.classList.toggle('active');
            overlay.classList.toggle('active');
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            interactions.init('{content_type}', '{content_id}');
            interactions.loadComments();
        }});
    </script>
"""

# Content filter patterns — strip personal/P&G sections for public sharing
FILTER_PATTERNS = [
    r"对\s*A\s*哥.*",           # "对 A 哥意味着什么"
    r"对A哥.*",
    r"宝洁.*",
    r"P&G.*",
    r"Procter.*Gamble.*",
    r"\bFDE\b.*",
    r"Frank\s*Shen.*",
    r"A\s*哥.*",
]

# Section-level filters — remove entire sections
SECTION_FILTER_HEADERS = [
    r"#+\s*.*FDE\s*启示.*",
    r"#+\s*.*对\s*A\s*哥.*",
    r"#+\s*.*对A哥.*",
    r"#+\s*.*对宝洁.*",
    r"#+\s*.*宝洁.*启示.*",
]


def should_filter_content():
    """Whether to apply content filtering (always True for public site)."""
    return True


def filter_report_content(text):
    """Remove personal/P&G content from report text."""
    if not should_filter_content():
        return text

    lines = text.split('\n')
    filtered_lines = []
    skip_section = False
    skip_level = 0

    for line in lines:
        # Check if this line starts a section that should be filtered
        is_section_header = False
        for pattern in SECTION_FILTER_HEADERS:
            if re.search(pattern, line):
                is_section_header = True
                skip_section = True
                # Determine header level
                match = re.match(r'^(#+)', line)
                skip_level = len(match.group(1)) if match else 1
                break

        if is_section_header:
            continue

        # Check if we've exited the filtered section
        if skip_section:
            # A new section at same or higher level ends the skip
            header_match = re.match(r'^(#+)\s', line)
            if header_match and len(header_match.group(1)) <= skip_level:
                skip_section = False
            else:
                continue

        # Filter individual lines matching patterns
        should_skip = False
        for pattern in FILTER_PATTERNS:
            if re.search(pattern, line):
                should_skip = True
                break

        if not should_skip:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


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
    cover_m = re.search(r'^cover_image:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    categories_m = re.search(r'^categories:\s*\[([^\]]+)\]', fm, re.MULTILINE)

    if not title_m or not date_m:
        return None

    title = title_m.group(1).strip()
    date_str = date_m.group(1).strip()
    
    # Get report_type from front matter, or infer from categories/title/filename
    if type_m:
        report_type = type_m.group(1).strip()
    else:
        report_type = None
        
        # Try to infer from categories like [ai-news, evening]
        if categories_m:
            cats = [c.strip().strip('"').strip("'") for c in categories_m.group(1).split(',')]
            for cat in cats:
                if cat in ['morning', 'noon', 'evening', 'weekly']:
                    report_type = cat
                    break
        
        # Try to infer from title (Chinese names)
        if not report_type:
            if '早报' in title or 'Morning' in title:
                report_type = 'morning'
            elif '午报' in title or 'Noon' in title:
                report_type = 'noon'
            elif '晚报' in title or 'Evening' in title:
                report_type = 'evening'
            elif '周报' in title or 'Weekly' in title:
                report_type = 'weekly'
        
        # Infer from filename like 2026-06-27-evening.md
        if not report_type:
            fname = filepath.stem
            parts = fname.split('-')
            if len(parts) >= 4:
                report_type = parts[3]  # evening, morning, noon, weekly
            else:
                report_type = "morning"
    
    cover_image = cover_m.group(1).strip() if cover_m else None

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
        "cover_image": cover_image,
    }


def parse_knowledge_card(filepath):
    """Extract metadata from an x-article knowledge card."""
    text = filepath.read_text(encoding="utf-8", errors="replace")

    # Parse metadata from markdown header
    title = ""
    author = ""
    source = ""
    date = ""
    tags = []

    # First, try to parse YAML front matter
    if text.startswith('---'):
        fm_end = text.find('---', 3)
        if fm_end != -1:
            front_matter = text[3:fm_end]
            for line in front_matter.split('\n'):
                if line.startswith('title:'):
                    title = line[6:].strip().strip('"\'')
                elif line.startswith('author:'):
                    author = line[7:].strip().strip('"\'')
                elif line.startswith('source:'):
                    source = line[7:].strip().strip('"\'')
                elif line.startswith('date:'):
                    date = line[5:].strip().strip('"\'')
                elif line.startswith('tags:'):
                    tags_str = line[5:].strip()
                    # Parse YAML list format: [tag1, tag2] or [tag1,tag2]
                    if tags_str.startswith('[') and tags_str.endswith(']'):
                        tags_str = tags_str[1:-1]
                        tags = [t.strip().strip('"\'') for t in tags_str.split(',') if t.strip()]

    # Fallback: parse markdown header (old format)
    if not title:
        for line in text.split('\n')[:20]:
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('**Author:**'):
                author = line.replace('**Author:**', '').strip()
            elif line.startswith('**Source:**'):
                source = line.replace('**Source:**', '').strip()
            elif line.startswith('**Date:**'):
                date = line.replace('**Date:**', '').strip()
            elif line.startswith('**Tags:**'):
                tags_str = line.replace('**Tags:**', '').strip()
                tags = [t.strip() for t in tags_str.split(',')]

    if not title:
        title = filepath.stem

    # Extract date from filename
    fname = filepath.stem  # e.g. "2026-06-28-loop-harness-engineering"
    date_prefix = fname[:10] if len(fname) >= 10 else ""

    # Build URL — strip all extensions (.md.processed -> slug without .md)
    slug = filepath.name
    for ext in ['.processed', '.md']:
        if slug.endswith(ext):
            slug = slug[:-len(ext)]
    url = f"/ai-news/cards/{slug}/"

    # Extract summary (first paragraph after metadata)
    summary = ""
    in_content = False
    for line in text.split('\n'):
        if line.startswith('---') and in_content:
            break
        if line.startswith('# '):
            in_content = True
            continue
        if in_content and line.strip() and not line.startswith('**') and not line.startswith('-'):
            summary = line.strip()[:200]
            break

    return {
        "title": title,
        "author": author,
        "source": source,
        "date": date,
        "date_prefix": date_prefix,
        "tags": tags,
        "url": url,
        "slug": slug,
        "summary": summary,
        "filepath": filepath,
    }


def simple_md_to_html(md_text):
    """Convert markdown to HTML (basic support for headers, lists, links, bold, etc.)."""
    lines = md_text.split('\n')
    html_lines = []
    in_list = False
    in_paragraph = False
    in_code_block = False
    code_lang = ""

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if in_paragraph:
                    html_lines.append('</p>')
                    in_paragraph = False
                code_lang = stripped[3:]
                html_lines.append(f'<pre><code class="language-{code_lang}">')
                in_code_block = True
            continue

        if in_code_block:
            # Escape HTML in code blocks
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(escaped)
            continue

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
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
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
            text = re.sub(r'(?<!["\(])(https?://[^\s<>"\']+)', r'<a href="\1">\1</a>', text)
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
            text = re.sub(r'(?<!["\(])(https?://[^\s<>"\']+)', r'<a href="\1">\1</a>', text)
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
        # Auto-link bare URLs (not already in href="" or <tag>)
        text = re.sub(r'(?<!["\(])(https?://[^\s<>"\']+)', r'<a href="\1">\1</a>', text)
        html_lines.append(text)

    if in_list:
        html_lines.append('</ul>')
    if in_paragraph:
        html_lines.append('</p>')
    if in_code_block:
        html_lines.append('</code></pre>')

    return '\n'.join(html_lines)


def generate_report_page(post, all_posts_count, filtered_content=None):
    """Generate an individual report HTML page from a post."""
    # Read the full markdown content
    md_file = POSTS_DIR / f"{post['date_prefix']}-{post['report_type']}.md"
    if not md_file.exists():
        return None

    md_text = md_file.read_text(encoding="utf-8", errors="replace")

    # Remove front matter
    md_text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", md_text, count=1, flags=re.DOTALL)

    # Apply content filtering
    if should_filter_content():
        md_text = filter_report_content(md_text)

    # Convert markdown to HTML
    content_html = simple_md_to_html(md_text)

    type_labels = {"morning": "早报", "noon": "午报", "evening": "晚报", "weekly": "周报"}
    label = type_labels.get(post["report_type"], post["report_type"])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - Alex Guan's AI Knowledge Base</title>
    <link rel="stylesheet" href="../../styles.css">
    {SUPABASE_HEAD}
</head>
<body>
    <nav class="navbar">
        <a href="../../" class="logo">Alex Guan's AI Knowledge Base</a>
        <div class="nav-stats">
            <div><span class="stat-value">{all_posts_count}</span> reports</div>
            <div><span class="stat-value">35</span> sources</div>
            <div><span class="stat-value">24/7</span> monitoring</div>
        </div>
        {supabase_nav_auth()}
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

            {f'<div class="cover-image"><img src="/ai-news{post["cover_image"]}" alt="Cover"></div>' if post.get('cover_image') else ''}

            <div class="content">
                {content_html}
            </div>
        </article>

        {interaction_bar('report', post['date_prefix'] + '-' + post['report_type'])}

        <footer class="footer">
            <p><a href="../../">← Back to All Reports</a></p>
            <p>Alex Guan's AI Knowledge Base — 由 Hermes Agent 自动采集、分析、生成</p>
        </footer>
    </main>
</body>
</html>"""


def generate_card_page(card, total_cards):
    """Generate an individual knowledge card HTML page."""
    md_text = card["filepath"].read_text(encoding="utf-8", errors="replace")

    # Convert markdown to HTML
    content_html = simple_md_to_html(md_text)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{card['title']} - Knowledge Card</title>
    <link rel="stylesheet" href="../../styles.css">
    {SUPABASE_HEAD}
</head>
<body>
    <nav class="navbar">
        <a href="../../" class="logo">Alex Guan's AI Knowledge Base</a>
        <div class="nav-stats">
            <div><span class="stat-value">{total_cards}</span> cards</div>
            <div><span class="stat-value">X</span> curated</div>
        </div>
        {supabase_nav_auth()}
    </nav>

    <main class="container">
        <article class="card-content">
            <header class="card-header">
                <span class="card-badge">Knowledge Card</span>
                <h1>{card['title']}</h1>
                <div class="meta">
                    <span class="author">{card['author']}</span>
                    <time>{card['date']}</time>
                    {" | ".join(f'<span class="tag">{t}</span>' for t in card['tags'])}
                </div>
                {"<p><a href='" + card['source'] + "' target='_blank'>Original ↗</a></p>" if card['source'] else ""}
            </header>

            <div class="content">
                {content_html}
            </div>
        </article>

        {interaction_bar('card', card['slug'])}

        <footer class="footer">
            <p><a href="../../">← Back to Home</a></p>
            <p>Alex Guan's AI Knowledge Base — Knowledge Card</p>
        </footer>
    </main>
</body>
</html>"""


def generate_html(posts, cards):
    """Generate the full index.html content."""
    # Sort posts by date descending
    posts.sort(key=lambda p: p["date"], reverse=True)
    cards.sort(key=lambda c: c["date_prefix"], reverse=True)

    total_posts = len(posts)
    total_cards = len(cards)
    latest = posts[:6]
    latest_cards = cards[:8]

    type_labels = {"morning": "Morning", "noon": "Noon", "evening": "Evening"}

    def render_card(p):
        label = type_labels.get(p["report_type"], p["report_type"])
        emoji = "🌅" if p["report_type"] == "morning" else "☀️" if p["report_type"] == "noon" else "🌙"
        
        # Use cover image if available, otherwise fall back to emoji
        if p.get("cover_image"):
            # Fix path for GitHub Pages subdirectory
            cover_src = p["cover_image"]
            if cover_src.startswith("/"):
                cover_src = "/ai-news" + cover_src
            card_image = f'<img src="{cover_src}" alt="{p["title"]}" loading="lazy">'
        else:
            card_image = emoji
        
        return f"""        <article class="report-card">
            <a href="{p['url']}">
                <div class="card-image">{card_image}</div>
                <div class="card-content">
                    <h3>{p['title']}</h3>
                    <time>{p['date']}</time>
                    <span class="report-type type-{p['report_type']}">{label}</span>
                </div>
            </a>
        </article>"""

    def render_knowledge_card(c):
        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in c['tags'][:3])
        return f"""        <article class="knowledge-card">
            <a href="{c['url']}">
                <div class="kc-header">
                    <span class="kc-badge">📚 Knowledge Card</span>
                    <time>{c['date_prefix']}</time>
                </div>
                <h3>{c['title']}</h3>
                <p class="kc-summary">{c['summary']}</p>
                <div class="kc-footer">
                    <span class="kc-author">{c['author']}</span>
                    <div class="kc-tags">{tags_html}</div>
                </div>
            </a>
        </article>"""

    def render_archive(p):
        label = type_labels.get(p["report_type"], p["report_type"])
        return f"""        <div class="archive-item" data-type="{p['report_type']}">
            <a href="{p['url']}">{p['title']}</a>
            <time>{p['date']}</time>
            <span class="report-type type-{p['report_type']}">{label}</span>
        </div>"""

    def render_card_archive(c):
        return f"""        <div class="archive-item" data-type="card">
            <a href="{c['url']}">{c['title']}</a>
            <time>{c['date_prefix']}</time>
            <span class="report-type type-card">📚 Card</span>
        </div>"""

    cards_html = "\n".join(render_card(p) for p in latest)
    knowledge_cards_html = "\n".join(render_knowledge_card(c) for c in latest_cards)
    
    # Archive: show first 20, collapse the rest
    archive_visible = "\n".join(render_archive(p) for p in posts[:20])
    archive_hidden = "\n".join(render_archive(p) for p in posts[20:])
    archive_items = archive_visible
    if archive_hidden:
        archive_items += f"""
                    </div>
                    <div class="archive-hidden" id="archive-hidden" style="display:none;">
{archive_hidden}
                    </div>
                    <button class="show-all-btn" id="show-all-btn" onclick="toggleArchive()">
                        <span class="show-text">Show All ({total_posts})</span>
                        <span class="hide-text" style="display:none;">Show Less</span>
                    </button>
                    <div class="report-archive" style="display:none;">
"""
    
    card_archive_items = "\n".join(render_card_archive(c) for c in cards)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#ffffff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <title>Alex Guan's AI Knowledge Base</title>
    <link rel="stylesheet" href="styles.css">
    {SUPABASE_HEAD}
</head>
<body>
    <nav class="navbar">
        <a href="/ai-news/" class="logo">Alex Guan's AI Knowledge Base</a>
        <div class="nav-stats">
            <div><span class="stat-value">{total_posts}</span> reports</div>
            <div><span class="stat-value">{total_cards}</span> cards</div>
            <div><span class="stat-value">35</span> sources</div>
        </div>
        {supabase_nav_auth()}
    </nav>

    <main class="container">
        <section class="hero">
            <h1>Alex Guan's AI Knowledge Base</h1>
            <p>Daily AI industry insights · Curated knowledge cards · Auto-collected and analyzed by AI</p>
        </section>

        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-number">{total_posts}</div>
                <div class="stat-label">Reports</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_cards}</div>
                <div class="stat-label">Knowledge Cards</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">35+</div>
                <div class="stat-label">Data Sources</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Auto Collection</div>
            </div>
        </div>

        <section class="search-section">
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="Search..." autocomplete="off">
                <span id="searchCount" class="search-count"></span>
            </div>
        </section>

        <div class="tab-container">
            <div class="tab-nav">
                <button class="tab-btn active" data-tab="reports">📰 Reports ({total_posts})</button>
                <button class="tab-btn" data-tab="cards">📚 Knowledge Cards ({total_cards})</button>
            </div>

            <div class="tab-content active" id="reports-tab">
                <div class="filter-tags">
                    <button class="filter-tag active" data-filter="all">All</button>
                    <button class="filter-tag" data-filter="morning">Morning</button>
                    <button class="filter-tag" data-filter="noon">Noon</button>
                    <button class="filter-tag" data-filter="evening">Evening</button>
                </div>

                <section class="reports-list">
                    <div class="section-header">
                        <h2>Latest Reports</h2>
                        <span class="count">{min(6, total_posts)} most recent</span>
                    </div>
                    <div class="report-grid">
{cards_html}
                    </div>
                </section>

                <section class="all-reports">
                    <div class="section-header">
                        <h2>Archive</h2>
                        <span class="count">{total_posts} reports</span>
                    </div>
                    <div class="report-archive">
{archive_items}
                    </div>
                </section>
            </div>

            <div class="tab-content" id="cards-tab">
                <section class="knowledge-cards-section">
                    <div class="section-header">
                        <h2>Featured Knowledge Cards</h2>
                        <span class="count">{min(8, total_cards)} of {total_cards} cards</span>
                    </div>
                    <div class="knowledge-cards-grid">
{knowledge_cards_html}
                    </div>
                </section>

                <section class="all-cards">
                    <div class="section-header">
                        <h2>All Cards</h2>
                        <span class="count">{total_cards} cards</span>
                    </div>
                    <div class="report-archive">
{card_archive_items}
                    </div>
                </section>
            </div>
        </div>
    </main>

    <footer class="footer">
        <p>Alex Guan's AI Knowledge Base — 由 Hermes Agent 自动采集、分析、生成</p>
        <p class="footer-brand">COLLECTOR V3 · PIPELINE ARCHITECTURE · {total_posts} REPORTS · {total_cards} CARDS</p>
    </footer>

    <script>
    // Toggle archive visibility
    function toggleArchive() {{
        const hidden = document.getElementById('archive-hidden');
        const btn = document.getElementById('show-all-btn');
        const showText = btn.querySelector('.show-text');
        const hideText = btn.querySelector('.hide-text');
        
        if (hidden.style.display === 'none') {{
            hidden.style.display = 'block';
            showText.style.display = 'none';
            hideText.style.display = 'inline';
        }} else {{
            hidden.style.display = 'none';
            showText.style.display = 'inline';
            hideText.style.display = 'none';
        }}
    }}
    
    (function() {{
        const searchInput = document.getElementById('searchInput');
        const searchCount = document.getElementById('searchCount');
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        const filterTags = document.querySelectorAll('.filter-tag');
        let activeTab = 'reports';
        let activeFilter = 'all';

        // Tab switching
        function switchTab(tabName) {{
            activeTab = tabName;
            tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabName));
            tabContents.forEach(content => {{
                content.classList.toggle('active', content.id === tabName + '-tab');
            }});
            // Reset filter when switching tabs
            activeFilter = 'all';
            filterTags.forEach(t => t.classList.toggle('active', t.dataset.filter === 'all'));
            filterContent();
        }}

        tabBtns.forEach(btn => {{
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        }});

        // Filter within active tab
        function filterContent() {{
            const query = searchInput.value.toLowerCase().trim();
            let visibleCount = 0;

            if (activeTab === 'reports') {{
                const reportCards = document.querySelectorAll('#reports-tab .report-card');
                const archiveItems = document.querySelectorAll('#reports-tab .archive-item');

                reportCards.forEach(card => {{
                    const text = card.textContent.toLowerCase();
                    const type = card.querySelector('.report-type');
                    const typeClass = type ? type.className : '';
                    const matchesSearch = !query || text.includes(query);
                    const matchesFilter = activeFilter === 'all' || typeClass.includes('type-' + activeFilter);
                    card.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
                    if (card.style.display !== 'none') visibleCount++;
                }});

                archiveItems.forEach(item => {{
                    const text = item.textContent.toLowerCase();
                    const type = item.dataset.type || '';
                    const matchesSearch = !query || text.includes(query);
                    const matchesFilter = activeFilter === 'all' || type === activeFilter;
                    item.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
                }});
            }} else {{
                const knowledgeCards = document.querySelectorAll('#cards-tab .knowledge-card');
                const cardArchiveItems = document.querySelectorAll('#cards-tab .archive-item');

                knowledgeCards.forEach(card => {{
                    const text = card.textContent.toLowerCase();
                    const matchesSearch = !query || text.includes(query);
                    card.style.display = matchesSearch ? '' : 'none';
                    if (card.style.display !== 'none') visibleCount++;
                }});

                cardArchiveItems.forEach(item => {{
                    const text = item.textContent.toLowerCase();
                    const matchesSearch = !query || text.includes(query);
                    item.style.display = matchesSearch ? '' : 'none';
                }});
            }}

            if (query || activeFilter !== 'all') {{
                searchCount.textContent = visibleCount + ' 条结果';
            }} else {{
                searchCount.textContent = '';
            }}
        }}

        searchInput.addEventListener('input', filterContent);
        filterTags.forEach(tag => {{
            tag.addEventListener('click', function() {{
                filterTags.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                activeFilter = this.dataset.filter;
                filterContent();
            }});
        }});

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.key === '/' && document.activeElement !== searchInput) {{
                e.preventDefault();
                searchInput.focus();
            }}
            if (e.key === 'Escape') {{
                searchInput.value = '';
                searchInput.blur();
                filterContent();
            }}
        }});
    }})();
    </script>
</body>
</html>"""


def main():
    dry_run = "--dry-run" in sys.argv

    if not POSTS_DIR.exists():
        print(f"Error: {POSTS_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    # Parse posts
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md")):
        post = parse_post(f)
        if post:
            posts.append(post)

    # Parse knowledge cards (support both .md and .md.processed files)
    cards = []
    if X_ARTICLE_DIR.exists():
        for f in sorted(X_ARTICLE_DIR.glob("*.md*")):
            if f.name.endswith('.processed'):
                # Strip .processed suffix for parsing
                card = parse_knowledge_card(f)
                if card:
                    cards.append(card)
            elif f.suffix == '.md':
                card = parse_knowledge_card(f)
                if card:
                    cards.append(card)

    print(f"Found {len(posts)} posts, {len(cards)} knowledge cards", file=sys.stderr)

    total_posts = len(posts)
    total_cards = len(cards)

    if dry_run:
        html = generate_html(posts, cards)
        print(f"Would write {len(html)} bytes to {OUTPUT_FILE}")
        # Count report pages that would be generated
        missing = 0
        for p in posts:
            report_dir = WEBSITE_DIR / p["date_prefix"] / p["report_type"]
            report_file = report_dir / "index.html"
            if not report_file.exists():
                missing += 1
        print(f"Would generate {missing} missing report pages")
        print(f"Would generate {total_cards} knowledge card pages")
    else:
        # Generate index.html
        html = generate_html(posts, cards)
        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print(f"✅ Generated index.html ({total_posts} reports, {total_cards} cards)")

        # Generate individual report pages
        generated = 0
        for p in posts:
            report_dir = WEBSITE_DIR / p["date_prefix"] / p["report_type"]
            report_file = report_dir / "index.html"

            report_html = generate_report_page(p, total_posts)
            if report_html:
                report_dir.mkdir(parents=True, exist_ok=True)
                report_file.write_text(report_html, encoding="utf-8")
                generated += 1

        print(f"✅ Generated {generated} report pages")

        # Generate knowledge card pages
        cards_generated = 0
        for c in cards:
            card_dir = CARDS_DIR / c["slug"]
            card_file = card_dir / "index.html"

            card_html = generate_card_page(c, total_cards)
            if card_html:
                card_dir.mkdir(parents=True, exist_ok=True)
                card_file.write_text(card_html, encoding="utf-8")
                cards_generated += 1

        print(f"✅ Generated {cards_generated} knowledge card pages")


if __name__ == "__main__":
    main()
