# RAG Step 04：ChromaDB 入库与检索验证

## 本步目标

验证以下组合可以完整运行：

```text
clean Markdown
  -> BGE embedding
  -> ChromaDB persistent collection
  -> retriever query
```

## 实际执行命令

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

执行结果：

```text
Loaded 19 documents.
Indexed 1084 chunks into data\index\coc7_bge_chroma.
```

## Collection 验证

```powershell
python -c "import chromadb; c=chromadb.PersistentClient(path='data/index/coc7_bge_chroma'); col=c.get_collection('keeperkit_coc7'); print('count', col.count())"
```

结果：

```text
count 1084
```

## 检索验证

命令：

```powershell
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

Top 结果命中：

```text
source=18-第十六章-附录.md
title=游戏系统摘要 / 技能检定 / 奖励骰与惩罚骰
```

第二结果命中核心章节：

```text
source=07-第五章-游戏系统.md
title=第五章 游戏系统 / 5.8 奖励骰与惩罚骰
```

## 当前判断

ChromaDB 版本已经完成向量库升级。

当前可用配置：

```env
RAW_DOCS_DIR=./data/raw/private/clean_markdown_chapters
INDEX_DIR=./data/index/coc7_bge_chroma
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_coc7
```

## 注意事项

安装 `chromadb` 时，当前环境出现过 opentelemetry 版本冲突提示：

```text
opentelemetry-exporter-otlp-proto-http 1.41.0 requires ...
```

目前不影响 KeeperKit 的 Chroma 检索。如果后续其他项目依赖 OTLP HTTP exporter，再单独处理环境隔离。

## 下一步

接入真实 LLM 生成：

```text
retriever
  -> reranker/simple top-k
  -> DeepSeek grounded answer
```

要求 LLM 只能基于检索片段回答，并输出引用来源。
