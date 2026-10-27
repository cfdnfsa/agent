# AI Agent 工作流平台

仓库包含两个独立工程，各自在自己的目录中安装依赖、启动和使用 IDE 打开。

当前按个人使用的极简版本维护：配置输入原样保存，不增加业务字段校验、前端输入限制、重复 DTO 或无必要转换。数据库已有约束和框架/SDK 基础要求仍然生效。规则见 [后端规则](agent/AGENTS.md) 和 [前端规则](web/AGENTS.md)。

```text
web/    Vue 3 + TypeScript + Vite 前端
agent/  Python 3.12+ + FastAPI 后端
```

- [前端启动说明](web/README.md)
- [后端启动与 PyCharm 配置](agent/README.md)
- [技术方案](1.md)

使用 PyCharm 打开本目录后，可在右上角选择 `agent` 运行配置并启动后端；该配置使用 `agent/.venv` 中的解释器。
