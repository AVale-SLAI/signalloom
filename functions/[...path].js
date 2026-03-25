// Cloudflare Pages Function: handles ALL requests to /v1/* API routes
// Proxies to the tunnel backend at api.signalloomai.com
// Static HTML files are served automatically by Cloudflare Pages — this only handles /v1/*

export async function onRequest({ request, params, env }) {
  const url = new URL(request.url);
  const pathname = url.pathname; // e.g., /v1/transcribe or /v1/status/abc123

  // Only handle /v1/* routes
  if (!pathname.startsWith('/v1/')) {
    return new Response('Not Found', { status: 404 });
  }

  // Proxy to tunnel backend
  const target = `https://relatively-extension-secretary-charles.trycloudflare.com${pathname}${url.search || ''}`;

  // Forward relevant headers
  const headers = {};
  for (const [k, v] of request.headers.entries()) {
    const kl = k.toLowerCase();
    if (!['host', 'connection', 'content-length', 'cf-connecting-ip'].includes(kl)) {
      headers[k] = v;
    }
  }

  // Copy Authorization header if present
  const auth = request.headers.get('Authorization');
  if (auth) headers['Authorization'] = auth;

  let body;
  if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
    body = await request.text();
  }

  const proxyReq = new Request(target, {
    method: request.method,
    headers,
    body,
  });

  let resp;
  try {
    resp = await fetch(proxyReq);
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Backend unreachable', detail: e.message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const respBody = await resp.text();
  const newHeaders = new Headers();
  newHeaders.set('Content-Type', 'application/json');
  newHeaders.set('Access-Control-Allow-Origin', '*');
  newHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  newHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  return new Response(respBody, { status: resp.status, headers: newHeaders });
}
