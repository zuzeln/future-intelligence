---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: f158224a48fbb356097a06a36e843bb1_4b81b141750d11f1aabe5254007bceed
    ReservedCode1: wlvleuuDorRyS306njzO5LO9EgE6NGeTcJmTCN93j8TdSxG5uefvMfIO5Rr185suji+wwYieVTvDzuLtK//c3dXAF6cKGPoLPq86A/APB8+taHHeot1l4GkvGie8NldA0f4+YXy1PyfegacbuYBY4tJE/q00GpZj39FEeuJFQ0jqmzJ9cFzu4gV0Y+k=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: f158224a48fbb356097a06a36e843bb1_4b81b141750d11f1aabe5254007bceed
    ReservedCode2: wlvleuuDorRyS306njzO5LO9EgE6NGeTcJmTCN93j8TdSxG5uefvMfIO5Rr185suji+wwYieVTvDzuLtK//c3dXAF6cKGPoLPq86A/APB8+taHHeot1l4GkvGie8NldA0f4+YXy1PyfegacbuYBY4tJE/q00GpZj39FEeuJFQ0jqmzJ9cFzu4gV0Y+k=
---

# Future Intelligence 更新标准

> 最后修订：2026-07-01 | 所有条目必须逐条通过本标准的每项检查

---

## 一、字段架构

### 必须字段
每个条目必须包含以下字段，缺一不可：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | number | 递增整数，取现有最大 id + 1 |
| date | string | 格式 `YYYY-MM-DD`，操作当天日期 |
| title | string | 因果叙事标题 |
| coreInsight | string | 核心洞察 |
| whyItMatters | string | 为什么重要 |
| direction | string | 方向预测 |
| opportunities | string[] | 机会列表，**必须是数组**，3-4 条 |
| risks | string[] | 风险列表，**必须是数组**，2 条 |
| signals | object[] | 信号列表，每个对象含 source / time / title / summary / url |

### 字段类型校验（强制）
- `opportunities` 和 `risks` **必须是数组**（`isinstance(x, list)`），**严禁**写成字符串
- `signals` 必须是对象数组
- 写入前用 `json.dump(ensure_ascii=False, indent=2)` 序列化

---

## 二、标题标准

### 必须满足
- **因果叙事**：标题必须揭示事件背后的因果链条，不能只描述现象
- **具体主体**：必须出现具体公司名/产品名/政策名
- **行业信号**：标题本身应传递行业趋势信号

### 禁用表述
- "观测到集中信号"
- "发现多个信号"
- "出现了一系列信号"
- 任何模板化空泛前缀

### 正例
- 「苹果弃用NVIDIA之后转向自研推理芯片，暴露云厂商算力自主化加速」
- 「Anthropic MCP 协议获 AWS/GCP 双云原生支持，智能体基础设施走向标准化」

---

## 三、各字段字数与深度标准

### coreInsight（核心洞察）
- **字数**：120-213 字
- **内容要求**：因果推演，用具体数据/产品名支撑，不得泛泛而谈
- 需回答："这个趋势发生的根本原因是什么？"

### whyItMatters（为什么重要）
- **内容要求**：从行业痛点做因果推演，串联多条 signals 中的信号
- 需回答："这个趋势为什么对从业者/投资者重要？"

### direction（方向预测）
- **字数**：80-110 字
- **内容要求**：给出多条具体时间线预测，每条含时间节点
- 需回答："这个趋势在近期/中期/长期会如何演变？"

### opportunities（机会）
- **数量**：3-4 条
- 每条 1-2 句，给出具体可操作方向

### risks（风险）
- **数量**：统一 2 条
- 每条 1-2 句，从趋势反面推导

---

## 四、格式规范

### 中文引号
- 统一使用「」（U+300C / U+300D），**禁止**使用 ASCII 双引号 `""` 或英文引号 `“”`

### 去重
- 管线追加前按 `title` 精确匹配去重
- 标题变化后的旧低质量版本需手动清理，避免重复

### 数组不可变性
- 管线追加**只追加新条目**，不得修改已有条目的任何字段
- 已有条目 ID、日期、内容全部不可变

---

## 五、部署流程

1. 管线运行 → 追加新条目到 `data.json`
2. `git add data.json && git commit -m "auto: pipeline update YYYY-MM-DD HH:MM"` && `git push origin main`
3. GitHub Pages 自动从 main 分支部署到 `zuzeln.github.io/future-intelligence/`
4. 浏览器端通过 5 分钟轮询 `data.json?_=timestamp` 感知更新

---

## 六、验收清单

每次追加新条目后，逐项确认：

- [ ] `opportunities` 和 `risks` 是数组，不是字符串
- [ ] 中文引号使用「」
- [ ] 标题为因果叙事，无禁用表述
- [ ] coreInsight 120-213 字
- [ ] direction 80-110 字
- [ ] risks 恰好 2 条
- [ ] signals 含 source / time / title / summary / url
- [ ] 新条目 id 递增，date 为当天
- [ ] Git 已提交并推送
- [ ] 浏览器端已验证新条目可点击渲染
*（内容由AI生成，仅供参考）*
