import {getSession} from './auth-api.js';
try {
  const session=await getSession();
  for(const link of document.querySelectorAll('[data-account-link]')) {
    link.textContent=session?'Minha conta':'Entrar';
    if(session) link.title=`Conta de ${session.user.name}`;
  }
} catch { /* A loja estática continua navegável sem o backend. */ }
