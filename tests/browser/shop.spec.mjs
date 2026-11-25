import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {money} from '../../dist/shop.js';

test('girassóis permitem escolher tamanho, cor e descrição sem misturar personalizações',async({page})=>{
  await page.goto('/#bouquet/sunflower');
  await expect(page.locator('.product-info h1')).toHaveText('Buquê de Girassóis');
  for(const size of ['Pequeno','Médio','Grande'])await expect(page.locator('.size-grid label').filter({hasText:size})).toBeVisible();
  await page.locator('.size-grid input[value="abundant"]').check();
  await page.locator('.color-choices input[value="yellow"]').check();
  await page.locator('#delivery-zip').fill('97201');
  await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();
  await selectAvailableDate(page);
  await expect(page.locator('#add-to-bag')).toBeDisabled();
  await page.locator('#bouquet-description').fill('<b>Girassóis com folhagens leves e papel kraft.</b>');
  await expect(page.locator('#add-label')).toHaveText(`Adicionar ao carrinho · ${money(104)}`);
  await page.locator('#add-to-bag').click();
  await expect(page.locator('#bag-content')).toContainText('Cor: Amarelo');
  await expect(page.locator('#bag-content')).toContainText('<b>Girassóis com folhagens leves e papel kraft.</b>');
  await expect(page.locator('.bag-personalization b')).toHaveCount(0);
  await page.keyboard.press('Escape');
  await page.locator('.color-choices input[value="pink"]').check();
  await page.locator('#bouquet-description').fill('Girassóis com flores de apoio rosas e laço de tecido.');
  await page.locator('#add-to-bag').click();
  await expect(page.locator('.bag-item')).toHaveCount(2);
  await page.reload();
  await page.getByRole('button',{name:'Abrir carrinho, 2 itens'}).click();
  await expect(page.locator('.bag-item')).toHaveCount(2);
  await expect(page.locator('#bag-content')).toContainText('Cor: Rosa');
  await page.getByRole('button',{name:'Revisar carrinho demonstrativo'}).click();
  await expect(page.locator('.review-list')).toContainText('Girassóis com flores de apoio rosas');
  await expect(page.locator('.review-list b')).toHaveCount(0);
  await page.keyboard.press('Escape');
  for(const width of [320,390,768]){
    await page.setViewportSize({width,height:900});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
});

async function selectAvailableDate(page,selector='#delivery-date',index=0){const dates=await page.locator(`${selector} option:not([disabled])`).evaluateAll(options=>options.map(o=>o.value).filter(Boolean));await page.locator(selector).selectOption(dates[index]);return dates[index];}
async function openProduct(page){await page.goto('/#bouquet/sunday-morning');await expect(page.locator('.product-info h1')).toHaveText('Manhã de Domingo');await page.locator('#bouquet-description').fill('Um buquê delicado com folhagens leves e embalagem kraft.');}
async function addBouquet(page){await openProduct(page);await page.locator('#delivery-zip').fill('97201');await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();await selectAvailableDate(page);await page.locator('#add-to-bag').click();}
test('complete purchase configuration, delivery rejection, bag edits and persistence',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));await openProduct(page);
  await expect(page.locator('#add-to-bag')).toBeDisabled();
  await page.getByRole('button',{name:'Ver o buquê de cima'}).click();await expect(page.locator('#gallery-main')).toHaveAttribute('src',/detail.webp/);
  await page.locator('#delivery-zip').fill('10001');await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();await expect(page.locator('#delivery-status')).toContainText('Não entregamos');await expect(page.locator('#delivery-date')).toBeDisabled();
  await page.locator('#delivery-zip').fill('97201');await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();await expect(page.locator('#delivery-status')).toContainText(`${money(6)} por buquê`);
  await page.locator('.size-grid label').filter({hasText:'Pequeno'}).click();await expect(page.locator('#product-dimensions')).toContainText('28 cm');
  const date=await selectAvailableDate(page);await page.getByLabel('Incluir um vaso de vidro').check();await page.locator('#gift-message').fill('You make ordinary days lovely. — Sam');
  await expect(page.locator('#add-label')).toHaveText(`Adicionar ao carrinho · ${money(72)}`);await page.locator('#add-to-bag').click();
  await expect(page.locator('#bag-dialog')).toBeVisible();await expect(page.locator('.grand-total')).toContainText(money(72));
  await page.getByRole('button',{name:'Aumentar quantidade de Manhã de Domingo'}).click();await expect(page.locator('.grand-total')).toContainText(money(144));
  await page.locator('.bag-message summary').click();await page.locator('.bag-message textarea').fill('<b>Thinking of you</b>');await page.getByRole('button',{name:'Salvar mensagem'}).click();
  await page.reload();await page.getByRole('button',{name:'Abrir carrinho, 2 itens'}).click();await expect(page.locator('.grand-total')).toContainText(money(144));await expect(page.locator('[data-bag-date]')).toHaveValue(date);
  await page.locator('.bag-message summary').click();await expect(page.locator('.bag-message textarea')).toHaveValue('<b>Thinking of you</b>');
  await page.getByRole('button',{name:'Revisar carrinho demonstrativo'}).click();await expect(page.locator('#info-dialog')).toContainText('Nenhum pedido foi feito ou confirmado.');await expect(page.locator('.review-list')).toContainText('<b>Thinking of you</b>');await expect(page.locator('.review-list b')).toHaveCount(0);
  await page.getByRole('button',{name:'Voltar ao carrinho'}).click();await page.getByRole('button',{name:'Remover Manhã de Domingo'}).click();await expect(page.locator('.empty-bag')).toBeVisible();expect(errors).toEqual([]);
});
test('delivery edits require a fresh ZIP check and unavailable dates stay disabled',async({page})=>{await openProduct(page);await page.locator('#delivery-zip').fill('97201');await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();await selectAvailableDate(page);await expect(page.locator('#add-to-bag')).toBeEnabled();expect(await page.locator('#delivery-date option[disabled]').count()).toBeGreaterThan(1);await page.locator('#delivery-zip').fill('97206');await expect(page.locator('#add-to-bag')).toBeDisabled();await page.getByRole('button',{name:'Consultar ZIP',exact:true}).click();await expect(page.locator('#purchase-delivery')).toHaveText(money(9));});
test('collection filters, occasion navigation and empty result recovery',async({page})=>{await page.goto('/');await page.locator('[data-occasion="Thinking of You"]').click();await expect(page.locator('#product-grid .product-card')).toHaveCount(2);await page.locator('#filters [name="budget"]').selectOption('50');await page.locator('#filters [name="color"]').selectOption('rich');await expect(page.locator('.no-results')).toBeVisible();await page.getByRole('button',{name:'Ver todas as flores'}).click();await expect(page.locator('#product-grid .product-card')).toHaveCount(5);await page.locator('#filters [name="availability"]').selectOption('next');expect(await page.locator('#product-grid .product-card').count()).toBeGreaterThan(0);});
test('finder respects occasion, style and budget, with keyboard modal dismissal',async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Encontre as flores ideais'}).click();await page.locator('#finder-form label').filter({hasText:'Parabéns pela conquista'}).click();await page.getByRole('button',{name:'Continuar'}).click();await page.locator('#finder-form label').filter({hasText:'Livre e surpreendente'}).click();await page.getByRole('button',{name:'Continuar'}).click();await page.locator('#finder-form label').filter({hasText:'Até US$ 80'}).click();await page.getByRole('button',{name:'Encontrar minhas flores'}).click();await expect(page.locator('.finder-result').first()).toContainText('Espírito Livre');await page.keyboard.press('Tab');expect(await page.evaluate(()=>!!document.activeElement.closest('#finder-dialog'))).toBe(true);await page.keyboard.press('Escape');await expect(page.locator('#finder-dialog')).not.toBeVisible();await expect(page.getByRole('button',{name:'Encontre as flores ideais'})).toBeFocused();});
test('expired bag dates must be updated before sample review',async({page})=>{await addBouquet(page);await page.evaluate(()=>{const bag=JSON.parse(localStorage.getItem('petal-stem-bag-v1'));bag[0].date='2020-01-01';localStorage.setItem('petal-stem-bag-v1',JSON.stringify(bag));});await page.reload();await page.getByRole('button',{name:'Abrir carrinho, 1 item'}).click();await expect(page.getByRole('button',{name:'Revisar carrinho demonstrativo'})).toBeDisabled();await expect(page.locator('#bag-content')).toContainText('não está mais disponível');await selectAvailableDate(page,'[data-bag-date]');await expect(page.getByRole('button',{name:'Revisar carrinho demonstrativo'})).toBeEnabled();});
test('mobile navigation and sample subscription plan remain usable at narrow widths',async({page})=>{await page.setViewportSize({width:390,height:844});await page.goto('/');await page.getByRole('button',{name:'Abrir menu'}).click();await page.locator('#mobile-nav').getByRole('link',{name:'Assinaturas'}).click();await expect(page.locator('#mobile-nav')).not.toBeVisible();await page.getByRole('button',{name:'Escolha seu ritmo de flores'}).click();await page.locator('#subscription-form label').filter({hasText:'Mensal'}).click();await page.locator('#subscription-form label').filter({hasText:'Médio'}).click();await expect(page.locator('#subscription-summary')).toContainText(`Flores mensais · ${money(58)}`);await page.getByRole('button',{name:'Salvar meu plano demonstrativo'}).click();await expect(page.locator('#toast')).toContainText('Nenhuma assinatura foi iniciada');await page.reload();await page.getByRole('button',{name:'Escolha seu ritmo de flores'}).click();await expect(page.locator('#subscription-summary')).toContainText(`Flores mensais · ${money(58)}`);await page.keyboard.press('Escape');for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);}});
test('homepage, populated bag and finder pass automated accessibility checks',async({page})=>{await page.goto('/');for(const state of ['home','finder','bag']){if(state==='finder')await page.getByRole('button',{name:'Encontre as flores ideais'}).click();if(state==='bag'){await page.keyboard.press('Escape');await addBouquet(page);}const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(results.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);}});
test('images load, navigation recovers unknown routes, and corrupt storage is safe',async({page})=>{await page.goto('/');await expect(page.locator('html')).toHaveAttribute('lang','pt-BR');await page.evaluate(()=>{document.querySelectorAll('img').forEach(img=>img.loading='eager');});await expect.poll(()=>page.locator('img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);await page.evaluate(()=>localStorage.setItem('petal-stem-bag-v1','not json'));await page.goto('/#bouquet/not-a-flower');await expect(page.locator('#product-view')).toContainText('não foi encontrado');await page.getByRole('link',{name:'Ver as flores'}).click();await expect(page.locator('#home-view')).toBeVisible();await page.goto('/#%ZZ');await expect(page.locator('#home-view')).toBeVisible();});
