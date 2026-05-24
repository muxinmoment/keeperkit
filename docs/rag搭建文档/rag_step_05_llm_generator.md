# RAG Step 05：接入 DeepSeek Grounded Answer

## 本步目标

让 `/api/v1/rules/ask` 可以调用 LLM 基于检索片段生成回答。

为了保持可回退，新增配置：

```env
GENERATOR_PROVIDER=template
```

或：

```env
GENERATOR_PROVIDER=llm
```

默认仍然是 `template`，没有 API key 时系统仍然可运行。

## 修改内容

更新：

```text
backend/app/config.py
backend/.env.example
backend/app/rag/generator.py
backend/app/rag/prompts.py
backend/app/services/rule_qa_service.py
```

新增生成器：

```python
LLMRuleGenerator
```

新增工厂：

```python
create_rule_generator(provider)
```

同时修复了早期 `generator.py` 和 `prompts.py` 中的中文编码乱码。

## 推荐运行配置

```env
RAW_DOCS_DIR=./data/raw/private/clean_markdown_chapters
INDEX_DIR=./data/index/coc7_bge_chroma

EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_coc7

GENERATOR_PROVIDER=llm
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_key
LLM_MODEL=deepseek-chat
```

## 启动后端

PowerShell 临时配置：

```powershell
cd keeperkit\backend
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
$env:GENERATOR_PROVIDER = "llm"
$env:LLM_BASE_URL = "https://api.deepseek.com"
$env:LLM_API_KEY = "your_key"
$env:LLM_MODEL = "deepseek-chat"
uvicorn app.main:app --reload
```

## 测试接口

打开：

```text
http://127.0.0.1:8000/docs
```

调用：

```http
POST /api/v1/rules/ask
```

请求：

```json
{
  "question": "奖励骰和惩罚骰怎么计算？",
  "top_k": 8,
  "rerank_top_k": 3
}
```

期望：

1. 回答严格基于检索片段。
2. 涉及奖励骰和惩罚骰时说明十位骰取较好/较差结果。
3. 回答末尾列出依据来源。
4. `sources` 字段仍然返回结构化引用。

## 当前限制

当前 reranker 仍然是 `SimpleReranker`，也就是按向量分数排序。

下一步如果要继续提高准确率，应接入：

```text
BAAI/bge-reranker-v2-m3
```

目标流程：

```text
Chroma Top 20
  -> BGE Reranker Top 5
  -> DeepSeek Answer
```
