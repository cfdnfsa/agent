import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    // 按页面实际使用的标签加载组件和样式，并生成 IDE 使用的组件类型声明。
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  // 浏览器统一请求 /api，由开发服务器转发到后端，避免本地开发的跨域问题。
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
