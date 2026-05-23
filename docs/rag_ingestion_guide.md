# KeeperKit Rules RAG 入库原理与操作指南

本文档说明如何把已经清洗完成的 CoC 规则书 Markdown 放入 KeeperKit 的 RAG 检索索引中。

当前项目已有的清洗结果目录是：

```text
backend/data/raw/private/clean_markdown_chapters/
```

当前项目已有的入库脚本是：

```text
backend/scripts/ingest_rules.py
```

## 1. 当前阶段的目标

现在先做 V0/V1 验证版入库，目标不是一步到位做到生产级 RAG，而是验证这条链路：

```text
clean Markdown
  -> 文档加载
  -> Markdown 标题切块
  -> 生成向量
  -> 写入本地索引
  -> 检索测试
  -> FastAPI 问答接口
```

当前项目使用的是轻量实现：

```text
HashEmbeddingModel + JsonVectorStore
```

它的优点是不用下载模型，不用启动向量数据库，适合验证切块、检索和接口闭环。

它的缺点也很明确：检索效果不代表最终效果。后面要换成：

```text
BGE-M3 / bge-small-zh-v1.5 + ChromaDB
```

## 2. RAG 入库原理

### 2.1 文档加载

入口模块：

```text
backend/app/rag/document_loader.py
```

当前加载器会读取指定目录下的：

```text
.md
.markdown
.txt
```

每个文件会被转成一个 `RawDocument`：

```python
RawDocument(
    content="Markdown 正文",
    metadata={
        "source": "06-第四章-技能.md",
        "suffix": ".md"
    }
)
```

### 2.2 文档切块

入口模块：

```text
backend/app/rag/splitter.py
```

当前切块逻辑会：

1. 识别 Markdown 标题。
2. 维护 `title_path`。
3. 将长文本按字符长度切成 chunk。
4. 给每个 chunk 生成稳定 ID。

例如清洗后的 Markdown：

```md
# 第四章 技能

## 4.1 技能定义

技能表现了一个角色...
```

会被切成类似结构：

```json
{
  "id": "stable-hash",
  "content": "## 4.1 技能定义\n技能表现了一个角色...",
  "metadata": {
    "source": "06-第四章-技能.md",
    "suffix": ".md",
    "title_path": ["第四章 技能", "4.1 技能定义"]
  }
}
```

这就是后面回答里引用来源的基础。

### 2.3 向量化

入口模块：

```text
backend/app/rag/embeddings.py
```

当前是 `HashEmbeddingModel`。

它不是语义模型，只是一个确定性的本地开发替身。它能让流程跑通，但不能代表真实 RAG 的效果。

后续替换建议：

```text
轻量本地：BAAI/bge-small-zh-v1.5
效果优先：BAAI/bge-m3
```

### 2.4 索引存储

入口模块：

```text
backend/app/rag/vector_store.py
```

当前索引会写到：

```text
backend/data/index/chunks.json
```

每条记录包含：

```json
{
  "id": "...",
  "content": "...",
  "metadata": {},
  "embedding": []
}
```

后续换 ChromaDB 时，建议保持服务层接口不变，只替换 `vector_store.py` 的实现。

## 3. 入库前检查

确认清洗结果存在：

```powershell
cd keeperkit
Get-ChildItem backend\data\raw\private\clean_markdown_chapters -Filter *.md
```

正常应该看到 19 个文件。

确认 `.gitignore` 已经忽略私有语料：

```gitignore
backend/data/raw/private/
```

完整规则书文本、PDF、清洗结果都不要提交到 Git。

## 4. 入库方式

当前入库脚本读取配置项：

```env
RAW_DOCS_DIR
INDEX_DIR
```

默认 `.env.example` 中是：

```env
RAW_DOCS_DIR=./data/raw
INDEX_DIR=./data/index
```

因为你的清洗结果在 private 目录，所以推荐使用临时环境变量运行，避免把 `.env` 固定改成私有规则书路径。

### 4.1 推荐方式：临时指定清洗目录

PowerShell：

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_clean"
python scripts\ingest_rules.py
```

成功后应看到类似输出：

```text
Loaded 19 documents.
Indexed xxx chunks into ...\backend\data\index\coc7_clean.
```

### 4.2 备选方式：修改 `.env`

编辑：

```text
backend/.env
```

改成：

```env
RAW_DOCS_DIR=./data/raw/private/clean_markdown_chapters
INDEX_DIR=./data/index/coc7_clean
```

然后运行：

```powershell
cd keeperkit\backend
python scripts\ingest_rules.py
```

这个方式更省事，但容易忘记当前 `.env` 指向的是私有规则书目录。

## 5. 检索测试

入库后先不要直接接前端，先用命令行测试召回。

```powershell
cd keeperkit\backend
$env:INDEX_DIR = ".\data\index\coc7_clean"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

继续测试：

```powershell
python scripts\test_retrieval.py "孤注一掷失败会发生什么？"
python scripts\test_retrieval.py "困难成功和极难成功怎么算？"
python scripts\test_retrieval.py "战斗中闪避和反击怎么判定？"
python scripts\test_retrieval.py "理智检定失败后怎么处理？"
python scripts\test_retrieval.py "追逐中 MOV 怎么使用？"
```

当前 Hash 检索结果不一定很准。这里主要检查：

1. 索引能否正常读取。
2. chunk metadata 是否有 `source` 和 `title_path`。
3. 返回内容是否来自清洗后的章节。
4. 文本没有明显乱码。

## 6. 接入 FastAPI 问答接口

如果命令行检索能跑，再启动后端：

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_clean"
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

调用：

```http
POST /api/v1/rules/ask
```

请求体示例：

```json
{
  "question": "奖励骰和惩罚骰怎么计算？",
  "top_k": 8,
  "rerank_top_k": 3
}
```

当前 `generator.py` 还是模板生成器，不会调用真实 LLM，只会返回检索依据。

也就是说，现在接口的作用是验证：

```text
问题 -> 检索 -> sources -> 返回
```

不是最终自然语言回答。

## 7. 当前版本的局限

当前入库链路是开发验证版，有几个明显限制：

### 7.1 HashEmbeddingModel 不是真语义检索

它只是为了让系统不用下载模型也能跑起来。

实际问题如：

```text
"奖励骰怎么判？"
```

和规则书中的：

```text
"奖励骰和惩罚骰会影响十位骰"
```

Hash 检索未必能稳定匹配。

后续必须换成真正的中文/多语言 embedding 模型。

### 7.2 JsonVectorStore 不适合长期使用

JSON 索引适合开发验证。

后续应换成：

```text
ChromaDB
```

原因：

1. 支持高效向量检索。
2. 支持持久化 collection。
3. 支持 metadata filter。
4. 后续可以按规则书、章节、版本过滤。

### 7.3 当前切块策略还比较粗

当前按 Markdown 标题和字符长度切。

对普通段落够用，但对这些内容还不够理想：

```text
武器表
技能列表
怪物属性块
法术条目
模组段落
```

后续可以增加专门处理：

1. 表格独立成 chunk。
2. 怪物条目独立成 chunk。
3. 法术条目独立成 chunk。
4. 每个 chunk 保留 `page_start/page_end`。

## 8. 推荐验收问题集

入库后至少测试这些问题：

```text
奖励骰和惩罚骰怎么计算？
孤注一掷失败会发生什么？
困难成功和极难成功怎么算？
大失败怎么判定？
战斗轮中角色行动顺序怎么决定？
近战中闪避和反击有什么区别？
火器故障值是什么？
伤害加值怎么计算？
理智检定失败后怎么处理？
临时疯狂怎么判定？
追逐中 MOV 怎么影响行动？
魔法值如何恢复？
阅读神话典籍会发生什么？
法术施放需要什么成本？
怪物的护甲和伤害如何理解？
```

每个问题检查三点：

1. Top 3 是否来自正确章节。
2. source 是否能定位到具体文件和标题路径。
3. 返回片段是否足够完整，能支撑回答。

## 9. 后续升级路线

### 9.1 替换 Embedding

建议新增一个真实 embedding 实现：

```text
backend/app/rag/embeddings_bge.py
```

候选模型：

```text
BAAI/bge-small-zh-v1.5
BAAI/bge-m3
```

### 9.2 替换向量库

新增：

```text
backend/app/rag/chroma_store.py
```

保留统一接口：

```python
save(chunks)
search(query, top_k)
```

### 9.3 增加 Rerank

第一版可以用：

```text
BAAI/bge-reranker-v2-m3
```

流程变成：

```text
query
  -> Chroma Top 20
  -> Rerank Top 5
  -> LLM grounded answer
```

### 9.4 接入真实 LLM 回答

当前 `TemplateRuleGenerator` 只是返回检索依据。

后续替换成 DeepSeek/Qwen 调用后，Prompt 必须要求：

1. 只基于检索片段回答。
2. 规则未检索到时明确说没有依据。
3. 涉及数值时列步骤。
4. 回答末尾列出引用来源。

## 10. 建议当前操作顺序

现在最合理的下一步是：

```powershell
cd keeperkit\backend
$env:RAW_DOCS_DIR = ".\data\raw\private\clean_markdown_chapters"
$env:INDEX_DIR = ".\data\index\coc7_clean"
python scripts\ingest_rules.py
```

然后跑：

```powershell
$env:INDEX_DIR = ".\data\index\coc7_clean"
python scripts\test_retrieval.py "奖励骰和惩罚骰怎么计算？"
```

如果能召回清洗后的章节，就说明 V0 入库闭环完成。

之后再进入真正提高效果的阶段：

```text
HashEmbeddingModel -> BGE
JsonVectorStore -> ChromaDB
SimpleReranker -> BGE Reranker
TemplateRuleGenerator -> DeepSeek grounded answer
```
