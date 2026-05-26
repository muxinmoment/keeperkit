# Step 02 模组导入与问答

这一步把模组资料真正接进来了。

## 已完成

- 新增模组文件加载器，支持 Markdown、TXT、PDF。
- 新增上传接口，可以把文件保存到当前模组的 `documents/` 目录。
- 新增模组入库服务，能把模组切块并写入独立索引。
- 新增模组问答服务和接口。
- 新增模组来源结构，能区分模组知识库信息。

## 现在能做什么

- 把模组文件放进 `backend/data/modules/private/<module_id>/documents/`。
- 或者调用 `POST /api/v1/modules/{module_id}/upload` 上传文件。
- 调用 `POST /api/v1/modules/{module_id}/ingest` 建索引。
- 调用 `POST /api/v1/modules/{module_id}/ask` 做模组问答。

## 下一步

- 做前端模组列表和当前模组选择器。
- 接上导入按钮和基础工作台。
- 让用户在界面里直接看到模组与来源。
