# Web 前端

Vue 3 + TypeScript + Vite + Element Plus。使用兼容 Vite 的 Node.js 版本（本机已使用 Node.js 24 验证）。

在本目录执行：

```powershell
npm install
npm run dev
```

访问 http://localhost:5173 。执行 `npm run build` 进行类型检查并构建。

## 模型配置管理

首页提供模型配置列表、新增、编辑、删除确认和分页，每页 20 条。接入方式支持 OpenAI 兼容、Ollama、Anthropic、Google GenAI，与后端枚举一致。

表格、表单、字段校验、弹窗、分页、加载状态与提示使用 Element Plus，组件通过 `unplugin-vue-components` 自动按需导入，不全量注册。`App.vue` 中的 Config Provider 统一设置中文。

API Key 不回显。编辑时留空保留原密钥，填写新值替换，勾选“清除已保存的 API Key”则提交 null。删除前需要确认；保存或删除失败时保留弹窗，显示错误后可以重试。请求进行中禁止重复提交和关闭操作弹窗。

先启动 Python 后端（默认 `http://127.0.0.1:8000`），再启动前端。页面请求 `/api/model-configs`，由 `vite.config.ts` 的开发代理转发到后端。后端地址不同时修改代理目标即可；不需要添加后端跨域配置。

## 文件职责

| 文件 | 职责 |
|---|---|
| `src/App.vue` | 应用外壳、中文组件配置、页面入口 |
| `src/views/ModelConfigs.vue` | 模型配置页面、表单校验、分页及交互状态 |
| `src/api/modelConfigs.ts` | 请求与响应类型、列表和增删改接口 |
| `src/components.d.ts` | 自动生成的组件与指令类型声明，供 IDE 和类型检查使用 |
| `src/style.css` | 应用布局、主题颜色与小屏适配，控件样式交给组件库 |
| `vite.config.ts` | Vue 构建、Element Plus 按需导入和本地 `/api` 代理 |

接口继续使用浏览器原生 fetch。`src/components.d.ts` 在启动或构建时生成，随项目保存，不手工修改。Vite 的代理仅用于开发环境；部署时需要由 Web 服务器把 `/api` 转发到后端。

## 后续流程编排选型

流程画布采用 Vue Flow，负责节点拖动、连线、缩放和节点展示；后端负责执行流程。当前先完成模型管理，尚未安装画布组件或实现编排页面。

出现多个页面时再引入 Vue Router；流程编辑需要多个组件共享状态时再引入 Pinia。流程执行层到对应阶段再评估 LangGraph，不在当前前端引入整套 Dify 或 Coze 平台。

修改接口、字段或密钥处理方式时，同步维护本文档、[页面文档](src/views/README.md)和 [API 文档](src/api/README.md)。
