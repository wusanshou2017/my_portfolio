---
title: Tailwind CSS 实用技巧
date: 2026-04-25
tags: [CSS, Tailwind, 前端]
description: 编写更简洁高效的 Tailwind CSS 的实用技巧，包括自定义工具类和响应式设计模式。
---

## 为什么选择 Tailwind CSS？

Tailwind CSS 是一个实用优先的 CSS 框架，让你无需离开 HTML 即可构建自定义设计。不用写自定义 CSS，而是通过预定义的工具类组合设计。

## 技巧一：用 @apply 处理重复模式

如果你发现自己重复使用相同的类，可以用 `@apply`：

```css
.btn-primary {
  @apply px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-700;
}
```

## 技巧二：响应式设计变得简单

Tailwind 使用移动优先的断点。使用 `sm:`、`md:`、`lg:` 前缀：

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  <!-- 响应式网格 -->
</div>
```

## 技巧三：用 Group 实现父子元素悬停效果

`group` 类让你可以根据父元素的悬停状态来样式化子元素：

```html
<div class="group cursor-pointer">
  <h3 class="group-hover:text-blue-500">悬停试试</h3>
</div>
```

## 技巧四：任意值

需要默认缩放中没有的特定值？使用方括号语法：

```html
<div class="mt-[17px] text-[13px]">
  <!-- 精确值 -->
</div>
```

## 总结

Tailwind CSS 是一个强大的工具，能显著提升开发效率。一旦习惯了实用优先的方式，你会发现自己很难回到传统 CSS 了。
