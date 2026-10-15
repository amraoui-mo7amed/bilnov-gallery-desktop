import path from 'path'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import { syncFeeds } from './scripts/sync-feeds.js'

function feedSyncPlugin(): Plugin {
  return {
    name: 'feed-sync-plugin',
    buildStart() {
      syncFeeds()
    },
    configureServer(server) {
      syncFeeds()
      const feedsDir = path.resolve(import.meta.dirname, '../../feeds')
      server.watcher.add(feedsDir)
      server.watcher.on('all', (_event, filePath) => {
        if (typeof filePath === 'string' && filePath.startsWith(feedsDir)) {
          syncFeeds()
        }
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), feedSyncPlugin()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
})
