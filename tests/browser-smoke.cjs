// Optional development-only Playwright checks; no browser library ships in the app.
const assert = require('node:assert/strict');
const {chromium, firefox} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const base = process.env.TEST_URL || 'http://localhost:8000';
const output = process.env.TEST_OUTPUT || '/tmp/camagru-browser';
fs.mkdirSync(output,{recursive:true});

async function run(type, options, label) {
    console.log('Starting '+label+' browser smoke check.');
    const browser = await type.launch({headless:true,timeout:15000,...options});
    const context = await browser.newContext({viewport:{width:1280,height:900}});
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(15000);
    const problems = [];
    page.on('pageerror',error=>problems.push(error.message));
    page.on('console',message=>{
        if (['error','warning'].includes(message.type()) && !/getUserMedia|camera/i.test(message.text())) problems.push(message.text());
    });
    page.on('requestfailed',request=>problems.push(request.url()+': '+request.failure().errorText));
    const name = 'browser_' + label + '_' + Date.now().toString(36);
    fs.appendFileSync(path.join(output,'accounts.txt'),name+'\n');
    try {
        await page.goto(base);
        assert.equal(await page.evaluate(()=>document.compatMode),'CSS1Compat');
        await page.goto(base+'/?page=register');
        await page.locator('[name=username]').fill(name);
        await page.locator('[name=email]').fill(name+'@example.com');
        await page.locator('[name=password]').fill('BrowserPassword1!');
        await Promise.all([page.waitForURL('**/*page=register-done'),page.getByRole('button',{name:'Register',exact:true}).click()]);
        const messages = await (await context.request.get('http://localhost:8025/api/v1/messages?limit=200')).json();
        const message = messages.messages.find(m=>m.To.some(to=>to.Address===name+'@example.com'));
        assert.ok(message,'Confirmation email received');
        const detail = await (await context.request.get('http://localhost:8025/api/v1/message/'+message.ID)).json();
        const link = detail.Text.match(/http:\/\/localhost:8000\/\?page=confirm&token=[a-f0-9]+/)[0];
        await page.goto(link);
        await page.locator('[name=username]').fill(name);
        await page.locator('[name=password]').fill('BrowserPassword1!');
        await Promise.all([page.waitForURL('**/*page=home'),page.getByRole('button',{name:'Log in',exact:true}).click()]);
        await page.goto(base+'/?page=editor');
        await page.locator('#file-input').setInputFiles(path.resolve('public/cat-cartoon.png'));
        await page.waitForFunction(()=>document.querySelector('#file-input').files.length===1);
        assert.ok(await page.locator('#btn-capture').isDisabled(),'Base alone must not enable capture');
        // Wait until upload decoding has enabled overlay selection.
        await page.waitForFunction(()=>!document.getElementById('webcam').srcObject);
        await page.locator('.overlay-thumb').first().click();
        await page.waitForFunction(()=>!document.getElementById('btn-capture').disabled);
        await page.screenshot({path:path.join(output,label+'-editor.png'),fullPage:true});
        await Promise.all([page.waitForURL('**/*preview=*'),page.locator('#btn-capture').click()]);
        assert.ok(await page.locator('.thumb-item').count(),'Saved image thumbnail');
        await page.goto(base+'/?page=profile');
        assert.equal(await page.locator('[name=notify_on_comment]').isChecked(),true);
        await page.setViewportSize({width:375,height:812});
        for (const route of ['home','editor','profile']) {
            await page.goto(base+'/?page='+route);
            const widths = await page.evaluate(()=>({body:document.documentElement.scrollWidth,view:innerWidth}));
            assert.ok(widths.body<=widths.view,route+' mobile horizontal overflow');
            await page.screenshot({path:path.join(output,label+'-'+route+'-mobile.png'),fullPage:true});
        }
        await Promise.all([page.waitForURL('**/*page=login'),page.getByRole('button',{name:'Log out',exact:true}).click()]);
        await page.goto(base+'/?page=editor');
        assert.ok(page.url().includes('page=login'),'Editor protected after logout');
        assert.deepEqual(problems,[],'No unexpected browser console/network errors');
        console.log('Passed '+label+': registration/email/login, uploaded composition, preferences, mobile widths, logout and console.');
    } finally {
        await browser.close();
        execFileSync('docker',['compose','exec','-T','web','python','/app/tests/cleanup_browser.py'],{input:name+'\n'});
    }
}

(async()=>{
    if (process.env.TEST_BROWSER !== 'firefox') await run(chromium,process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {channel:'chrome'},'chrome');
    if (process.env.TEST_BROWSER !== 'chrome') await run(firefox,process.env.FIREFOX_PATH ? {executablePath:process.env.FIREFOX_PATH} : {},'firefox');
})().catch(error=>{console.error(error);process.exitCode=1;});
