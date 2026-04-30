---
title: Building a Blog with Nuxt Content
date: 2026-04-30
tags: [Nuxt, Markdown, Blog]
description: Learn how to create a powerful blog system using Nuxt Content, with Markdown support, automatic routing, and full-text search.
---

## What is Nuxt Content?

`@nuxt/content` is a Nuxt module that lets you write content in Markdown files and serve them through a powerful API. It handles parsing, rendering, and searching for you.

## Setup

First, install the module:

```bash
npm install @nuxt/content
```

Then add it to your `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],
})
```

## Writing Your First Post

Create a Markdown file at `content/blog/my-first-post.md`:

```markdown
---
title: My First Post
date: 2026-04-30
tags: [tutorial]
description: This is my first blog post.
---

# Hello World!

This is the content of my first post.
```

## Displaying the Blog List

In your blog page, use the `ContentList` component:

```vue
<ContentList path="/blog" v-slot="{ list }">
  <article v-for="article in list" :key="article._path">
    <h2>{{ article.title }}</h2>
    <p>{{ article.description }}</p>
    <NuxtLink :to="article._path">Read more</NuxtLink>
  </article>
</ContentList>
```

## The Benefits

- **No database needed** — Content is stored as Git-managed Markdown files
- **Version control** — Every change to your content is tracked
- **Fast** — Content is pre-rendered at build time
- **Flexible** — Full Markdown support with Vue components inside
