import { createRouter, createWebHashHistory } from 'vue-router'

// 使用 hash 路由，刷新调试台时无需额外配置 Web 服务器的页面回退规则。
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/model-configs' },
    { path: '/model-configs', component: () => import('./views/ModelConfigs.vue') },
    { path: '/playground', component: () => import('./views/Playground.vue') },
  ],
})
