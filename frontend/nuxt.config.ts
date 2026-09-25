export default defineNuxtConfig({
  compatibilityDate: '2026-09-25',
  telemetry: false,
  devtools: { enabled: false },
  experimental: { appManifest: false },
  modules: ['@nuxt/eslint'],
  css: ['~/assets/main.css'],
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
