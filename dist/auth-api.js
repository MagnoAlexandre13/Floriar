// O identificador da sessão permanece apenas no cookie HttpOnly.
let activeSession = null;
const unavailableMessage = 'A API da floricultura não está disponível neste endereço. No computador onde o projeto está rodando, inicie o backend e abra http://127.0.0.1:8010/conta.html.';

export class ApiError extends Error {
  constructor(message, status, code) { super(message); this.status = status; this.code = code; }
}

async function checkAccountService(signal) {
  let response;
  try {
    response = await fetch('/api/health', {signal, cache: 'no-store', redirect: 'error'});
  } catch (error) {
    if (error.name === 'AbortError') throw error;
  }
  if (!response?.ok || response.headers.get('X-Petal-Service') !== 'petal-and-stem') {
    throw new ApiError(unavailableMessage, 503, 'api_unavailable');
  }
}

export async function request(path, method = 'GET', body, signal) {
  const write = !['GET', 'HEAD'].includes(method);
  const publicAuth = ['/api/auth/login', '/api/auth/cadastro'].includes(path);
  if (publicAuth) await checkAccountService(signal);
  if (write && !publicAuth && !activeSession) await getSession();
  const headers = body ? {'Content-Type': 'application/json'} : {};
  if (write && !publicAuth && activeSession) headers['X-CSRF-Token'] = activeSession.csrf_token;
  let response;
  try {
    response = await fetch(path, {method, signal, credentials: 'include', headers,
      body: body ? JSON.stringify(body) : undefined});
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Não foi possível acessar a API. Confira se o backend está em execução.', 503, 'api_unavailable');
  }
  if (response.status === 204) { if (path === '/api/auth/logout') activeSession = null; return null; }
  if (path.startsWith('/api/auth/') && [404, 405, 503].includes(response.status)) {
    throw new ApiError(unavailableMessage, 503, 'api_unavailable');
  }
  let data;
  try { data = await response.json(); }
  catch { throw new ApiError('API indisponível. Inicie o backend Python e recarregue a página.', 503, 'api_unavailable'); }
  if (!response.ok) {
    if (response.status === 401) activeSession = null;
    const details = data.error?.details?.map(item => item.message).join(' ');
    throw new ApiError(details || data.error?.message || `Erro HTTP ${response.status}`, response.status, data.error?.code);
  }
  if (data.user && data.csrf_token) activeSession = data;
  return data;
}

export async function getSession() {
  try { return await request('/api/auth/me'); }
  catch (error) { if (error.status === 401) return null; throw error; }
}
