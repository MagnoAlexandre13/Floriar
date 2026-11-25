import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('dist');
const frontendPort=Number(process.env.PETAL_FRONTEND_PORT||4173);
const apiPort=Number(process.env.PETAL_API_PORT||8010);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.webp':'image/webp','.svg':'image/svg+xml','.woff2':'font/woff2'};
const server=http.createServer((req,res)=>{
  try {
    const url=new URL(req.url,'http://localhost');
    if(url.pathname.startsWith('/api/')||['/cliente','/cliente.js','/docs','/redoc','/openapi.json'].includes(url.pathname)) {
      const proxy=http.request({hostname:'127.0.0.1',port:apiPort,path:req.url,method:req.method,headers:req.headers},upstream=>{
        res.writeHead(upstream.statusCode,upstream.headers);upstream.pipe(res);
      });
      proxy.on('error',()=>{if(!res.headersSent)res.writeHead(503,{'Content-Type':'application/json'});res.end(JSON.stringify({error:{code:'api_unavailable',message:'Inicie o backend Python na porta 8010 para usar sua conta e seus pedidos.'}}));});
      proxy.setTimeout(10000,()=>proxy.destroy());req.pipe(proxy);return;
    }
    const target=path.resolve(root,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));
    if(!target.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
    const content=fs.readFileSync(target);
    res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(content);
  } catch {res.writeHead(404);res.end('Not found');}
});
server.listen(frontendPort,'127.0.0.1',()=>console.log(`Petal & Stem local preview: http://127.0.0.1:${frontendPort}`));
