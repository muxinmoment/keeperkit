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
Step 06：固定评测问题集脚本
Step 07：BGE Reranker
Step 08：前端接入真实问答接口
Step 09：黑话检索改写与弱依据回答策略
```

当前可用链路：

```text
clean Markdown
  -> Markdown splitter
  -> BAAI/bge-small-zh-v1.5 embedding
  -> ChromaDB persistent collection
  -> retriever top-k
  -> slang query rewrite
  -> configurable reranker top-k
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

RERANKER_PROVIDER=simple
# RERANKER_PROVIDER=bge
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
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

### 黑话检索改写已接入

当前会对常见 TRPG/CoC 黑话做轻量检索扩展：

```text
车卡 -> 创建调查员、角色创建、属性、技能、职业、背景
撕卡 -> 调查员死亡、濒死、疯狂
SC/SAN -> 理智检定、理智损失、理智值
DB -> 伤害加值、体格、力量、体型
```

规则回答仍以检索片段为准；没有明确依据时，会先说明缺少规则书依据，再给出通用建议或提问引导。

### 前端已接入真实问答接口

当前前端会调用：

```text
POST /api/v1/rules/ask
```

默认后端地址：

```text
http://127.0.0.1:8000
```

可通过前端环境变量覆盖：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 已有固定评测问题集

当前已有固定问题集和脚本：

```text
backend/data/eval/rules_eval_questions.json
backend/scripts/evaluate_rules.py
```

运行方式：

```powershell
cd keeperkit\backend
$env:KEEPERKIT_DISABLE_DOTENV = "1"
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
python scripts\evaluate_rules.py --top-k 8 --rerank-top-k 3
```

### Reranker 已可配置

当前：

```text
RERANKER_PROVIDER=simple
```

可启用：

```env
RERANKER_PROVIDER=bge
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

默认仍是 `simple`，避免没有下载 reranker 模型时影响本地启动。

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

1. 用固定评测集记录 simple 与 BGE reranker 对比结果。
2. 优化前端 sources 展示与长回答阅读体验。
3. 优化 chunk 切分，特别是表格、怪物属性块、法术条目。
4. 扩充评测问题集到 20 个以上。
5. 增加 SSE 流式 LLM 输出。
