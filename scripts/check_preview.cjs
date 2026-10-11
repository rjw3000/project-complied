/* Browser checks for synthetic navigation, data scope and accessible interactions. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..');
  const server=spawn('python3',['-m','http.server','8097','--bind','127.0.0.1','--directory',path.join(root,'public')],{stdio:'ignore'});
  let browser;
  try {
    for(let i=0;i<100;i++) {try{const r=await fetch('http://127.0.0.1:8097/');if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
    browser=await chromium.launch({headless:true});
    const context=await browser.newContext({viewport:{width:1440,height:1100},acceptDownloads:true});
    const page=await context.newPage();const errors=[];const external=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8097/'))external.push(r.url());});
    await page.goto('http://127.0.0.1:8097/');
    await page.locator('h1').waitFor();
    assert.equal(await page.locator('h1').textContent(),'Business overview');
    assert.equal(await page.locator('#menu-button').isVisible(),false,'Mobile menu must be hidden on desktop');
    const output=process.env.COMPLIED_UI_OUTPUT;if(output){fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,'dashboard-desktop.png'),fullPage:true});}
    await page.locator('[data-scope]').selectOption('ivy');
    assert.match(await page.locator('.sales-total').textContent(),/5,000/);
    assert.equal(await page.locator('.location-row').count(),1);
    await page.locator('[data-scope]').selectOption('both');
    await page.locator('.side-nav a[href="#requirements"]').click();
    await page.locator('#requirement-search').fill('Albemarle');
    assert.equal(await page.locator('#requirement-results tbody tr').count(),1);
    await page.locator('#requirement-results [data-detail]').click();
    assert.equal(await page.locator('dialog').evaluate(d=>d.open),true);
    assert.match(await page.locator('#dialog-title').textContent(),/Pantops/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('dialog').evaluate(d=>d.open),false);
    await page.locator('#clear-filters').click();
    await page.locator('#requirement-type').selectOption('Tax filing');
    assert.equal(await page.locator('#requirement-results tbody tr').count(),1);
    await page.locator('.side-nav a[href="#upload"]').click();
    await page.getByRole('heading',{name:'Monthly sales workspace',exact:true}).waitFor();
    await page.locator('a[href="#reconcile"]').first().click();
    await page.getByRole('heading',{name:'Reconcile monthly sales',exact:true}).waitFor();
    await page.locator('[data-scope]').selectOption('pantops');
    assert.match(await page.locator('.total-row').textContent(),/8,000/);
    await page.locator('[data-scope]').selectOption('both');
    assert.match(await page.locator('.total-row').textContent(),/13,000/);
    await page.locator('[data-detail="source-ivy"]').click();
    const downloaded=page.waitForEvent('download');await page.locator('dialog [data-download="ivy"]').click();
    const download=await downloaded;const bytes=fs.readFileSync(await download.path());
    const fixture=fs.readFileSync(path.join(root,'fixtures/synthetic/ivy-2026-10.csv'));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),createHash('sha256').update(fixture).digest('hex'));
    await page.keyboard.press('Escape');
    await page.locator('a[href="#review"]').first().click();
    await page.getByRole('heading',{name:'Review monthly source package',exact:true}).waitFor();
    await page.locator('#review-notes').fill('<script>alert("injection")</script>');
    await page.locator('#preview-decision').click();
    assert.match(await page.locator('dialog').textContent(),/Not saved/);
    assert.equal(await page.locator('dialog script').count(),0);
    assert.match(await page.locator('dialog').textContent(),/<script>/);
    await page.keyboard.press('Escape');
    await page.locator('.side-nav a[href="#calendar"]').click();
    await page.getByRole('heading',{name:'Compliance calendar',exact:true}).waitFor();
    await page.locator('.skip-link').focus();await page.locator('.skip-link').press('Enter');
    assert.equal(new URL(page.url()).hash,'#calendar','Skip to content must preserve the current workspace');
    assert.equal(await page.locator('.calendar-day:not(.blank)').count(),31);
    assert.equal(await page.locator('.calendar-day.blank').count(),4);
    const routeTitles={overview:'Business overview',upload:'Monthly sales workspace',reconcile:'Reconcile monthly sales',review:'Review monthly source package',requirements:'Requirement register',calendar:'Compliance calendar',queue:'Review queue',evidence:'Evidence library',integrations:'Connected services',settings:'Workspace settings'};
    for(const route of ['queue','evidence','integrations','settings']) {await page.locator('.side-nav a[href="#'+route+'"]').click();await page.getByRole('heading',{name:routeTitles[route],exact:true}).waitFor();assert.equal(await page.locator('h1').count(),1);}
    await page.locator('.side-nav a[href="#evidence"]').click();
    await page.getByRole('heading',{name:'Evidence library',exact:true}).waitFor();
    const packetDownload=page.waitForEvent('download');await page.locator('[data-download="packet"]').click();
    const packet=JSON.parse(fs.readFileSync(await (await packetDownload).path(),'utf8'));assert.equal(packet.synthetic,true);assert.equal(packet.return_ready,false);assert.equal(packet.sources.length,2);
    await page.setViewportSize({width:390,height:844});
    for(const route of ['overview','upload','reconcile','review','requirements','calendar','queue','evidence','integrations','settings']) {
      await page.evaluate(r=>location.hash=r,route);await page.getByRole('heading',{name:routeTitles[route],exact:true}).waitFor();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,'Unexpected page overflow on '+route);
    }
    await page.locator('#menu-button').click();assert.equal(await page.locator('#menu-button').getAttribute('aria-expanded'),'true');
    await page.keyboard.press('Escape');assert.equal(await page.locator('#menu-button').getAttribute('aria-expanded'),'false');
    await page.locator('#menu-button').click();await page.locator('.side-nav a[href="#overview"]').click();
    await page.getByRole('heading',{name:'Business overview',exact:true}).waitFor();
    assert.equal(await page.locator('#menu-button').getAttribute('aria-expanded'),'false');
    if(output){await page.screenshot({path:path.join(output,'dashboard-mobile.png'),fullPage:true});await page.evaluate(()=>location.hash='reconcile');await page.waitForTimeout(100);await page.screenshot({path:path.join(output,'reconcile-mobile.png'),fullPage:true});}
    assert.deepEqual(errors,[],'Browser errors');assert.deepEqual(external,[],'Preview must not make external requests');
    console.log('Preview browser checks passed: routes, scope totals, filters, dialogs, downloads, escaping, calendar, mobile navigation and overflow.');
  } finally {if(browser)await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
