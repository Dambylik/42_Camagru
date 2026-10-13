const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const editor = fs.readFileSync('public/js/editor.js', 'utf8');
const move = editor.slice(editor.indexOf('    function onMove('), editor.indexOf('    function onUp('));
for (const left of [false, true]) for (const top of [false, true]) {
    for (const target of [50, 300, 550, -100, 700]) {
        const s = {x: 100, y: 100, w: 400, h: 400};
        const ctx = {drag: 'resize', frozen: false, active: 0, stickers: [s],
            SIZE: 600, resizeLeft: left, resizeTop: top,
            anchorX: left ? 500 : 100, anchorY: top ? 500 : 100,
            canvas: {style: {}}, canvasXY: () => ({x: target, y: target})};
        vm.createContext(ctx);
        vm.runInContext(move + '\nonMove({preventDefault(){}});', ctx);
        assert.equal(left ? s.x + s.w : s.x, ctx.anchorX);
        assert.equal(top ? s.y + s.h : s.y, ctx.anchorY);
        assert.ok(s.w >= 40 && s.h >= 40);
        assert.ok(s.x >= 0 && s.y >= 0 && s.x + s.w <= 600 && s.y + s.h <= 600);
        if (!left && !top && target === 550) assert.deepEqual(s, {x:100,y:100,w:450,h:450});
    }
}
const gallery = fs.readFileSync('public/js/gallery.js', 'utf8');
const get = gallery.slice(gallery.indexOf('    function get('), gallery.indexOf('    // ── Build'));
const load = gallery.slice(gallery.indexOf('    function loadNext('), gallery.indexOf('    // ── Scroll listener'));
for (const failure of ['http', 'network', 'timeout', 'abort', 'json', 'shape', 'send', 'card']) {
    let xhr;
    class Xhr {
        constructor() { xhr = this; }
        open() {}
        send() { if (failure === 'send') throw Error('send'); }
    }
    const ctx = {XMLHttpRequest: Xhr, loading:false, failed:false, curPage:1, maxPages:3,
        retry:{style:{}, addEventListener(){}}, loader:{style:{}},
        grid:{appendChild(){}}, document:{createDocumentFragment:()=>({appendChild(){}})},
        buildCard:()=> { if (failure === 'card') throw Error('card'); return {}; }};
    vm.createContext(ctx);
    vm.runInContext(get + load + '\nloadNext();', ctx);
    if (failure !== 'send') {
        xhr.status = failure === 'http' ? 500 : 200;
        xhr.responseText = failure === 'json' ? '{' : JSON.stringify(failure === 'shape' ? {} : {page:2,pages:3,images:[{}]});
        if (['network','timeout','abort'].includes(failure)) xhr['on' + (failure === 'network' ? 'error' : failure)]();
        else xhr.onload();
    }
    assert.equal(ctx.loading, false, failure);
    assert.equal(ctx.curPage, 1, failure);
    assert.equal(ctx.retry.style.display, 'inline-block', failure);
    assert.equal(ctx.loader.style.display, 'none', failure);
    // The same page can be successfully retried after any failure.
    Xhr.prototype.send = function(){};
    ctx.buildCard = () => ({});
    vm.runInContext('loadNext();', ctx);
    xhr.status = 200;
    xhr.responseText = JSON.stringify({page:2,pages:3,images:[]});
    xhr.onload();
    assert.equal(ctx.curPage, 2, failure + ' retry');
    assert.equal(ctx.loading, false);
    assert.equal(ctx.failed, false);
}
console.log('Passed: 20 corner resize cases and 8 gallery failure/retry cases.');
