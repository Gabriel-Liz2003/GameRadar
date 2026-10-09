const STATIC_CACHE="gameradar-static-v1";
const ASSETS=["./","./index.html","./styles.css","./app.js","./icon.svg","./icon-192.png","./icon-512.png","./manifest.webmanifest"];
self.addEventListener("install",event=>{event.waitUntil(caches.open(STATIC_CACHE).then(cache=>cache.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener("activate",event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==STATIC_CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener("fetch",event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=="GET"||url.origin!==self.location.origin)return;
 if(url.pathname.endsWith("/data/feed.json")){event.respondWith(fetch(event.request,{cache:"no-store"}));return}
 event.respondWith(fetch(event.request).then(resp=>{if(resp.ok){const copy=resp.clone();caches.open(STATIC_CACHE).then(cache=>cache.put(event.request,copy))}return resp}).catch(()=>caches.match(event.request)))
});