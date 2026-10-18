// The only way the frontend talks to the backend. Requests go to same-origin
// /api/*, which Nitro proxies to BACKEND_URL (see routeRules in nuxt.config.ts),
// so no page ever needs the backend's address and there's no CORS preflight.

import { $fetch, tryUseNuxtApp, useState } from '#imports'

export const useDemoUser = () => useState<string>('demo-user', () => 'demo')

// Safe to call anywhere, including after an await or inside onMounted, where
// Nuxt's composable context may be gone.
function currentDemoUser(): string {
  const nuxtApp = tryUseNuxtApp()
  if (!nuxtApp) return 'demo'
  return nuxtApp.runWithContext(() => useDemoUser().value) || 'demo'
}

export function useApi<T = unknown>(path: string, opts: Parameters<typeof $fetch>[1] = {}) {
  return $fetch<T>(path, {
    ...opts,
    baseURL: '/api',
    headers: { ...(opts.headers as Record<string, string> | undefined), 'X-Demo-User': currentDemoUser() }
  })
}
