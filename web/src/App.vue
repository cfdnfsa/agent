<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import ModelConfigs from './views/ModelConfigs.vue'
</script>

<template>
  <!-- 分页、弹窗等组件统一使用中文；业务页面与应用外壳分开维护。 -->
  <el-config-provider :locale="zhCn">
    <header class="app-header">
      <div class="header-content">
        <a class="brand" href="/" aria-label="AI Agent 首页">
          <span class="brand-icon">A</span> AI Agent
        </a>
        <span class="header-divider"></span>
        <span class="header-section">配置管理</span>
      </div>
    </header>
    <main class="page"><ModelConfigs /></main>
  </el-config-provider>
</template>
