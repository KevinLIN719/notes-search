# notes-search

个人讲义库的**中文全文检索 + 语义检索**服务。

> **状态**：🚧 开发中（2026-10 起）
> **目标交付**：2026-11-15

---

## ⚠️ 关于 `notes/` 目录

**这个仓库不包含任何讲义内容。**

`notes/` 被 `.gitignore` 排除，原因有两个：

1. **版权**：讲义是课程材料，版权属于老师与学校，不应随代码一起分发
2. **隐私与体积**：个人笔记可能含个人信息，且 PDF 体积较大

**要自己运行本项目，请把你的讲义（PDF / Markdown）放进 `notes/` 目录后再执行 `ingest`。**

```bash
mkdir -p notes
cp /path/to/your/lectures/*.pdf notes/
notes-search ingest ./notes --course CS3402
```

---

## 快速开始

```bash
git clone https://github.com/KevinLIN719/notes-search.git
cd notes-search
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e .
notes-search --help
```

---

## 架构

```
┌─────────────┐
│  PDF / MD   │
└──────┬──────┘
       │ ① 解析（PyMuPDF / markdown）
       ▼
┌─────────────┐
│  分块 chunk  │  ② 按段落/句子边界滑窗切分，带元数据
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ SQLite      │   │ embedding   │   │ 自造倒排索引 │
│ FTS5 全文索引│   │ → 向量 (BLOB)│   │ 哈希表+分离链 │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │
       └────────┬─────────┴──────────────────┘
                ▼
        ┌───────────────┐
        │ 混合检索 + RRF │  ③ Reciprocal Rank Fusion 融合排序
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ FastAPI + 网页 │
        └───────────────┘
```

---

## 📋 交付清单

> **规则：先让核心跑通，再加衍生功能。某一层卡住 → 砍掉后面所有衍生项，保证核心层交付。**
> 完整计划见 `internship-plan-2027/25-项目B收尾执行计划.md`

### 🟢 核心层（12h）— 项目成立

- [ ] `pyproject.toml` + 目录结构 + CLI 入口能跑
- [ ] `parse.py`：PDF / Markdown → 纯文本 + 页码元数据
- [ ] `chunk.py`：边界感知分块（段落/句子边界 + 40 字重叠）+ 单测
- [ ] `store.py`：建表 + CJK 逐字切分 + SQLite FTS5 导入
- [ ] 🎯 **验收：`ingest` + `search` 端到端跑通，能查到真实讲义片段** ← **M1**

### 🟡 主体层（17h）— 简历能写

- [ ] `cli.py`：`ingest` / `search` 支持 `--top` / `--mode`
- [ ] `embed.py`：embedding API 封装 + 向量 BLOB 存储
- [ ] `search.py`：向量检索 + **RRF 融合**（`--mode hybrid`）
- [ ] `hash_index.py`：自造倒排索引（哈希表 + **分离链**）
- [ ] `api.py`：FastAPI `/health` `/documents` `/search`

### 🟠 差异化层（10h）— 面试能追问 20 分钟

- [ ] `evals.jsonl`：评测集（≥20 条 query，含 3 个已知失败 query）
- [ ] **三后端 A/B 回测**（自造哈希 / FTS5 / 混合）→ 一张对比表
- [ ] **装载因子实验**（0.1 → 1.0 的延迟曲线）→ 能看出性能拐点
- [ ] **B+ 树索引对照**（`EXPLAIN QUERY PLAN` + 耗时对比）
- [ ] `search_log` 表 + `stats` 命令（零结果查询 / 慢查询）

### 🔵 收尾层（9h）— 完成度

- [ ] `web/index.html`：查询界面 + 命中高亮
- [ ] 单元测试补齐到 8–10 个（全绿）
- [ ] README：架构图 + 一行命令启动 + **取舍说明 + 对比表 + 复杂度表**
- [ ] **部署上线 + 贴链接**

### ⛔ 明确不做（记为「未来工作」）

- 线性探测版索引（分离链已足够做对照实验）
- LLM 自动摘要
- Docker 化 · 文件监听 · 增量索引
- 用户系统 / 多语言 / 移动端
- pgvector / Elasticsearch（几千 chunk 用不上，是过度设计）

---

## 技术取舍（README 的核心价值）

> 面试官看的不是「你用了什么」，而是「你**为什么**用它、**代价**是什么」。

| 决策 | 选择 | 代价 / 替代方案 |
|---|---|---|
| 中文分词 | **CJK 逐字切分** | 索引体积变大、短语匹配弱；替代：FTS5 `trigram` 或 jieba |
| 向量存储 | **BLOB (float32)** | 比 JSON 小约 4 倍、读取无解析开销；不可直接人读 |
| 检索融合 | **RRF** | 只依赖排名、无需调参；不如学习式排序精细 |
| 索引后端 | **SQLite FTS5**（默认） | 持久化 + ACID；比自造内存索引慢（有实测数据） |
| 何时换 pgvector | **暂不换** | 几千 chunk 内存余弦是毫秒级；十万级再迁移 |

---

## 复杂度

| 操作 | 复杂度 | 说明 |
|---|---|---|
| 建索引 | O(N × L) | N 个 chunk，平均 L 个词 |
| BM25 查询 | O(Q × avg_postings) | Q 个查询词 |
| 向量检索（暴力） | O(N × d) | d 是向量维度 |
| Top-K（最小堆） | O(N log k) | 优于全排序 O(N log N) |
| 分块 | O(total_chars) | 单次线性扫描 |

---

## 许可

代码：[MIT](LICENSE)
`notes/` 目录下的内容不属于本项目，版权归原作者所有。
