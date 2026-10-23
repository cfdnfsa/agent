# Agent 后端

Python 3.12+ + FastAPI + Uvicorn，使用 uv 管理依赖。

在本目录执行：

```powershell
uv sync --locked
uv run python -m uvicorn main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看接口文档。当前未添加业务接口。
