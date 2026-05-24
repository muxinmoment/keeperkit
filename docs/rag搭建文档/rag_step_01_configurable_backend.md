# RAG Step 01：可配置 Embedding 与 Vector Store

## 本步目标

把原本硬编码的 RAG 底座拆成可配置入口：

```text
EMBEDDING_PROVIDER
EMBEDDING_MODEL
VECTOR_STORE_PROVIDER
```

这样后续从 V0 的：

```text
HashEmbeddingModel + JsonVectorStore
```

升级到：

```text
BGE Embedding + ChromaDB
```

时，不需要改 API 层和服务层。

## 修改内容

新增配置项：

```text
backend/app/config.py
backend/.env.example
```

当前默认值：

```env
EMBEDDING_PROVIDER=hash
EMBEDDING_MODEL=hash-256
VECTOR_STORE_PROVIDER=json
```

新增工厂：

```text
backend/app/rag/vector_store_factory.py
```

扩展 embedding 工厂：

```text
backend/app/rag/embeddings.py
```

更新使用方：

```text
backend/scripts/ingest_rules.py
backend/app/rag/retriever.py
```

## 当前行为

现在不改 `.env` 的情况下，行为和原来保持一致：

```text
hash embedding -> json chunks.json
```

也就是说，V0 索引仍然可用。

## 验证命令

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_clean"
$env:EMBEDDING_PROVIDER = "hash"
$env:VECTOR_STORE_PROVIDER = "json"
python scripts\ingest_rules.py
```

检索：

```powershell
$env:INDEX_DIR = ".\data\index\coc7_clean"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

## 下一步

接入 `sentence-transformers`，增加：

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

先保留 JSON vector store，验证真实 embedding 本身可用。
