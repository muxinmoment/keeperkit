# KeeperKit Rules 开发文档

## 1. 项目定位

KeeperKit 是一个面向 TRPG 守秘人、GM 和玩家的本地优先工具箱。第一阶段只做 `KeeperKit Rules`：把规则书或规则笔记变成可检索、可引用、可问答的 RAG 服务。

V1 的核心目标不是“全能跑团平台”，而是先做一个可靠的查书助手：

```text
规则文档 -> 切块 -> 建索引 -> 检索 -> 精排 -> 基于片段回答 -> 返回引用
```

## 2. 当前骨架

```text
keeperkit/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI 路由
│   │   ├── rag/               # 文档加载、切块、检索、生成
│   │   ├── schemas/           # 请求和响应模型
│   │   ├── services/          # 应用服务编排
│   │   ├── config.py          # 环境配置
│   │   └── main.py            # FastAPI 入口
│   ├── data/
│   │   ├── raw/               # 原始规则文档
│   │   ├── processed/         # 预处理产物
│   │   └── index/             # 本地开发索引
│   ├── scripts/
│   │   ├── ingest_rules.py    # 导入并建立索引
│   │   └── test_retrieval.py  # 命令行检索测试
│   └── tests/
├── frontend/
│   └── src/                   # React 查询界面
└── docs/
```

## 3. 后端模块职责

### `document_loader.py`

读取 `backend/data/raw` 下的 `.md`、`.markdown`、`.txt` 文件，转成统一的 `RawDocument`。

V1 建议优先使用 Markdown，因为标题结构天然适合规则书 RAG。PDF 解析放到后续阶段，不要让复杂排版消耗第一版的开发热情。

### `splitter.py`

按 Markdown 标题维护 `title_path`，再用长度窗口做兜底切分。每个 chunk 保留：

- `source`
- `suffix`
- `title_path`

这会直接影响后续引用质量。

### `embeddings.py`

当前使用 `HashEmbeddingModel`，这是一个轻量、确定性的本地开发替身。它的作用是让骨架在没有下载 BGE 模型、没有配置 ChromaDB 的情况下也能跑通。

后续替换方向：

- `BAAI/bge-small-zh-v1.5`：本地轻量优先。
- `BAAI/bge-m3`：中英混合、长文本效果优先。

### `vector_store.py`

当前使用 `JsonVectorStore`，索引文件落在 `backend/data/index/chunks.json`。

V1.1 可以替换成 ChromaDB，但对外保留类似接口：

```python
save(chunks)
search(query, top_k)
```

### `retriever.py`

封装召回逻辑，默认返回 Top K 候选片段。

### `reranker.py`

当前是 `SimpleReranker`，直接按召回分数排序。后续可以接：

- `BAAI/bge-reranker-v2-m3`
- 你自己的 RoBERTa cross-encoder reranker

### `generator.py`

当前是 `TemplateRuleGenerator`，不会调用真实 LLM，只返回检索依据。这样做是为了先确认“查得到、引用对、接口通”。

后续接入 DeepSeek 或 Qwen 时，把这个类替换成 OpenAI-compatible 客户端即可。

## 4. API 设计

### 健康检查

```http
GET /api/v1/health
```

### 规则问答

```http
POST /api/v1/rules/ask
```

请求：

```json
{
  "question": "孤注一掷失败后会发生什么？",
  "top_k": 8,
  "rerank_top_k": 3
}
```

响应：

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample_rules.md",
      "title_path": ["KeeperKit 示例规则", "孤注一掷"],
      "score": 0.42,
      "content_preview": "..."
    }
  ]
}
```

### SSE 问答

```http
POST /api/v1/rules/ask/stream
```

当前流式接口会把模板回答逐字吐出。接入真实 LLM 后，再把 token 流换成模型输出。

## 5. 本地运行流程

进入后端：

```powershell
cd keeperkit\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\ingest_rules.py
python scripts\test_retrieval.py "孤注一掷失败后会发生什么？"
uvicorn app.main:app --reload
```

进入前端：

```powershell
cd keeperkit\frontend
npm install
npm run dev
```

## 6. 下一阶段建议

### V1.1：替换向量能力

- 用 `sentence-transformers` 加载 `BAAI/bge-small-zh-v1.5`。
- 用 ChromaDB 替换 JSON 索引。
- 保持 `RuleRetriever` 对服务层的接口不变。

### V1.2：接入真实 LLM

- 使用 OpenAI-compatible SDK。
- 读取 `.env` 中的 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。
- Prompt 必须强制模型只基于检索片段回答。

### V1.3：加入 Rerank

- 先用 `BAAI/bge-reranker-v2-m3`。
- 后续再尝试自训或微调 RoBERTa cross-encoder。
- 目标是解决“召回有了，但前 3 条不够准”的问题。

### V2：扩展工具箱

- 骰子表达式解析和投掷。
- NPC 快速生成。
- 模组笔记搜索。
- 多规则书 collection。
- 会话日志和复盘。

## 7. 工程约束

- V1 只保证本地开发，不做用户系统。
- 规则资料默认放在本地，不上传云端。
- 回答必须带 sources，避免无依据结论。
- 先支持 Markdown/TXT，PDF 放到后续专门处理。
- 所有 RAG 组件保持可替换，不把业务路由写死在具体模型实现上。
