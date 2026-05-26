# Step 10 PostgreSQL 会话记忆

这一步把 LangGraph 的会话状态接到 PostgreSQL。

## 已完成

- 在 `keeperkit` Python 环境安装 `langgraph-checkpoint-postgres`。
- 新增 PostgreSQL checkpointer 依赖。
- 新增后端配置：
  - `LANGGRAPH_CHECKPOINTER`
  - `LANGGRAPH_POSTGRES_URI`
- 本地 `.env` 已配置为 PostgreSQL。
- 每个模组会生成稳定的 `thread_id`。
- LangGraph 调用会携带 `configurable.thread_id`。
- 前端会显示当前备团草稿使用的 thread 简短编号。

## 现在能做什么

- 同一个模组的备团草稿会使用同一个 LangGraph thread。
- 章节修改不是重新开新会话，而是围绕同一个 thread 继续。
- PostgreSQL 可作为 LangGraph checkpoint 存储。

## 本地配置

`.env` 使用：

```env
LANGGRAPH_CHECKPOINTER=postgres
LANGGRAPH_POSTGRES_URI=postgresql://postgres:你的密码@127.0.0.1:5432/keeperkit
```

真实密码只写在本地 `.env`，不提交到 git。

## 当前限制

- 仍保留 `processed/prep_draft.json` 作为可读草稿备份。
- 如果 PostgreSQL 数据库不存在，需要先创建 `keeperkit` 数据库。
- 后续可以把文件草稿也迁移到 PostgreSQL 表中。
