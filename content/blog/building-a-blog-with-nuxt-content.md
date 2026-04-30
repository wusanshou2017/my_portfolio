---
title: 用 Nuxt Content 搭建博客系统
date: 2026-04-30
tags: [Nuxt, Markdown, 博客]
description: 学习如何使用 Nuxt Content 创建强大的博客系统，支持 Markdown 写作、自动路由和全文搜索。
---

## 什么是 Nuxt Content？

`@nuxt/content` 是一个 Nuxt 模块，让你可以用 Markdown 文件编写内容，并通过强大的 API 提供服务。它帮你处理了解析、渲染和搜索。

## 安装配置

首先，安装模块：

```bash
npm install @nuxt/content
```

然后在 `nuxt.config.ts` 中添加：

```ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],
})
```

## 编写第一篇文章

在 `content/blog/my-first-post.md` 创建 Markdown 文件：

```markdown
---
title: 我的第一篇文章
date: 2026-04-30
tags: [教程]
description: 这是我的第一篇博客文章。
---

# 你好世界！

这是第一篇文章的内容。
```

## 展示博客列表

在博客页面，使用 `ContentList` 组件：

```vue
<ContentList path="/blog" v-slot="{ list }">
  <article v-for="article in list" :key="article._path">
    <h2>{{ article.title }}</h2>
    <p>{{ article.description }}</p>
    <NuxtLink :to="article._path">阅读更多</NuxtLink>
  </article>
</ContentList>
```

## 优势

- **无需数据库** — 内容以 Git 管理的 Markdown 文件存储
- **版本控制** — 每次内容变更都有记录
- **速度快** — 内容在构建时预渲染
- **灵活** — 完整 Markdown 支持，可在其中嵌入 Vue 组件
