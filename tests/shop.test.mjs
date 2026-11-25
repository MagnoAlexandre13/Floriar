import test from 'node:test';
import assert from 'node:assert/strict';
import {PRODUCTS,today,dateStatus,datesFor,deliveryFor,unitPrice,bagTotals,sanitizeBag,filterProducts,recommend,escapeHtml} from '../dist/shop.js';
const now=new Date('2026-11-05T20:00:00Z');
const item={id:'a',product:'sunday-morning',size:'classic',vase:true,quantity:2,zip:'97201',date:'2026-11-07',message:'For you <3'};
test('calendar uses Portland time across UTC midnight',()=>{assert.equal(today(new Date('2026-11-06T01:00:00Z')),'2026-11-05');});
test('delivery rejects malformed and unsupported ZIPs and returns both fee zones',()=>{assert.equal(deliveryFor('123').ok,false);assert.equal(deliveryFor('10001').ok,false);assert.equal(deliveryFor('97201').fee,6);assert.equal(deliveryFor(' 97206 ').fee,9);});
test('dates enforce preparation, closures, capacity and booking horizon',()=>{assert.match(dateStatus('2026-11-06',PRODUCTS[0],now),/preparação/);assert.equal(dateStatus('2026-11-07',PRODUCTS[0],now),'');assert.match(dateStatus('2026-11-08',PRODUCTS[0],now),/fecha/);assert.match(dateStatus('2026-11-07',PRODUCTS[3],now),/preparação/);assert.match(dateStatus('2026-12-08',PRODUCTS[0],now),/30 dias/);assert.match(dateStatus('2026-02-30',PRODUCTS[0],now),/Escolha/);const monday=new Date('2026-11-02T20:00:00Z');assert.match(dateStatus('2026-11-12',PRODUCTS[0],monday),/lotada/);});
test('each product has available dates and no unavailable date passes validation',()=>{for(const p of PRODUCTS){const dates=datesFor(p,now);assert.ok(dates.some(d=>!d.reason));for(const d of dates)assert.equal(dateStatus(d.date,p,now),d.reason);}});
test('totals include size, optional vase, quantity and per-bouquet delivery',()=>{assert.equal(unitPrice(item),86);assert.deepEqual(bagTotals([item]),{subtotal:172,delivery:12,total:184,count:2});const extra={...item,product:'garden-party',size:'petite',vase:false,quantity:1,zip:'97206'};assert.deepEqual(bagTotals([item,extra]),{subtotal:234,delivery:21,total:255,count:3});});
test('stored bag is validated and client-supplied prices are never trusted',()=>{assert.deepEqual(sanitizeBag({}),[]);assert.equal(sanitizeBag([{...item,quantity:99},{...item,product:'unknown'},{...item,zip:'10001'}]).length,0);const safe=sanitizeBag([{...item,id:'<script>',price:1,message:'x'.repeat(400)}]);assert.equal(safe[0].message.length,240);assert.equal(safe[0].id,'item-0');assert.equal(unitPrice(safe[0]),86);});
test('budget and color filters combine; no-results can occur',()=>{assert.deepEqual(filterProducts({budget:'50'},now).map(p=>p.id),['sunday-morning']);assert.equal(filterProducts({budget:'50',color:'rich'},now).length,0);assert.equal(filterProducts({occasion:'Thinking of You'},now).length,2);});
test('next delivery day advances past closed days',()=>{const friday=new Date('2026-11-06T20:00:00Z');const available=filterProducts({availability:'next'},friday);assert.equal(available.length,4);assert.ok(available.every(p=>p.lead===2));});
test('recommendations respect budget even when preferred style costs more',()=>{const results=recommend({occasion:'Happy Birthday',style:'bright',budget:'50'});assert.equal(results[0].id,'sunday-morning');assert.ok(results.every(p=>p.price<=50));assert.equal(recommend({occasion:'Congratulations',style:'wild',budget:'80'})[0].id,'wild-at-heart');});
test('gift messages are rendered as text rather than executable markup',()=>{assert.equal(escapeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');});

test('cart preserves custom colors and descriptions and accepts older saved items',()=>{
  const custom=sanitizeBag([{...item,color:'pink',description:'Flores rosas com folhagens leves.'}])[0];
  assert.equal(custom.color,'pink');assert.equal(custom.description,'Flores rosas com folhagens leves.');
  const legacy=sanitizeBag([item])[0];assert.equal(legacy.color,'original');assert.equal(legacy.description,'');
  const invalid=sanitizeBag([{...item,product:'sunflower',color:'red',description:'x'.repeat(1200)}])[0];
  assert.equal(invalid.color,'original');assert.equal(invalid.description.length,1000);
});
