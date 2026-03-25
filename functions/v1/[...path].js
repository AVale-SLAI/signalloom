// Cloudflare Pages Function: handles /v1/* API routes
// Proxies all /v1/* requests to the tunnel backend
// Static files are served automatically by Cloudflare Pages — this file only handles /v1/*

export async function onRequest({ request, params, env }) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/v1/', '');
  const proxyUrl = `https://relatively-extension-secretary-charles.trycloudflare.com/v1/${path}${url.search || ''}`;

  const headers = {};
  for (const [k, v] of request.headers.entries()) {
    if (!['host', 'connection', 'content-length'].includes(k.toLowerCase())) {
      headers[k] = v;
    }
  }

  let body;
  if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
    body = await request.text();
  }

  const proxyReq = new Request(proxyUrl, {
    method: request.method,
    headers,
    body,
  });

  const resp = await fetch(proxyReq);
  const respBody = await resp.text();

  const newHeaders = new Headers();
  newHeaders.set('Content-Type', 'application/json');
  newHeaders.set('Access-Control-Allow-Origin', '*');

  return new Response(respBody, { status: resp.status, headers: newHeaders });
}
