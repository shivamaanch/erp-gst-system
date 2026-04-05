// Service Worker for Milk Entry PWA
const CACHE_NAME = 'milk-entry-v1';
const urlsToCache = [
  '/',
  '/milk/mobile-entry',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Service Worker: Caching files');
        return cache.addAll(urlsToCache);
      })
      .then(function() {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', function(event) {
  console.log('Service Worker: Fetching ', event.request.url);
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // If the request is in cache, return it
        if (response) {
          console.log('Service Worker: Serving from cache');
          return response;
        }
        
        // If not in cache, fetch from network
        console.log('Service Worker: Fetching from network');
        return fetch(event.request).then(function(response) {
          // Check if valid response
          if(!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          // Clone the response for caching
          var responseToCache = response.clone();
          
          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });
          
          return response;
        }).catch(function(error) {
          // For API requests, return a basic offline response
          if (event.request.url.includes('/milk/')) {
            return new Response(
              JSON.stringify({ success: false, message: 'Offline - Please check your internet connection' }),
              { 
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
              }
            );
          }
        });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', function(event) {
  console.log('Service Worker: Background sync triggered');
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Handle any pending offline actions
  console.log('Service Worker: Performing background sync');
  return Promise.resolve();
}

// Push notifications (if needed later)
self.addEventListener('push', function(event) {
  console.log('Service Worker: Push received');
  const options = {
    body: event.data ? event.data.text() : 'New milk entry update',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/static/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/xmark.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Milk Entry', options)
  );
});
