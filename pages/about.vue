<template>
  <div class="py-16">
    <div class="container-main max-w-3xl">
      <h1 class="text-3xl sm:text-4xl font-bold mb-8">关于我</h1>

      <div class="space-y-6 text-gray-500 leading-relaxed">
        <p>
          你好！我是一名热爱技术的全栈开发者，专注于构建
          简洁、高性能、用户友好的 Web 应用。
        </p>

        <p>
          出于对 Web 技术运作原理的好奇，我开始了编程之旅，
          如今它已成为我的职业和热爱所在。我喜欢使用现代
          JavaScript 框架，探索新技术，并通过博客分享所学所得。
        </p>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">我在做什么</h2>

        <ul class="list-disc pl-6 space-y-2">
          <li>使用 Vue.js、Nuxt 和 Node.js 构建 Web 应用</li>
          <li>撰写技术文章，分享学习经验</li>
          <li>参与开源项目贡献</li>
          <li>探索新工具和框架</li>
        </ul>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">工作经历</h2>

        <div class="space-y-4">
          <div class="border-l-2 border-gray-200 pl-4">
            <h3 class="font-medium text-gray-900">AI 开发工程师</h3>
            <p class="text-sm text-gray-400">公司名称 | 2024 - 至今</p>
            <p class="text-sm mt-1">构建可扩展的 Web 应用和服务。</p>
          </div>
          <div class="border-l-2 border-gray-200 pl-4">
            <h3 class="font-medium text-gray-900">前端开发工程师</h3>
            <p class="text-sm text-gray-400">前公司 | 2022 - 2024</p>
            <p class="text-sm mt-1">使用 Vue.js 开发交互式用户界面。</p>
          </div>
        </div>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">联系我</h2>

        <p>
          如果你想合作项目、有问题咨询，或者只是想打个招呼，欢迎随时联系！
        </p>

        <div class="flex flex-wrap gap-4 pt-2">
          <a href="https://github.com/wusanshou2017" target="_blank" class="btn-outline text-sm">
            GitHub
          </a>
          <a href="mailto:hello@example.com" class="btn-outline text-sm">
            邮箱
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
useHead({
  title: '关于',
})
</script>
