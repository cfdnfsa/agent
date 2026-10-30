<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <!-- 分页、弹窗等组件统一使用中文；业务页面与应用外壳分开维护。 -->
  <el-config-provider :locale="zhCn">
    <header v-if="!route.meta.fullscreen" class="app-header">
      <div class="header-content">
        <RouterLink class="brand" to="/model-configs" aria-label="AI Agent 首页">
          <span class="brand-icon">A</span> AI Agent
        </RouterLink>
        <span class="header-divider"></span>
        <nav class="app-nav" aria-label="主导航">
          <RouterLink to="/model-configs">模型配置</RouterLink>
          <RouterLink to="/prompt-configs">提示词配置</RouterLink>
          <RouterLink to="/workflow-configs" :class="{ 'router-link-active': route.path.startsWith('/workflow-configs') }">流程配置</RouterLink>
          <RouterLink to="/playground">调试台</RouterLink>
        </nav>
      </div>
    </header>
    <main :class="route.meta.fullscreen ? 'page-fullscreen' : 'page'"><RouterView /></main>
  </el-config-provider>
</template>
