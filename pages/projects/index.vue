<template>
  <div class="py-16">
    <div class="container-main">
      <div class="mb-12">
        <h1 class="text-3xl sm:text-4xl font-bold mb-4">项目</h1>
        <p class="text-gray-500">我构建和参与的项目集合。</p>
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
              源码 &rarr;
            </a>
            <a v-if="project.demo" :href="project.demo" target="_blank" class="text-sm text-gray-400 hover:text-gray-900 transition-colors">
              演示 &rarr;
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
  {
    title: 'CLI 工具',
    description: '自动化常见开发工作流的命令行工具。替换为你的实际工具。',
    tags: ['Node.js', 'CLI', 'TypeScript'],
    github: '#',
  },
  {
    title: '移动应用',
    description: '使用现代框架构建的跨平台移动应用。替换为你的真实项目。',
    tags: ['React Native', 'Firebase'],
    github: '#',
  },
]

useHead({
  title: '项目',
})
</script>
