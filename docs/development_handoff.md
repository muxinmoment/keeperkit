# KeeperKit 后续开发交接文档

这份文档用于在新对话中继续开发 KeeperKit Rules，避免当前长上下文压缩后丢失关键信息。

## 1. 项目位置

工作区：

```text
d:\01_Study_Projects\03_code_project\2026study_notes\keeperkit
```

后端：

```text
backend/
```

前端：

```text
frontend/
```

文档：

```text
docs/
```

## 2. 当前项目目标

KeeperKit Rules 是一个面向 TRPG / CoC 守秘人的规则书 RAG 问答工具。

当前目标是：

```text
CoC 7版规则书 Markdown
  -> BGE embedding
  -> ChromaDB 检索
  -> DeepSeek 基于检索片段回答
  -> 返回答案和 sources
```

## 3. 当前已完成状态

已经完成：

```text
1. PDF 按书签章节切分
2. PDF 章节转 Markdown 初稿
3. Markdown 机械预清洗
4. DeepSeek 全量清洗 Markdown
5. V0 Hash + JSON 入库验证
6. BGE embedding 接入
7. ChromaDB 向量库接入
8. DeepSeek grounded answer 接入
9. FastAPI /api/v1/rules/ask 可用
10. 文档分步骤记录
```

当前可用链路：

```text
backend/data/raw/private/clean_markdown_chapters/
  -> backend/scripts/ingest_rules.py
  -> backend/data/index/coc7_bge_chroma/
  -> POST /api/v1/rules/ask
```

## 4. 当前关键配置

`.env` 位于：

```text
backend/.env
```

推荐配置：

```env
APP_NAME=KeeperKit Rules
APP_ENV=development

RAW_DOCS_DIR=./data/raw/private/clean_markdown_chapters
PROCESSED_DOCS_DIR=./data/processed
INDEX_DIR=./data/index/coc7_bge_chroma

RETRIEVAL_TOP_K=8
RERANK_TOP_K=3

EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_coc7

GENERATOR_PROVIDER=llm
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=replace-with-your-key
LLM_MODEL=deepseek-chat
```

不要把真实 `LLM_API_KEY` 提交到 Git。

## 5. 当前重要文件

后端入口：

```text
backend/app/main.py
```

配置：

```text
backend/app/config.py
backend/.env.example
```

RAG 核心：

```text
backend/app/rag/document_loader.py
backend/app/rag/splitter.py
backend/app/rag/embeddings.py
backend/app/rag/vector_store.py
backend/app/rag/chroma_store.py
backend/app/rag/vector_store_factory.py
backend/app/rag/retriever.py
backend/app/rag/reranker.py
backend/app/rag/generator.py
backend/app/rag/prompts.py
```

服务层：

```text
backend/app/services/rule_qa_service.py
```

API：

```text
backend/app/api/routes/rules.py
backend/app/api/routes/health.py
```

脚本：

```text
backend/scripts/split_pdf_by_bookmarks.py
backend/scripts/convert_pdf_chapters_to_md.py
backend/scripts/preclean_markdown_chapters.py
backend/scripts/clean_markdown_with_deepseek.py
backend/scripts/ingest_rules.py
backend/scripts/test_retrieval.py
```

## 6. 当前索引

V0 Hash + JSON：

```text
backend/data/index/coc7_clean/chunks.json
```

BGE + JSON：

```text
backend/data/index/coc7_bge_json/chunks.json
```

BGE + ChromaDB：

```text
backend/data/index/coc7_bge_chroma/
```

当前推荐使用：

```text
backend/data/index/coc7_bge_chroma/
```

Chroma collection：

```text
keeperkit_coc7
```

已验证 chunk 数量：

```text
1084
```

## 7. 运行方式

进入后端：

```powershell
cd d:\01_Study_Projects\03_code_project\2026study_notes\keeperkit\backend
```

检索测试：

```powershell
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

启动 API：

```powershell
uvicorn app.main:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

测试接口：

```http
POST /api/v1/rules/ask
```

请求示例：

```json
{
  "question": "奖励骰和惩罚骰怎么计算？",
  "top_k": 8,
  "rerank_top_k": 3
}
```

## 8. 已验证问题

这些问题已经用于检索/问答验证：

```text
奖励骰和惩罚骰怎么计算？
孤注一掷失败会发生什么？
理智检定失败后怎么处理？
```

`奖励骰和惩罚骰怎么计算？` 已验证：

```text
source: 18-第十六章-附录.md
title_path: 游戏系统摘要 / 技能检定 / 奖励骰与惩罚骰
```

DeepSeek 能基于 sources 生成回答，并列出依据来源。

## 9. 当前 Git 状态

最近关键提交：

```text
98e5ee8 feat：接入DeepSeek规则问答生成器
021dcb1 data：提交BGE与Chroma规则索引验证产物
b815d56 feat：接入可配置BGE与Chroma检索底座
2b94ad7 feat：RAGv0实验功能
```

注意：此前提交了 BGE/Chroma 索引验证产物，仓库会变大一些。

## 10. 已知问题与技术债

### 10.1 Reranker 还没升级

当前：

```text
backend/app/rag/reranker.py
SimpleReranker
```

它只是按向量分数排序。

建议下一步接：

```text
BAAI/bge-reranker-v2-m3
```

目标链路：

```text
Chroma Top 20
  -> BGE Reranker Top 5
  -> DeepSeek Answer
```

### 10.2 表格和条目 chunk 还可以优化

需要重点优化：

```text
武器表
技能列表
怪物属性块
法术条目
附录摘要
```

### 10.3 前端还比较基础

前端位置：

```text
frontend/
```

当前可继续做：

```text
React 查询界面
sources 展示
loading 状态
SSE 流式输出
```

### 10.4 环境依赖提醒

安装 `sentence-transformers` 和 `chromadb` 时，Anaconda base 环境出现过依赖冲突提示：

```text
gradio / pillow
opentelemetry-exporter-otlp-proto-http
```

当前 KeeperKit 可用，但后续建议创建独立虚拟环境。

## 11. 推荐下一步开发顺序

建议按这个顺序继续：

```text
1. 增加固定评测问题集脚本
2. 接入 BGE reranker
3. 优化 sources 展示和回答格式
4. 前端接入真实后端
5. SSE 流式输出
6. 针对表格/怪物/法术优化 chunk 切分
```

## 12. 新对话提示词

在新对话中可以直接复制下面这段：

```text
我在继续开发 keeperkit 项目，路径是：
d:\01_Study_Projects\03_code_project\2026study_notes\keeperkit

请先阅读 docs/development_handoff.md、docs/rag_upgrade_progress.md、docs/rag_ingestion_guide.md，以及最近的 RAG 步骤文档：
- docs/rag_step_01_configurable_backend.md
- docs/rag_step_02_bge_embedding.md
- docs/rag_step_03_chromadb_store.md
- docs/rag_step_04_chroma_verification.md
- docs/rag_step_05_llm_generator.md

当前已经完成：
- CoC 7版规则书 PDF 切分、转 Markdown、预清洗、DeepSeek 清洗
- BGE embedding
- ChromaDB 向量库
- DeepSeek grounded answer
- FastAPI /api/v1/rules/ask

当前推荐配置是：
INDEX_DIR=./data/index/coc7_bge_chroma
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_coc7
GENERATOR_PROVIDER=llm
LLM_MODEL=deepseek-chat

不要读取或输出 backend/.env 中的真实 API key。

请先检查 git status 和项目结构，然后继续下一步开发。我想优先做：
1. 固定评测问题集脚本
2. BGE reranker
3. 前端接入真实问答接口

每完成一个小步骤，请在 docs 目录新增或更新对应 Markdown 文档，并用中文 commit message 提交。
```
