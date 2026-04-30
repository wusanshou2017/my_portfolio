<template>
  <div class="py-16">
    <div class="container-main max-w-3xl">
      <NuxtLink to="/blog" class="text-sm text-gray-400 hover:text-gray-900 transition-colors mb-8 inline-block">
        &larr; 返回博客
      </NuxtLink>

      <article v-if="article">
        <header class="mb-10">
          <div class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="tag in article.tags"
              :key="tag"
              class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded"
            >
              {{ tag }}
            </span>
          </div>
          <h1 class="text-3xl sm:text-4xl font-bold mb-4">{{ article.title }}</h1>
          <p class="text-gray-500">{{ article.description }}</p>
          <p class="text-sm text-gray-400 mt-2">{{ formatDate(article.date) }}</p>
        </header>

        <div class="prose-blog">
          <ContentRenderer :value="article" />
        </div>
      </article>

      <div v-else class="text-center py-20">
        <p class="text-gray-400">文章未找到。</p>
        <NuxtLink to="/blog" class="btn-primary mt-4 inline-block">返回博客</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup>
const route = useRoute()

const { data: article } = await useAsyncData(`blog-${route.path}`, () =>
  queryContent(route.path).findOne()
)

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

useHead(() => ({
  title: article.value ? `${article.value.title} - 博客` : '文章未找到',
}))
</script>
