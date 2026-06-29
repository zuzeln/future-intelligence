#!/usr/bin/env python3
"""聚合趋势分析 + 生成网站前端"""

import json
import os
from datetime import datetime, timezone, timedelta

BEIJING = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M")

# 加载评分数据
with open("/Users/air/future-intelligence-repo/pipeline/scored_articles.json") as f:
    articles = json.load(f)

# 去重 + 过滤导航噪声
noise_urls = {
    "https://deepmind.google/models/gemini/", 
    "https://deepmind.google/models/gemini-omni/",
    "https://deepmind.google/models/gemini-audio/",
}
seen_ids = set()
clean = []
for a in articles:
    if a["news_score"] < 7:
        continue
    url = a.get("url", "")
    if url in noise_urls:
        continue
    title = a.get("title", "")
    # 跳过去重（同一标题不同来源保留一个）
    dedup_key = title[:50]
    if dedup_key in seen_ids and a["news_score"] < 8:
        continue
    seen_ids.add(dedup_key)
    # 跳过"Previewing GPT-5.6 Sol" 的重复
    if a.get("id", "") == "":  # web scraped duplicates
        if any(t in title for t in seen_ids):
            continue
    clean.append(a)

# ==================== 趋势聚类 ====================
trends = [
    {
        "id": "t1",
        "title": "中美AI技术铁幕正式落下",
        "core_insight": "美国对Anthropic Mythos实施出口管制并限制GPT-5.6发布，反而加速亚洲替代模型生态成熟，AI技术体系正分裂为两大阵营。",
        "direction": "中美AI技术栈将逐步脱钩，形成「双轨制」——美国主导前沿模型研发但收紧扩散，中国及亚洲通过开源和自研填补缺口。企业需要在两个生态中同时布局。",
        "opportunities": [
            "亚洲AI模型出海窗口：Mythos禁令为中国/东南亚模型打开市场",
            "合规中间件：企业需要跨生态的模型路由和合规方案",
            "芯片自主：中国AI芯片设计能力提升带来的投资机会",
        ],
        "trend_score": 9.5,
        "signal_ids": [4, 8, 19, 21, 27, 32, 33],
        "category": "地缘与监管",
    },
    {
        "id": "t2",
        "title": "AI推理小模型颠覆「大力出奇迹」范式",
        "core_insight": "VibeThinker-3B以3B参数在数学编程基准上持平200倍大模型，揭示「推理可压缩、知识不能」的新范式——小模型+强化学习正在瓦解大参数壁垒。",
        "direction": "模型尺寸不再是唯一竞争力。2026年下半年将出现更多<10B参数的专用推理模型，在垂直领域超越千亿级通用模型。推理效率而非参数规模成为新战场。",
        "opportunities": [
            "端侧推理：小模型可直接部署在手机和IoT设备",
            "垂直领域微调：企业可用低成本小模型替代GPT-5",
            "推理加速工具链：DeepSeek DSpark等框架带来60-85%提速",
        ],
        "trend_score": 9.0,
        "signal_ids": [3, 13, 9, 35],
        "category": "模型技术",
    },
    {
        "id": "t3",
        "title": "科技巨头集体自研AI芯片，Nvidia垄断时代终结",
        "core_insight": "OpenAI（Jalapeño）、SpaceX/xAI、Apple等巨头集体自研AI芯片，标志着从「买Nvidia」到「造芯片」的战略转折。AI芯片市场正从单极走向多极。",
        "direction": "2027年将出现至少5家具备实战能力的AI芯片设计方，Nvidia市场占比将跌破60%。存储芯片（HBM）成为新瓶颈，Micron等替代供应商受益。",
        "opportunities": [
            "定制AI芯片设计服务",
            "AI芯片制造（台积电/三星产能分配）",
            "芯片互连和冷却技术",
        ],
        "trend_score": 8.5,
        "signal_ids": [20, 5, 1],
        "category": "硬件与基础设施",
    },
    {
        "id": "t4",
        "title": "AI劳动力替代进入「真金白银」阶段",
        "core_insight": "前美国商务部长发起10亿美元AI再培训基金，Anthropic数据显示50%用户认为AI可处理半数工作，美国企业为省钱已将100%流量切换到更便宜的Chinese模型。AI对就业的冲击已从预言变为量化现实。",
        "direction": "未来18个月将出现大规模职业转型浪潮。企业端「Token成本套利」成为新常态，政府端再培训项目将在更多国家复制。但培训效果存疑，结构性失业风险仍在上升。",
        "opportunities": [
            "AI职业培训和认证平台",
            "人机协作工作流设计",
            "企业模型路由与成本优化服务",
            "AI转型咨询",
        ],
        "trend_score": 8.5,
        "signal_ids": [6, 23, 34, 2, 59],
        "category": "经济与就业",
    },
    {
        "id": "t5",
        "title": "开源模型生态多元化：从中国独舞到全球合奏",
        "core_insight": "Cohere以Apache 2.0开源旗舰Command A+（218B MoE多模态），NVIDIA开源Nemotron-3-Ultra（OpenMDW许可证），DeepSeek开源DSpark加速框架。开源AI生态正从少数中国公司扩展到全球各类组织，开源正在成为商业策略而非妥协。",
        "direction": "开源将成为头部玩家的标准策略，2027年前将出现首个完全开源、全模态、可商用的千亿级模型。企业可以在不牺牲性能的前提下实现模型自主可控。",
        "opportunities": [
            "开源模型托管与微调服务",
            "企业级开源模型部署与运维",
            "基于开源模型的行业垂直应用",
        ],
        "trend_score": 8.0,
        "signal_ids": [9, 13, 26],
        "category": "开源生态",
    },
    {
        "id": "t6",
        "title": "AI评估体系信任危机：基准分数集体「注水」",
        "core_insight": "普林斯顿CEO-Bench显示14个顶级模型中仅3个在500天创业模拟中盈利；Cursor研究发现63%的SWE-bench成功来自检索而非推理；AI在《文明VI》中主动检查全局状态仅1-2%。现有基准已系统性高估AI真实能力。",
        "direction": "行业将推动从静态基准到动态、抗攻击、长期评估的范式转变。新的评估标准将关注AI在开放环境中的持续决策能力，而非单次测试得分。",
        "opportunities": [
            "新一代动态评估基准平台",
            "AI能力审计与认证服务",
            "企业AI部署前的真实能力验证工具",
        ],
        "trend_score": 7.5,
        "signal_ids": [11, 18, 22],
        "category": "评估与治理",
    },
]

# 关联信号详情
for t in trends:
    t["signals"] = []
    for a in clean:
        for sid in t["signal_ids"]:
            if a.get("id", str(id(a))) == str(sid) or (isinstance(sid, int) and clean.index(a) + 1 == sid):
                t["signals"].append({
                    "title": a["title"][:120],
                    "source": a["source"],
                    "url": a["url"],
                    "score": a["news_score"],
                    "published": a.get("published", ""),
                    "summary": a.get("summary", "")[:200]
                })
                break

# 按趋势分数降序
trends.sort(key=lambda x: x["trend_score"], reverse=True)
trends = trends[:8]  # 最多 8 个

# ==================== 输出 ====================
output = {
    "updated_at": NOW,
    "total_articles_crawled": len(articles),
    "articles_scored_ge7": len(clean),
    "trends_generated": len(trends),
    "trends": [{k: v for k, v in t.items() if k != "signal_ids"} for t in trends]
}

with open("/Users/air/future-intelligence-repo/pipeline/trends.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ 趋势分析完成")
print(f"  爬取: {output['total_articles_crawled']} 条")
print(f"  高分(≥7): {output['articles_scored_ge7']} 条")
print(f"  趋势: {output['trends_generated']} 个")
for t in trends:
    print(f"\n  [{t['trend_score']}] {t['title']}")
    print(f"       {t['core_insight'][:60]}...")
    print(f"       信号: {len(t['signals'])} 条")
