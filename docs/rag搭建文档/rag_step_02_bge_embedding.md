# RAG Step 02：接入 Sentence-Transformers / BGE Embedding

## 本步目标

在不引入向量数据库的前提下，先把 embedding 从开发用的 Hash 模型升级为真实语义模型。

当前新增能力：

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

此阶段仍然使用：

```env
VECTOR_STORE_PROVIDER=json
```

也就是说，索引仍然写成 `chunks.json`，但 embedding 已经是真实语义向量。

## 修改内容

新增依赖：

```text
sentence-transformers
```

修改：

```text
backend/app/rag/embeddings.py
backend/app/rag/vector_store.py
backend/app/rag/vector_store_factory.py
backend/.env.example
backend/requirements.txt
```

新增类：

```python
SentenceTransformerEmbeddingModel
```

## 推荐模型

轻量中文优先：

```text
BAAI/bge-small-zh-v1.5
```

效果更强但更重：

```text
BAAI/bge-m3
```

当前建议先用 `bge-small-zh-v1.5`，因为它下载和推理压力更小。

## 安装依赖

```powershell
cd keeperkit\backend
pip install -r requirements.txt
```

如果只想安装新增依赖：

```powershell
pip install sentence-transformers
```

## 建立 BGE + JSON 索引

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_bge_json"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "json"
python scripts\ingest_rules.py
```

首次运行会下载模型，耗时取决于网络。

## 检索测试

```powershell
$env:INDEX_DIR = ".\data\index\coc7_bge_json"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "json"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

建议测试：

```powershell
python scripts\test_retrieval.py "孤注一掷失败会发生什么？"
python scripts\test_retrieval.py "理智检定失败后怎么处理？"
python scripts\test_retrieval.py "战斗中闪避和反击怎么判定？"
```

## 本步验收标准

1. 能成功生成 `data/index/coc7_bge_json/chunks.json`。
2. chunk 数量仍约为 1084。
3. embedding 维度从 Hash 的 256 变成 BGE 模型维度。
4. 检索排序比 Hash 版本更贴近语义。

## 下一步

接入 ChromaDB：

```env
VECTOR_STORE_PROVIDER=chroma
```

届时索引不再保存为单个 `chunks.json`，而是 Chroma 的持久化 collection。
