---
title: Nuxt 3 入门指南
date: 2026-04-28
tags: [Nuxt, Vue, 前端]
description: 一篇面向初学者的 Nuxt 3 教程，带你了解如何用这个基于 Vue.js 的全栈框架构建现代 Web 应用。
---

## 为什么选择 Nuxt 3？

Nuxt 3 是广受欢迎的 Vue.js 元框架的最新版本。它提供了出色的开发体验，内置以下特性：

- **自动导入** — 组件、composables 和工具函数自动导入，无需手动引入
- **文件路由** — 在 `pages/` 目录下创建文件即可自动生成路由
- **服务端渲染** — 内置 SSR、SSG 和 ISR 支持
- **混合渲染** — 每个路由可以选择不同的渲染模式

## 创建你的第一个项目

开始非常简单，打开终端运行：

```bash
npx nuxi init my-app
cd my-app
npm install
npm run dev
```

这会创建一个新的 Nuxt 3 项目，并在 `http://localhost:3000` 启动开发服务器。

## 项目结构

以下是 Nuxt 3 项目的基本结构：

```
my-app/
├── pages/        # 文件路由
├── components/   # Vue 组件（自动导入）
├── composables/  # 共享状态和逻辑（自动导入）
├── layouts/      # 页面布局
├── server/       # API 路由和服务端中间件
├── content/      # Markdown 内容（配合 @nuxt/content）
├── public/       # 静态资源
└── nuxt.config.ts # 配置文件
```

## 下一步

在下一篇文章中，我们将探索如何使用 `@nuxt/content` 为 Nuxt 3 网站添加博客功能。敬请期待！
