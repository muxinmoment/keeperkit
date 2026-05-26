# RAG Step 10：固定后端启动环境

## 本步目标

后端必须使用 `keeperkit` conda 环境启动，否则容易回到 Anaconda base：

```text
D:\anaconda3\python.exe
```

base 环境里曾经是 CPU 版 PyTorch，会导致：

```text
torch.cuda.is_available() = False
BGE reranker 不走 GPU
依赖版本和 keeperkit 环境不一致
```

本步新增一个明确使用 keeperkit 环境的启动脚本。

## 启动脚本

```text
backend/scripts/start_backend.ps1
```

默认使用：

```text
D:\anaconda3\envs\keeperkit\python.exe
```

并默认设置：

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
```

这样后端启动时会直接使用本地 Hugging Face 模型缓存，不会因为访问 `huggingface.co` 超时而卡住。

## 推荐启动方式

项目根目录：

```powershell
.\backend\scripts\start_backend.ps1
```

开启开发 reload：

```powershell
.\backend\scripts\start_backend.ps1 -Reload
```

如果需要重新联网检查或下载 Hugging Face 模型：

```powershell
.\backend\scripts\start_backend.ps1 -OnlineHuggingFace
```

## 验证方式

启动后访问：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health
```

期望：

```text
200 OK
```

确认 8000 端口对应环境：

```powershell
Get-NetTCPConnection -LocalPort 8000 |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

再用进程 ID 查看路径：

```powershell
Get-Process -Id <PID> | Select-Object Path
```

期望：

```text
D:\anaconda3\envs\keeperkit\python.exe
```

## 注意

如果前端显示：

```text
Failed to fetch
```

先检查后端健康接口是否可访问。多数情况下是后端没有启动、启动在错误环境，或模型加载阶段卡在 Hugging Face 远程检查。
