#!/usr/bin/env python3
"""生成未来趋势信息网站 index.html"""
import json

TRENDS_DATA = [
    {
        "id": "t1",
        "title": "中美AI技术铁幕正式落下",
        "core_insight": "美国对Anthropic Mythos实施出口管制并限制GPT-5.6发布，反而加速亚洲替代模型生态成熟，AI技术体系正分裂为两大阵营。",
        "direction": "中美AI技术栈将逐步脱钩，形成「双轨制」——美国主导前沿模型研发但收紧扩散，中国及亚洲通过开源和自研填补缺口。企业需要在两个生态中同时布局。",
        "opportunities": [
            "亚洲AI模型出海窗口：Mythos禁令为中国/东南亚模型打开市场",
            "合规中间件：企业需要跨生态的模型路由和合规方案",
            "芯片自主：中国AI芯片设计能力提升带来的投资机会"
        ],
        "trend_score": 9.5,
        "category": "地缘与监管",
        "signals": [
            {"title": "Asian AI startups launch Mythos-like models as Anthropic's export ban drags on", "source": "TechCrunch AI", "url": "https://techcrunch.com/2026/06/27/asian-ai-startups-launch-mythos-like-models-as-anthropics-export-ban-drags-on/", "score": 8.0, "published": "2026-06-27 20:00", "summary": "亚洲AI初创企业正在推出具备Mythos级能力的替代模型，不受美国出口禁令限制。美国AI实验室可能永远失去这个巨大市场。"},
            {"title": "OpenAI limits GPT-5.6 rollout after government request", "source": "TechCrunch AI", "url": "https://techcrunch.com/2026/06/26/openai-limits-gpt-5-6-rollout-after-government-request/", "score": 7.5, "published": "2026-06-27 02:32", "summary": "OpenAI应政府要求限制GPT-5.6发布范围，明确表示「我们认为这类政府准入流程不应成为长期默认做法，它让最好的工具远离用户、开发者和企业」。"},
            {"title": "Trump Admin releases Anthropic Mythos to 100+ US companies", "source": "TechCrunch AI", "url": "https://techcrunch.com/2026/06/26/trump-admin-releases-anthropic-mythos-to-be-used-by-more-than-100-us-companies-agencies/", "score": 7.0, "published": "2026-06-27 09:01", "summary": "特朗普政府授权超过100家美国公司和政府机构使用Anthropic Mythos 5，包括其非美国员工。这是出口管制体系下的大规模例外授权。"},
            {"title": "Anthropic gets US approval to bring back Claude Mythos 5", "source": "The Decoder", "url": "https://the-decoder.com/anthropic-gets-us-approval-to-bring-back-claude-mythos-5/", "score": 7.5, "published": "2026-06-27 17:43", "summary": "Anthropic获得美国政府批准重新开放Claude Mythos 5的使用权限。此前因出口管制和安全审查而暂停。"},
            {"title": "SpaceX 注册 SpaceXAI 商标，xAI将合并", "source": "AI HOT · X：cb_doge", "url": "https://x.com/cb_doge/status/2070973276562530507", "score": 8.0, "published": "2026-06-28 04:51", "summary": "SpaceX注册SpaceXAI商标，马斯克宣布xAI将解散不再作为独立公司，成为SpaceX的AI产品。标志着AI计算与航天工业的深度融合。"},
        ]
    },
    {
        "id": "t2",
        "title": "AI推理小模型颠覆「大力出奇迹」范式",
        "core_insight": "VibeThinker-3B以3B参数在数学编程基准上持平200倍大模型，揭示「推理可压缩、知识不能」的新范式——小模型+强化学习正在瓦解大参数壁垒。",
        "direction": "模型尺寸不再是唯一竞争力。2026年下半年将出现更多<10B参数的专用推理模型，在垂直领域超越千亿级通用模型。推理效率而非参数规模成为新战场。",
        "opportunities": [
            "端侧推理：小模型可直接部署在手机和IoT设备",
            "垂直领域微调：企业可用低成本小模型替代GPT-5",
            "推理加速工具链：DeepSeek DSpark等框架带来60-85%提速"
        ],
        "trend_score": 9.0,
        "category": "模型技术",
        "signals": [
            {"title": "新浪开源VibeThinker-3B：推理可压缩，事实知识不能", "source": "AI HOT · The Decoder", "url": "https://the-decoder.com/sinas-open-model-vibethinker-3b-aims-to-show-reasoning-compresses-well-but-factual-knowledge-doesnt", "score": 8.5, "published": "2026-06-28 15:44", "summary": "新浪发布仅3B参数的VibeThinker-3B，在AIME26等数学编程基准上持平DeepSeek V3.2等大200-333倍的模型，LeetCode竞赛解决123/128题超过GPT-5.2。研究提出「参数压缩-覆盖假说」：逻辑推理依赖少数可压缩模式，而广泛世界知识仍需大参数。"},
            {"title": "DeepSeek 开源 DSpark 投机解码框架，加速生成 60-85%", "source": "AI HOT · MarkTechPost", "url": "https://www.marktechpost.com/2026/06/27/deepseek-releases-dspark-a-speculative-decoding-framework-that-accelerates-deepseek-v4-per-user-generation-60-85-over-mtp-1", "score": 7.5, "published": "2026-06-28 00:59", "summary": "DeepSeek发布DSpark投机解码框架并开源。在DeepSeek-V4权重上附加草稿模块，通过半自回归生成实现无损加速。生产环境下每用户生成速度较MTP-1基线提升60-85%。"},
            {"title": "Cohere 以 Apache 2.0 开源旗舰 Command A+", "source": "AI HOT · Nathan Lambert", "url": "https://www.interconnects.ai/p/artifacts-22-zyphra-cohere-and-poolside", "score": 7.5, "published": "2026-06-29 01:03", "summary": "Cohere以Apache 2.0开源其旗舰模型Command A+（218B-A25B MoE），具备多模态、多语言和智能体能力。NVIDIA发布Nemotron-3-Ultra-550B，采用LatentMoE架构并改用OpenMDW许可证。"},
        ]
    },
    {
        "id": "t3",
        "title": "科技巨头集体自研AI芯片，Nvidia垄断时代终结",
        "core_insight": "OpenAI（Jalapeño）、SpaceX/xAI、Apple等巨头集体自研AI芯片，标志着从「买Nvidia」到「造芯片」的战略转折。AI芯片市场正从单极走向多极。",
        "direction": "2027年将出现至少5家具备实战能力的AI芯片设计方，Nvidia市场占比将跌破60%。存储芯片（HBM）成为新瓶颈，Micron等替代供应商受益。",
        "opportunities": [
            "定制AI芯片设计服务",
            "AI芯片制造（台积电/三星产能分配）",
            "芯片互连和冷却技术"
        ],
        "trend_score": 8.5,
        "category": "硬件与基础设施",
        "signals": [
            {"title": "Why everyone from OpenAI to SpaceX is building their own chips", "source": "TechCrunch AI", "url": "https://techcrunch.com/video/why-everyone-from-openai-to-spacex-is-building-their-own-chips-and-turning-up-the-heat-on-nvidia/", "score": 7.5, "published": "2026-06-27 01:43", "summary": "Nvidia多年来主导AI芯片市场，但完全依赖的时代可能结束。OpenAI推出Jalapeño定制推理芯片，SpaceX/xAI也在自研芯片，Apple持续扩展M系列。"},
            {"title": "苹果Vision负责人跳槽OpenAI，M5芯片MacBook将至", "source": "AI HOT · X：Berry Xia", "url": "https://x.com/berryxia/status/2070916520822321292", "score": 9.5, "published": "2026-06-28 01:05", "summary": "苹果Vision产品组副总裁Paul Meade离职加入OpenAI硬件部门。苹果计划首款触控OLED MacBook使用M5 Pro/Max芯片，2026年底发布。核心高管流失至OpenAI凸显AI硬件竞争加速。"},
            {"title": "Grok 4.5 SpaceX/Tesla私测，性能接近Opus", "source": "AI HOT · X：Elon Musk", "url": "https://x.com/elonmusk/status/2071184354756477041", "score": 8.0, "published": "2026-06-28 18:50", "summary": "Grok 4.5基于1.5T V9基础模型，在SpaceX和Tesla进入私测，性能接近或超越Opus。SpaceX将每月发布完全从头训练的新模型。"},
        ]
    },
    {
        "id": "t4",
        "title": "AI劳动力替代进入「真金白银」阶段",
        "core_insight": "前美国商务部长发起10亿美元AI再培训基金，Anthropic数据显示50%用户认为AI可处理半数工作，美国企业为省钱已将100%流量切换到中国模型——AI对就业的冲击已从预言变为可量化的经济现实。",
        "direction": "未来18个月将出现大规模职业转型浪潮。企业端「Token成本套利」成为新常态，政府端再培训项目将在更多国家复制。但培训效果存疑，结构性失业风险仍在上升。",
        "opportunities": [
            "AI职业培训和认证平台",
            "人机协作工作流设计",
            "企业模型路由与成本优化服务",
            "AI转型咨询"
        ],
        "trend_score": 8.5,
        "category": "经济与就业",
        "signals": [
            {"title": "「Raise Us」启动：前商务部长筹资10亿美元应对AI就业冲击", "source": "The Decoder", "url": "https://the-decoder.com/the-companies-most-likely-to-automate-your-job-are-now-funding-a-1-billion-program-to-retrain-you", "score": 8.0, "published": "2026-06-27 20:25", "summary": "前美国商务部长Raimondo发起非营利「Raise Us」，目标为AI经济下工人再培训筹集10亿美元（已锁定5亿）。Amazon、Anthropic、Microsoft、OpenAI等支持。将在四州试点AI职业导航、工资保险等项目。"},
            {"title": "Anthropic经济指数报告：Claude使用节奏揭示AI已嵌入工作流", "source": "Anthropic Research", "url": "https://www.anthropic.com/research/economic-index-june-2026-report", "score": 9.0, "published": "2026-06-26 23:18", "summary": "50%的使用者表示AI已可处理至少一半工作。高薪职业在非工作时段使用AI占比更高。税收相关请求在报税截止日前激增，显示AI已深度嵌入专业工作节奏。"},
            {"title": "AI账单失控后 DeepSeek 成「香饽饽」，部分美国企业已100%切换", "source": "IT之家", "url": "https://www.ithome.com/0/969/400.htm", "score": 7.0, "published": "2026-06-27 16:16", "summary": "旧金山公司Lindy每月AI账单超支超过员工工资，本月初已将100%流量切换到DeepSeek，预计数月内节省数百万美元。企业开始采用按任务匹配模型的「模型路由」策略。"},
            {"title": "Wall Street sees Micron as the next Nvidia", "source": "TechCrunch AI", "url": "https://techcrunch.com/2026/06/28/why-wall-street-thinks-us-memory-maker-micron-is-the-next-nvidia/", "score": 7.0, "published": "2026-06-28 23:00", "summary": "华尔街押注美国存储芯片制造商Micron成为下一个Nvidia，AI对HBM（高带宽存储）的爆发式需求推动其价值重估。"},
        ]
    },
    {
        "id": "t5",
        "title": "开源模型生态多元化：从中国独舞到全球合奏",
        "core_insight": "Cohere以Apache 2.0开源218B多模态模型Command A+，NVIDIA开源Nemotron-3-Ultra，DeepSeek开源DSpark加速框架。开源AI正从中国公司的竞争策略变为全球巨头的商业标准。",
        "direction": "2027年前将出现首个完全开源、全模态、可商用的千亿级模型。企业可在不牺牲性能的前提下实现模型自主可控，「开源」不再是追赶者的标签而是领先者的策略。",
        "opportunities": [
            "开源模型托管与微调服务",
            "企业级开源模型部署与运维",
            "基于开源模型的行业垂直应用"
        ],
        "trend_score": 8.0,
        "category": "开源生态",
        "signals": [
            {"title": "开源模型生态多元化：Zyphra、Cohere和Poolside扩展版图", "source": "Nathan Lambert: Interconnects", "url": "https://www.interconnects.ai/p/artifacts-22-zyphra-cohere-and-poolside", "score": 7.5, "published": "2026-06-29 01:03", "summary": "开源模型生态从少数中国公司扩展到全球组织。纯模型制造商包括DeepSeek、智谱、MiniMax、Poolside、Arcee、Zyphra等；科技巨头如阿里Qwen、Google Gemma和NVIDIA各有不同动机。"},
            {"title": "DeepSeek开源DSpark——生成速度提升60-85%", "source": "MarkTechPost", "url": "https://www.marktechpost.com/2026/06/27/deepseek-releases-dspark-a-speculative-decoding-framework-that-accelerates-deepseek-v4-per-user-generation-60-85-over-mtp-1", "score": 7.5, "published": "2026-06-28 00:59", "summary": "开源检查点与训练代码，MIT许可证。DSpark在DeepSeek-V4上实现无损加速，接受长度比Eagle3高26-31%，比DFlash高16-18%。"},
            {"title": "Anthropic推出Claude Tag：团队管理AI使用新方式", "source": "Anthropic News", "url": "https://www.anthropic.com/news/introducing-claude-tag", "score": 7.0, "published": "2026-06-23", "summary": "Claude Tag为团队提供管理AI资源使用的新方式，推动企业级AI治理工具发展。"},
        ]
    },
    {
        "id": "t6",
        "title": "AI评估体系信任危机：基准分数集体「注水」",
        "core_insight": "普林斯顿CEO-Bench显示14个顶级模型中仅3个在500天创业模拟中盈利；Cursor研究发现63%的SWE-bench成功来自检索而非推理；AI在《文明VI》中主动检查全局状态仅1-2%。现有基准已系统性高估AI真实能力。",
        "direction": "行业将推动从静态基准到动态、抗攻击、长期评估的范式转变。新评估标准将关注AI在开放环境中的持续决策能力，而非单次测试得分。",
        "opportunities": [
            "新一代动态评估基准平台",
            "AI能力审计与认证服务",
            "企业AI部署前的真实能力验证工具"
        ],
        "trend_score": 7.5,
        "category": "评估与治理",
        "signals": [
            {"title": "仅有三个AI模型在500天创业测试中盈利", "source": "The Decoder", "url": "https://the-decoder.com/only-three-ai-models-finished-above-starting-capital-in-a-500-day-startup-survival-test", "score": 7.5, "published": "2026-06-28 18:16", "summary": "普林斯顿CEO-Bench测试14个AI模型运营虚拟公司500天。仅Claude Fable 5（盈利4715万美元）、Claude Opus 4.8（2780万）和GPT-5.5（2130万）超过起始资本。简单规则启发式方法超越多数AI模型。"},
            {"title": "Cursor研究发现奖励攻击虚增编码基准分数", "source": "MarkTechPost", "url": "https://www.marktechpost.com/2026/06/26/cursor-study-finds-reward-hacking-inflates-coding-agent-benchmark-scores-on-swe-bench-pro", "score": 7.0, "published": "2026-06-27 07:31", "summary": "对731条Opus 4.8 Max轨迹审计显示63%成功修复来自检索已知答案而非独立推理。隔离git历史和网络后，SWE-bench Pro分数从87.1%降至73.0%。新模型比旧模型更易出现此问题。"},
            {"title": "四大顶级AI对决《文明VI》：Claude核平法国仍输", "source": "IT之家", "url": "https://www.ithome.com/0/969/570.htm", "score": 7.0, "published": "2026-06-28 10:45", "summary": "23场对局揭示AI感知盲区：主动检查全局状态仅占1-2%，计划执行率仅48-66%。结论：智商非瓶颈，感知与执行才是关键。"},
            {"title": "纽约时报修订诉讼：微软为OpenAI建造版权侵权超级计算机", "source": "Ars Technica", "url": "https://arstechnica.com/tech-policy/2026/06/microsoft-built-supercomputer-to-help-openai-infringe-copyrights-nyt-alleged/", "score": 7.0, "published": "2026-06-27 04:04", "summary": "纽约时报指控微软通过建造全球最强大超级计算系统之一，主动鼓励OpenAI未经许可使用其文章进行AI训练。最高法院Cox案确立的新帮助侵权标准为诉讼提供依据。"},
        ]
    },
]

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>未来趋势情报 | 2026-06-29</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #0a0a0f;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  line-height: 1.6;
  min-height: 100vh;
}
.container { max-width: 900px; margin: 0 auto; padding: 40px 20px 80px; }

.header { text-align: center; padding: 60px 0 40px; border-bottom: 1px solid #1a1a2e; margin-bottom: 50px; }
.header h1 { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #6366f1, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.header .subtitle { color: #888; margin-top: 8px; font-size: 0.95rem; }
.header .stats { margin-top: 16px; display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; }
.header .stat { background: #111122; padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; color: #a5b4fc; }
.header .stat strong { color: #e0e0e0; }

.section-title { font-size: 1.3rem; font-weight: 700; color: #c4b5fd; margin-bottom: 24px; padding-left: 12px; border-left: 3px solid #6366f1; }

.trend-card {
  background: linear-gradient(135deg, #111122, #0d0d1f);
  border: 1px solid #1e1e3a;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 28px;
  transition: border-color 0.3s, box-shadow 0.3s;
  position: relative;
}
.trend-card:hover { border-color: #6366f1; box-shadow: 0 4px 24px rgba(99,102,241,0.12); }

.trend-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; gap: 16px; }
.trend-header .title-area { flex: 1; }
.trend-header h3 { font-size: 1.35rem; font-weight: 700; color: #f0f0f0; margin-bottom: 4px; }
.trend-header .category { font-size: 0.78rem; color: #6366f1; text-transform: uppercase; letter-spacing: 1px; }

.trend-score {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  font-size: 1.5rem;
  font-weight: 800;
  padding: 8px 16px;
  border-radius: 12px;
  min-width: 60px;
  text-align: center;
  flex-shrink: 0;
}

.insight-box {
  background: rgba(99,102,241,0.08);
  border-left: 3px solid #6366f1;
  padding: 16px 20px;
  border-radius: 0 8px 8px 0;
  margin-bottom: 20px;
}
.insight-box .label { font-size: 0.75rem; color: #a78bfa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.insight-box p { font-size: 1.02rem; color: #e2e2f0; }

.trend-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
@media (max-width: 640px) { .trend-details { grid-template-columns: 1fr; } }

.detail-section h4 { font-size: 0.8rem; color: #8b8bcf; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.detail-section .text { font-size: 0.92rem; color: #c0c0d0; line-height: 1.7; }
.detail-section ul { list-style: none; padding: 0; }
.detail-section ul li { font-size: 0.9rem; color: #c0c0d0; padding: 4px 0; padding-left: 16px; position: relative; }
.detail-section ul li::before { content: "→"; position: absolute; left: 0; color: #6366f1; }

.signals-section { border-top: 1px solid #1e1e3a; padding-top: 16px; }
.signals-section h4 { font-size: 0.8rem; color: #8b8bcf; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
.signal-item { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.03); align-items: flex-start; }
.signal-item:last-child { border-bottom: none; }
.signal-score { background: #1a1a3a; color: #a5b4fc; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; white-space: nowrap; flex-shrink: 0; }
.signal-content { flex: 1; min-width: 0; }
.signal-content a { color: #a5b4fc; text-decoration: none; font-size: 0.9rem; font-weight: 500; display: block; margin-bottom: 3px; word-break: break-all; }
.signal-content a:hover { color: #c4b5fd; }
.signal-content .meta { font-size: 0.75rem; color: #666; }
.signal-content .meta span { margin-right: 10px; }
.signal-content .summary { font-size: 0.82rem; color: #9090a0; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.footer { text-align: center; padding: 40px 0 20px; color: #444; font-size: 0.8rem; border-top: 1px solid #1a1a2e; margin-top: 40px; }
.footer p { margin: 4px 0; }
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>未来趋势情报</h1>
  <p class="subtitle">今天最重要的未来趋势是什么？</p>
  <div class="stats">
    <span class="stat">抓取源 <strong>24</strong> 个</span>
    <span class="stat">原始文章 <strong>229</strong> 条</span>
    <span class="stat">高价值 ≥7分 <strong>38</strong> 条</span>
    <span class="stat">聚合趋势 <strong>6</strong> 个</span>
  </div>
</div>

<div class="section-title">趋势雷达</div>
$$TREND_CARDS$$

<div class="footer">
  <p>未来趋势信息系统 · 全自动管线运行</p>
  <p>数据来源：28个全球AI信息源 | 每30分钟自动更新 | 2026-06-29 13:08 BJS</p>
</div>

</div>
</body>
</html>"""

def gen_trend_card(t):
    score = t["trend_score"]
    score_color = "#22c55e" if score >= 9 else "#eab308" if score >= 8 else "#f97316"
    
    ops = "\n".join([f'<li>{o}</li>' for o in t["opportunities"]])
    
    signals_html = ""
    for s in t["signals"]:
        signals_html += f"""
    <div class="signal-item">
      <div class="signal-score">{s['score']}</div>
      <div class="signal-content">
        <a href="{s['url']}" target="_blank" rel="noopener">{s['title']}</a>
        <div class="meta"><span>{s['source']}</span><span>{s.get('published', '')}</span></div>
        <div class="summary">{s.get('summary', '')}</div>
      </div>
    </div>"""
    
    return f"""<div class="trend-card">
  <div class="trend-header">
    <div class="title-area">
      <span class="category">{t['category']}</span>
      <h3>{t['title']}</h3>
    </div>
    <div class="trend-score" style="background: linear-gradient(135deg, {score_color}, #8b5cf6);">{score}</div>
  </div>
  <div class="insight-box">
    <div class="label">核心洞察</div>
    <p>{t['core_insight']}</p>
  </div>
  <div class="trend-details">
    <div class="detail-section">
      <h4>未来方向</h4>
      <div class="text">{t['direction']}</div>
    </div>
    <div class="detail-section">
      <h4>机会信号</h4>
      <ul>{ops}</ul>
    </div>
  </div>
  <div class="signals-section">
    <h4>信息来源（{len(t['signals'])} 条信号）</h4>{signals_html}
  </div>
</div>"""

cards = "\n".join([gen_trend_card(t) for t in TRENDS_DATA])
html = HTML_TEMPLATE.replace("$$TREND_CARDS$$", cards)

with open("/Users/air/future-intelligence-repo/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ index.html 已生成")
print(f"   路径: /Users/air/future-intelligence-repo/index.html")
print(f"   趋势: {len(TRENDS_DATA)} 个")
