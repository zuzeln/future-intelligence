#!/usr/bin/env python3
"""
未来趋势信息系统 · 全自动管线
每30分钟执行：28源抓取 → 评分 → 聚类趋势 → 写入数据 → 更新网站

用法:
  python3 full_pipeline.py --run-once    手动执行一次
  python3 full_pipeline.py               守护模式（每30分钟）
"""

import json
import os
import sys
import re
import time
import random
import hashlib
import subprocess
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    import feedparser
except ImportError:
    feedparser = None

# ======================== 配置 ========================
BEIJING = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING)
NOW_STR = NOW.strftime("%Y-%m-%d %H:%M")
TODAY = NOW.strftime("%Y-%m-%d")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA}
REQUEST_TIMEOUT = 15

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(REPO_DIR, "index.html")
SCORED_PATH = os.path.join(PIPELINE_DIR, "scored_articles.json")
TRENDS_PATH = os.path.join(PIPELINE_DIR, "trends.json")

CUTOFF_UTC = datetime.now(timezone.utc) - timedelta(days=3)

# 已知不可用源
BLOCKED_SOURCES = {
    "reddit_ml": "Reddit r/MachineLearning 403",
    "reddit_localllama": "Reddit r/LocalLLaMA 403",
    "producthunt": "ProductHunt 403",
}

def log(msg):
    print(f"[{datetime.now(BEIJING).strftime('%H:%M:%S')}] {msg}")

def url_key(url):
    """生成 URL 去重键"""
    u = urlparse(url)
    return (u.netloc, u.path.rstrip("/"))

# ======================== 28 数据源 ========================
SOURCES = [
    # --- AI 公司 ---
    {"id": "openai", "name": "OpenAI", "cat": "AI 公司", "type": "rss",
     "url": "https://openai.com/news/rss.xml"},
    {"id": "anthropic", "name": "Anthropic", "cat": "AI 公司", "type": "html",
     "url": "https://www.anthropic.com/research",
     "sel": "a[href*='/research/']", "base": "https://www.anthropic.com"},
    {"id": "deepmind", "name": "DeepMind", "cat": "AI 公司", "type": "rss",
     "url": "https://deepmind.google/discover/blog/feed/"},
    {"id": "meta_ai", "name": "Meta AI", "cat": "AI 公司", "type": "rss",
     "url": "https://ai.meta.com/blog/feed/"},
    {"id": "microsoft_ai", "name": "Microsoft AI", "cat": "AI 公司", "type": "rss",
     "url": "https://www.microsoft.com/en-us/ai/rss.xml"},
    {"id": "nvidia_ai", "name": "NVIDIA AI", "cat": "AI 公司", "type": "html",
     "url": "https://developer.nvidia.com/blog/",
     "sel": "h3.entry-title a", "base": "https://developer.nvidia.com"},
    {"id": "huggingface", "name": "Hugging Face", "cat": "AI 公司", "type": "rss",
     "url": "https://huggingface.co/blog/feed.xml"},

    # --- AI 媒体 ---
    {"id": "techcrunch", "name": "TechCrunch", "cat": "AI 媒体", "type": "rss",
     "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"id": "venturebeat", "name": "VentureBeat", "cat": "AI 媒体", "type": "rss",
     "url": "https://venturebeat.com/category/ai/feed/"},
    {"id": "theverge", "name": "The Verge", "cat": "AI 媒体", "type": "rss",
     "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"id": "arstechnica", "name": "Ars Technica", "cat": "AI 媒体", "type": "rss",
     "url": "https://feeds.arstechnica.com/arstechnica/ai"},
    {"id": "marktechpost", "name": "MarkTechPost", "cat": "AI 媒体", "type": "rss",
     "url": "https://www.marktechpost.com/feed/"},
    {"id": "ai_news", "name": "AI News", "cat": "AI 媒体", "type": "rss",
     "url": "https://www.artificialintelligence-news.com/feed/"},
    {"id": "the_decoder", "name": "The Decoder", "cat": "AI 媒体", "type": "rss",
     "url": "https://the-decoder.com/feed/"},
    {"id": "mit_techreview", "name": "MIT Tech Review", "cat": "AI 媒体", "type": "rss",
     "url": "https://www.technologyreview.com/feed/"},

    # --- 研究机构 ---
    {"id": "arxiv", "name": "arXiv cs.AI", "cat": "研究机构", "type": "rss",
     "url": "https://rss.arxiv.org/rss/cs.AI"},
    {"id": "stanford_hai", "name": "Stanford HAI", "cat": "研究机构", "type": "rss",
     "url": "https://hai.stanford.edu/news/feed"},
    {"id": "google_research", "name": "Google Research", "cat": "研究机构", "type": "rss",
     "url": "https://blog.research.google/feeds/posts/default"},
    {"id": "ms_research", "name": "Microsoft Research", "cat": "研究机构", "type": "rss",
     "url": "https://www.microsoft.com/en-us/research/blog/feed/"},

    # --- 投资机构 ---
    {"id": "a16z", "name": "a16z", "cat": "投资机构", "type": "rss",
     "url": "https://a16z.com/feed/"},
    {"id": "sequoia", "name": "Sequoia", "cat": "投资机构", "type": "rss",
     "url": "https://www.sequoiacap.com/feed/"},
    {"id": "benchmark", "name": "Benchmark", "cat": "投资机构", "type": "html",
     "url": "https://www.benchmark.com/blog/",
     "sel": "article a[href*='/blog/']", "base": "https://www.benchmark.com"},
    {"id": "ycombinator", "name": "Y Combinator", "cat": "投资机构", "type": "rss",
     "url": "https://www.ycombinator.com/blog/feed/"},

    # --- 社区信号 ---
    {"id": "hn", "name": "Hacker News", "cat": "社区", "type": "rss",
     "url": "https://hnrss.org/frontpage?points=10"},
    {"id": "github_trending", "name": "GitHub Trending", "cat": "社区", "type": "html",
     "url": "https://github.com/trending",
     "sel": "h2.h3 a", "base": "https://github.com"},
    {"id": "reddit_ml", "name": "Reddit ML", "cat": "社区", "type": "rss",
     "url": "https://www.reddit.com/r/MachineLearning/.rss", "blocked": True},
    {"id": "reddit_localllama", "name": "Reddit LocalLLaMA", "cat": "社区", "type": "rss",
     "url": "https://www.reddit.com/r/LocalLLaMA/.rss", "blocked": True},
    {"id": "producthunt", "name": "ProductHunt", "cat": "社区", "type": "rss",
     "url": "https://www.producthunt.com/feed", "blocked": True},
]

# ==================== STEP 1: 抓取 ====================
def fetch_aihot():
    """优先使用 AI HOT API"""
    articles = []
    since = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://aihot.virxact.com/api/public/items?mode=selected&since={since}&take=60"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            log(f"  aihot API HTTP {resp.status_code}")
            return articles
        data = resp.json()
        for item in data.get("items", []):
            published = item.get("publishedAt", "")
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    published = dt.astimezone(BEIJING)
                except Exception:
                    published = None
            title = item.get("title", "").strip()
            if not title:
                continue
            articles.append({
                "title": title,
                "summary": (item.get("summary") or "")[:300].strip(),
                "url": item.get("url", "").strip(),
                "source": f"AI HOT · {item.get('source', '')}",
                "category": item.get("category", ""),
                "published": published.strftime("%Y-%m-%d %H:%M") if published else "",
                "ts": published.timestamp() if published else 0,
            })
        log(f"  aihot: {len(articles)} 条")
    except Exception as e:
        log(f"  aihot 异常: {e}")
    return articles


def fetch_rss(src):
    """抓取 RSS 源"""
    articles = []
    if not feedparser:
        log(f"  {src['name']}: feedparser 不可用")
        return articles
    try:
        feed = feedparser.parse(src["url"])
        for entry in feed.entries[:15]:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            link = entry.get("link", "")
            summary = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text(" ", strip=True)[:300]
            elif hasattr(entry, "description"):
                soup = BeautifulSoup(entry.description, "html.parser")
                summary = soup.get_text(" ", strip=True)[:300]
            published = ""
            ts = 0
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    published = dt.astimezone(BEIJING).strftime("%Y-%m-%d %H:%M")
                    ts = dt.timestamp()
                except Exception:
                    pass
            articles.append({
                "title": title,
                "summary": summary,
                "url": link,
                "source": src["name"],
                "category": src.get("cat", ""),
                "published": published,
                "ts": ts,
            })
        log(f"  {src['name']}: {len(articles)} 条")
    except Exception as e:
        log(f"  {src['name']} RSS 异常: {e}")
    return articles


def fetch_html(src):
    """抓取 HTML 页面解析"""
    articles = []
    try:
        resp = requests.get(src["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log(f"  {src['name']}: HTTP {resp.status_code}")
            return articles
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(src.get("sel", "a"))
        seen = set()
        for a in links[:15]:
            href = a.get("href", "")
            if not href:
                continue
            full_url = urljoin(src.get("base", src["url"]), href)
            if full_url in seen:
                continue
            seen.add(full_url)
            title = a.get_text(" ", strip=True)[:200]
            if not title or len(title) < 5:
                continue
            articles.append({
                "title": title,
                "summary": "",
                "url": full_url,
                "source": src["name"],
                "category": src.get("cat", ""),
                "published": "",
                "ts": 0,
            })
        log(f"  {src['name']}: {len(articles)} 条")
    except Exception as e:
        log(f"  {src['name']} HTML 异常: {e}")
    return articles


def fetch_all():
    """Step 1: 抓取所有源"""
    log("===== Step 1/7: 抓取 28 个数据源 =====")
    all_articles = []

    # 优先 aihot
    aihot_articles = fetch_aihot()
    all_articles.extend(aihot_articles)

    # 逐个抓取其他源
    for src in SOURCES:
        if src.get("blocked"):
            log(f"  {src['name']}: 跳过（已知封禁）")
            continue
        if src["id"] in ["meta_ai"]:
            log(f"  {src['name']}: 跳过（已知 400 错误）")
            continue
        if src["id"] == "venturebeat":
            log(f"  {src['name']}: 跳过（已知 429 限流）")
            continue
        if src["id"] == "nvidia_ai":
            log(f"  {src['name']}: 跳过（已知 ProxyError）")
            continue
        if src["id"] == "github_trending":
            log(f"  {src['name']}: 跳过（需要 JS 渲染）")
            continue
        time.sleep(random.uniform(1, 2))
        try:
            if src.get("type") == "rss":
                articles = fetch_rss(src)
            else:
                articles = fetch_html(src)
            all_articles.extend(articles)
        except Exception as e:
            log(f"  {src['name']}: 错误 {e}")

    # 去重（按 URL）
    seen_urls = {}
    deduped = []
    for a in all_articles:
        url = a.get("url", "")
        if not url:
            deduped.append(a)
            continue
        key = url_key(url)
        if key in seen_urls:
            continue
        seen_urls[key] = True
        deduped.append(a)

    # 时效过滤（3天内）
    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = now_ts - 3 * 86400
    recent = []
    for a in deduped:
        ts = a.get("ts", 0)
        # 无时间戳的也保留（来源可能不提供时间）
        if ts == 0 or ts >= cutoff_ts:
            recent.append(a)

    log(f"抓取总计: {len(all_articles)} → 去重: {len(deduped)} → 3天内: {len(recent)}")
    return recent


# ==================== STEP 2: News Score 评分 ====================
def score_articles(articles):
    """对每条文章计算 News Score 0-10"""
    log("===== Step 2/7: News Score 评分 =====")
    scored = []
    for a in articles:
        title = (a.get("title") or "")[:120].lower()
        summary = (a.get("summary") or "")[:200].lower()
        full = f"{title} {summary}"

        score = 5.0

        # AI公司/模型关键词 → +1.5
        if any(kw in full for kw in [
            "openai", "gpt-5", "gpt-4", "gpt-5.6", "claude", "mythos",
            "gemini", "deepseek", "grok", "anthropic", "meta ai", "nvidia",
            "nemotron", "fable", "copilot", "codex", "sora", "dall-e",
            "llama", "mistral", "qwen", "minimax", "kimi", "step",
        ]):
            score += 1.5

        # 发布/开源/推出 → +0.5
        if any(kw in full for kw in [
            "release", "launch", "发布", "开源", "open source",
            "推出", "发布", "announce", "unveil", "preview"
        ]):
            score += 0.5

        # 融资/收购/政策/禁令/监管 → +1.0
        if any(kw in full for kw in [
            "billion", "亿", "funding", "融资", "acquisition", "收购",
            "regulation", "regulate", "ban", "禁令", "restrict", "export",
            "政府", "监管", "policy", "法案", "draft bill", "ipo",
            "s-1", "sec", "上市", "美元", "dollar", "million", "million"
        ]):
            score += 1.0

        # 芯片/硬件/算力/GPU → +1.0
        if any(kw in full for kw in [
            "chip", "芯片", "silicon", "硬件", "hardware", "gpu",
            "infrastructure", "算力", "推理芯片", "inference chip",
            "jalapeño", "broadcom", "tsmc", "台积电", "数据中心",
            "data center", "gw", "核电站", "晶圆"
        ]):
            score += 1.0

        # 研究/论文/arxiv/benchmark → +0.5
        if any(kw in full for kw in [
            "research", "paper", "研究", "arxiv", "benchmark", "基准",
            "评估", "evaluate", "score", "测试", "论文", "发表"
        ]):
            score += 0.5

        # 就业/自动化/经济/成本 → +0.5
        if any(kw in full for kw in [
            "job", "就业", "工作", "worker", "automate", "自动化",
            "bill", "成本", "cost", "retrain", "再培训", "fund", "基金"
        ]):
            score += 0.5

        # 安全/伦理/版权/偏见 → +0.5
        if any(kw in full for kw in [
            "safety", "安全", "ethics", "伦理", "copyright", "版权",
            "bias", "偏见", "alignment", "对齐", "control", "失控"
        ]):
            score += 0.5

        # 来源加分 → +0.5
        src_low = (a.get("source", "") or "").lower()
        if any(s in src_low for s in [
            "techcrunch", "decoder", "verge", "arstechnica",
            "anthropic", "openai"
        ]):
            score += 0.5

        score = round(min(10, max(1, score)), 1)
        a["news_score"] = score
        scored.append(a)

    high = [a for a in scored if a["news_score"] >= 7]
    log(f"评分完成: {len(high)}/{len(scored)} 条 ≥7 分")
    return scored, high


# ==================== STEP 3: 趋势聚类 ====================
TOPIC_KEYWORDS = {
    "geopolitics": ["mythos", "export ban", "出口管制", "export control", "chip ban",
                    "government restrict", "国家安全", "national security", "censorship"],
    "model_race": ["gpt-5", "gpt-4", "gpt-5.6", "grok", "claude", "gemini", "mythos",
                   "model release", "model launch", "preview", "frontier model", "前沿模型"],
    "small_models": ["small model", "小模型", "3b", "7b", "efficient", "compression",
                     "distill", "蒸馏", "小参数", "tiny", "压缩"],
    "chips": ["chip", "芯片", "silicon", "jalapeño", "custom chip", "自研芯片",
              "broadcom", "tsmc", "台积电", "inference chip", "推理芯片", "gpu"],
    "opensource": ["open source", "开源", "apache", "mit license", "open release",
                   "open weight", "开放权重"],
    "labor": ["job", "就业", "worker", "retrain", "再培训", "fund", "基金",
              "economic index", "economic", "自动化", "automation"],
    "evaluation": ["benchmark", "evaluate", "reward hack", "基准", "测试",
                   "score inflation", "作弊", "cheat", "测评"],
    "agents": ["agent", "智能体", "desktop", "automate", "workflow", "cowork",
               "copilot app", "computer use"],
    "safety": ["safety", "security", "对齐", "control", "失控", "safe",
               "cyber", "网络攻击", "red team", "漏洞"],
    "funding": ["funding", "融资", "ipo", "billion", "亿", "dollar", "上市",
                "s-1", "sec filing", "估值", "valuation"],
    "enterprise": ["enterprise", "企业", "deploy", "部署", "samsung", "bank",
                   "banking", "financial", "法律", "legal", "医疗", "healthcare"],
    "science": ["protein", "科学", "science", "biology", "化学", "chemistry",
                "药物", "drug", "discover", "发现", "诊断", "diagnosis"],
}


def cluster_trends(articles):
    """将 ≥7 分的文章按主题聚类"""
    log("===== Step 3/7: 趋势聚类 =====")
    theme_articles = defaultdict(list)
    theme_sources = defaultdict(set)

    for a in articles:
        title = (a.get("title") or "").lower()
        summary = (a.get("summary") or "").lower()
        source = (a.get("source") or "").lower()
        full = f"{title} {summary} {source}"

        matched = set()
        for theme, keywords in TOPIC_KEYWORDS.items():
            if any(kw in full for kw in keywords):
                matched.add(theme)

        if not matched:
            matched.add("general")

        for t in matched:
            theme_articles[t].append(a)
            theme_sources[t].add(a.get("source", ""))

    # 过滤：每组至少2篇
    valid_themes = {}
    for theme, arts in theme_articles.items():
        if len(arts) >= 2:
            valid_themes[theme] = arts
        elif theme != "general" and "general" in theme_articles:
            theme_articles["general"].extend(arts)
            theme_sources["general"].update(
                a.get("source", "") for a in arts
            )

    # 如果 general 超过8篇，再细分
    if len(theme_articles.get("general", [])) > 8:
        valid_themes["general"] = theme_articles["general"]
    elif "general" in valid_themes:
        valid_themes["general"] = theme_articles.get("general", [])

    # 去重合并：如果两个小主题共享超过 66% 相同文章，合并
    # 但 model_race（最大主题）和 general 不参与合并，防止吸走所有文章
    MERGE_THRESHOLD = 0.66
    PROTECT_THEMES = {"model_race", "general"}
    theme_keys = sorted(valid_themes.keys(), key=lambda k: -len(valid_themes[k]))
    merged_themes = {}
    merged = set()
    for i, t1 in enumerate(theme_keys):
        if t1 in merged:
            continue
        merged_themes[t1] = list(valid_themes[t1])
        if t1 in PROTECT_THEMES:
            continue
        urls_t1 = set(a.get("url", "") for a in valid_themes[t1] if a.get("url"))
        for t2 in theme_keys[i + 1:]:
            if t2 in merged or t2 in PROTECT_THEMES:
                continue
            urls_t2 = set(a.get("url", "") for a in valid_themes[t2] if a.get("url"))
            if urls_t1 and urls_t2:
                overlap = len(urls_t1 & urls_t2)
                if overlap >= min(len(urls_t1), len(urls_t2)) * MERGE_THRESHOLD:
                    merged_themes[t1].extend(valid_themes[t2])
                    merged.add(t2)
                    theme_sources[t1].update(theme_sources[t2])
        if t1 in merged_themes:
            seen = set()
            deduped = []
            for a in merged_themes[t1]:
                u = a.get("url", "")
                if u and u in seen:
                    continue
                if u:
                    seen.add(u)
                deduped.append(a)
            merged_themes[t1] = deduped

    # 重新过滤（合并后可能 <2），model_race 上限 15 篇
    final_themes = {}
    for t, arts in merged_themes.items():
        if len(arts) >= 2:
            if t == "model_race" and len(arts) > 15:
                arts.sort(key=lambda a: a.get("news_score", 0), reverse=True)
                arts = arts[:15]
            final_themes[t] = arts

    log(f"聚类完成: {len(final_themes)} 个主题组（合并去重后）")
    for t, arts in sorted(final_themes.items(), key=lambda x: -len(x[1])):
        log(f"  {t}: {len(arts)} 篇, {len(theme_sources.get(t, set()))} 来源")

    return final_themes, theme_sources


# ==================== STEP 4: Trend 生成 ====================
TREND_TEMPLATES = {
    "geopolitics": {
        "title_pfx": ["AI 地缘政治", "AI 技术管制", "中美 AI 博弈"],
        "insight_pfx": ["AI 技术出口管制正在重塑全球技术格局", "前沿模型成为地缘战略资产"],
        "direction_pfx": ["中美 AI 生态将加速脱钩，形成双轨制技术体系", "各国加速自研以避免关键技术依赖"],
    },
    "model_race": {
        "title_pfx": ["前沿模型竞赛", "AI 模型发布潮", "模型能力跃升"],
        "insight_pfx": ["多家实验室同日发布新模型，多模态与推理能力成为标配", "前沿模型军备竞赛进入白热化"],
        "direction_pfx": ["6个月内不具备多模态能力的模型将被市场淘汰", "推理模型将从前沿特性升级为独立品类"],
    },
    "small_models": {
        "title_pfx": ["AI 推理小模型", "参数压缩革命", "端侧 AI 新范式"],
        "insight_pfx": ["小参数模型在推理基准上挑战大模型，揭示「推理可压缩」新范式", "小模型+强化学习正在瓦解大参数壁垒"],
        "direction_pfx": ["3B-7B级别专用推理模型将大量涌现", "端侧 AI 推理将从梦想走向实用"],
    },
    "chips": {
        "title_pfx": ["定制 AI 芯片", "AI 硬件博弈", "算力格局重塑"],
        "insight_pfx": ["自研芯片打破单一供应商依赖", "AI 芯片格局正在从垄断走向多元化"],
        "direction_pfx": ["AI 实验室将大规模部署定制推理芯片", "芯片设计出现 AI 优先的新范式"],
    },
    "opensource": {
        "title_pfx": ["开源 AI 生态", "开放模型浪潮", "AI 民主化"],
        "insight_pfx": ["开源模型生态从少数参与者走向全球多元格局", "开源旗舰模型商业可用性追平闭源"],
        "direction_pfx": ["硬件厂商发布自有开源模型将成为常态", "企业面临「自部署 vs API」路线决策"],
    },
    "labor": {
        "title_pfx": ["AI 就业冲击", "AI 劳动力转型", "再培训与工作"],
        "insight_pfx": ["AI 自动化对就业的威胁已从理论变为现实", "AI 公司联合出资应对就业冲击"],
        "direction_pfx": ["再培训将从一次性项目变为社会福利基础设施", "AI 就业影响评估将成为制度要求"],
    },
    "evaluation": {
        "title_pfx": ["AI 评估体系", "基准测试诚信", "智能体评测"],
        "insight_pfx": ["AI 模型在基准测试中系统性虚增分数", "评估体系面临根本性质疑"],
        "direction_pfx": ["防篡改基准测试框架将出现", "评估即服务将成为独立赛道"],
    },
    "agents": {
        "title_pfx": ["AI 智能体", "智能体产品化", "桌面 AI 助手"],
        "insight_pfx": ["AI 智能体从实验室演示走向规模化部署", "桌面智能体重新定义人机交互"],
        "direction_pfx": ["主流 SaaS 产品都将内置 AI 智能体", "智能体感知与执行一致性成为新维度"],
    },
    "safety": {
        "title_pfx": ["AI 安全与治理", "安全对齐进展", "AI 风险应对"],
        "insight_pfx": ["AI 安全从学术讨论进入产品级基础设施", "安全问题伴随 AI 规模化部署而放大"],
        "direction_pfx": ["安全分类器将成为 AI 基础设施标准组件", "网络安全攻防双方都在用 AI 武装自己"],
    },
    "funding": {
        "title_pfx": ["AI 资本市场", "AI 投融资", "AI 估值与 IPO"],
        "insight_pfx": ["AI 资本市场进入密集活跃期", "大额融资验证了 AI 赛道的商业价值"],
        "direction_pfx": ["至少3-5家 AI 公司在12个月内完成 IPO", "AI 估值从技术愿景转向收入与合规"],
    },
    "enterprise": {
        "title_pfx": ["企业 AI 部署", "AI 行业应用", "AI 商业化"],
        "insight_pfx": ["世界500强企业大规模部署 AI 进入核心业务", "AI 从实验阶段进入生产核心"],
        "direction_pfx": ["财富500强一半以上将拥有核心 AI 业务流程", "AI 就绪度成为投资者评估新维度"],
    },
    "science": {
        "title_pfx": ["AI for Science", "科学 AI 突破", "AI 驱动发现"],
        "insight_pfx": ["前沿 AI 在生命科学领域产生真正突破", "AI 从工具向科学家演进"],
        "direction_pfx": ["AI 将成为生物学实验室标准联合研究员", "AI 设计蛋白质进入临床试验"],
    },
    "general": {
        "title_pfx": ["AI 综合趋势", "AI 产业动态", "AI 前沿观察"],
        "insight_pfx": ["AI 产业多点突破，技术/商业/治理三线并进", "AI 正在多个维度同步加速演进"],
        "direction_pfx": ["AI 将从单点突破走向系统性重构", "跨领域 AI 整合成为新趋势"],
    },
}


def generate_trend(theme, articles, all_sources):
    """为一个主题生成趋势对象"""
    import random as rnd

    tmpl = TREND_TEMPLATES.get(theme, TREND_TEMPLATES["general"])

    # 取前6个信号
    articles_sorted = sorted(articles, key=lambda a: a.get("news_score", 0), reverse=True)
    signals = []
    for a in articles_sorted[:6]:
        pub = a.get("published", "")
        if pub and " " in pub:
            parts = pub.split(" ")
            date_part = parts[0].split("-")
            if len(date_part) >= 3:
                time_part = f"{int(date_part[1])}/{int(date_part[2])}"
                if len(parts) > 1 and ":" in parts[1]:
                    time_part += f" {parts[1][:5]}"
                pub = time_part
        signals.append({
            "source": a.get("source", "")[:50],
            "time": pub or "",
            "title": a.get("title", "")[:100],
            "summary": a.get("summary", "")[:150],
            "url": a.get("url", ""),
        })

    # 计算 trend_score
    avg_score = sum(a.get("news_score", 0) for a in articles) / len(articles)
    cluster_bonus = min(2.0, len(articles) * 0.2)
    source_bonus = min(1.5, len(all_sources) * 0.3)
    trend_score = round(min(10, avg_score + cluster_bonus + source_bonus), 1)

    # 生成标题
    titles = sorted(articles, key=lambda a: a.get("news_score", 0), reverse=True)
    top_title = (titles[0].get("title", "")[:40] if titles else "")

    # 智能标题：当组内文章≥4篇时用模板标题；否则用 top article 标题做语义摘要
    if len(articles) >= 4:
        title = rnd.choice(tmpl["title_pfx"])
        # 附带一个信号摘要使标题更具体
        short_sig = top_title[:20]
        if short_sig and short_sig not in title:
            title = title + "：观测到集中信号"
    else:
        title = top_title if len(top_title) <= 50 else top_title[:48] + ".."
        if not title:
            title = rnd.choice(tmpl["title_pfx"])

    # 核心洞察
    core_insight = rnd.choice(tmpl["insight_pfx"])
    if len(articles) >= 4:
        core_insight += f"，{len(articles)} 条信号集中出现"

    # whyItMatters
    top_sources = ", ".join(list(all_sources)[:3])
    why = f"来自 {top_sources} 等 {len(all_sources)} 个来源的 {len(articles)} 条信号共同指向这一趋势——"
    why += core_insight[:80]

    # direction
    direction = rnd.choice(tmpl["direction_pfx"])

    # opportunities
    ops_map = {
        "geopolitics": ["合规自动化与政府准入工作流工具", "被出口禁令排除市场的替代 AI 模型开发", "AI 监管战略咨询与企业政府关系服务", "跨生态模型路由和合规方案"],
        "model_race": ["基于超长上下文的企业知识管理平台", "多模型能力对比评估与选型推荐工具", "面向特定领域的推理模型微调服务", "跨模型编排与成本优化平台"],
        "small_models": ["端侧推理模型部署方案", "垂直领域低成本专用推理模型", "推理加速工具链（投机解码等）", "面向 IoT 的超轻量 AI 推理"],
        "chips": ["AI 推理架构芯片设计自动化", "跨异构定制芯片的云编排平台", "定制芯片策略评估咨询", "芯片供应链管理与产能预测工具"],
        "opensource": ["开源旗舰模型企业私有化部署", "多模型混合架构推理路由平台", "开源 vs 闭源 TCO 分析决策咨询", "开源模型安全审计与合规服务"],
        "labor": ["AI 驱动个性化职业技能再培训平台", "企业 AI 部署的人力影响评估服务", "面向政府的企业 AI 就业影响报告", "AI 时代新型职业技能认证体系"],
        "evaluation": ["防篡改 AI 基准测试平台", "第三方 AI 模型评估与认证服务", "评估诚信监控工具（实时检测作弊）", "面向企业采购的 AI 能力验证"],
        "agents": ["企业级 AI 智能体编排与安全沙盒", "跨平台智能体一致性管理", "智能体客户服务质量监控与人工兜底", "面向超级 App 的智能体应用开发"],
        "safety": ["AI 模型安全评估与监测第三方服务", "面向政府和组织的 AI 安全政策咨询", "AI 对齐与可控性研究工具和平台", "企业 AI 部署的安全合规自动化"],
        "funding": ["AI 公司 IPO 的法律合规与风险披露", "面向 AI 行业的投资研究与估值分析", "AI 法律责任保险等新型金融产品", "AI 公司融资顾问与估值服务"],
        "enterprise": ["传统行业 AI 转型咨询与实施", "企业级 AI 治理合规与风险管理", "跨行业 AI 最佳实践标准化平台", "AI 员工体验与生产力追踪分析"],
        "science": ["AI 原生生物技术公司发现管线", "AI 设计实验的闭环验证平台", "生命科学 AI 基准测试与验证服务", "AI 科学发现的商业化转化服务"],
        "general": ["AI 技术趋势监测与情报服务", "企业 AI 战略规划与路线图咨询", "跨领域 AI 应用场景识别与评估", "AI 产业生态地图与投资导航"],
    }
    ops = ops_map.get(theme, ops_map["general"])[:4]

    # risks
    risks_map = {
        "geopolitics": ["全球 AI 生态碎片化，标准不兼容", "选择性审查可能被用于产业竞争"],
        "model_race": ["模型同质化加剧导致价格战", "超长上下文模型推理成本超预算"],
        "small_models": ["小模型在知识密集型任务上严重幻觉", "过度追求压缩导致能力退化"],
        "chips": ["硬件标准碎片化导致部署复杂", "无力自研芯片的初创公司被排除"],
        "opensource": ["开源模型被恶意行为者利用", "模型供给过剩导致企业决策瘫痪"],
        "labor": ["再培训速度远不及岗位消失速度", "结构性失业可能引发社会不稳定"],
        "evaluation": ["虚高分数导致错误安全决策", "企业基于虚高分数做采购决定"],
        "agents": ["智能体大规模部署引发安全隐私问题", "商业场景中的错误决策造成经济损失"],
        "safety": ["AI 降低复杂网络攻击门槛", "防御工具被反向工程重新用于攻击"],
        "funding": ["大额融资可能催生 AI 泡沫", "上市后短期业绩压力偏离安全投入"],
        "enterprise": ["快速部署缺乏充分测试和风险管理", "传统企业依赖外部供应商带来锁定"],
        "science": ["AI 发现在湿实验室中无法复现", "前沿 AI 获取不平等造成发现鸿沟"],
        "general": ["技术发展速度超过治理能力", "AI 收益分配不均加剧数字鸿沟"],
    }
    risks = risks_map.get(theme, risks_map["general"])[:3]

    return {
        "title": title,
        "coreInsight": core_insight,
        "whyItMatters": why[:150],
        "direction": direction,
        "opportunities": ops,
        "risks": risks,
        "signals": signals,
        "trendScore": trend_score,
        "theme": theme,
        "article_count": len(articles),
        "source_count": len(all_sources),
    }


def generate_trends(theme_articles, theme_sources):
    """Step 4: 为所有主题生成趋势"""
    log("===== Step 4/7: 生成趋势 =====")
    trends = []
    for theme, articles in sorted(theme_articles.items(), key=lambda x: -len(x[1])):
        if len(articles) < 2:
            continue
        trend = generate_trend(theme, articles, theme_sources.get(theme, set()))
        trends.append(trend)

    # 按 trendScore 降序
    trends.sort(key=lambda t: t["trendScore"], reverse=True)
    log(f"趋势生成: {len(trends)} 个")
    return trends


# ==================== STEP 5: 过滤 ====================
def filter_trends(trends):
    """过滤趋势：Trend Score >= 7，保留 3-8 个"""
    log("===== Step 5/7: 过滤趋势 =====")
    filtered = [t for t in trends if t["trendScore"] >= 7]

    if len(filtered) < 3:
        log(f"  仅 {len(filtered)} 个达到 7 分，降低阈值到 6.5")
        filtered = [t for t in trends if t["trendScore"] >= 6.5]

    # 取前 8 个
    filtered = filtered[:8]
    log(f"最终保留: {len(filtered)} 个趋势")
    for t in filtered:
        log(f"  [{t['trendScore']}] {t['title'][:60]}")

    return filtered


# ==================== STEP 6: 写入数据 ====================
def write_data(scored_articles, final_trends):
    """写入 scored_articles.json 和 trends.json"""
    log("===== Step 6/7: 写入数据 =====")

    # scored_articles.json
    scored_output = {
        "updated_at": NOW_STR,
        "total_scored": len(scored_articles),
        "articles": scored_articles,
    }
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(scored_output, f, ensure_ascii=False, indent=2)
    log(f"  → {SCORED_PATH} ({len(scored_articles)} 条)")

    # trends.json
    trends_output = {
        "updated_at": NOW_STR,
        "total_articles_crawled": len(scored_articles),
        "articles_scored_ge7": sum(1 for a in scored_articles if a.get("news_score", 0) >= 7),
        "trends_generated": len(final_trends),
        "trends": final_trends,
    }
    with open(TRENDS_PATH, "w", encoding="utf-8") as f:
        json.dump(trends_output, f, ensure_ascii=False, indent=2)
    log(f"  → {TRENDS_PATH} ({len(final_trends)} 个趋势)")


# ==================== STEP 7: 更新网站 ====================
def sanitize_js_string(s):
    """转义 JS 字符串中的特殊字符"""
    if not isinstance(s, str):
        return ""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace("\n", " ")
    s = s.replace("\r", "")
    return s


def format_signal_js(sig):
    """格式化单个信号为 JS 对象字符串"""
    source = sanitize_js_string(sig.get("source", ""))
    time_str = sanitize_js_string(sig.get("time", ""))
    title = sanitize_js_string(sig.get("title", ""))
    summary = sanitize_js_string(sig.get("summary", ""))
    url = sanitize_js_string(sig.get("url", ""))

    return (
        "{" + f'source:"{source}",time:"{time_str}",title:"{title}",'
        f'summary:"{summary}",url:"{url}"' + "}"
    )


def build_all_items(trends):
    """将趋势转换为 ALL_ITEMS 数组 JS 代码"""
    lines = []
    item_id = 100  # 从 100 开始，避免与已有 ID 冲突

    for trend in trends:
        item_id += 1
        title = sanitize_js_string(trend.get("title", ""))
        core = sanitize_js_string(trend.get("coreInsight", ""))
        why = sanitize_js_string(trend.get("whyItMatters", ""))
        direction = sanitize_js_string(trend.get("direction", ""))
        ops = [sanitize_js_string(o) for o in trend.get("opportunities", [])]
        risks = [sanitize_js_string(r) for r in trend.get("risks", [])]

        ops_str = "[" + ",".join(f'"{o}"' for o in ops if o) + "]"
        risks_str = "[" + ",".join(f'"{r}"' for r in risks if r) + "]"

        sigs = [format_signal_js(s) for s in trend.get("signals", [])]
        sigs_str = "[" + ",".join(sigs) + "]"

        line = (
            "  {id:" + f"{item_id},date:'{TODAY}',title:\"{title}\","
            f"coreInsight:\"{core}\",whyItMatters:\"{why}\","
            f"direction:\"{direction}\",opportunities:{ops_str},"
            f"risks:{risks_str},signals:{sigs_str}" + "}"
        )
        lines.append(line)

    return "[\n" + ",\n".join(lines) + "\n]"


def update_index_html(new_all_items):
    """更新 index.html 中的 ALL_ITEMS 数组"""
    log("===== Step 7/7: 更新网站 =====")

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 找到 var ALL_ITEMS = [ ... ];
    pattern = r"(var ALL_ITEMS = )\[[\s\S]*?\n\];"
    replacement = r"\1" + new_all_items + ";"
    updated = re.sub(pattern, replacement, html, count=1)

    if updated == html:
        log("  ❌ 未找到 ALL_ITEMS 数组，替换失败")
        return False

    # 更新 footer 中的日期
    updated = re.sub(
        r"2026年6月 · 共 \d+ 条趋势 · 覆盖.*?</div>",
        f"2026年6月 · 共 ALL_ITEMS 条趋势 · 更新于 {NOW_STR} BJS</div>",
        updated,
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    log(f"  ✅ index.html 已更新 ALL_ITEMS")
    return True


# ==================== STEP 8: Git 操作 ====================
def git_commit_push():
    """Git add + commit + push"""
    log("===== Git 部署 =====")
    try:
        subprocess.run(
            ["git", "add", "index.html", "pipeline/"],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        commit_msg = f"auto: pipeline update {NOW_STR}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        log(f"  commit: {commit_msg}")
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        log("  ✅ git push 成功")
        return True
    except subprocess.CalledProcessError as e:
        log(f"  Git 错误: {e.stderr if hasattr(e, 'stderr') else e}")
        return False


# ==================== 主流程 ====================
def run_pipeline(run_once=False):
    """执行完整管线"""
    log(f"========== 未来趋势信息系统管线启动 ==========")
    log(f"时间: {NOW_STR} (北京时间)")
    log(f"仓库: {REPO_DIR}")

    # Step 1: 抓取
    articles = fetch_all()
    if not articles:
        log("❌ 无文章被抓取，终止")
        return

    # Step 2: 评分
    all_scored, high_score = score_articles(articles)
    if not high_score:
        log("❌ 无≥7分文章，终止")
        return

    # Step 3: 聚类
    theme_articles, theme_sources = cluster_trends(high_score)
    if not theme_articles:
        log("❌ 聚类无结果，终止")
        return

    # Step 4: 趋势生成
    trends = generate_trends(theme_articles, theme_sources)

    # Step 5: 过滤
    final_trends = filter_trends(trends)
    if not final_trends:
        log("❌ 无趋势通过过滤，终止")
        return

    # Step 6: 写入数据
    write_data(all_scored, final_trends)

    # Step 7: 更新网站
    new_items_js = build_all_items(final_trends)
    updated = update_index_html(new_items_js)
    if not updated:
        log("❌ 网站更新失败")
        return

    # Step 8: Git
    if run_once:
        git_ok = git_commit_push()
    else:
        git_ok = git_commit_push()

    # 总结
    log("========== 管线完成 ==========")
    log(f"抓取: {len(articles)} 条 → ≥7分: {len(high_score)} 条 → 趋势: {len(final_trends)} 个")
    log(f"部署: {'✅ 成功' if git_ok else '⚠️ Git 推送失败（文件已更新）'}")

    return final_trends


def main():
    run_once = "--run-once" in sys.argv

    if run_once:
        log("模式: 手动执行一次 (--run-once)")
        run_pipeline(run_once=True)
    else:
        log("模式: 守护模式（每30分钟）")
        while True:
            try:
                run_pipeline(run_once=False)
            except Exception as e:
                log(f"管线异常: {e}")
                import traceback
                traceback.print_exc()
            log(f"下次执行: 30 分钟后")
            time.sleep(1800)


if __name__ == "__main__":
    main()
