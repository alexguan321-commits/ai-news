#!/usr/bin/env python3
"""
Title utilities for AI News Website.

Shared module for title formatting and headline extraction.
Used by both generate_index.py and website_keeper.py to ensure consistency.
"""

import re
from pathlib import Path


def format_title(title: str) -> str:
    """
    Normalize report title to consistent format: MMDD-早报/午报/晚报 | ...
    
    Examples:
        "0705午报" -> "0705-午报"
        "0705 午报 | headline" -> "0705-午报 | headline"
        "AI 早报 - 2026-07-05" -> "0705-早报"
        "AI 午报 - 2026-07-05 | headline" -> "0705-午报 | headline"
    """
    # Pattern 1: "0705午报" or "0705 午报" or "0705-午报" (with optional suffix)
    m = re.match(r'^(\d{4})\s*[-]?\s*(早报|午报|晚报|周报)\s*\|?\s*(.*)$', title)
    if m:
        date_part = m.group(1)
        type_part = m.group(2)
        suffix = m.group(3).strip()
        if suffix:
            return f"{date_part}-{type_part} | {suffix}"
        else:
            return f"{date_part}-{type_part}"
    
    # Pattern 2: "AI 早报 - 2026-07-05" or similar
    m = re.match(r'^AI\s+(早报|午报|晚报|周报)\s*[-–—]\s*(\d{4}-\d{2}-\d{2})\s*\|?\s*(.*)$', title)
    if m:
        type_part = m.group(1)
        full_date = m.group(2)
        suffix = m.group(3).strip()
        # Extract MMDD from YYYY-MM-DD
        date_part = full_date[5:7] + full_date[8:10]
        if suffix:
            return f"{date_part}-{type_part} | {suffix}"
        else:
            return f"{date_part}-{type_part}"
    
    # No match, return original
    return title


def extract_headline(content: str, title: str) -> str:
    """
    Extract headline from content if title doesn't already have one.
    
    Priority:
    1. If title already contains '|', return as-is
    2. Try to extract from H1 title like "# 0707午报 | headline"
    3. Look for "**标题：** `MMDD早报 | headline`" pattern
    4. Fallback: look for "**今日头条：** headline" in content
    
    Args:
        content: Full markdown content of the report
        title: Base title (already formatted by format_title)
    
    Returns:
        Title with headline appended (if found), or original title
    """
    # If title already has headline, return as-is
    if '|' in title:
        return title
    
    # Try to extract from H1 title
    h1_match = re.search(r'^#\s+(.+?)(?:\n|$)', content, re.MULTILINE)
    if h1_match and '|' in h1_match.group(1):
        h1_title = h1_match.group(1).strip()
        parts = h1_title.split('|', 1)
        if len(parts) > 1:
            headline = parts[1].strip()
            # Limit headline length
            if len(headline) > 50:
                headline = headline[:47] + "..."
            return f"{title} | {headline}"
    
    # Look for "**标题：** `MMDD早报 | headline`" pattern
    title_match = re.search(r'\*\*标题[：:]\*\*\s*`([^`]+)`', content)
    if title_match:
        full_title = title_match.group(1).strip()
        if '|' in full_title:
            parts = full_title.split('|', 1)
            if len(parts) > 1:
                headline = parts[1].strip()
                # Limit headline length
                if len(headline) > 50:
                    headline = headline[:47] + "..."
                return f"{title} | {headline}"
    
    # Fallback: look for "今日头条" in content
    headline_match = re.search(r'\*\*今日头条[：:]\*\*\s*(.+?)(?:\n|$)', content)
    if headline_match:
        headline = headline_match.group(1).strip()
        # Limit headline length
        if len(headline) > 50:
            headline = headline[:47] + "..."
        return f"{title} | {headline}"
    
    return title


def get_display_title(filepath: Path) -> str:
    """
    Get the display title for a report file.
    
    This is the main entry point for getting a report's display title.
    It handles:
    1. Reading front matter
    2. Formatting the base title
    3. Extracting headline from content
    
    Args:
        filepath: Path to the markdown report file
    
    Returns:
        Formatted display title with headline (if available)
    """
    if not filepath.exists():
        return ""
    
    text = filepath.read_text(encoding="utf-8", errors="replace")
    
    # Parse front matter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not fm_match:
        return ""
    
    fm = fm_match.group(1)
    title_m = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    if not title_m:
        return ""
    
    # Format base title
    base_title = format_title(title_m.group(1).strip())
    
    # Extract headline from content
    display_title = extract_headline(text, base_title)
    
    return display_title


if __name__ == "__main__":
    # Test cases
    test_titles = [
        "0705午报",
        "0705 午报 | headline",
        "AI 早报 - 2026-07-05",
        "AI 午报 - 2026-07-05 | headline",
    ]
    
    print("Testing format_title():")
    for title in test_titles:
        result = format_title(title)
        print(f"  '{title}' -> '{result}'")
