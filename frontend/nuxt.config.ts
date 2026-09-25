export default defineNuxtConfig({
  vite: {
    server: {
      allowedHosts: [
        '.tunnelmole.net'
      ]
    }
  },
  compatibilityDate: '2026-09-25',
  telemetry: false,
  devtools: { enabled: false },
  experimental: { appManifest: false },
  modules: ['@nuxt/eslint'],
  css: ['~/assets/main.css'],
  // Same-origin proxy to the Spring Boot backend, so the browser never needs CORS.
  routeRules: {
    '/api/**': { proxy: `${process.env.BACKEND_URL ?? 'http://localhost:8080'}/api/**` },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'de' },
      title: 'MünsterMatch · Date dein Münster',
      meta: [
        { name: 'description', content: 'Entdecke Freizeitaktivitäten in Münster – mit deiner Zeit, deinem Startpunkt und Lust auf etwas Neues.' },
        { name: 'theme-color', content: '#f7f7ef' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },
})
