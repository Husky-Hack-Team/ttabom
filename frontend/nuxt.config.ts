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
  // Same-origin API: /api/* is proxied to the backend, so the browser never
  // needs the backend's URL and there's no CORS. BACKEND_URL is read at build
  // time; set it in the Vercel project before deploying.
  routeRules: {
    '/api/**': { proxy: `${(process.env.BACKEND_URL || 'http://localhost:8000').replace(/\/+$/, '')}/api/**` }
  }
})
