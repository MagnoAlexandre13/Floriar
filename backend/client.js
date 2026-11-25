import {getSession, request as apiRequest} from '/auth-api.js';
const $ = selector => document.querySelector(selector);
const currency = cents => new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'USD'}).format(cents / 100);
const notice = text => { $('#notice').textContent = text; };
let datesController;
let activeUser = null;
let productsById = new Map();
const colorLabels = {original:'Paleta da foto',yellow:'Amarelo',pink:'Rosa',white:'Branco',red:'Vermelho',lilac:'Lilás'};

async function request(path, method = 'GET', body, signal) {
  try { return await apiRequest(path, method, body, signal); }
  catch(error) { if(error.status===401) renderAuth(null); throw error; }
}

function renderAuth(session) {
  activeUser=session?.user || null;
  $('#order-workspace').hidden=!activeUser;
  $('#login-link').hidden=!!activeUser;
  $('#client-logout').hidden=!activeUser;
  $('#session-name').textContent=activeUser?`Conectado como ${activeUser.name}${activeUser.role==='admin'?' · Administrador':''}`:'Entre na sua conta para criar e acompanhar pedidos.';
  if(!activeUser) {$('#result').textContent='As respostas da API aparecerão aqui.';$('#order-id').value='';}
  const choices=activeUser?.role==='admin'?[['em_preparacao','Em preparação'],['enviado','Enviado'],['entregue','Entregue'],['cancelado','Cancelado']]:[['cancelado','Cancelar meu pedido']];
  $('#status').replaceChildren(...choices.map(([value,label])=>new Option(label,value)));
}

$('#client-logout').addEventListener('click',async()=>{
  $('#client-logout').disabled=true;
  try {await request('/api/auth/logout','POST');renderAuth(null);notice('Você saiu da sua conta.');}
  catch(error){notice(error.message);}
  finally{$('#client-logout').disabled=false;}
});

function show(data) {
  $('#result').textContent = JSON.stringify(data, null, 2);
  if (data.id) $('#order-id').value = data.id;
}

async function loadDates() {
  datesController?.abort();
  datesController = new AbortController();
  $('#date').disabled = true;
  $('#create').disabled = true;
  $('#date').replaceChildren();
  const product = productsById.get($('#product').value);
  $('#color').replaceChildren(...product.colors.map(color => new Option(colorLabels[color], color)));
  $('#color').disabled = false;
  try {
    const dates = await request(`/api/produtos/${encodeURIComponent($('#product').value)}/datas`, 'GET', undefined, datesController.signal);
    for (const date of dates) {
      const option = new Option(`${date.date}${date.reason ? ` — ${date.reason}` : ''}`, date.date);
      option.disabled = !date.available;
      $('#date').add(option);
    }
    $('#date').value = dates.find(date => date.available)?.date || '';
    $('#date').disabled = false;
    $('#create').disabled = !$('#date').value;
    notice('Catálogo e datas consultados na API.');
  } catch (error) {
    if (error.name !== 'AbortError') notice(`Não foi possível consultar as datas: ${error.message}`);
  }
}

$('#product').addEventListener('change', loadDates);
$('#order-form').addEventListener('submit', async event => {
  event.preventDefault();
  if ($('#create').disabled) return;
  $('#create').disabled = true;
  const form = new FormData(event.currentTarget);
  const item = Object.fromEntries(form);
  item.quantity = Number(item.quantity);
  item.vase = form.has('vase');
  try {
    const order = await request('/api/pedidos', 'POST', {items: [item]});
    show(order);
    notice(`Pedido demonstrativo criado. Total: ${currency(order.total_cents)}. Guarde o identificador para consultar depois.`);
  } catch (error) {
    notice(`Não foi possível criar o pedido: ${error.message}`);
  } finally {
    $('#create').disabled = false;
  }
});

$('#lookup-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    show(await request(`/api/pedidos/${encodeURIComponent($('#order-id').value.trim())}`));
    notice('Pedido consultado na API.');
  } catch (error) { notice(error.message); }
});

$('#status-form').addEventListener('submit', async event => {
  event.preventDefault();
  const id = $('#order-id').value.trim();
  if (!id) { notice('Informe ou crie um pedido primeiro.'); return; }
  const button = event.currentTarget.querySelector('button');
  button.disabled = true;
  try {
    show(await request(`/api/pedidos/${encodeURIComponent(id)}/status`, 'PATCH', {status: $('#status').value}));
    notice('Estado atualizado na API.');
  } catch (error) { notice(error.message); }
  finally { button.disabled = false; }
});

$('#list').addEventListener('click', async () => {
  try { show(await request('/api/pedidos?limit=10')); notice('Últimos pedidos consultados na API.'); }
  catch (error) { notice(error.message); }
});

try {
  renderAuth(await getSession());
  const products = await request('/api/produtos');
  productsById = new Map(products.map(product => [product.id, product]));
  for (const product of products) $('#product').add(new Option(`${product.name} — a partir de ${currency(product.price_cents)}`, product.id));
  if (!products.length) throw new Error('O catálogo está vazio.');
  $('#product').disabled = false;
  await loadDates();
  if(!activeUser)notice('Entre na sua conta para continuar. O catálogo da loja é público.');
} catch (error) { notice(`API indisponível: ${error.message}. Recarregue a página para tentar novamente.`); }
