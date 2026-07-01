# Future Intelligence 每30分钟自动更新策略

> 版本：v1.0 | 分析日期：2026-07-01 | 适用架构：index.html + data.json 分离式

---

## 1. 当前架构概况

### 1.1 管线脚本一览

| 脚本 | 职责 | 输入 | 输出 | 状态 |
|---|---|---|---|---|
| `fetch_all.py` | 从 28 个源抓取文章 | RSS/HTML/API | `pipeline/data/raw_articles.json` | 可独立运行 |
| `full_pipeline.py` | 全流程管线（**覆盖模式**） | 28 源 → 评分 → 聚类 → 生成 | `scored_articles.json` + `trends.json` + **覆盖 index.html 内嵌 ALL_ITEMS** | ⚠️ 覆盖模式，不能用于增量更新 |
| `append_pipeline.py` | 全流程管线（**追加模式**） | 同上，但读出现有 ALL_ITEMS 后追加 | 同上 + **追加到 index.html 内嵌 ALL_ITEMS** | ✅ 追加模式，但目标文件已过时 |
| `generate_trends.py` | 从 `scored_articles.json` 生成趋势 | 硬编码路径读取 scored_articles.json | `trends.json` | 手动触发型 |
| `build_site.py` | 静态站点生成 | 硬编码 TRENDS_DATA | 覆盖生成 index.html | 已废弃（被动态 index.html 替代） |
| `lightweight_pipeline.py` | 轻量版管线 | 未知 | 未知 | 备选方案 |

### 1.2 前端数据加载（当前）

```
index.html
  └── fetch('data.json')  ← ALL_ITEMS 数据源
       └── 数据格式：JSON 数组，每个条目含 id / date / title / coreInsight /
                        whyItMatters / direction / opportunities / risks / signals
```

**关键变化**：此前 ALL_ITEMS 硬编码在 index.html 的 `<script>` 中，`full_pipeline.py` 和 `append_pipeline.py` 通过正则替换 `var ALL_ITEMS = [...];` 来更新数据。优化后 index.html 改为 `fetch('data.json')` 异步加载，管线脚本需要适配这一新架构。

### 1.3 管线 7 步流程（以 full_pipeline.py / append_pipeline.py 为准）

```
Step 1: fetch_all()         28 源抓取 → 去重 + 3天时效过滤
Step 2: score_articles()    News Score 评分 (0-10)，≥7 分进入聚类
Step 3: cluster_trends()    关键词匹配聚类（12 个主题）
Step 4: generate_trends()   趋势标题/洞察/方向/机会/风险生成
Step 5: filter_trends()     按 trendScore ≥7 过滤，保留 3-8 个
Step 6: 写入数据            scored_articles.json + trends.json
Step 7: 更新网站            目前写 index.html 内嵌 ALL_ITEMS ← **需要改造**
Step 8: git commit + push   自动部署
```

---

## 2. 流程分析：自动化可行性

### 2.1 全自动步骤（无需人工介入）

| 步骤 | 说明 |
|---|---|
| **Step 1 抓取** | 从 28 个源自动抓取，含错误处理和已知不可用源跳过逻辑。部分源可能超时/403→静默跳过，不影响整体。 |
| **Step 2 评分** | 纯关键词规则评分，确定性算法，无外部 API 依赖。 |
| **Step 3 聚类** | 纯关键词匹配聚类，确定性算法。 |
| **Step 4-5 趋势生成** | 模板驱动 + 随机选择标题前缀。文本由 Python 代码自动生成，无 LLM API 依赖。 |
| **Step 6 数据写入** | 纯文件 I/O。 |
| **Step 8 Git 部署** | subprocess 调用 git。 |

### 2.2 需要人工判断的步骤

| 步骤 | 原因 | 当前处理 |
|---|---|---|
| **趋势质量审核** | 模板生成的趋势标题和洞察可能不够精准、重复或与现有条目语义高度重叠 | 未处理——管线直接追加 |
| **重复条目判定** | append_pipeline 仅按标题全等去重，无法检测「同一事件不同描述」的语义重复 | 仅字符串精确匹配 |
| **日期边界** | 跨日运行时 TODAY 变量变化，可能出现同一天多次追加 | 按日期字段分组时自然处理 |

### 2.3 风险评估

| 风险 | 严重度 | 缓解措施 |
|---|---|---|
| 数据源大面积宕机 | 中 | pipeline 抓取为空时直接终止，不覆盖现有数据 |
| 生成低质量趋势 | 中 | trendScore < 7 自动过滤；可后续加入标题相关性校验 |
| index.html 架构不匹配 | **高** | 当前管线写 index.html 内嵌 ALL_ITEMS，但页面已改为 data.json 加载。**必须适配**。 |
| 重复条目 | 低 | 标题精确去重已实现 |
| data.json 损坏 | 低 | Git 历史可回滚；可增加写入前备份 |
| Browser 缓存旧 data.json | 中 | 可用 URL 参数 ?v=timestamp 破缓存；或 Service Worker 策略 |

---

## 3. 改造方案：适配 data.json 架构

### 3.1 核心变更

**将管线 Step 7 从「正则替换 index.html 内嵌 ALL_ITEMS」改为「追加写入 data.json」**。

旧逻辑（full_pipeline.py / append_pipeline.py）：
```
正则匹配 index.html → 替换 var ALL_ITEMS = [...]; → 写回 index.html
```

新逻辑：
```
读取 data.json → 解析现有条目 → 追加新趋势 → 写回 data.json
```

### 3.2 data.json 写入逻辑

index.html 期望的 data.json 是一个**纯数组**（不是 `{trends: [...]}` 这样的包装对象），每个元素的结构如下：

```json
{
  "id": 101,
  "date": "2026-07-01",
  "title": "...",
  "coreInsight": "...",
  "whyItMatters": "...",
  "direction": "...",
  "opportunities": ["...", "..."],
  "risks": ["...", "..."],
  "signals": [
    {
      "source": "TechCrunch",
      "time": "7/1 14:30",
      "title": "...",
      "summary": "...",
      "url": "https://..."
    }
  ]
}
```

### 3.3 字段映射（pipeline 输出 → data.json 条目）

pipeline 趋势对象（来自 `generate_trend()`）与 data.json 条目的字段对应：

| pipeline 字段 | data.json 字段 | 说明 |
|---|---|---|
| `title` | `title` | 直接映射 |
| `coreInsight` | `coreInsight` | 直接映射 |
| `whyItMatters` | `whyItMatters` | 直接映射 |
| `direction` | `direction` | 直接映射 |
| `opportunities` | `opportunities` | 直接映射（字符串数组） |
| `risks` | `risks` | 直接映射（字符串数组） |
| `signals` | `signals` | 直接映射（对象数组） |
| `trendScore` | — | data.json 不使用此字段，可保留 |
| — | `id` | **需要自动分配**（现有最大 id + 1） |
| — | `date` | **需要自动填充**（当天日期 YYYY-MM-DD） |

### 3.4 需改造的脚本

**推荐改造 `append_pipeline.py`**（因其已具备追加逻辑），主要改动点：

1. **Step 6 替换**：将 `read_existing_items()` 从「正则解析 index.html」改为「读取并解析 data.json」
2. **Step 7 替换**：将 `update_index_html_append()` 改为「构建新数组 → 写回 data.json」
3. **去重方式保持**：按 `title` 精确匹配去重
4. **id 分配**：`max(现有条目 id) + 1`
5. **data.json 写入**：`json.dump(array, f, ensure_ascii=False, indent=2)`（保持与现有格式一致：2 空格缩进）

**`full_pipeline.py` 不建议直接用于定时任务**，因为是覆盖模式会丢失历史数据。保留它用于手工全量重建。

### 3.5 新增：备份机制

在写入 data.json 之前自动备份：
```python
BACKUP_PATH = DATA_JSON_PATH + ".bak"
shutil.copy2(DATA_JSON_PATH, BACKUP_PATH)
```

写入失败时可以从 .bak 恢复。

---

## 4. 定时执行方案

### 4.1 推荐方案：macOS launchd（每30分钟）

使用 launchd 是 macOS 原生的定时任务机制，比 cron 更适合桌面环境。

**Plist 配置文件**（`~/Library/LaunchAgents/com.futureintelligence.update.plist`）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.futureintelligence.update</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/air/future-intelligence-repo/pipeline/append_pipeline.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/air/future-intelligence-repo/pipeline</string>

    <key>StartInterval</key>
    <integer>1800</integer>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/Users/air/future-intelligence-repo/pipeline/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/air/future-intelligence-repo/pipeline/logs/stderr.log</string>
</dict>
</plist>
```

**启动命令**：
```bash
# 创建日志目录
mkdir -p /Users/air/future-intelligence-repo/pipeline/logs

# 加载任务
launchctl load ~/Library/LaunchAgents/com.futureintelligence.update.plist

# 查看状态
launchctl list | grep futureintelligence

# 停止任务
launchctl unload ~/Library/LaunchAgents/com.futureintelligence.update.plist
```

### 4.2 备选方案：cron

```bash
*/30 * * * * cd /Users/air/future-intelligence-repo/pipeline && /usr/bin/python3 append_pipeline.py >> logs/cron.log 2>&1
```

⚠️ macOS 上 cron 需要给终端/ Python 完整磁盘访问权限，否则可能因沙盒限制无法访问网络和文件。

### 4.3 手动执行

```bash
cd /Users/air/future-intelligence-repo/pipeline
python3 append_pipeline.py
```

---

## 5. 安全追加策略

### 5.1 不覆盖已有条目

```
流程：
  1. 读取 data.json → 解析出所有现有条目
  2. 提取现有标题集合 existing_titles
  3. 新趋势逐个检查 title NOT IN existing_titles → 才追加
  4. 写入 data.json = 现有条目 + 仅新增条目
```

### 5.2 去重粒度

| 策略 | 实现 | 效果 |
|---|---|---|
| **标题精确匹配** | `new_title in existing_titles` | 当前已实现，覆盖大部分场景 |
| **URL 去重（信号层面）** | 暂未实现 | 可避免同一新闻源的不同标题版本 |
| **语义去重** | 暂未实现 | 需要 embedding 或 LLM，复杂度高，暂不纳入 |

### 5.3 格式一致性保证

- **读取**：`json.load()` 读取现有 data.json
- **新条目构建**：使用 Python dict，字段名与 data.json 定义一致
- **追加到数组末尾**：`existing_data.append(new_item)`
- **写入**：`json.dump(existing_data, f, ensure_ascii=False, indent=2)`
- **验证**：写入后立即 `json.load()` 重新读取并校验数组长度 = 原长度 + 新条目数

### 5.4 ID 分配策略

```python
# 取现有最大 id + 1
existing_ids = [item["id"] for item in existing_data]
next_id = max(existing_ids) + 1 if existing_ids else 101

for i, trend in enumerate(new_trends):
    trend["id"] = next_id + i
    trend["date"] = TODAY  # 格式 "YYYY-MM-DD"
```

---

## 6. 边界情况处理

### 6.1 抓取失败

pipeline 已有处理：
- 单个源超时/403 → 静默跳过，继续下一个
- 全部源失败（`len(articles) == 0`）→ 整个流程终止，**不修改 data.json**
- `aihot` API 失败 → 仅跳过该源

### 6.2 无新趋势

- 追加数量 `appended_count == 0` → 日志记录，跳过写入和 Git 操作
- 不更新 data.json（避免无意义的时间戳变更）

### 6.3 重复条目

- 标题精确匹配 → 跳过
- 趋势 score < 7 → 跳过
- 同一天多次运行 → 每次运行都会检查现有标题，不会重复追加

### 6.4 data.json 不存在或损坏

```python
try:
    with open(DATA_JSON_PATH, "r") as f:
        existing_data = json.load(f)
    if not isinstance(existing_data, list):
        raise ValueError("data.json 不是数组")
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    log(f"⚠️ data.json 读取失败: {e}，尝试从 .bak 恢复")
    # 尝试从备份恢复
    if os.path.exists(DATA_JSON_PATH + ".bak"):
        shutil.copy2(DATA_JSON_PATH + ".bak", DATA_JSON_PATH)
        # 重试读取
        with open(DATA_JSON_PATH, "r") as f:
            existing_data = json.load(f)
    else:
        log("❌ 无备份可用，终止")
        return
```

### 6.5 Git push 失败

- 文件已写入本地，数据不丢失
- 日志标记 `⚠️ Git push failed`
- 下次运行时 Git 会自动合并 commits

---

## 7. 页面感知新数据（刷新策略）

### 7.1 问题

index.html 在浏览器中打开后，`fetch('data.json')` 只在页面加载时执行一次。如果 data.json 被 pipeline 更新，已打开的页面不会自动刷新。

### 7.2 解决方案

**方案 A：浏览器端定时轮询（推荐，改动最小）**

在 index.html 的 JS 中增加轮询逻辑：

```javascript
// 每5分钟检查一次 data.json 是否有更新
var POLL_INTERVAL = 5 * 60 * 1000; // 5分钟
var lastDataLength = 0;

function pollForUpdates() {
    fetch('data.json?_=' + Date.now())
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.length !== lastDataLength) {
                // 数据有变化，重新加载
                ALL_ITEMS = data;
                groups = groupByDate(ALL_ITEMS);
                renderSidebar();
                if (activeItemId) renderMain();
                lastDataLength = data.length;
            }
        })
        .catch(function() { /* 静默失败 */ });
}

// 初始加载完成后开始轮询
setInterval(pollForUpdates, POLL_INTERVAL);
```

**方案 B：URL 参数缓存破坏**

每次加载 data.json 时追加 `?_v=timestamp` 参数，确保不命中浏览器缓存：

```javascript
fetch('data.json?_=' + Date.now())
```

**方案 C：用户手动刷新提示**

更轻量的方案：在页面 footer 显示「上次更新：YYYY-MM-DD HH:MM」，并在检测到新数据时显示浮动提示条「发现新趋势，点击刷新」。

### 7.3 推荐组合

- **方案 B（缓存破坏）**：在所有 `fetch('data.json')` 调用上追加时间戳参数
- **方案 A（轮询）**：每 5-10 分钟自动检查数据长度变化，变化时无刷新更新列表
- **方案 C（用户提示）**：作为轮询的视觉反馈

---

## 8. 执行计划（推荐步骤）

### 阶段一：改造管线脚本（约 1 小时）

1. 修改 `append_pipeline.py`：
   - 移除对 index.html 的正则操作（`read_existing_items()` / `update_index_html_append()`）
   - 新增 `read_data_json()` 函数：读取 data.json，返回条目列表 + 最大 id
   - 新增 `write_data_json()` 函数：现有条目 + 新条目 → 写回 data.json（含备份）
   - 去重逻辑保留标题精确匹配
   - ID 分配改为 `max_id + 1`
   - 日期字段自动填充 `TODAY`

2. 手动运行验证：`python3 append_pipeline.py`

### 阶段二：配置定时任务（约 15 分钟）

1. 创建 launchd plist 文件
2. 创建日志目录 `pipeline/logs/`
3. `launchctl load` 加载
4. 等待 30 分钟验证第一次自动执行

### 阶段三：前端刷新机制（约 30 分钟）

1. 在 index.html 中添加轮询逻辑
2. 添加 `?_t=` 参数破坏缓存
3. 本地测试：手动修改 data.json 后观察页面是否自动更新

### 阶段四：监控与优化（持续）

1. 检查 `pipeline/logs/stdout.log` 确认每次执行结果
2. 监控趋势质量——如果模板生成质量不佳，考虑引入 LLM 摘要
3. 如发现误追加或重复，从 Git 历史恢复 data.json

---

## 9. 风险与回滚

| 场景 | 回滚方式 |
|---|---|
| append_pipeline 写入错误数据 | `git checkout data.json` 恢复上一版本 |
| 脚本运行报错 | launchd 自动记录日志，不影响页面 |
| data.json 损坏 | 从 `.bak` 自动恢复；或 git checkout |
| 定时任务未触发 | 检查 `launchctl list`；检查日志；手动执行 |

---

## 10. 后续优化建议

1. **语义去重**：引入 sentence-transformers 计算标题余弦相似度，相似度 > 0.85 的视为重复
2. **LLM 增强**：趋势标题和洞察改用 LLM 生成，替代当前模板随机选择
3. **趋势衰减**：旧趋势的 trendScore 随时间递减，避免首页长期被同一主题占据
4. **索引页**：为 data.json 中的条目生成静态索引页，便于搜索引擎收录
5. **Webhook 通知**：新趋势追加后通过 webhook 推送到企业微信/钉钉
6. **Docker 化**：将管线打包为 Docker 镜像，便于部署到服务器（脱离 macOS 定时任务依赖）
