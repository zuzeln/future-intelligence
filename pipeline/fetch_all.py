#!/usr/bin/env python3
"""
Future Intelligence 数据抓取管线
从 28 个信息源批量抓取最新文章标题、链接、摘要、发布时间。
输出: pipeline/data/raw_articles.json
"""

import json
import time
import random
import sys
import os
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    import feedparser
except ImportError:
    feedparser = None

# 工作目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(DATA_DIR, "raw_articles.json")

# 请求配置
REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}

# ========== 28 个数据源定义 ==========
SOURCES = [
    # --- AI 公司（7）---
    {
        "id": "openai",
        "name": "OpenAI Blog",
        "category": "AI 公司",
        "type": "rss",
        "url": "https://openai.com/blog/rss.xml",
    },
    {
        "id": "deepmind",
        "name": "Google DeepMind",
        "category": "AI 公司",
        "type": "rss",
        "url": "https://deepmind.google/discover/blog/feed/",
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "category": "AI 公司",
        "type": "html",
        "url": "https://www.anthropic.com/research",
        "article_selector": "a[href*='/research/']",
    },
    {
        "id": "meta_ai",
        "name": "Meta AI",
        "category": "AI 公司",
        "type": "rss",
        "url": "https://ai.meta.com/blog/feed/",
    },
    {
        "id": "stability_ai",
        "name": "Stability AI",
        "category": "AI 公司",
        "type": "html",
        "url": "https://stability.ai/news",
        "article_selector": "a[href*='/news/']",
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "category": "AI 公司",
        "type": "rss",
        "url": "https://mistral.ai/news/feed.xml",
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "category": "AI 公司",
        "type": "rss",
        "url": "https://cohere.com/blog/rss",
    },
    # --- AI 媒体（8）---
    {
        "id": "techcrunch_ai",
        "name": "TechCrunch AI",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "id": "venturebeat_ai",
        "name": "VentureBeat AI",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "id": "theverge_ai",
        "name": "The Verge AI",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    },
    {
        "id": "arstechnica_ai",
        "name": "Ars Technica AI",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/ai",
    },
    {
        "id": "marktechpost",
        "name": "MarkTechPost",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://www.marktechpost.com/feed/",
    },
    {
        "id": "ai_news",
        "name": "AI News",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://www.artificialintelligence-news.com/feed/",
    },
    {
        "id": "the_decoder",
        "name": "The Decoder",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://the-decoder.com/feed/",
    },
    {
        "id": "mit_tech_review",
        "name": "MIT Tech Review AI",
        "category": "AI 媒体",
        "type": "rss",
        "url": "https://www.technologyreview.com/feed/",
    },
    # --- 聚合平台（1）---
    {
        "id": "ai_hot",
        "name": "AI HOT",
        "category": "聚合平台",
        "type": "api",
        "url": "https://aihot.virxact.com/api/public/items?mode=selected&since=24h",
    },
    # --- 研究机构（4）---
    {
        "id": "arxiv_ai",
        "name": "arXiv AI",
        "category": "研究机构",
        "type": "api",
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&max_results=10",
    },
    {
        "id": "stanford_hai",
        "name": "Stanford HAI",
        "category": "研究机构",
        "type": "rss",
        "url": "https://hai.stanford.edu/news/rss.xml",
    },
    {
        "id": "bair",
        "name": "BAIR Blog",
        "category": "研究机构",
        "type": "rss",
        "url": "https://bair.berkeley.edu/blog/feed.xml",
    },
    {
        "id": "cmu_ai",
        "name": "CMU AI News",
        "category": "研究机构",
        "type": "html",
        "url": "https://www.cs.cmu.edu/news",
        "article_selector": "a[href*='/news/']",
    },
    # --- 投资机构（4）---
    {
        "id": "a16z",
        "name": "a16z AI",
        "category": "投资机构",
        "type": "rss",
        "url": "https://a16z.com/feed/",
    },
    {
        "id": "sequoia",
        "name": "Sequoia Capital",
        "category": "投资机构",
        "type": "html",
        "url": "https://www.sequoiacap.com/perspectives/",
        "article_selector": "a[href*='/perspectives/']",
    },
    {
        "id": "lightspeed",
        "name": "Lightspeed Venture Partners",
        "category": "投资机构",
        "type": "html",
        "url": "https://lsvp.com/stories/",
        "article_selector": "a[href*='/stories/']",
    },
    {
        "id": "accel",
        "name": "Accel",
        "category": "投资机构",
        "type": "rss",
        "url": "https://www.accel.com/feed",
    },
    # --- 专家博客（3）---
    {
        "id": "karpathy",
        "name": "Andrej Karpathy",
        "category": "专家博客",
        "type": "html",
        "url": "https://karpathy.github.io/",
        "article_selector": "a[href]",
    },
    {
        "id": "simon_willison",
        "name": "Simon Willison",
        "category": "专家博客",
        "type": "atom",
        "url": "https://simonwillison.net/atom/everything/",
    },
    {
        "id": "lilian_weng",
        "name": "Lilian Weng",
        "category": "专家博客",
        "type": "rss",
        "url": "https://lilianweng.github.io/feed.xml",
    },
    # --- 基础设施（1）---
    {
        "id": "nvidia",
        "name": "NVIDIA AI",
        "category": "基础设施",
        "type": "rss",
        "url": "https://blogs.nvidia.com/feed/",
    },
]


def random_delay():
    """随机延迟 1-3 秒"""
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)


def fetch_rss(source):
    """抓取 RSS/Atom feed"""
    if feedparser is None:
        return {
            "status": "failed",
            "error": "feedparser not installed",
            "articles": [],
        }

    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        articles = []
        for entry in feed.entries[:15]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    pass

            articles.append({
                "title": getattr(entry, "title", "Untitled"),
                "url": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", "")[:500] if hasattr(entry, "summary") else "",
                "published": published,
            })

        return {
            "status": "success",
            "articles": articles,
        }
    except requests.Timeout:
        return {"status": "timeout", "error": "Request timed out", "articles": []}
    except requests.RequestException as e:
        return {"status": "failed", "error": str(e), "articles": []}
    except Exception as e:
        return {"status": "failed", "error": str(e), "articles": []}


def fetch_html(source):
    """抓取网页，提取文章标题和链接"""
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")

        articles = []
        seen_urls = set()

        for link in soup.select(source.get("article_selector", "a[href]"))[:20]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or not href or len(title) < 5:
                continue
            if href in seen_urls:
                continue

            full_url = urljoin(source["url"], href)
            seen_urls.add(href)

            # 尝试提取更多文本上下文
            parent = link.parent
            context = ""
            if parent:
                context = parent.get_text(strip=True)[:500]

            articles.append({
                "title": title[:200],
                "url": full_url,
                "summary": context,
                "published": None,
            })

        return {
            "status": "success",
            "articles": articles[:15],
        }
    except requests.Timeout:
        return {"status": "timeout", "error": "Request timed out", "articles": []}
    except requests.RequestException as e:
        return {"status": "failed", "error": str(e), "articles": []}
    except Exception as e:
        return {"status": "failed", "error": str(e), "articles": []}


def fetch_api(source):
    """抓取 REST API"""
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # arXiv 返回 XML
        if "arxiv" in source["id"]:
            soup = BeautifulSoup(resp.content, "lxml-xml")
            articles = []
            for entry in soup.find_all("entry")[:10]:
                title = entry.find("title")
                link = entry.find("id")
                summary = entry.find("summary")

                published = None
                published_tag = entry.find("published")
                if published_tag:
                    try:
                        published = published_tag.get_text(strip=True)
                    except Exception:
                        pass

                articles.append({
                    "title": title.get_text(strip=True).replace("\n", " ") if title else "Untitled",
                    "url": link.get_text(strip=True) if link else "",
                    "summary": (summary.get_text(strip=True)[:500] if summary else ""),
                    "published": published,
                })

            return {"status": "success", "articles": articles}

        # JSON API
        data = resp.json()
        articles = []

        if source["id"] == "ai_hot":
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            for item in items[:20]:
                articles.append({
                    "title": item.get("title", item.get("name", "Untitled")),
                    "url": item.get("url", item.get("link", "")),
                    "summary": item.get("description", item.get("summary", ""))[:500],
                    "published": item.get("published", item.get("date", item.get("created_at"))),
                })
        else:
            items = data if isinstance(data, list) else data.get("items", data.get("results", []))
            for item in items[:20]:
                articles.append({
                    "title": item.get("title", item.get("name", "Untitled")),
                    "url": item.get("url", item.get("link", "")),
                    "summary": item.get("description", item.get("summary", ""))[:500],
                    "published": item.get("published", item.get("date", item.get("created_at"))),
                })

        return {"status": "success", "articles": articles[:15]}
    except requests.Timeout:
        return {"status": "timeout", "error": "Request timed out", "articles": []}
    except requests.RequestException as e:
        return {"status": "failed", "error": str(e), "articles": []}
    except Exception as e:
        return {"status": "failed", "error": str(e), "articles": []}


def fetch_source(source):
    """抓取单个数据源"""
    print(f"  [{source['id']}] {source['name']} ...", end=" ", flush=True)
    source_type = source["type"]

    if source_type in ("rss", "atom"):
        result = fetch_rss(source)
    elif source_type == "html":
        result = fetch_html(source)
    elif source_type == "api":
        result = fetch_api(source)
    else:
        result = {"status": "failed", "error": f"Unknown type: {source_type}", "articles": []}

    status_icon = "OK" if result["status"] == "success" else "FAIL"
    article_count = len(result["articles"])
    print(f"{status_icon} ({article_count} articles)")

    if result["status"] != "success":
        print(f"    -> {result.get('error', 'Unknown error')}")

    return result


def main():
    start_time = time.time()
    print(f"Future Intelligence 数据抓取管线")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"数据源总数: {len(SOURCES)}")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"{'='*60}")

    results = {}
    success_count = 0
    fail_count = 0
    timeout_count = 0

    for i, source in enumerate(SOURCES, 1):
        print(f"\n[{i}/{len(SOURCES)}]", end=" ")
        result = fetch_source(source)

        results[source["id"]] = {
            "name": source["name"],
            "category": source["category"],
            "url": source["url"],
            "status": result["status"],
            "error": result.get("error"),
            "articles": result["articles"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        if result["status"] == "success":
            success_count += 1
        elif result["status"] == "timeout":
            timeout_count += 1
        else:
            fail_count += 1

        # 随机延迟避免被封
        random_delay()

    elapsed = time.time() - start_time
    total_articles = sum(len(r["articles"]) for r in results.values())

    print(f"\n{'='*60}")
    print(f"抓取完成")
    print(f"  成功: {success_count}/{len(SOURCES)}")
    print(f"  超时: {timeout_count}/{len(SOURCES)}")
    print(f"  失败: {fail_count}/{len(SOURCES)}")
    print(f"  文章总数: {total_articles}")
    print(f"  耗时: {elapsed:.1f}s")

    # 写入 JSON
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(SOURCES),
        "success_count": success_count,
        "fail_count": fail_count + timeout_count,
        "total_articles": total_articles,
        "sources": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n已写入: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
