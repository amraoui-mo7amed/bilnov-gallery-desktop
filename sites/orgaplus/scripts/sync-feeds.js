import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const FEEDS_SRC = path.resolve(ROOT, '../../feeds')
const FEEDS_DEST = path.resolve(ROOT, 'public/feeds')
const OUTPUT_JSON = path.resolve(ROOT, 'src/data/discoveredFeeds.json')

function naturalSort(a, b) {
  const numA = parseInt((a.match(/\d+/) || [NaN])[0], 10)
  const numB = parseInt((b.match(/\d+/) || [NaN])[0], 10)
  if (!isNaN(numA) && !isNaN(numB) && numA !== numB) {
    return numA - numB
  }
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

export function syncFeeds() {
  if (!fs.existsSync(FEEDS_SRC)) {
    console.log('[sync-feeds] No root feeds/ directory found, skipping.')
    return []
  }

  fs.mkdirSync(FEEDS_DEST, { recursive: true })
  fs.cpSync(FEEDS_SRC, FEEDS_DEST, { recursive: true, force: true })
  console.log(`[sync-feeds] Synchronized ${FEEDS_SRC} -> ${FEEDS_DEST}`)

  const discovered = []
  const imageExts = new Set(['.jpg', '.jpeg', '.png', '.webp', '.bmp'])

  function walk(currentDir, relPath = '') {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true })
    const files = entries.filter((e) => e.isFile())
    const dirs = entries.filter((e) => e.isDirectory())

    const images = files
      .filter((f) => imageExts.has(path.extname(f.name).toLowerCase()))
      .map((f) => f.name)
      .sort(naturalSort)

    if (images.length > 0) {
      const segments = relPath.split(path.sep).filter(Boolean)
      const folderName = path.basename(currentDir)
      const category = segments.length >= 3 ? segments[0] : (segments[0] || 'Scenes')
      const subcategory = segments.length >= 3 ? segments[1] : (segments[1] || 'Exteriors')
      const cleanTitle = folderName
        .replace(/^\d+[_\s-]*/, '')
        .replace(/_/g, ' ')
        .trim()

      const imageUrls = images.map((img) => `/feeds/${relPath}/${img}`.replace(/\\/g, '/'))

      discovered.push({
        id: folderName.toLowerCase().replace(/[^a-z0-9_-]/g, '_'),
        rawFolder: folderName,
        title: cleanTitle.length > 0 ? cleanTitle : folderName,
        category,
        subcategory,
        format: '.skp',
        imageUrls,
        imageUrl: imageUrls[0],
        relPath: relPath.replace(/\//g, '\\'),
      })
    }

    for (const dir of dirs) {
      walk(path.join(currentDir, dir.name), relPath ? `${relPath}/${dir.name}` : dir.name)
    }
  }

  walk(FEEDS_SRC)

  fs.mkdirSync(path.dirname(OUTPUT_JSON), { recursive: true })
  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(discovered, null, 2), 'utf-8')
  console.log(`[sync-feeds] Discovered ${discovered.length} asset folders from feeds/. Saved to ${OUTPUT_JSON}`)
  return discovered
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  syncFeeds()
}
