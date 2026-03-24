export async function onRequest({ request, next, env }) {
  const url = new URL(request.url);
  
  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Max-Age": "86400",
      },
    });
  }
  
  // Proxy all /v1/* API calls
  if (url.pathname.startsWith("/v1")) {
    const proxyPath = url.pathname + (url.search || "");
    const proxyUrl = "https://relatively-extension-secretary-charles.trycloudflare.com" + proxyPath;
    
    const headers = {};
    for (const [k, v] of request.headers.entries()) {
      if (!["host", "connection", "content-length"].includes(k.toLowerCase())) {
        headers[k] = v;
      }
    }
    
    let body = undefined;
    if (["POST", "PUT", "PATCH"].includes(request.method)) {
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
    newHeaders.set("Content-Type", "application/json");
    newHeaders.set("Access-Control-Allow-Origin", "*");
    return new Response(respBody, { status: resp.status, headers: newHeaders });
  }
  
  return next();
}
