#!/usr/bin/env python3
"""
Future Intelligence 站点生成脚本
读取 pipeline/data/raw_articles.json，结合 index.html 模板生成更新后的网站。
"""

import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
DATA_FILE = os.path.join(BASE_DIR, "data", "raw_articles.json")
INDEX_FILE = os.path.join(REPO_ROOT, "index.html")


def load_articles():
    """加载抓取数据"""
    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在: {DATA_FILE}")
        print("请先运行 python fetch_all.py")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def generate_signal_html(data):
    """生成「原始信号」板块 HTML"""
    sources = data.get("sources", {})

    # 收集所有成功抓取的文章，按源组织
    articles_by_category = {}
    for src_id, src_data in sources.items():
        category = src_data.get("category", "其他")
        if category not in articles_by_category:
            articles_by_category[category] = []

        for article in src_data.get("articles", []):
            articles_by_category[category].append({
                "source_name": src_data["name"],
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "summary": article.get("summary", ""),
                "published": article.get("published", ""),
            })

    # 生成 HTML
    html_parts = []
    for category, articles in articles_by_category.items():
        if not articles:
            continue
        display_articles = articles[:10]

        items_html = ""
        for a in display_articles:
            title = escape_html(a["title"][:120])
            source = escape_html(a["source_name"])
            summary = escape_html((a.get("summary") or "")[:200])
            url = escape_html(a.get("url", "#"))

            items_html += f"""
            <div class="signal-item">
              <div class="signal-source">{source}</div>
              <div class="signal-title">{title}</div>
              <div class="signal-summary">{summary}</div>
              <a href="{url}" target="_blank" rel="noopener">阅读原文</a>
            </div>"""

        html_parts.append(f"""
          <div class="source-category">
            <h5>{escape_html(category)} ({len(display_articles)} 篇)</h5>
            {items_html}
          </div>""")

    return "\n".join(html_parts)


def escape_html(text):
    """HTML 转义"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def main():
    print("Future Intelligence 站点生成")
    print(f"数据文件: {DATA_FILE}")
    print(f"输出文件: {INDEX_FILE}")

    data = load_articles()
    print(f"  数据源总数: {data.get('source_count', 0)}")
    print(f"  成功抓取: {data.get('success_count', 0)}")
    print(f"  文章总数: {data.get('total_articles', 0)}")

    if not os.path.exists(INDEX_FILE):
        print(f"错误: index.html 不存在: {INDEX_FILE}")
        sys.exit(1)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # 生成原始信号板块 HTML
    signal_html = generate_signal_html(data)

    # 更新抓取时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = html.replace(
        '更新于 2026-06-28 凌晨',
        f'更新于 {now}'
    )

    # 查找插入位置：在「归档区」之前插入「原始信号」板块
    archive_marker = '<div class="archive-toggle"'
    if archive_marker in html:
        raw_signal_block = f"""
  <!-- ===== 原始信号板块（自动生成） ===== -->
  <div class="raw-signals-section">
    <h3 style="margin-bottom: 20px; font-size: 1.1em; color: var(--text-secondary); letter-spacing: 0.5px;">
      原始信号 · 最新抓取 ({data.get('total_articles', 0)} 条)
    </h3>
    <div class="sources-grid">
      {signal_html}
    </div>
  </div>

  <div class="archive-toggle"></div>"""

        # 用占位替换方式插入：先标记位置，再替换
        # 直接在 archive_marker 前插入
        html = html.replace(
            archive_marker,
            raw_signal_block.replace('<div class="archive-toggle"></div>', '')
            + '\n  '
            + archive_marker
        )

    # 更新时间戳
    html = html.replace(
        '更新于 2026-06-28 凌晨 · 基于过去24小时信号分析',
        f'更新于 {now} · 基于过去24小时信号分析 + 28 源实时抓取'
    )

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n已更新: {INDEX_FILE}")
    print("完成。")


if __name__ == "__main__":
    main()
