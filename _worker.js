// _worker.js - للتوجيه إلى Worker الأساسي
export default {
    async fetch(request, env) {
        // في حالة استخدام Pages مع Worker
        // هذا الملف بيشتغل كـ middleware
        
        // إذا كان الطلب للصفحة الرئيسية، اعرض index.html
        const url = new URL(request.url);
        if (url.pathname === '/' || url.pathname === '') {
            // استخدم الـ assets المرفوعة
            return env.ASSETS.fetch(request);
        }
        
        // باقي الطلبات ترسل للـ Worker الأساسي
        const workerUrl = 'https://raseedapp.omarawaad69.workers.dev';
        const newUrl = new URL(url.pathname + url.search, workerUrl);
        const newRequest = new Request(newUrl, {
            method: request.method,
            headers: request.headers,
            body: request.body
        });
        return fetch(newRequest);
    }
};