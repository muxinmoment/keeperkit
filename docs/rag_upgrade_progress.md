# KeeperKit RAG 升级进度

本文档记录从 V0 入库到当前可用 RAG 问答链路的完成状态。

## 当前完成状态

已完成：

```text
Step 01：可配置 Embedding / Vector Store
Step 02：Sentence-Transformers BGE Embedding
Step 03：ChromaDB Vector Store
Step 04：ChromaDB 入库与检索验证
Step 05：DeepSeek Grounded Answer
```

当前可用链路：

```text
clean Markdown
  -> Markdown splitter
  -> BAAI/bge-small-zh-v1.5 embedding
  -> ChromaDB persistent collection
  -> retriever top-k
  -> SimpleReranker top-k
  -> DeepSeek answer
  -> sources
```

## 当前索引

Chroma 索引目录：

```text
backend/data/index/coc7_bge_chroma/
```

Collection：

```text
keeperkit_coc7
```

chunk 数量：

```text
1084
```

## 当前推荐配置

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

## 推荐启动命令

PowerShell：

```powershell
cd keeperkit\backend
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
$env:GENERATOR_PROVIDER = "llm"
uvicorn app.main:app --reload
```

如果 `.env` 中已经配置 `LLM_API_KEY`，启动命令不需要再显式设置 key。

## 已验证问题

问题：

```text
奖励骰和惩罚骰怎么计算？
```

接口：

```text
POST /api/v1/rules/ask
```

结果：

```text
status=200
```

Top source：

```text
18-第十六章-附录.md
游戏系统摘要 / 技能检定 / 奖励骰与惩罚骰
```

DeepSeek 回答能说明：

```text
奖励骰取较好十位骰
惩罚骰取较差十位骰
奖励骰与惩罚骰互相抵消
```

并能列出依据来源。

## 已知限制

### Reranker 仍然是简单排序

当前：

```text
SimpleReranker
```

后续建议：

```text
BAAI/bge-reranker-v2-m3
```

### 模型加载较慢

每次脚本或服务启动都会加载：

```text
BAAI/bge-small-zh-v1.5
```

后续可以考虑：

1. 服务启动时单例加载。
2. 使用更轻量模型。
3. 将 embedding 服务独立出来。

### 环境依赖有冲突提示

安装 `chromadb` 时出现过 opentelemetry 相关版本冲突提示。

目前 KeeperKit 的 Chroma 检索可用。如果其他项目依赖旧版本 opentelemetry，建议使用独立虚拟环境。

## 下一步建议

优先级从高到低：

1. 接入 BGE reranker。
2. 优化 chunk 切分，特别是表格、怪物属性块、法术条目。
3. 增加检索评测脚本，固定 20 个规则问题做回归。
4. 前端接入真实 `/api/v1/rules/ask`。
5. 增加 SSE 流式 LLM 输出。
