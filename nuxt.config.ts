export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/content',
    '@nuxtjs/tailwindcss',
    '@nuxtjs/google-fonts',
  ],

  app: {
    head: {
      title: 'My Portfolio',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '个人作品集与技术博客' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      ],
    },
  },

  googleFonts: {
    families: {
      'Inter': [400, 500, 600, 700],
      'JetBrains Mono': [400, 500],
    },
  },

  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
  },
})
