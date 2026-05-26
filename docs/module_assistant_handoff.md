# KeeperKit 模组助手接续文档

本文档用于新对话继续开发 KeeperKit 的下一阶段：在现有规则书 RAG 基础上，加入用户自定义模组，让 AI 能围绕指定模组进行问答、时间线整理、模组修改、细节添加和图片生成等工作。

## 1. 当前结论

当前规则书 RAG 可以视为 **V1 闭环完成**：

```text
CoC 7 规则书清洗 Markdown
  -> BGE embedding
  -> ChromaDB
  -> BGE/simple reranker
  -> DeepSeek grounded answer
  -> FastAPI /api/v1/rules/ask
  -> React 前端真实问答
```

但它还不是完整的“模组助手”。现在系统主要擅长回答：

```text
规则书里写过什么？
某条 CoC 规则怎么理解？
某个规则问题的依据来源是什么？
```

它还不能稳定完成：

```text
基于我选中的模组回答
整理模组时间线
修改模组结构
补充 NPC、线索、场景细节
生成图片提示词或图片资产
区分规则书资料与模组私有资料
```

## 2. 已完成能力

### 2.1 规则书 RAG

已完成：

```text
PDF 切分
PDF 转 Markdown
Markdown 预清洗
DeepSeek 清洗
BGE embedding
ChromaDB 持久化索引
DeepSeek grounded answer
BGE reranker 可配置
固定评测问题集
黑话检索改写
弱依据回答策略
前端真实接口接入
keeperkit conda 后端启动脚本
```

关键文档在：

```text
docs/rag搭建文档/
```

后端启动入口：

```powershell
.\keeperkit.ps1 backend
```

开发 reload：

```powershell
.\keeperkit.ps1 backend -Reload
```

### 2.2 当前推荐运行配置

`backend/.env` 中推荐：

```env
RAW_DOCS_DIR=./data/raw/private/clean_markdown_chapters
INDEX_DIR=./data/index/coc7_bge_chroma

EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_STORE_PROVIDER=chroma
CHROMA_COLLECTION=keeperkit_coc7

RETRIEVAL_TOP_K=20
RERANK_TOP_K=5
RERANKER_PROVIDER=bge
RERANKER_MODEL=BAAI/bge-reranker-v2-m3

GENERATOR_PROVIDER=llm
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_key
LLM_MODEL=deepseek-v4-pro
```

不要提交真实 `LLM_API_KEY`。

## 3. 当前 RAG 还未完成的优化项

这些不是模组功能的前置阻塞，但会影响质量：

```text
1. 评测脚本命中规则还比较粗，只按关键词判断。
2. fixed eval 需要支持同义词，例如“孤注一掷/孤注一骰”“临时疯狂/临时性疯狂”。
3. 表格、法术、怪物属性块、职业列表等 chunk 切分还可以优化。
4. 前端 sources 展示还比较基础，缺少展开全文、复制来源、按章节聚合。
5. SSE 流式输出还没有接到前端。
6. 黑话表目前写在代码里，后续可以迁移到 JSON/YAML。
```

## 4. 下一阶段目标：模组助手

目标不是把模组混进规则书索引里，而是建立多知识域：

```text
规则书知识域：coc7_rules
模组知识域：module_<module_id>
用户笔记知识域：notes_<module_id>
生成资产知识域：assets_<module_id>
```

回答时根据用户当前选择的模组和任务类型进行检索：

```text
用户问题
  -> 判断任务类型
  -> 检索当前模组
  -> 必要时检索规则书
  -> 必要时检索用户笔记
  -> LLM 生成回答/改写/整理
  -> 返回 sources 和操作建议
```

## 5. 模组资料需求

第一版建议支持这些输入：

```text
Markdown
TXT
PDF
JSON/YAML 元数据
图片引用或图片目录
```

模组元数据建议：

```json
{
  "id": "module_id",
  "title": "模组名称",
  "system": "coc7",
  "language": "zh",
  "keeper_notes": "可选说明",
  "spoiler_level": "keeper_only"
}
```

模组原文与用户笔记应放入私有目录，避免提交：

```text
backend/data/modules/private/
```

建议 `.gitignore` 后续加入：

```gitignore
backend/data/modules/private/
```

## 6. 模组索引设计

不要直接复用规则书 collection。

建议 Chroma collection：

```text
keeperkit_coc7_rules
keeperkit_module_<module_id>
keeperkit_module_notes_<module_id>
```

每个 chunk metadata 至少包含：

```json
{
  "knowledge_base": "module",
  "module_id": "xxx",
  "source": "chapter.md",
  "title_path": ["场景一", "书房"],
  "content_type": "scene|npc|clue|timeline|handout|note|rule",
  "spoiler_level": "keeper_only",
  "order_index": 12
}
```

## 7. 模组切块建议

模组和规则书不同，不能只按标题和长度切。

建议优先识别：

```text
场景
NPC
线索
时间线事件
地点
手稿/手牌
怪物/遭遇
结局分支
守秘人提示
```

推荐第一版先做轻量切块：

```text
Markdown 标题路径
关键词标记 NPC/线索/地点
保留 order_index
保留 source
```

后续再做结构化抽取。

## 8. 模组任务类型

第一版建议支持这些任务：

### 8.1 模组问答

示例：

```text
这个模组里奈亚出现了吗？
玩家错过了某个线索怎么办？
这个 NPC 的动机是什么？
```

检索策略：

```text
当前模组 top-k
必要时规则书 top-k
```

### 8.2 时间线整理

示例：

```text
帮我整理这个模组的时间线。
按调查员可能接触到的顺序整理事件。
```

需要输出：

```text
事件时间
事件地点
参与 NPC
线索
触发条件
对玩家可见/仅守秘人可见
```

### 8.3 模组修改

示例：

```text
把这个模组改成三小时短团。
把恐怖程度降低一点。
把最终 Boss 换成奈亚的化身。
```

要求：

```text
必须标注哪些来自原模组
哪些是 AI 建议修改
不能悄悄改动规则书规则
保留修改前后对照
```

### 8.4 细节添加

示例：

```text
给这个场景补 5 个可调查细节。
给这个 NPC 写一段口癖和临场反应。
给书房补三条线索。
```

要求：

```text
区分“原文线索”和“新增细节”
新增内容不能破坏核心谜题
```

### 8.5 图片生成

第一阶段不直接生成图片，可以先生成图片提示词：

```text
NPC 肖像 prompt
场景氛围 prompt
手稿/道具 prompt
怪物外观 prompt
```

后续再接 image generation。

## 9. API 需求草案

建议新增：

```http
POST /api/v1/modules
GET /api/v1/modules
GET /api/v1/modules/{module_id}
POST /api/v1/modules/{module_id}/ingest
POST /api/v1/modules/{module_id}/ask
POST /api/v1/modules/{module_id}/timeline
POST /api/v1/modules/{module_id}/rewrite
POST /api/v1/modules/{module_id}/details
POST /api/v1/modules/{module_id}/image-prompts
```

第一版可以只做：

```text
1. 模组导入/入库
2. 选择模组
3. 模组问答
4. 时间线整理
```

## 10. 前端需求草案

前端需要新增：

```text
模组列表
当前模组选择器
模组上传/导入入口
模组问答视图
时间线视图
NPC/地点/线索标签页
生成内容与原文来源对照
```

不要把模组助手做成单纯聊天框。建议左侧是模组导航，中间是任务工作区，右侧是 sources/notes。

## 11. 安全与边界

必须明确三类内容：

```text
规则书依据
模组原文依据
AI 新增建议
```

回答格式建议：

```text
规则依据：
模组依据：
建议改动：
风险提示：
来源：
```

尤其是模组修改功能，必须避免：

```text
把 AI 生成内容伪装成原模组内容
把房规伪装成 CoC 规则
把缺失线索编造成原文线索
```

## 12. 推荐下一步开发顺序

建议按这个顺序做：

```text
Step M01：模组数据目录和 metadata 结构
Step M02：模组 Markdown/TXT 加载器
Step M03：模组 chunk 切分与 metadata
Step M04：模组 Chroma collection
Step M05：模块化 retriever，支持 rules/module 双检索
Step M06：/api/v1/modules/{module_id}/ask
Step M07：前端模组选择器和模组问答
Step M08：时间线整理
Step M09：模组修改与新增细节
Step M10：图片提示词，再考虑图片生成
```

## 13. 新对话提示词

可以在新对话中复制：

```text
我在继续开发 KeeperKit。当前规则书 RAG V1 已完成：CoC 7 清洗 Markdown、BGE embedding、ChromaDB、BGE reranker、DeepSeek grounded answer、FastAPI /api/v1/rules/ask、前端真实问答、黑话检索改写、keeperkit conda 后端启动入口。

请先阅读：
- docs/module_assistant_handoff.md
- docs/rag搭建文档/rag_upgrade_progress.md
- docs/rag搭建文档/rag_step_09_slang_and_fallback.md
- docs/rag搭建文档/rag_step_10_backend_conda_start.md

不要读取或输出 backend/.env 中的真实 API key。

我想进入下一阶段：让用户可以导入自己的 CoC 模组，并选择某个模组，让 AI 基于该模组进行问答、时间线整理、模组修改、细节添加，以及后续图片生成。请先检查 git status 和项目结构，然后按 Step M01 开始设计和实现。每完成一个小步骤，请在 docs 下新增或更新对应 Markdown 文档，并用中文 commit message 提交。
```
