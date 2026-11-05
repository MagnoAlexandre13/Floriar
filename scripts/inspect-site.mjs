import {chromium} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
fs.mkdirSync('.cache',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const response=await page.goto('http://127.0.0.1:4173');
  await page.evaluate(()=>document.fonts.ready);
  await page.evaluate(async()=>{for(const img of document.querySelectorAll('img[loading="lazy"]')){img.loading='eager';}await Promise.all([...document.images].map(img=>img.decode().catch(()=>{})));});
  await page.screenshot({path:'.cache/home-desktop.png',fullPage:true});
  const desktop=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  console.log(JSON.stringify({http:response.status(),errors,desktopViolations:desktop.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}));
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'.cache/home-mobile.png',fullPage:true});
  console.log('mobile overflow',await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));
  await page.goto('http://127.0.0.1:4173/#bouquet/sunday-morning');
  await page.screenshot({path:'.cache/product-mobile.png',fullPage:true});
  const product=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  console.log(JSON.stringify({productViolations:product.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}));
}finally{await browser.close();}
