# RAG Step 07：接入 BGE Reranker

## 本步目标

把原来的 `SimpleReranker` 升级为可配置 reranker，默认仍然使用简单分数排序，同时支持 BGE cross-encoder reranker：

```env
RERANKER_PROVIDER=bge
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

目标链路：

```text
Chroma Top 20
  -> BGE Reranker Top 5
  -> DeepSeek Answer
```

## 修改内容

更新配置：

```text
backend/app/config.py
backend/.env.example
```

更新 reranker：

```text
backend/app/rag/reranker.py
```

新增：

```python
BGEReranker
create_reranker(provider, model_name)
```

更新调用方：

```text
backend/app/services/rule_qa_service.py
backend/scripts/evaluate_rules.py
```

服务层和评测脚本现在都会读取同一组配置，因此可以直接用固定评测集对比 `simple` 与 `bge` 的召回差异。

## 推荐配置

仍然保留可回退默认值：

```env
RERANKER_PROVIDER=simple
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

启用 BGE reranker：

```env
RETRIEVAL_TOP_K=20
RERANK_TOP_K=5
RERANKER_PROVIDER=bge
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

## 评测命令

不读取 `backend/.env`，使用临时环境变量：

```powershell
cd keeperkit\backend
$env:KEEPERKIT_DISABLE_DOTENV = "1"
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
$env:RERANKER_PROVIDER = "bge"
$env:RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
python scripts\evaluate_rules.py --top-k 20 --rerank-top-k 5
```

首次运行会下载或加载 `BAAI/bge-reranker-v2-m3`，耗时会明显长于 simple reranker。

## 当前注意事项

`BGEReranker` 使用 `sentence_transformers.CrossEncoder` 加载模型。rerank 分数会经过 sigmoid 归一化到 0 到 1，便于继续在 `sources.score` 中展示；排序顺序与原始模型分数保持一致。

如果本地环境还没有下载该模型，第一次评测可能需要较久，并可能受 Hugging Face 访问速度影响。

## 本步验证

已完成：

```powershell
$env:KEEPERKIT_DISABLE_DOTENV = "1"
python -m pytest tests
```

结果：

```text
3 passed
```

同时用 `RERANKER_PROVIDER=simple` 跑过固定评测集，结果与接入前一致：

```text
Total: 15  PASS: 12  CANDIDATE_ONLY: 1  MISS: 2
```

`RERANKER_PROVIDER=bge` 的完整评测在本机首次模型下载/加载阶段超过 5 分钟超时，后续可以在模型缓存完成后再次运行同一条评测命令。
