import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

export default defineConfig({
  plugins: [vue(), {
    name: 'offline-file-list',
    closeBundle() {
      const walk = (dir: string, prefix = ''): string[] => readdirSync(dir, { withFileTypes: true }).flatMap(entry =>
        entry.isDirectory() ? walk(join(dir, entry.name), prefix + entry.name + '/') : ['/' + prefix + entry.name])
      writeFileSync('dist/precache.json', JSON.stringify(walk('dist').filter(f => f !== '/sw.js' && f !== '/precache.json')))
      writeFileSync('dist/sw.js', readFileSync('dist/sw.js','utf8').replace('pp-daily-v1', 'pp-daily-' + Date.now()))
    },
  }],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { target: 'safari17' },
})
