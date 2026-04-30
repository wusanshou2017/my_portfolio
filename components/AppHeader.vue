<template>
  <header class="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
    <div class="container-main flex items-center justify-between h-16">
      <NuxtLink to="/" class="text-lg font-bold tracking-tight">
        Portfolio
      </NuxtLink>

      <nav class="hidden sm:flex items-center gap-8">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="text-sm text-gray-500 hover:text-gray-900 transition-colors"
          active-class="!text-gray-900 font-medium"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>

      <button
        class="sm:hidden p-2 text-gray-500 hover:text-gray-900"
        @click="mobileMenuOpen = !mobileMenuOpen"
      >
        <svg v-if="!mobileMenuOpen" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div v-if="mobileMenuOpen" class="sm:hidden border-t border-gray-200 bg-white">
      <nav class="container-main py-4 flex flex-col gap-3">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="text-sm text-gray-500 hover:text-gray-900 transition-colors py-1"
          active-class="!text-gray-900 font-medium"
          @click="mobileMenuOpen = false"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>
    </div>
  </header>
</template>

<script setup>
const mobileMenuOpen = ref(false)

const navItems = [
  { label: 'Home', path: '/' },
  { label: 'Projects', path: '/#projects' },
  { label: 'Blog', path: '/blog' },
  { label: 'About', path: '/about' },
]
</script>
