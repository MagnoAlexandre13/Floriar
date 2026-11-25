import {test, expect} from '@playwright/test';

test.beforeEach(async({page})=>{
  const response=await page.request.post('/api/auth/login',{data:{email:'admin-browser@example.com',password:'senha-browser-apenas-testes'}});
  expect(response.status()).toBe(200);
});

test('cliente envia a personalização do buquê de girassóis',async({page})=>{
  await page.goto('/cliente');
  await expect(page.locator('#create')).toBeEnabled();
  await page.locator('#product').selectOption('sunflower');
  await expect(page.locator('#create')).toBeEnabled();
  await expect(page.locator('#color option')).toHaveCount(4);
  await page.locator('#color').selectOption('pink');
  await page.locator('#size').selectOption('abundant');
  const description='Girassóis com flores de apoio rosas e embalagem em papel kraft.';
  await page.locator('#description').fill(description);
  await page.getByRole('button',{name:'Criar pedido demonstrativo'}).click();
  await expect(page.locator('#notice')).toContainText('Pedido demonstrativo criado.');
  const order=JSON.parse(await page.locator('#result').textContent());
  expect(order.total_cents).toBe(10400);
  expect(order.items[0]).toMatchObject({product_id:'sunflower',color:'pink',size:'abundant',description});
});

test('cliente cria, consulta e atualiza um pedido pela API', async ({page}) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/cliente');
  await expect(page.locator('#create')).toBeEnabled();
  await page.locator('#description').fill('Um buquê delicado com flores claras e embalagem kraft.');
  await expect(page.locator('#product option')).toHaveCount(5);
  await page.locator('#quantity').fill('2');
  await page.getByLabel('Incluir vaso').check();
  await page.locator('#message').fill('<b>Para você!</b>');
  await page.getByRole('button', {name: 'Criar pedido demonstrativo'}).click();
  await expect(page.locator('#notice')).toContainText('Pedido demonstrativo criado.');
  const order = JSON.parse(await page.locator('#result').textContent());
  expect(order.total_cents).toBe(18400);
  expect(order.items[0].message).toBe('<b>Para você!</b>');
  await expect(page.locator('#result b')).toHaveCount(0);
  await expect(page.locator('#order-id')).toHaveValue(order.id);
  await page.reload();
  await page.locator('#order-id').fill(order.id);
  await page.getByRole('button', {name: 'Consultar pedido', exact: true}).click();
  await expect(page.locator('#notice')).toHaveText('Pedido consultado na API.');
  await expect(page.locator('#result')).toContainText(order.id);
  await page.locator('#status').selectOption('entregue');
  await page.getByRole('button', {name: 'Atualizar estado'}).click();
  await expect(page.locator('#notice')).toContainText('Não é permitido mudar de recebido para entregue');
  for (const status of ['em_preparacao', 'enviado', 'entregue']) {
    await page.locator('#status').selectOption(status);
    const response = page.waitForResponse(response => response.request().method() === 'PATCH');
    await page.getByRole('button', {name: 'Atualizar estado'}).click();
    expect((await (await response).json()).status).toBe(status);
    await expect(page.locator('#notice')).toHaveText('Estado atualizado na API.');
  }
  await page.getByRole('button', {name: 'Listar últimos pedidos'}).click();
  await expect(page.locator('#notice')).toHaveText('Últimos pedidos consultados na API.');
  expect(JSON.parse(await page.locator('#result').textContent()).items.some(item => item.id === order.id)).toBe(true);
  expect(errors).toEqual([]);
});

test('cliente mostra erro de entrega e se recupera', async ({page}) => {
  await page.goto('/cliente');
  await expect(page.locator('#create')).toBeEnabled();
  await page.locator('#description').fill('Um buquê delicado com flores claras e embalagem kraft.');
  await page.locator('#zip').fill('10001');
  await page.getByRole('button', {name: 'Criar pedido demonstrativo'}).click();
  await expect(page.locator('#notice')).toContainText('Entrega disponível apenas');
  await expect(page.locator('#create')).toBeEnabled();
  await page.locator('#description').fill('Um buquê delicado com flores claras e embalagem kraft.');
  await page.locator('#zip').fill('97206');
  await page.getByRole('button', {name: 'Criar pedido demonstrativo'}).click();
  await expect(page.locator('#notice')).toContainText('Pedido demonstrativo criado.');
  expect(JSON.parse(await page.locator('#result').textContent()).total_cents).toBe(7700);
});

test('cliente trata falha da API e cabe em tela estreita', async ({page}) => {
  await page.setViewportSize({width: 360, height: 800});
  await page.route('**/api/produtos', route => route.abort());
  await page.goto('/cliente');
  await expect(page.locator('#notice')).toContainText('API indisponível');
  await expect(page.locator('#create')).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
