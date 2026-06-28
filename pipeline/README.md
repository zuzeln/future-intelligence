# Future Intelligence 数据抓取管线

从 28 个信息源批量抓取 AI 领域最新文章，生成网站数据。

## 使用方式

```bash
cd pipeline
pip install -r requirements.txt
python fetch_all.py    # 抓取所有源
python generate_site.py # 生成网站
```

## 输出

- `pipeline/data/raw_articles.json` — 原始抓取结果（含每源抓取状态）
- `index.html`（仓库根目录）— 更新后的网站

## 信息源

28 个信息源覆盖 AI 公司、AI 媒体、聚合平台、研究机构、投资机构、专家博客和基础设施七个类别。
