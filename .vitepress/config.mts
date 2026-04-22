import { defineConfig } from 'vitepress'
import { generateSidebar } from 'vitepress-sidebar'
import fs from 'node:fs'
import path from 'node:path'
// @ts-ignore
import texmath from 'markdown-it-texmath'
import katex from 'katex'
// @ts-ignore
import markdownItMark from 'markdown-it-mark'
import { headupPlugin } from 'vitepress-headup/plugin'

const firstfile = (subDir: string) => {
  const docsRoot = '.'
  const fullPath = path.resolve(process.cwd(), docsRoot, subDir)
  
  const folderName = path.basename(subDir)
  
  try {
    if (!fs.existsSync(fullPath)) return '#'
    
    const files = fs.readdirSync(fullPath)
      .filter(file => {
        const isMd = file.endsWith('.md');
        const isIndex = file.toLowerCase().includes('index');
        const isSameName = file.replace('.md', '') === folderName;
        
        return isMd && !isIndex && !isSameName;
      })
      .sort()
    
    return files.length > 0 ? `${subDir}/${files[0].replace('.md', '')}` : '#'
  } catch (e) {
    return '#'
  }
}

const folders = ['physik', 'compact']

export default defineConfig({
  base: "/",
  vite: {
    plugins: [
      headupPlugin({
        hud: {
          enabled: true,
          label: '{commit}',
          title: 'Git commit {commit}'
        },
        detail: {
          enabled: true,
          title: 'Archive status',
          iconLabel: 'Open archive status'
        },
        lastUpdated: {
          include: ['compact', 'physik', '.vitepress', 'index.md', 'package.json']
        },
        custom: {
          project: 'physics compact archive'
        }
      })
    ],
    server: {
      allowedHosts: true
    }
  },
  title: "Archive",
  ignoreDeadLinks: true,
  description: "Physics Archive",
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['link', { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css' }],
    ['link', { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/markdown-it-texmath/css/texmath.min.css' }]
  ],
  markdown: {
    config: (md) => {
      md.use(markdownItMark)
      md.use(texmath, {
        engine: katex,
        delimiters: 'dollars',
        katexOptions: { macros: { "\\RR": "\\mathbb{R}" } }
      })
    }
  },
  themeConfig: {
    nav: [
      {
        text: 'notes',
        items: [
          { text: 'Home', link: '/' },
          { text: 'Weltbild', link: firstfile('physik/01_weltbild') },
          { text: 'Elektrizität', link: firstfile('physik/02_elektrizitaet') },
          { text: 'Elektromagnetismus', link: firstfile('physik/03_elektromagnetismus') },
          { text: 'Gravitationstheorie', link: firstfile('physik/04_gravitationstheorie') },
          { text: 'Rätsel', link: firstfile('physik/99_raetsel') }
        ]
      },
      {
        text: 'Compact',
        items: [{ text: 'Compact', link: '/compact/index.md' }]
      }
    ],
sidebar: generateSidebar(
      folders.map(folder => ({
        scanStartPath: folder,
        resolvePath: `/${folder}/`,
        useTitleFromFrontmatter: true,
        collapsed: true,
        hyphenToSpace: true,
        sortByFileName: true,
        underscoreToSpace: true,
        includeRootIndexFile: false,
        removePrefixAfterMatch: true, 
        prefixSeparator: '_',
        useFolderLinkFromSameNameSubFile: true,
      }))
    ),
    socialLinks: [
      { icon: 'github', link: 'https://github.com/tangxiaoyi97/p3' },
      { icon: 'discord', link: 'https://discord.gg/byDV7RpK' },
      { icon: 'buymeacoffee', link: 'https://buymeacoffee.com/tangxy97' }

    ]
  }
})
