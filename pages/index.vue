<template>
  <div>
    <section class="py-20 sm:py-28">
      <div class="container-main">
        <div class="max-w-2xl">
          <p class="text-sm text-gray-400 font-medium mb-4 tracking-wider uppercase">Full-Stack Developer</p>
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
            Hi, I'm <span class="text-gray-400">Your Name</span>
          </h1>
          <p class="text-lg text-gray-500 leading-relaxed mb-8">
            A passionate developer who loves building clean, performant web applications.
            I write about technology, share my projects, and document my learning journey.
          </p>
          <div class="flex flex-wrap gap-4">
            <NuxtLink to="/projects" class="btn-primary">View Projects</NuxtLink>
            <NuxtLink to="/blog" class="btn-outline">Read Blog</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <section id="projects" class="py-16 border-t border-gray-200">
      <div class="container-main">
        <div class="flex items-center justify-between mb-10">
          <h2 class="text-2xl font-bold">Featured Projects</h2>
          <NuxtLink to="/blog" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
            View all &rarr;
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
                GitHub &rarr;
              </a>
              <a v-if="project.demo" :href="project.demo" target="_blank" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
                Demo &rarr;
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 border-t border-gray-200">
      <div class="container-main">
        <h2 class="text-2xl font-bold mb-10">Skills & Technologies</h2>
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
          <h2 class="text-2xl font-bold">Latest Posts</h2>
          <NuxtLink to="/blog" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
            All posts &rarr;
          </NuxtLink>
        </div>
        <ContentList path="/blog" :query="{ limit: 3, sort: { date: -1 } }" v-slot="{ list }">
          <div v-if="list.length" class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <NuxtLink
              v-for="article in list"
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
          <p v-else class="text-gray-400 text-sm">No posts yet. Stay tuned!</p>
        </ContentList>
      </div>
    </section>
  </div>
</template>

<script setup>
const projects = [
  {
    title: 'Portfolio Website',
    description: 'A personal portfolio built with Nuxt 3, featuring a blog system powered by Nuxt Content and styled with Tailwind CSS.',
    tags: ['Nuxt 3', 'Vue', 'Tailwind'],
    github: 'https://github.com/wusanshou2017/my_portfolio',
    demo: 'https://my-portfolio-psi-sooty-96.vercel.app',
  },
  {
    title: 'Project Template',
    description: 'A starter template for full-stack web applications. Replace this with your own project description.',
    tags: ['Vue', 'Node.js', 'MongoDB'],
    github: '#',
  },
  {
    title: 'Open Source Contribution',
    description: 'Contributed to various open source projects. Replace this with your actual contributions.',
    tags: ['Open Source', 'TypeScript'],
    github: '#',
  },
  {
    title: 'API Service',
    description: 'A RESTful API service built for learning purposes. Replace with your real project details.',
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
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

useHead({
  title: 'My Portfolio - Developer & Blogger',
})
</script>
