#!/usr/bin/env node
// Mirrors the patcher's GitHub Discussions and issues into the website.
// Every list: pinned items first (in pin order), then the newest. Closed
// discussions/issues are left out, so closing one removes it from the site.
//
//   /announcements/  STRICTLY announcements: open discussions in the
//                    ANNOUNCEMENTS_CATEGORY (default "announcements") that were
//                    written by a maintainer (owner, member or collaborator).
//   /discussions/    every other open discussion (all other categories, plus
//                    posts by non-maintainers that ended up in Announcements)
//   /issues/         open issues
//
// Writes:
//   .vitepress/announcements.json  - read at build time to generate
//                                    /announcements/ and one page per post
//   public/announcements.xml       - RSS 2.0 feed of the same posts
//   public/notify.json             - newest announcements for browser notifications
//   .vitepress/discussions.json    - same for /discussions/
//   public/discussions.xml         - RSS 2.0 feed of the other discussions
//   .vitepress/issues.json         - same for /issues/
//   public/issues.xml              - RSS 2.0 feed of the open issues
//
// All six files are build artifacts (git-ignored). The CI workflow runs this
// script before `vitepress build`. Locally:
//   GITHUB_TOKEN=$(gh auth token) yarn announcements
//
// The GitHub GraphQL API needs a token even for public data; the workflow's
// built-in GITHUB_TOKEN is enough since the patcher repo is public.

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const OUT_JSON = path.join(ROOT, '.vitepress', 'announcements.json')
const OUT_FEED = path.join(ROOT, 'public', 'announcements.xml')
// Latest announcements for the notification service worker (public/notify-sw.js).
const OUT_NOTIFY = path.join(ROOT, 'public', 'notify.json')
const OUT_DISCUSSIONS_JSON = path.join(ROOT, '.vitepress', 'discussions.json')
const OUT_DISCUSSIONS_FEED = path.join(ROOT, 'public', 'discussions.xml')
const OUT_ISSUES_JSON = path.join(ROOT, '.vitepress', 'issues.json')
const OUT_ISSUES_FEED = path.join(ROOT, 'public', 'issues.xml')

const REPO = process.env.ANNOUNCEMENTS_REPO || 'bridgepatcher/BridgePatcher'
const CATEGORY = process.env.ANNOUNCEMENTS_CATEGORY || 'announcements'
const LIMIT = Number(process.env.ANNOUNCEMENTS_LIMIT || 100)
// Discussions of all categories are fetched in one go and split afterwards.
const DISCUSSIONS_LIMIT = Number(process.env.DISCUSSIONS_LIMIT || 300)
// Only posts by these GitHub author associations count as announcements.
const MAINTAINER_ROLES = new Set(['OWNER', 'MEMBER', 'COLLABORATOR'])
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN

const SITE_URL = 'https://bridgepatcher.github.io/'
const SITE_TITLE = 'BridgePatcher'

const [OWNER, NAME] = REPO.split('/')

// Note: repository.discussionCategory(slug:) can't be resolved with a GitHub
// Actions token ("Could not resolve to a DiscussionCategory"), so list the
// categories and pick the right one by slug instead.
const CATEGORIES_QUERY = `
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    discussionCategories(first: 100) { nodes { id name slug } }
  }
}`

const DISCUSSION_FIELDS = `
fragment AnnouncementFields on Discussion {
  id
  number
  title
  url
  closed
  createdAt
  updatedAt
  lastEditedAt
  bodyHTML
  bodyText
  author { login url }
  authorAssociation
  category { name slug }
  comments { totalCount }
}`

// Comments of a discussion, each with its replies (threaded).
const DISCUSSION_COMMENT_FIELDS = `
fragment DiscussionReplyFields on DiscussionComment {
  url
  createdAt
  lastEditedAt
  isMinimized
  bodyHTML
  author { login url }
}`

const DISCUSSION_COMMENTS_QUERY = `
query ($id: ID!, $after: String) {
  node(id: $id) {
    ... on Discussion {
      comments(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isAnswer
          ...DiscussionReplyFields
          replies(first: 50) {
            pageInfo { hasNextPage endCursor }
            nodes { ...DiscussionReplyFields }
          }
        }
      }
    }
  }
}
${DISCUSSION_COMMENT_FIELDS}`

const MORE_REPLIES_QUERY = `
query ($id: ID!, $after: String) {
  node(id: $id) {
    ... on DiscussionComment {
      replies(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes { ...DiscussionReplyFields }
      }
    }
  }
}
${DISCUSSION_COMMENT_FIELDS}`

const DISCUSSIONS_QUERY = `
query ($owner: String!, $name: String!, $category: ID, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: $first, after: $after, categoryId: $category, states: [OPEN],
                orderBy: { field: CREATED_AT, direction: DESC }) {
      pageInfo { hasNextPage endCursor }
      nodes { ...AnnouncementFields }
    }
  }
}
${DISCUSSION_FIELDS}`

const PINNED_QUERY = `
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pinnedDiscussions(first: 25) {
      nodes { discussion { ...AnnouncementFields } }
    }
  }
}
${DISCUSSION_FIELDS}`

const ISSUE_COMMENT_FIELDS = `
fragment IssueCommentFields on IssueComment {
  url
  createdAt
  lastEditedAt
  isMinimized
  bodyHTML
  author { login url }
}`

const ISSUE_FIELDS = `
fragment IssueFields on Issue {
  id
  number
  title
  url
  closed
  createdAt
  updatedAt
  lastEditedAt
  bodyHTML
  bodyText
  author { login url }
  labels(first: 10) { nodes { name color } }
  comments(first: 100) {
    totalCount
    pageInfo { hasNextPage endCursor }
    nodes { ...IssueCommentFields }
  }
}
${ISSUE_COMMENT_FIELDS}`

const MORE_COMMENTS_QUERY = `
query ($id: ID!, $after: String) {
  node(id: $id) {
    ... on Issue {
      comments(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes { ...IssueCommentFields }
      }
    }
  }
}
${ISSUE_COMMENT_FIELDS}`

const ISSUES_QUERY = `
query ($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: $first, after: $after, states: [OPEN],
           orderBy: { field: CREATED_AT, direction: DESC }) {
      pageInfo { hasNextPage endCursor }
      nodes { ...IssueFields }
    }
  }
}
${ISSUE_FIELDS}`

const PINNED_ISSUES_QUERY = `
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pinnedIssues(first: 3) {
      nodes { issue { ...IssueFields } }
    }
  }
}
${ISSUE_FIELDS}`

async function graphql(query, variables) {
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: {
      'Authorization': `bearer ${TOKEN}`,
      'Content-Type': 'application/json',
      'User-Agent': 'oclp-t2-website',
    },
    body: JSON.stringify({ query, variables }),
  })
  if (!res.ok) {
    throw new Error(`GitHub API responded with ${res.status} ${res.statusText}`)
  }
  const json = await res.json()
  if (json.errors?.length) {
    throw new Error(json.errors.map((e) => e.message).join('; '))
  }
  return json.data
}

// GitHub renders uploaded images/videos as private-user-images.githubusercontent.com
// URLs carrying a JWT that expires after 5 minutes, so on the built site they
// break almost immediately. Swap them for the permanent
// github.com/user-attachments/assets/<id> URL, which redirects to a freshly
// signed one every time it is loaded.
const PRIVATE_ATTACHMENT = /https:\/\/private-user-images\.githubusercontent\.com\/\d+\/\d+-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.[A-Za-z0-9]+\?jwt=[A-Za-z0-9._-]+/g

const stableAttachments = (html) =>
  (html || '').replace(PRIVATE_ATTACHMENT, 'https://github.com/user-attachments/assets/$1')

function excerpt(text, max = 220) {
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  if (clean.length <= max) return clean
  const cut = clean.slice(0, max)
  const space = cut.lastIndexOf(' ')
  return `${(space > max * 0.6 ? cut.slice(0, space) : cut).replace(/[\s.,;:!?-]+$/, '')}…`
}

// All open discussions (pinned first), split into strict announcements and
// everything else.
async function fetchDiscussions() {
  const categoryData = await graphql(CATEGORIES_QUERY, { owner: OWNER, name: NAME })
  const categories = categoryData.repository?.discussionCategories?.nodes ?? []
  const announcementCategory = categories.find(
    (c) => c.slug === CATEGORY || c.name.toLowerCase() === CATEGORY.toLowerCase())
  if (!announcementCategory) {
    const available = categories.map((c) => c.slug).join(', ') || 'none visible'
    throw new Error(`Discussion category "${CATEGORY}" not found in ${REPO} (available: ${available})`)
  }

  const nodes = []
  let after = null
  do {
    const data = await graphql(DISCUSSIONS_QUERY, {
      owner: OWNER,
      name: NAME,
      category: null,
      first: Math.min(50, DISCUSSIONS_LIMIT - nodes.length),
      after,
    })
    const page = data.repository.discussions
    nodes.push(...page.nodes)
    after = page.pageInfo.hasNextPage ? page.pageInfo.endCursor : null
  } while (after && nodes.length < DISCUSSIONS_LIMIT)

  const pinnedData = await graphql(PINNED_QUERY, { owner: OWNER, name: NAME })
  const pinned = pinnedData.repository.pinnedDiscussions.nodes.map((n) => n.discussion)
  const pinnedNumbers = new Set(pinned.map((d) => d.number))

  const merged = [...pinned, ...nodes.filter((d) => !pinnedNumbers.has(d.number))]
    .filter((d) => !d.closed)

  const isAnnouncement = (d) =>
    d.category?.slug === announcementCategory.slug && MAINTAINER_ROLES.has(d.authorAssociation)

  const announcements = merged.filter(isAnnouncement).slice(0, LIMIT)
  const discussions = merged.filter((d) => !isAnnouncement(d))

  const toItem = async (d) => ({
    commentList: await fetchDiscussionComments(d.id),
    number: d.number,
    pinned: pinnedNumbers.has(d.number),
    category: d.category?.name ?? null,
    title: d.title.trim(),
    url: d.url,
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    lastEditedAt: d.lastEditedAt,
    // null when the author's GitHub account was deleted ("ghost")
    author: d.author ? { login: d.author.login, url: d.author.url } : null,
    comments: d.comments.totalCount,
    excerpt: excerpt(d.bodyText),
    // Already sanitised by GitHub, same HTML github.com renders.
    bodyHTML: stableAttachments(d.bodyHTML),
  })

  const mapAll = async (list) => {
    const out = []
    for (const d of list) out.push(await toItem(d))
    return out
  }

  return { announcements: await mapAll(announcements), discussions: await mapAll(discussions) }
}

const mapComment = (c) => ({
  url: c.url,
  createdAt: c.createdAt,
  lastEditedAt: c.lastEditedAt,
  author: c.author ? { login: c.author.login, url: c.author.url } : null,
  bodyHTML: stableAttachments(c.bodyHTML),
})

// All comments of one discussion with all their replies. Comments hidden on
// GitHub (spam, off-topic, ...) stay hidden here.
async function fetchDiscussionComments(id) {
  const comments = []
  let after = null
  do {
    const data = await graphql(DISCUSSION_COMMENTS_QUERY, { id, after })
    const page = data.node.comments
    comments.push(...page.nodes)
    after = page.pageInfo.hasNextPage ? page.pageInfo.endCursor : null
  } while (after)

  for (const comment of comments) {
    let { hasNextPage, endCursor } = comment.replies.pageInfo
    while (hasNextPage) {
      const data = await graphql(MORE_REPLIES_QUERY, { id: comment.id, after: endCursor })
      const page = data.node.replies
      comment.replies.nodes.push(...page.nodes)
      ;({ hasNextPage, endCursor } = page.pageInfo)
    }
  }

  return comments
    .filter((c) => !c.isMinimized)
    .map((c) => ({
      ...mapComment(c),
      isAnswer: c.isAnswer,
      replies: c.replies.nodes.filter((r) => !r.isMinimized).map(mapComment),
    }))
}

async function fetchIssues() {
  const nodes = []
  let after = null
  do {
    const data = await graphql(ISSUES_QUERY, {
      owner: OWNER,
      name: NAME,
      // Smaller pages, since every issue brings up to 100 comments along.
      first: Math.min(20, LIMIT - nodes.length),
      after,
    })
    const page = data.repository.issues
    nodes.push(...page.nodes)
    after = page.pageInfo.hasNextPage ? page.pageInfo.endCursor : null
  } while (after && nodes.length < LIMIT)

  const pinnedData = await graphql(PINNED_ISSUES_QUERY, { owner: OWNER, name: NAME })
  const pinned = pinnedData.repository.pinnedIssues.nodes.map((n) => n.issue)
  const pinnedNumbers = new Set(pinned.map((i) => i.number))

  const open = [...pinned, ...nodes.filter((i) => !pinnedNumbers.has(i.number))]
    .filter((i) => !i.closed)

  // Fetch the remaining comments of issues with more than 100 of them.
  for (const issue of open) {
    let { hasNextPage, endCursor } = issue.comments.pageInfo
    while (hasNextPage) {
      const data = await graphql(MORE_COMMENTS_QUERY, { id: issue.id, after: endCursor })
      const page = data.node.comments
      issue.comments.nodes.push(...page.nodes)
      ;({ hasNextPage, endCursor } = page.pageInfo)
    }
  }

  return open.map((i) => ({
      number: i.number,
      pinned: pinnedNumbers.has(i.number),
      category: null,
      labels: i.labels.nodes.map((l) => ({ name: l.name, color: l.color })),
      title: i.title.trim(),
      url: i.url,
      createdAt: i.createdAt,
      updatedAt: i.updatedAt,
      lastEditedAt: i.lastEditedAt,
      author: i.author ? { login: i.author.login, url: i.author.url } : null,
      comments: i.comments.totalCount,
      excerpt: excerpt(i.bodyText),
      bodyHTML: stableAttachments(i.bodyHTML),
      // Comments hidden on GitHub (spam, off-topic, ...) stay hidden here.
      commentList: i.comments.nodes
        .filter((c) => !c.isMinimized)
        .map((c) => ({
          url: c.url,
          createdAt: c.createdAt,
          lastEditedAt: c.lastEditedAt,
          author: c.author ? { login: c.author.login, url: c.author.url } : null,
          bodyHTML: stableAttachments(c.bodyHTML),
        })),
    }))
}

// What the three mirrored lists look like on the site and in their feeds.
const KINDS = {
  announcements: {
    json: OUT_JSON,
    feed: OUT_FEED,
    path: 'announcements/',
    feedFile: 'announcements.xml',
    title: `${SITE_TITLE} – Announcements`,
    description: `Announcements from the maintainers of ${SITE_TITLE}, mirrored from GitHub Discussions.`,
    discuss: 'Discuss this announcement on GitHub',
  },
  discussions: {
    json: OUT_DISCUSSIONS_JSON,
    feed: OUT_DISCUSSIONS_FEED,
    path: 'discussions/',
    feedFile: 'discussions.xml',
    title: `${SITE_TITLE} – Discussions`,
    description: `Open community discussions about ${SITE_TITLE}, mirrored from GitHub Discussions.`,
    discuss: 'Join this discussion on GitHub',
  },
  issues: {
    json: OUT_ISSUES_JSON,
    feed: OUT_ISSUES_FEED,
    path: 'issues/',
    feedFile: 'issues.xml',
    title: `${SITE_TITLE} – Issues`,
    description: `Open issues of ${SITE_TITLE}, mirrored from GitHub.`,
    discuss: 'Discuss this issue on GitHub',
  },
}

const escapeXml = (s) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&apos;')

const cdata = (s) => `<![CDATA[${String(s).replace(/]]>/g, ']]]]><![CDATA[>')}]]>`

function buildFeed(announcements, kind) {
  // Use the newest activity rather than "now" so the feed only changes when
  // an announcement actually changes.
  const newest = announcements
    .map((a) => a.lastEditedAt || a.createdAt)
    .sort()
    .at(-1)

  const items = announcements.map((a) => {
    const link = `${SITE_URL}${kind.path}${a.number}.html`
    const content = `${a.bodyHTML}\n<p><a href="${escapeXml(a.url)}">${kind.discuss}</a></p>`
    return [
      '    <item>',
      `      <title>${escapeXml(a.title)}</title>`,
      `      <link>${escapeXml(link)}</link>`,
      `      <guid isPermaLink="false">${escapeXml(a.url)}</guid>`,
      `      <comments>${escapeXml(a.url)}</comments>`,
      `      <pubDate>${new Date(a.createdAt).toUTCString()}</pubDate>`,
      a.author ? `      <dc:creator>${escapeXml(a.author.login)}</dc:creator>` : null,
      `      <description>${escapeXml(a.excerpt)}</description>`,
      `      <content:encoded>${cdata(content)}</content:encoded>`,
      '    </item>',
    ].filter(Boolean).join('\n')
  })

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    // Makes browsers render the feed as a readable page instead of raw XML
    // (public/feed.xsl). Feed readers ignore this line.
    '<?xml-stylesheet type="text/xsl" href="/feed.xsl"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">',
    '  <channel>',
    `    <title>${escapeXml(kind.title)}</title>`,
    `    <link>${escapeXml(`${SITE_URL}${kind.path}`)}</link>`,
    `    <description>${escapeXml(kind.description)}</description>`,
    '    <language>en</language>',
    `    <atom:link href="${escapeXml(`${SITE_URL}${kind.feedFile}`)}" rel="self" type="application/rss+xml"/>`,
    newest ? `    <lastBuildDate>${new Date(newest).toUTCString()}</lastBuildDate>` : null,
    ...items,
    '  </channel>',
    '</rss>',
    '',
  ].filter((line) => line !== null).join('\n')
}

function write(kindName, items) {
  const kind = KINDS[kindName]
  fs.mkdirSync(path.dirname(kind.json), { recursive: true })
  fs.mkdirSync(path.dirname(kind.feed), { recursive: true })
  const source = {
    issues: `${REPO} (issues)`,
    announcements: `${REPO} (${CATEGORY}, maintainers only)`,
    discussions: `${REPO} (all other discussions)`,
  }[kindName]
  fs.writeFileSync(kind.json, `${JSON.stringify({ source, [kindName]: items }, null, 2)}\n`)
  fs.writeFileSync(kind.feed, buildFeed(items, kind))
  if (kindName === 'announcements') {
    // Newest first, by creation date (pins don't matter for notifications).
    const latest = [...items]
      .sort((x, y) => y.createdAt.localeCompare(x.createdAt))
      .slice(0, 20)
      .map((x) => ({ number: x.number, title: x.title, createdAt: x.createdAt }))
    fs.writeFileSync(OUT_NOTIFY, `${JSON.stringify({ announcements: latest })}\n`)
  }
}

function readExisting(kindName) {
  try {
    return JSON.parse(fs.readFileSync(KINDS[kindName].json, 'utf8'))[kindName] ?? []
  } catch {
    return []
  }
}

function writeExisting() {
  for (const kindName of Object.keys(KINDS)) write(kindName, readExisting(kindName))
}

async function main() {
  if (!TOKEN) {
    console.warn('GITHUB_TOKEN is not set - skipping the download of announcements, discussions and issues.')
    if (process.env.CI) process.exit(1)
    writeExisting()
    return
  }
  const { announcements, discussions } = await fetchDiscussions()
  const issues = await fetchIssues()
  write('announcements', announcements)
  write('discussions', discussions)
  write('issues', issues)
  console.log(`Wrote ${announcements.length} announcement(s), ${discussions.length} discussion(s) `
    + `and ${issues.length} issue(s) from ${REPO}`)
}

main().catch((err) => {
  console.error(`::error::Could not fetch announcements/discussions/issues: ${err.message}`)
  // In CI, fail instead of deploying a site that silently lost its
  // announcements; the previously deployed site stays online.
  if (process.env.CI) process.exit(1)
  writeExisting()
})
