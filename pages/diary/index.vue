<template>
  <div class="py-16">
    <div class="container-main">
      <div class="mb-12">
        <h1 class="text-3xl sm:text-4xl font-bold mb-4">学习日记</h1>
        <p class="text-gray-500">记录每天的学习心得和成长足迹。</p>
      </div>

      <div class="mb-8 flex flex-wrap gap-2">
        <button
          :class="[
            'px-3 py-1.5 text-sm rounded-lg border transition-colors',
            selectedTag === null
              ? 'bg-gray-900 text-white border-gray-900'
              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
          ]"
          @click="selectedTag = null"
        >
          全部
        </button>
        <button
          v-for="tag in allTags"
          :key="tag"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg border transition-colors',
            selectedTag === tag
              ? 'bg-gray-900 text-white border-gray-900'
              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
          ]"
          @click="selectedTag = tag"
        >
          {{ tag }}
        </button>
      </div>

      <div v-if="filteredPosts.length" class="flex flex-col gap-6">
        <NuxtLink
          v-for="article in filteredPosts"
          :key="article._path"
          :to="article._path"
          class="card group block"
        >
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-2">
            <h2 class="text-lg font-semibold group-hover:text-gray-600 transition-colors">
              {{ article.title }}
            </h2>
            <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatDate(article.date) }}</span>
          </div>
          <p class="text-sm text-gray-500 mb-3">{{ article.description }}</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="tag in article.tags"
              :key="tag"
              class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded"
            >
              {{ tag }}
            </span>
          </div>
        </NuxtLink>
      </div>
      <p v-else class="text-gray-400 text-center py-20">暂无日记。</p>
    </div>
  </div>
</template>

<script setup>
const selectedTag = ref(null)

const { data: posts } = await useAsyncData('diary-posts', () =>
  queryContent('/diary').sort({ date: -1 }).find(),
  { default: () => [] }
)

const allTags = computed(() => {
  const tags = new Set()
  if (posts.value) {
    posts.value.forEach(item => {
      if (item.tags) item.tags.forEach(t => tags.add(t))
    })
  }
  return [...tags]
})

const filteredPosts = computed(() => {
  if (!posts.value) return []
  if (!selectedTag.value) return posts.value
  return posts.value.filter(post =>
    post.tags && post.tags.includes(selectedTag.value)
  )
})

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

useHead({
  title: '学习日记',
})
</script>
