---
title: Getting Started with Nuxt 3
date: 2026-04-28
tags: [Nuxt, Vue, Frontend]
description: A beginner-friendly guide to building modern web applications with Nuxt 3, the full-stack framework for Vue.js.
---

## Why Nuxt 3?

Nuxt 3 is the latest version of the popular Vue.js meta-framework. It provides a great developer experience with features like:

- **Auto-imports** — Components, composables, and utilities are automatically imported
- **File-based routing** — Create pages just by adding files to the `pages/` directory
- **Server-side rendering** — Built-in SSR, SSG, and ISR support
- **Hybrid rendering** — Choose the rendering mode per route

## Creating Your First Project

Getting started is simple. Open your terminal and run:

```bash
npx nuxi init my-app
cd my-app
npm install
npm run dev
```

This will create a new Nuxt 3 project and start the development server at `http://localhost:3000`.

## Project Structure

Here's the basic structure of a Nuxt 3 project:

```
my-app/
├── pages/        # File-based routing
├── components/   # Vue components (auto-imported)
├── composables/  # Shared state and logic (auto-imported)
├── layouts/      # Page layouts
├── server/       # API routes and server middleware
├── content/      # Markdown content (with @nuxt/content)
├── public/       # Static assets
└── nuxt.config.ts # Configuration file
```

## What's Next?

In the next post, we'll explore how to add a blog to your Nuxt 3 site using `@nuxt/content`. Stay tuned!
