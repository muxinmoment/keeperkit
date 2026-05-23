# RAG Step 03：接入 ChromaDB 持久化向量库

## 本步目标

把开发用的 JSON 向量索引升级为 ChromaDB 持久化 collection。

新增配置：

```env
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_rules
```

推荐组合：

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
```

## 修改内容

新增依赖：

```text
chromadb
```

新增文件：

```text
backend/app/rag/chroma_store.py
```

更新：

```text
backend/app/config.py
backend/app/rag/vector_store_factory.py
backend/.env.example
backend/requirements.txt
```

## Chroma 存储方式

ChromaDB 会把向量、正文和 metadata 持久化到：

```text
INDEX_DIR
```

例如：

```text
backend/data/index/coc7_bge_chroma/
```

每个 chunk 会写入：

```text
id
document
metadata
embedding
```

由于 Chroma metadata 不支持 list，`title_path` 会在写入时转换成字符串：

```text
第五章 游戏系统 / 5.8 奖励骰与惩罚骰
```

读取时再恢复成：

```python
["第五章 游戏系统", "5.8 奖励骰与惩罚骰"]
```

## 安装依赖

```powershell
cd keeperkit\backend
pip install chromadb
```

或：

```powershell
pip install -r requirements.txt
```

## 建立 Chroma 索引

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
python scripts\ingest_rules.py
```

## 检索测试

```powershell
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

## 本步验收标准

1. `backend/data/index/coc7_bge_chroma/` 被创建。
2. Chroma collection 中 chunk 数量约为 1084。
3. 检索能返回 `source` 和 `title_path`。
4. 关键问题能召回正确章节。

## 下一步

验证 Chroma 检索后，接入 LLM grounded answer：

```text
retriever -> reranker -> generator
```

当前 reranker 仍然是简单排序，generator 仍然是模板回答。
