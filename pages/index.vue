<template>
  <div>
    <section class="py-20 sm:py-28">
      <div class="container-main">
        <div class="max-w-2xl">
          <p class="text-sm text-gray-400 font-medium mb-4 tracking-wider uppercase">全栈开发者</p>
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
            你好，我是 <span class="text-gray-400">你的名字</span>
          </h1>
          <p class="text-lg text-gray-500 leading-relaxed mb-8">
            一个热爱技术的开发者，喜欢构建简洁、高性能的 Web 应用。
            在这里分享技术文章、展示项目作品，记录学习成长之路。
          </p>
          <div class="flex flex-wrap gap-4">
            <NuxtLink to="/projects" class="btn-primary">查看项目</NuxtLink>
            <NuxtLink to="/blog" class="btn-outline">阅读博客</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <section id="projects" class="py-16 border-t border-gray-200">
      <div class="container-main">
        <div class="flex items-center justify-between mb-10">
          <h2 class="text-2xl font-bold">精选项目</h2>
          <NuxtLink to="/projects" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
            查看全部 &rarr;
          </NuxtLink>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="project in projects" :key="project.title" class="card group cursor-pointer">
            <div class="flex items-center gap-2 mb-3">
              <span v-for="tag in project.tags" :key="tag" class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                {{ tag }}
              </span>
            </div>
            <h3 class="text-lg font-semibold mb-2 group-hover:text-gray-600 transition-colors">
              {{ project.title }}
            </h3>
            <p class="text-sm text-gray-500 leading-relaxed mb-4">
              {{ project.description }}
            </p>
            <div class="flex gap-4">
              <a :href="project.github" target="_blank" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
                源码 &rarr;
              </a>
              <a v-if="project.demo" :href="project.demo" target="_blank" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
                演示 &rarr;
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 border-t border-gray-200">
      <div class="container-main">
        <h2 class="text-2xl font-bold mb-10">技能 & 技术栈</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div v-for="skill in skills" :key="skill.name" class="card text-center py-8">
            <span class="text-2xl mb-3 block">{{ skill.icon }}</span>
            <p class="text-sm font-medium text-gray-700">{{ skill.name }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 border-t border-gray-200">
      <div class="container-main">
        <div class="flex items-center justify-between mb-10">
          <h2 class="text-2xl font-bold">最新文章</h2>
          <NuxtLink to="/blog" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
            全部文章 &rarr;
          </NuxtLink>
        </div>
        <div v-if="latestPosts && latestPosts.length" class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <NuxtLink
            v-for="article in latestPosts"
            :key="article._path"
            :to="article._path"
            class="card group"
          >
            <p class="text-xs text-gray-400 mb-2">{{ formatDate(article.date) }}</p>
            <h3 class="text-base font-semibold mb-2 group-hover:text-gray-600 transition-colors">
              {{ article.title }}
            </h3>
            <p class="text-sm text-gray-500 line-clamp-2">
              {{ article.description }}
            </p>
          </NuxtLink>
        </div>
        <p v-else class="text-gray-400 text-sm">暂无文章，敬请期待！</p>
      </div>
    </section>
  </div>
</template>

<script setup>
const { data: latestPosts } = await useAsyncData('latest-posts', () =>
  queryContent('/blog').sort({ date: -1 }).limit(3).find(),
  { default: () => [] }
)

const projects = [
  {
    title: '个人作品集网站',
    description: '基于 Nuxt 3 构建的个人作品集，集成 Nuxt Content 博客系统和 Tailwind CSS 样式。',
    tags: ['Nuxt 3', 'Vue', 'Tailwind'],
    github: 'https://github.com/wusanshou2017/my_portfolio',
    demo: 'https://my-portfolio-psi-sooty-96.vercel.app',
  },
  {
    title: '项目模板',
    description: '全栈 Web 应用启动模板。替换为你自己的项目描述。',
    tags: ['Vue', 'Node.js', 'MongoDB'],
    github: '#',
  },
  {
    title: '开源贡献',
    description: '参与了多个开源项目的贡献。替换为你的实际贡献。',
    tags: ['Open Source', 'TypeScript'],
    github: '#',
  },
  {
    title: 'API 服务',
    description: '用于学习的 RESTful API 服务。替换为你的真实项目详情。',
    tags: ['Express', 'PostgreSQL', 'Docker'],
    github: '#',
  },
]

const skills = [
  { name: 'JavaScript', icon: 'JS' },
  { name: 'TypeScript', icon: 'TS' },
  { name: 'Vue.js', icon: 'V' },
  { name: 'React', icon: 'R' },
  { name: 'Node.js', icon: 'N' },
  { name: 'Python', icon: 'Py' },
  { name: 'Git', icon: 'G' },
  { name: 'Docker', icon: 'D' },
]

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

useHead({
  title: '个人作品集 - 开发者 & 博主',
})
</script>
