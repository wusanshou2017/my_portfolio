<template>
  <div class="py-16">
    <div class="container-main">
      <div class="mb-12">
        <h1 class="text-3xl sm:text-4xl font-bold mb-4">Projects</h1>
        <p class="text-gray-500">A collection of things I've built and contributed to.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div v-for="project in projects" :key="project.title" class="card group">
          <div class="flex items-center gap-2 mb-3">
            <span v-for="tag in project.tags" :key="tag" class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
              {{ tag }}
            </span>
          </div>
          <h2 class="text-lg font-semibold mb-2 group-hover:text-gray-600 transition-colors">
            {{ project.title }}
          </h2>
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
  {
    title: 'CLI Tool',
    description: 'A command-line tool that automates common development workflows. Replace with your actual tool.',
    tags: ['Node.js', 'CLI', 'TypeScript'],
    github: '#',
  },
  {
    title: 'Mobile App',
    description: 'A cross-platform mobile application built with modern frameworks. Replace with your real project.',
    tags: ['React Native', 'Firebase'],
    github: '#',
  },
]

useHead({
  title: 'Projects',
})
</script>
