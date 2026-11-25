import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('cadastro avisa quando o endereço responde com outra API', async ({page}) => {
  let sent = false;
  await page.route('**/api/health', route => route.fulfill({json: {status: 'ok'}}));
  await page.route('**/api/auth/cadastro', route => { sent = true; return route.abort(); });
  await page.goto('/conta.html');
  await page.locator('#register-name').fill('Conta de teste');
  await page.locator('#register-email').fill('teste@example.com');
  await page.locator('#register-password').fill('senha-apenas-de-teste');
  await page.locator('#confirm-password').fill('senha-apenas-de-teste');
  await page.getByRole('button', {name: 'Criar conta', exact: true}).click();
  await expect(page.locator('#auth-notice')).toContainText('A API da floricultura não está disponível');
  expect(sent).toBe(false);
});

test('login também funciona no frontend Node com proxy da API',async({page})=>{
  await page.goto('http://127.0.0.1:4174/conta.html');
  await expect(page.locator('#auth-forms')).toBeVisible();
  await page.locator('#login-email').fill('admin-browser@example.com');
  await page.locator('#login-password').fill('senha-browser-apenas-testes');
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await expect(page.locator('#account-panel')).toBeVisible();
  await page.getByRole('link',{name:'Meus pedidos',exact:true}).click();
  await expect(page.locator('#order-workspace')).toBeVisible();
  await expect(page.locator('#session-name')).toContainText('Administrador');
  await page.getByRole('button',{name:'Sair da conta'}).click();
  await expect(page.locator('#order-workspace')).toBeHidden();
  expect((await page.request.get('http://127.0.0.1:4174/api/pedidos')).status()).toBe(401);
});

test('cadastro, sessão persistente, pedidos e logout no navegador',async({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/cliente');
  await expect(page.locator('#order-workspace')).toBeHidden();
  await page.getByRole('link',{name:'Entrar ou criar conta'}).click();
  await expect(page.locator('#auth-forms')).toBeVisible();
  await page.locator('#register-name').fill('Ana das Flores');
  const email=`ana-${Date.now()}@example.com`;
  await page.locator('#register-email').fill(email);
  await page.locator('#register-password').fill('minha-senha-de-flores');
  await page.locator('#confirm-password').fill('minha-senha-de-flores');
  await page.getByRole('button',{name:'Criar conta',exact:true}).click();
  await expect(page.locator('#account-panel')).toBeVisible();
  await expect(page.locator('#account-name')).toHaveText('Ana das Flores');
  expect(await page.evaluate(()=>document.cookie.includes('petal_session'))).toBe(false);
  await page.reload();
  await expect(page.locator('#account-panel')).toBeVisible();
  await page.getByRole('link',{name:'Meus pedidos',exact:true}).click();
  await expect(page.locator('#order-workspace')).toBeVisible();
  await expect(page.locator('#status option')).toHaveCount(1);
  await page.locator('#description').fill('Um buquê leve e alegre com flores da estação.');
  await page.getByRole('button',{name:'Criar pedido demonstrativo'}).click();
  await expect(page.locator('#notice')).toContainText('Pedido demonstrativo criado.');
  await page.getByRole('button',{name:'Atualizar estado'}).click();
  await expect(page.locator('#result')).toContainText('"status": "cancelado"');
  await page.getByRole('button',{name:'Sair da conta'}).click();
  await expect(page.locator('#order-workspace')).toBeHidden();
  expect((await page.request.get('/api/pedidos')).status()).toBe(401);
  await page.goto('/conta.html');
  await expect(page.locator('#auth-forms')).toBeVisible();
  await page.locator('#login-email').fill(email);
  await page.locator('#login-password').fill('incorreta');
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await expect(page.locator('#auth-notice')).toContainText('E-mail ou senha incorretos.');
  await page.locator('#login-password').fill('minha-senha-de-flores');
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await expect(page.locator('#account-panel')).toBeVisible();
  expect(errors).toEqual([]);
});

test('tela de conta é acessível e funciona em tela estreita',async({page})=>{
  await page.goto('/conta.html');
  await expect(page.locator('#auth-forms')).toBeVisible();
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  expect(audit.violations.map(item=>item.id)).toEqual([]);
  for(const width of [320,390,768,1440]){
    await page.setViewportSize({width,height:900});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
});
