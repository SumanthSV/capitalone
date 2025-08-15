
// Service Worker for KrishiMitra PWA
const CACHE_NAME = 'krishimitra-v2';
const OFFLINE_URL = '/offline.html';

// Resources to cache for offline use
const urlsToCache = [
    '/',
    '/static/styles.css',
    '/static/app.js',
    '/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Install event - cache resources
self.addEventListener('install', event => {
    console.log('[SW] Installing service worker');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching app shell');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('[SW] Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activating service worker');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Claiming clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Handle API requests differently
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Clone the response for caching
                    const responseClone = response.clone();
                    
                    // Cache successful API responses
                    if (response.status === 200) {
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    
                    return response;
                })
                .catch(() => {
                    // Try to serve from cache if network fails
                    return caches.match(event.request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            
                            // Return offline response for API calls
                            return new Response(
                                JSON.stringify({
                                    success: false,
                                    error: 'Offline - cached data not available',
                                    offline: true
                                }),
                                {
                                    status: 503,
                                    statusText: 'Service Unavailable',
                                    headers: { 'Content-Type': 'application/json' }
                                }
                            );
                        });
                })
        );
        return;
    }
    
    // Handle regular requests (HTML, CSS, JS, images)
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Return cached version if available
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Try network
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone the response for caching
                        const responseToCache = response.clone();
                        
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    });
            })
            .catch(() => {
                // If both cache and network fail, show offline page for navigation requests
                if (event.request.destination === 'document') {
                    return caches.match(OFFLINE_URL);
                }
                
                // For other requests, return a generic offline response
                return new Response('Offline', {
                    status: 503,
                    statusText: 'Service Unavailable'
                });
            })
    );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Push notification handling
self.addEventListener('push', event => {
    console.log('[SW] Push received');
    
    const options = {
        body: event.data ? event.data.text() : 'New agricultural update available',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View Details',
                icon: '/static/icons/icon-96x96.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/icons/icon-96x96.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('KrishiMitra Update', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification click received');
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Background sync function
async function doBackgroundSync() {
    try {
        // Sync offline data when connection is restored
        const cache = await caches.open(CACHE_NAME);
        const requests = await cache.keys();
        
        // Process any pending offline actions
        console.log('[SW] Processing', requests.length, 'cached requests');
        
        // Here you would implement logic to sync offline data
        // For example, send queued form submissions, sync user data, etc.
        
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
    }
}

// Message handling from main thread
self.addEventListener('message', event => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({
            version: '2.0.0',
            cacheVersion: 'v2'
        });
    }
});

console.log('[SW] Service worker loaded - Version 2.0.0');
