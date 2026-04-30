<template>
  <div class="py-16">
    <div class="container-main max-w-3xl">
      <h1 class="text-3xl sm:text-4xl font-bold mb-8">About Me</h1>

      <div class="space-y-6 text-gray-500 leading-relaxed">
        <p>
          Hello! I'm a passionate full-stack developer with a love for building
          clean, performant, and user-friendly web applications.
        </p>

        <p>
          I started my programming journey with curiosity about how things work on the web,
          and it has since become my career and passion. I enjoy working with modern
          JavaScript frameworks, exploring new technologies, and sharing what I learn
          through my blog.
        </p>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">What I Do</h2>

        <ul class="list-disc pl-6 space-y-2">
          <li>Build web applications with Vue.js, Nuxt, and Node.js</li>
          <li>Write about technology and share my learning experiences</li>
          <li>Contribute to open source projects</li>
          <li>Explore new tools and frameworks</li>
        </ul>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">Experience</h2>

        <div class="space-y-4">
          <div class="border-l-2 border-gray-200 pl-4">
            <h3 class="font-medium text-gray-900">Full-Stack Developer</h3>
            <p class="text-sm text-gray-400">Company Name | 2024 - Present</p>
            <p class="text-sm mt-1">Building scalable web applications and services.</p>
          </div>
          <div class="border-l-2 border-gray-200 pl-4">
            <h3 class="font-medium text-gray-900">Frontend Developer</h3>
            <p class="text-sm text-gray-400">Previous Company | 2022 - 2024</p>
            <p class="text-sm mt-1">Developed interactive user interfaces with Vue.js.</p>
          </div>
        </div>

        <h2 class="text-xl font-semibold text-gray-900 pt-4">Get In Touch</h2>

        <p>
          Feel free to reach out if you want to collaborate on a project,
          have a question, or just want to say hi!
        </p>

        <div class="flex flex-wrap gap-4 pt-2">
          <a href="https://github.com/wusanshou2017" target="_blank" class="btn-outline text-sm">
            GitHub
          </a>
          <a href="mailto:hello@example.com" class="btn-outline text-sm">
            Email
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
useHead({
  title: 'About',
})
</script>
