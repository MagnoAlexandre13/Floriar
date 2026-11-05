import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('dist');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.webp':'image/webp','.svg':'image/svg+xml','.woff2':'font/woff2'};
const server=http.createServer((req,res)=>{try{const url=new URL(req.url,'http://localhost');const target=path.resolve(root,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));if(!target.startsWith(root+path.sep)){res.writeHead(403);return res.end();}const content=fs.readFileSync(target);res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(content);}catch{res.writeHead(404);res.end('Not found');}});
server.listen(4173,'127.0.0.1',()=>console.log('Petal & Stem local preview: http://127.0.0.1:4173'));
