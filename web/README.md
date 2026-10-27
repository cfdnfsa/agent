# Web 前端

Vue 3 + TypeScript + Vite + Element Plus + Vue Router。使用兼容 Vite 的 Node.js 版本（本机已使用 Node.js 24 验证）。

当前是个人极简版本：不主动做字段必填、长度、URL、枚举等业务校验，也不自动去空格。输入原样提交，失败时显示后端或 SDK 返回的公开说明；维护规则见 [AGENTS.md](AGENTS.md)。

在本目录执行：

```powershell
npm install
npm run dev
```

访问 http://localhost:5173 。执行 `npm run build` 进行类型检查并构建。

顶部导航切换“模型配置”和“调试台”。页面使用 hash 路由：`/#/model-configs` 与 `/#/playground`，刷新子页面无需额外配置服务器回退规则。

## 调试台

选择已保存的模型，输入问题后发送，回答以聊天气泡完整展示。每次请求只提交模型配置ID和当前问题，不携带旧气泡中的消息，没有上下文记忆，也不保存聊天记录。切换模型、清空、导航离开或刷新页面会清除气泡。问题没有前端长度或空内容限制，不自动去空格，失败时保留输入供重试。

模型选择复用列表接口，分页读取全部已配置模型；没有模型时提示先到模型配置页添加。发送中禁止切换模型或重复发送，等待期间显示“正在回答”。

## 模型配置管理

模型配置页提供列表、新增、编辑、删除确认和分页，每页默认 20 条。接入方式提供 OpenAI 兼容、Ollama、Anthropic、Google GenAI 常用选项，也允许手工填写；保存时不检查枚举，实际能否调用由对应集成决定。

每条配置的“测试”按钮调用 `POST /api/model-configs/{id}/test`，验证已保存的模型配置。测试期间显示加载状态并禁止重复操作；成功展示耗时，失败展示错误说明。它会发送真实模型请求，可能消耗少量额度，不保存测试历史，也不展示 Key 或模型原始回复。

表格、表单、弹窗、分页、加载状态与提示使用 Element Plus，已移除表单校验、必填标记和输入限制。组件通过 `unplugin-vue-components` 自动按需导入，不全量注册。`App.vue` 中的 Config Provider 统一设置中文。

API Key 不回显。编辑时留空保留原密钥，填写新值替换，勾选“清除已保存的 API Key”则提交 null。删除前需要确认；保存或删除失败时保留弹窗，显示错误后可以重试。请求进行中禁止重复提交和关闭操作弹窗。

先启动 Python 后端（默认 `http://127.0.0.1:8000`），再启动前端。页面请求 `/api/model-configs`，由 `vite.config.ts` 的开发代理转发到后端。后端地址不同时修改代理目标即可；不需要添加后端跨域配置。

## 文件职责

| 文件 | 职责 |
|---|---|
| `src/App.vue` | 应用外壳、中文组件配置、页面入口 |
| `src/views/ModelConfigs.vue` | 模型配置页面、原样提交表单、分页及交互状态 |
| `src/views/Playground.vue` | 模型选择与单轮问答接口装配 |
| `src/components/ChatPanel.vue` | 可复用的输入、消息气泡和发送状态 |
| `src/router.ts` | 模型配置与调试台页面路由 |
| `src/api/modelConfigs.ts` | 请求与响应类型、列表和增删改接口 |
| `src/api/playground.ts` | 提交当前问题，取得回答 |
| `src/api/request.ts` | 共用 fetch 与统一响应处理 |
| `src/components.d.ts` | 自动生成的组件与指令类型声明，供 IDE 和类型检查使用 |
| `src/style.css` | 应用布局、主题颜色与小屏适配，控件样式交给组件库 |
| `vite.config.ts` | Vue 构建、Element Plus 按需导入和本地 `/api` 代理 |

接口继续使用浏览器原生 fetch。`src/components.d.ts` 在启动或构建时生成，随项目保存，不手工修改。Vite 的代理仅用于开发环境；部署时需要由 Web 服务器把 `/api` 转发到后端。

## 后续流程编排选型

流程画布采用 Vue Flow，负责节点拖动、连线、缩放和节点展示；后端负责执行流程。当前先完成模型管理，尚未安装画布组件或实现编排页面。

两个页面通过 Vue Router 切换；流程编辑需要多个组件共享状态时再引入 Pinia。流程执行层到对应阶段再评估 LangGraph。ChatPanel 通过提交函数复用展示，后续流程调试可接入对应接口，不提前增加未实现的流程或参数选项。

修改接口、字段或密钥处理方式时，同步维护本文档、[页面文档](src/views/README.md)和 [API 文档](src/api/README.md)。
