# 业务页面

本目录按业务维护 Vue 页面，`App.vue` 只保留应用外壳和页面装配。

## 模型配置页

`ModelConfigs.vue` 使用 Element Plus 的 Table、Form、Dialog、Pagination、Alert、Loading 等组件。`vite.config.ts` 的自动导入插件负责加载使用到的组件和样式，无需逐个注册。

| 入口 | 用途 |
|---|---|
| `loadModels` | 加载分页列表，删除末页最后一条记录时退回有效页码 |
| `openEditor` / `submitModel` | 回填公开字段、校验表单、提交新增或修改 |
| `openDelete` / `confirmDelete` | 确认后删除，失败时保留弹窗供重试 |

表单检查模型名称、模型标识、接入方式和 HTTP/HTTPS 服务地址，长度限制与后端保持一致；后端仍执行最终校验。

API Key 不从响应回填，不写入浏览器存储。编辑时留空保留，填写新值替换，勾选清除则提交 null。关闭编辑弹窗时清空输入的 Key。

API 请求统一使用 `src/api/modelConfigs.ts`，页面负责加载、错误和提交状态。普通列表请求失败时保留原列表并显示错误提示；保存、删除失败时不关闭弹窗。写入期间禁止重复操作，成功后刷新列表。

新增页面时更新本目录文档；模型字段、交互或密钥语义变化时，同步更新页面、接口类型和前端根目录 README。
