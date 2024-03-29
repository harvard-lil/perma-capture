import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  return {
    base: mode == 'development' ? '/vite/' : '/static/',
    plugins: [vue({
      template: {
        compilerOptions: {
          isCustomElement: tag => tag === 'replay-web-page'
        }
      }
    })],
    build: {
      outDir: '../main/static/',
      assetsDir: 'vite',
      // generate manifest.json in outDir
      manifest: true,
      rollupOptions: {
        // overwrite default .html entry
        input: 'src/main.ts'
      }
    }
  }
})
