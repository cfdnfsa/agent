# AI Agent 工作流平台

仓库包含两个独立工程，各自在自己的目录中安装依赖、启动和使用 IDE 打开。

```text
web/    Vue 3 + TypeScript + Vite 前端
agent/  Python 3.12+ + FastAPI 后端
```

- [前端启动说明](web/README.md)
- [后端启动与 PyCharm 配置](agent/README.md)
- [技术方案](1.md)

使用 PyCharm 打开本目录后，可在右上角选择 `agent` 运行配置并启动后端；该配置使用 `agent/.venv` 中的解释器。
