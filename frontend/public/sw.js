/**
 * Self-unregistering service worker.
 * A stale SW was previously registered. This file serves a valid response at
 * /sw.js so the browser can activate it — then it immediately unregisters
 * itself and reloads all clients so they fetch fresh JS chunks from the server.
 */
self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', () => {
  self.registration.unregister().then(() => {
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      clients.forEach((client) => client.navigate(client.url))
    })
  })
})
