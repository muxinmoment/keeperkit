# RAG Step 08：前端接入真实问答接口

## 本步目标

让 React 前端明确接入真实后端接口：

```text
POST /api/v1/rules/ask
```

并把 `top_k` 与 `rerank_top_k` 暴露到界面，方便对比 simple reranker 和 BGE reranker 的效果。

## 修改内容

更新 API 客户端：

```text
frontend/src/api/rules.ts
```

新增请求类型：

```ts
type RuleAskRequest = {
  question: string;
  top_k?: number;
  rerank_top_k?: number;
};
```

更新界面：

```text
frontend/src/components/ChatPanel.tsx
frontend/src/components/SourceList.tsx
frontend/src/styles/globals.css
```

新增前端环境变量示例：

```text
frontend/.env.example
```

## 运行方式

后端：

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

前端：

```powershell
cd keeperkit\frontend
npm install
npm run dev
```

默认 API 地址：

```text
http://127.0.0.1:8000
```

如需修改：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 当前行为

前端提交请求时会发送：

```json
{
  "question": "孤注一掷失败后会发生什么？",
  "top_k": 20,
  "rerank_top_k": 5
}
```

后端返回后，界面会展示：

```text
assistant answer
sources source/title/score/content_preview
```

后端已经启用 CORS，因此 Vite 开发服务器可以直接访问 `http://127.0.0.1:8000`。
