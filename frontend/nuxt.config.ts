// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()]
  },
  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      title: 'Demo Prototype · Stop the scam before the money moves',
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700&family=Patua+One&display=swap'
        }
      ]
    }
  },
  // The old demo routes now live on the single page.
  routeRules: {
    '/demo': { redirect: '/' },
    '/replay': { redirect: '/' },
    '/case': { redirect: '/' }
  }
})
