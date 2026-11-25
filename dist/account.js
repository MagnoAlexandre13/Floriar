import {getSession, request} from './auth-api.js';
const $ = selector => document.querySelector(selector);
const notice = (message, error=false) => { $('#auth-notice').textContent=message; $('#auth-notice').dataset.error=String(error); };
const next = new URLSearchParams(location.search).get('next');
if(next === '/' || next === '/cliente' || (next?.startsWith('/#bouquet/') && !next.includes('\\'))) $('#continue').href=next;

function render(session) {
  $('#auth-forms').hidden=!!session; $('#account-panel').hidden=!session;
  if(session) {
    $('#account-name').textContent=session.user.name;
    $('#account-email').textContent=session.user.email;
    $('#account-role').textContent=session.user.role==='admin'?'Conta de administrador':'Conta de cliente';
  }
}

for(const [selector,endpoint] of [['#login-form','login'],['#register-form','cadastro']]) {
  $(selector).addEventListener('submit',async event=>{
    event.preventDefault();
    if(endpoint==='cadastro' && $('#register-password').value!==$('#confirm-password').value) {
      notice('As senhas não conferem.',true); $('#confirm-password').focus(); return;
    }
    const button=event.currentTarget.querySelector('button');button.disabled=true;
    const payload=Object.fromEntries(new FormData(event.currentTarget));
    try {
      const session=await request(`/api/auth/${endpoint}`,'POST',payload);
      $('#login-form').reset();$('#register-form').reset();render(session);
      notice(endpoint==='cadastro'?'Conta criada. Você já está conectado.':'Você entrou na sua conta.');
      $('#continue').focus();
    } catch(error) { notice(error.message,true); }
    finally {button.disabled=false;}
  });
}

$('#logout').addEventListener('click',async()=>{
  $('#logout').disabled=true;
  try {await request('/api/auth/logout','POST');render(null);notice('Você saiu da sua conta.');$('#login-email').focus();}
  catch(error){notice(error.message,true);}
  finally{$('#logout').disabled=false;}
});

try{const session=await getSession();render(session);notice(session?'Sua sessão está ativa.':'Escolha entrar ou criar uma conta.');}
catch(error){render(null);notice(error.message,true);}
