#!/usr/bin/env python3
"""轻量化自动管线：aihot API → 评分 → 趋势 → 部署（每30分钟执行）"""
import json, os, sys, subprocess, time, re
from datetime import datetime, timezone, timedelta
from collections import Counter

import requests

BEIJING = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING)
NOW_STR = NOW.strftime("%Y-%m-%d %H:%M")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA}
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.join(REPO_DIR, "pipeline")
INDEX_PATH = os.path.join(REPO_DIR, "index.html")

def log(msg):
    print(f"[{datetime.now(BEIJING).strftime('%H:%M:%S')}] {msg}")

# ==================== STEP 1: 抓取 ====================
def fetch_aihot():
    articles = []
    since = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://aihot.virxact.com/api/public/items?mode=selected&since={since}&take=60"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            log(f"aihot API 错误: {resp.status_code}")
            return articles
        data = resp.json()
        for item in data.get("items", []):
            published = item.get("publishedAt", "")
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    published = dt.astimezone(BEIJING).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            articles.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "source": f"AI HOT · {item.get('source', '')}",
                "category": item.get("category", ""),
                "published": published,
            })
        log(f"aihot 抓取: {len(articles)} 条")
    except Exception as e:
        log(f"aihot 异常: {e}")
    return articles

# ==================== STEP 2: 评分 ====================
def score_articles(articles):
    scored = []
    for a in articles:
        title = a.get("title", "")[:80]
        summary = a.get("summary", "")[:200]
        full = f"{title.lower()} {summary.lower()}"
        
        score = 5.0
        # AI 公司/模型
        if any(kw in full for kw in ["openai", "gpt-5", "gpt-4", "claude", "gemini", "deepseek", "grok", "mythos", "anthropic", "meta ai", "nvidia"]):
            score += 1.5
        # 发布/开源
        if any(kw in full for kw in ["开源", "open source", "release", "launch", "发布", "发布", "推出"]):
            score += 0.5
        # 融资/政策
        if any(kw in full for kw in ["billion", "亿", "funding", "融资", "acquisition", "收购", "regulation", "ban", "restrict", "政府", "监管", "禁令"]):
            score += 1.0
        # 芯片/硬件
        if any(kw in full for kw in ["chip", "芯片", "silicon", "硬件", "hardware", "infrastructure", "算力", "gpu"]):
            score += 1.0
        # 研究
        if any(kw in full for kw in ["research", "paper", "研究", "arxiv", "benchmark", "基准"]):
            score += 0.5
        # 就业/经济
        if any(kw in full for kw in ["job", "就业", "工作", "worker", "automate", "自动化", "bill", "成本", "cost"]):
            score += 0.5
        # 安全/偏见
        if any(kw in full for kw in ["bias", "ethics", "safety", "安全", "伦理", "copyright", "版权"]):
            score += 0.5
        # 来源加分
        if any(kw in full for kw in ["techcrunch", "the decoder", "arstechnica", "anthropic", "openai"]):
            score += 0.5
        
        score = round(min(10, max(1, score)), 1)
        a["news_score"] = score
        scored.append(a)
    
    high = [a for a in scored if a["news_score"] >= 7]
    log(f"评分: {len(high)}/{len(scored)} 条 ≥7")
    return scored, high

# ==================== STEP 3: 聚类趋势 ====================
def cluster_trends(articles):
    """从高评文章中提取趋势主题"""
    themes = Counter()
    theme_map = {}
    
    for a in articles:
        title = a.get("title", "").lower()
        summary = a.get("summary", "").lower()
        full = title + " " + summary
        
        # 检测主题
        found = []
        if any(kw in full for kw in ["mythos", "export ban", "出口管制", "export control", "chip ban", "government restrict"]):
            found.append("geopolitics")
        if any(kw in full for kw in ["gpt-5", "grok 4", "claude", "gemini", "model release", "model launch", "preview"]):
            found.append("model_race")
        if any(kw in full for kw in ["small model", "小模型", "3b", "7b", "efficient", "compression", "distill", "蒸馏"]):
            found.append("small_models")
        if any(kw in full for kw in ["chip", "芯片", "silicon", "jalapeño", "custom chip"]):
            found.append("chips")
        if any(kw in full for kw in ["open source", "开源", "apache 2", "mit license", "open release"]):
            found.append("opensource")
        if any(kw in full for kw in ["job", "就业", "worker", "retrain", "再培训", "billion fund", "economic index"]):
            found.append("labor")
        if any(kw in full for kw in ["benchmark", "evaluate", "reward hack", "基准", "测试", "score inflation"]):
            found.append("evaluation")
        
        found = found or ["general"]
        for f in found:
            themes[f] += 1
    
    log(f"主题: {dict(themes.most_common(8))}")
    return themes

# ==================== STEP 4: 生成 HTML ====================
def build_html(trends_data):
    cards = ""
    for t in trends_data:
        score = t["trend_score"]
        color = "#22c55e" if score >= 9 else "#eab308" if score >= 8 else "#f97316"
        ops = "\n".join([f'<li>{o}</li>' for o in t.get("opportunities", [])])
        
        sigs = ""
        for s in t.get("signals", []):
            sigs += f"""<div class="signal-item"><div class="signal-score">{s.get('score','-')}</div>
<div class="signal-content"><a href="{s.get('url','#')}" target="_blank">{s.get('title','')}</a>
<div class="meta"><span>{s.get('source','')}</span></div></div></div>"""
        
        cards += f"""<div class="trend-card"><div class="trend-header"><div class="title-area">
<span class="category">{t.get('category','')}</span><h3>{t['title']}</h3></div>
<div class="trend-score" style="background:linear-gradient(135deg,{color},#8b5cf6)">{score}</div></div>
<div class="insight-box"><div class="label">核心洞察</div><p>{t.get('core_insight','')}</p></div>
<div class="trend-details"><div class="detail-section"><h4>未来方向</h4><div class="text">{t.get('direction','')}</div></div>
<div class="detail-section"><h4>机会信号</h4><ul>{ops}</ul></div></div>
<div class="signals-section"><h4>信息来源（{len(t.get('signals',[]))} 条）</h4>{sigs}</div></div>"""
    
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>未来趋势情报 | {NOW.strftime('%Y-%m-%d')}</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0a0a0f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;min-height:100vh}}
.container{{max-width:900px;margin:0 auto;padding:40px 20px 80px}}
.header{{text-align:center;padding:60px 0 40px;border-bottom:1px solid #1a1a2e;margin-bottom:50px}}
.header h1{{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#6366f1,#a78bfa,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.header .subtitle{{color:#888;margin-top:8px;font-size:.95rem}}
.section-title{{font-size:1.3rem;font-weight:700;color:#c4b5fd;margin-bottom:24px;padding-left:12px;border-left:3px solid #6366f1}}
.trend-card{{background:linear-gradient(135deg,#111122,#0d0d1f);border:1px solid #1e1e3a;border-radius:16px;padding:32px;margin-bottom:28px}}
.trend-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;gap:16px}}
.trend-header .title-area{{flex:1}}.trend-header h3{{font-size:1.35rem;font-weight:700;color:#f0f0f0;margin-bottom:4px}}
.trend-header .category{{font-size:.78rem;color:#6366f1;text-transform:uppercase;letter-spacing:1px}}
.trend-score{{color:white;font-size:1.5rem;font-weight:800;padding:8px 16px;border-radius:12px;min-width:60px;text-align:center;flex-shrink:0}}
.insight-box{{background:rgba(99,102,241,.08);border-left:3px solid #6366f1;padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:20px}}
.insight-box .label{{font-size:.75rem;color:#a78bfa;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}}
.insight-box p{{font-size:1.02rem;color:#e2e2f0}}
.trend-details{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}@media(max-width:640px){{.trend-details{{grid-template-columns:1fr}}}}
.detail-section h4{{font-size:.8rem;color:#8b8bcf;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.detail-section .text{{font-size:.92rem;color:#c0c0d0;line-height:1.7}}
.detail-section ul{{list-style:none;padding:0}}.detail-section ul li{{font-size:.9rem;color:#c0c0d0;padding:4px 0;padding-left:16px;position:relative}}
.detail-section ul li::before{{content:"→";position:absolute;left:0;color:#6366f1}}
.signals-section{{border-top:1px solid #1e1e3a;padding-top:16px}}
.signals-section h4{{font-size:.8rem;color:#8b8bcf;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.signal-item{{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.03);align-items:flex-start}}
.signal-item:last-child{{border-bottom:none}}.signal-score{{background:#1a1a3a;color:#a5b4fc;font-size:.75rem;font-weight:700;padding:2px 8px;border-radius:6px;white-space:nowrap;flex-shrink:0}}
.signal-content{{flex:1;min-width:0}}.signal-content a{{color:#a5b4fc;text-decoration:none;font-size:.9rem;font-weight:500;display:block;margin-bottom:3px}}
.signal-content a:hover{{color:#c4b5fd}}.signal-content .meta{{font-size:.75rem;color:#666}}
.footer{{text-align:center;padding:40px 0 20px;color:#444;font-size:.8rem;border-top:1px solid #1a1e2e;margin-top:40px}}
</style></head><body><div class="container">
<div class="header"><h1>未来趋势情报</h1><p class="subtitle">今天最重要的未来趋势是什么？</p></div>
<div class="section-title">趋势雷达</div>{cards}
<div class="footer"><p>未来趋势信息系统 · 轻量自动管线（aihot API）</p><p>每30分钟自动更新 · {NOW_STR} BJS</p></div>
</div></body></html>"""
    
    return html

# ==================== MAIN ====================
def main():
    log("===== 轻量抓取+评分启动 =====")
    
    # Step 1: 抓取
    log("Step 1/3: 抓取 aihot")
    articles = fetch_aihot()
    if not articles:
        log("无数据，终止")
        return
    
    # Step 2: 评分
    log("Step 2/3: 评分")
    all_scored, high_score = score_articles(articles)
    
    # Step 3: 输出 JSON（不写 index.html，不 git push）
    log("Step 3/3: 写入结果")
    output = {
        "updated": NOW_STR,
        "total_fetched": len(articles),
        "passed_score": len(high_score),
        "pass_threshold": 7,
        "articles": high_score,
    }
    out_path = os.path.join(PIPELINE_DIR, "raw_scored.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    log(f"✅ 完成: {len(articles)}条→{len(high_score)}条≥7分 → {out_path}")
    log("===== 管线完成（未部署） =====")

def build_html_index_direct(articles):
    """直接从评分文章生成简化趋势卡片"""
    if not articles:
        return "<html><body>暂无数据</body></html>"
    
    cards = ""
    for i, a in enumerate(articles[:8]):
        score = a["news_score"]
        color = "#22c55e" if score >= 9 else "#eab308" if score >= 8 else "#f97316"
        cards += f"""<div class="trend-card"><div class="trend-header"><div class="title-area">
<span class="category">{a.get('category','')}</span><h3>{a['title'][:100]}</h3></div>
<div class="trend-score" style="background:linear-gradient(135deg,{color},#8b5cf6)">{score}</div></div>
<div class="insight-box"><div class="label">摘要</div><p>{a.get('summary','')[:300]}</p></div>
<div class="signals-section"><h4>来源</h4>
<div class="signal-item"><div class="signal-content"><a href="{a.get('url','#')}" target="_blank">{a.get('source','')}</a>
<div class="meta"><span>{a.get('published','')}</span></div></div></div></div></div>"""
    
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>未来趋势情报 | {NOW.strftime('%Y-%m-%d')}</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0a0a0f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}}
.container{{max-width:900px;margin:0 auto;padding:40px 20px 80px}}
.header{{text-align:center;padding:60px 0 40px;border-bottom:1px solid #1a1a2e;margin-bottom:50px}}
.header h1{{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#6366f1,#a78bfa,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.header .subtitle{{color:#888;margin-top:8px;font-size:.95rem}}
.section-title{{font-size:1.3rem;font-weight:700;color:#c4b5fd;margin-bottom:24px;padding-left:12px;border-left:3px solid #6366f1}}
.trend-card{{background:linear-gradient(135deg,#111122,#0d0d1f);border:1px solid #1e1e3a;border-radius:16px;padding:32px;margin-bottom:28px}}
.trend-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;gap:16px}}
.trend-header .title-area{{flex:1}}.trend-header h3{{font-size:1.35rem;font-weight:700;color:#f0f0f0;margin-bottom:4px}}
.trend-header .category{{font-size:.78rem;color:#6366f1;text-transform:uppercase;letter-spacing:1px}}
.trend-score{{color:white;font-size:1.5rem;font-weight:800;padding:8px 16px;border-radius:12px;min-width:60px;text-align:center;flex-shrink:0}}
.insight-box{{background:rgba(99,102,241,.08);border-left:3px solid #6366f1;padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:20px}}
.insight-box .label{{font-size:.75rem;color:#a78bfa;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}}
.insight-box p{{font-size:1.02rem;color:#e2e2f0}}
.signals-section{{border-top:1px solid #1e1e3a;padding-top:16px}}
.signals-section h4{{font-size:.8rem;color:#8b8bcf;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.signal-item{{display:flex;gap:12px;padding:10px 0;align-items:flex-start}}
.signal-content{{flex:1;min-width:0}}.signal-content a{{color:#a5b4fc;text-decoration:none;font-size:.9rem;font-weight:500;display:block;margin-bottom:3px}}
.signal-content a:hover{{color:#c4b5fd}}.signal-content .meta{{font-size:.75rem;color:#666}}
.footer{{text-align:center;padding:40px 0 20px;color:#444;font-size:.8rem;border-top:1px solid #1a1e2e;margin-top:40px}}
</style></head><body><div class="container">
<div class="header"><h1>未来趋势情报</h1><p class="subtitle">今天最重要的未来趋势是什么？</p></div>
<div class="section-title">信号流（News Score ≥7）</div>{cards}
<div class="footer"><p>未来趋势信息系统 · 轻量自动管线</p><p>数据来源：aihot API · 每30分钟自动更新 · {NOW_STR} BJS</p></div>
</div></body></html>"""
    return html

if __name__ == "__main__":
    main()
