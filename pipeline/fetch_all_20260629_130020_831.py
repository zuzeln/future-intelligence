#!/usr/bin/env python3
"""数据抓取脚本：从 28 个指定源抓取最新 AI 相关内容，输出 raw_articles.json"""

import json
import sys
import os
import time
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

# 尝试导入可选依赖
try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system(f"{sys.executable} -m pip install beautifulsoup4 -q")
    from bs4 import BeautifulSoup

try:
    import feedparser
except ImportError:
    os.system(f"{sys.executable} -m pip install feedparser -q")
    import feedparser

# ==================== 配置 ====================
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA}
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "raw_articles.json")
BEIJING_TZ = timezone(timedelta(hours=8))

# 28 个数据源
SOURCES = {
    "AI公司": [
        {"name": "OpenAI News", "url": "https://openai.com/news/", "type": "web"},
        {"name": "Anthropic News", "url": "https://www.anthropic.com/news", "type": "web"},
        {"name": "Google DeepMind Blog", "url": "https://deepmind.google/discover/blog/", "type": "web"},
        {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/", "type": "web"},
        {"name": "Microsoft AI", "url": "https://www.microsoft.com/en-us/ai", "type": "web"},
        {"name": "NVIDIA AI", "url": "https://www.nvidia.com/en-us/ai-data-science/", "type": "web"},
        {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog", "type": "rss", "rss": "https://huggingface.co/blog/feed.xml"},
    ],
    "AI媒体": [
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/", "type": "rss", "rss": "https://techcrunch.com/category/artificial-intelligence/feed/"},
        {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/", "type": "rss", "rss": "https://venturebeat.com/category/ai/feed/"},
        {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence", "type": "rss", "rss": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
        {"name": "Ars Technica", "url": "https://arstechnica.com/information-technology/", "type": "rss", "rss": "https://feeds.arstechnica.com/arstechnica/ai"},
        {"name": "MarkTechPost", "url": "https://www.marktechpost.com/", "type": "rss", "rss": "https://www.marktechpost.com/feed/"},
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/", "type": "rss", "rss": "https://www.artificialintelligence-news.com/feed/"},
        {"name": "The Decoder", "url": "https://the-decoder.com/", "type": "rss", "rss": "https://the-decoder.com/feed/"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/", "type": "rss", "rss": "https://www.technologyreview.com/feed/"},
    ],
    "研究机构": [
        {"name": "arXiv cs.AI", "url": "https://arxiv.org/list/cs.AI/recent", "type": "rss", "rss": "https://rss.arxiv.org/rss/cs.AI"},
        {"name": "Stanford HAI", "url": "https://hai.stanford.edu/news", "type": "web"},
        {"name": "Google Research Blog", "url": "https://research.google/blog/", "type": "rss", "rss": "https://research.google/blog/rss/"},
        {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/blog/", "type": "rss", "rss": "https://www.microsoft.com/en-us/research/blog/feed/"},
    ],
    "投资机构": [
        {"name": "a16z", "url": "https://a16z.com/", "type": "web"},
        {"name": "Sequoia Capital", "url": "https://www.sequoiacap.com/", "type": "web"},
        {"name": "Benchmark", "url": "https://www.benchmark.com/", "type": "web"},
        {"name": "Y Combinator", "url": "https://www.ycombinator.com/blog/", "type": "rss", "rss": "https://www.ycombinator.com/blog/feed/"},
    ],
    "社区信号": [
        {"name": "Hacker News", "url": "https://news.ycombinator.com/", "type": "rss", "rss": "https://hnrss.org/frontpage?count=20"},
        {"name": "GitHub Trending", "url": "https://github.com/trending", "type": "web"},
        {"name": "Reddit ML", "url": "https://www.reddit.com/r/MachineLearning/", "type": "api", "api": "https://www.reddit.com/r/MachineLearning/hot.json?limit=15"},
        {"name": "Reddit LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA/", "type": "api", "api": "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=15"},
        {"name": "Product Hunt", "url": "https://www.producthunt.com/", "type": "web"},
        {"name": "AI HOT", "url": "https://aihot.virxact.com", "type": "aihot_api"},
    ],
}

def fetch_aihot():
    """从 AI HOT API 拉取最新条目"""
    articles = []
    try:
        # 尝试最近 7 天精选
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = f"https://aihot.virxact.com/api/public/items?mode=selected&since={since}&take=100"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("items", []):
                published = item.get("publishedAt", "")
                if published:
                    try:
                        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        published = dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                articles.append({
                    "title": item.get("title", ""),
                    "title_en": item.get("title_en", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "source": f"AI HOT · {item.get('source', '')}",
                    "category": item.get("category", ""),
                    "published": published,
                    "id": item.get("id", ""),
                })
    except Exception as e:
        print(f"  AI HOT 错误: {e}")
    return articles

def fetch_rss(source):
    """从 RSS/Atom feed 抓取"""
    articles = []
    try:
        feed = feedparser.parse(source["rss"])
        for entry in feed.entries[:10]:  # 最多 10 条
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                published = dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
            
            articles.append({
                "title": entry.get("title", "")[:200],
                "summary": (entry.get("summary", "") or entry.get("description", ""))[:500],
                "url": entry.get("link", ""),
                "source": source["name"],
                "category": source.get("_category", "industry"),
                "published": published,
            })
    except Exception as e:
        print(f"  RSS {source['name']}: {e}")
    return articles

def fetch_web(source):
    """从网页抓取（标题 + 链接）"""
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  Web {source['name']}: HTTP {resp.status_code}")
            return articles
        
        soup = BeautifulSoup(resp.text, "html.parser")
        # 通用提取：找文章链接
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if len(text) > 10 and len(text) < 200:
                # 构建完整 URL
                if href.startswith("/"):
                    parsed = urlparse(source["url"])
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif not href.startswith("http"):
                    continue
                links.append((text, href))
        
        # 去重 + 限 8 条
        seen = set()
        for title, url in links:
            if url in seen or len(articles) >= 8:
                continue
            seen.add(url)
            articles.append({
                "title": title,
                "summary": "",
                "url": url,
                "source": source["name"],
                "category": source.get("_category", "industry"),
                "published": datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        print(f"  Web {source['name']}: {e}")
    return articles

def fetch_reddit(source):
    """从 Reddit JSON API 抓取"""
    articles = []
    try:
        headers = {**HEADERS, "Accept": "application/json"}
        resp = requests.get(source["api"], headers=headers, timeout=15)
        if resp.status_code == 403:
            print(f"  Reddit {source['name']}: 403 反爬（跳过）")
            return articles
        if resp.status_code != 200:
            print(f"  Reddit {source['name']}: HTTP {resp.status_code}")
            return articles
        data = resp.json()
        for post in data.get("data", {}).get("children", [])[:10]:
            p = post["data"]
            created = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc)
            articles.append({
                "title": p.get("title", "")[:200],
                "summary": p.get("selftext", "")[:500],
                "url": f"https://www.reddit.com{p.get('permalink', '')}",
                "source": source["name"],
                "category": "community",
                "published": created.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        print(f"  Reddit {source['name']}: {e}")
    return articles

def main():
    all_articles = []
    stats = {}
    
    # 特殊处理：aihot 先跑（数据最全）
    print("📡 抓取 AI HOT API...")
    aihot_articles = fetch_aihot()
    all_articles.extend(aihot_articles)
    stats["AI HOT"] = len(aihot_articles)
    print(f"  → {len(aihot_articles)} 条")
    
    # 遍历其他源
    for category, sources in SOURCES.items():
        if category in ["社区信号"]:  # aihot 已处理
            continue
        for source in sources:
            if source["name"] == "AI HOT":
                continue
            source["_category"] = {
                "AI公司": "ai-models",
                "AI媒体": "industry",
                "研究机构": "paper",
                "投资机构": "industry",
                "社区信号": "community",
            }.get(category, "industry")
            
            print(f"📡 {source['name']} ({source['type']})...")
            time.sleep(1 + (hash(source['name']) % 3))  # 随机延迟 1-3 秒
            
            if source["type"] == "rss":
                articles = fetch_rss(source)
            elif source["type"] == "web":
                articles = fetch_web(source)
            elif source["type"] == "api":
                articles = fetch_reddit(source)
            else:
                continue
            
            all_articles.extend(articles)
            stats[source["name"]] = len(articles)
            print(f"  → {len(articles)} 条")
    
    # 去重（按 URL）
    seen_urls = set()
    unique_articles = []
    for a in all_articles:
        url = a.get("url", "")
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        unique_articles.append(a)
    
    # 保存
    output = {
        "fetched_at": datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "total_raw": len(all_articles),
        "total_unique": len(unique_articles),
        "stats": stats,
        "articles": unique_articles,
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 抓取完成：原始 {len(all_articles)} 条 → 去重 {len(unique_articles)} 条")
    print(f"📁 输出: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
