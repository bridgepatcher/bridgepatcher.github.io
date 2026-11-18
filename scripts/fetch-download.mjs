#!/usr/bin/env node
// Finds the newest release of the patcher that still has a downloadable
// BridgePatcher.pkg, for the homepage's "Download latest version" button.
//
// GitHub's /releases/latest/download/<file> always points at the newest
// published release, even if that release has no such file (assets not
// uploaded yet, or removed again) - the button then ends in a 404. So the
// newest release is skipped while its .pkg is missing, and the button links
// to the previous release that still has one.
//
// Writes .vitepress/download.json ({ tag, url }), a git-ignored build artifact
// read by .vitepress/config.mts. The CI workflow runs this script before
// `vitepress build`. Locally:
//   GITHUB_TOKEN=$(gh auth token) node scripts/fetch-download.mjs
//
// Never fails the build: if the releases can't be read, the file is removed
// and the button keeps its /releases/latest/download/ link.

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const OUT_JSON = path.join(ROOT, '.vitepress', 'download.json')

const REPO = process.env.DOWNLOAD_REPO || 'bridgepatcher/BridgePatcher'
const ASSET = process.env.DOWNLOAD_ASSET || 'BridgePatcher.pkg'
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN

// Newest published, non-pre-release with a fully uploaded asset named `asset`
// (same releases /releases/latest/ would consider), or null.
export function pickRelease(releases, asset = ASSET) {
  const candidates = releases
    .filter((r) => !r.draft && !r.prerelease && r.published_at)
    .sort((a, b) => b.published_at.localeCompare(a.published_at))
  for (const release of candidates) {
    const file = (release.assets || []).find((a) => a.name === asset && a.state === 'uploaded')
    if (file) return { tag: release.tag_name, url: file.browser_download_url }
  }
  return null
}

async function fetchReleases() {
  const res = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=30`, {
    headers: {
      'Accept': 'application/vnd.github+json',
      'User-Agent': 'oclp-t2-website',
      ...(TOKEN ? { Authorization: `bearer ${TOKEN}` } : {}),
    },
  })
  if (!res.ok) throw new Error(`GitHub API responded with ${res.status} ${res.statusText}`)
  return res.json()
}

async function main() {
  try {
    const releases = await fetchReleases()
    const picked = pickRelease(releases)
    if (!picked) throw new Error(`no published release of ${REPO} has ${ASSET}`)
    fs.mkdirSync(path.dirname(OUT_JSON), { recursive: true })
    fs.writeFileSync(OUT_JSON, `${JSON.stringify(picked, null, 2)}\n`)
    const newest = releases.find((r) => !r.draft && !r.prerelease)
    if (newest && newest.tag_name !== picked.tag) {
      console.warn(`::warning::Newest release ${newest.tag_name} has no ${ASSET} - `
        + `the download button links to ${picked.tag} instead.`)
    }
    console.log(`Download button: ${picked.url}`)
  } catch (err) {
    fs.rmSync(OUT_JSON, { force: true })
    console.warn(`::warning::Could not resolve the download link (${err.message}) - `
      + 'the button keeps its /releases/latest/download/ link.')
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) main()
