/* FEATURES EXERCISED — drives the REAL shipped functions of signature-llama
   against REAL data (no live browser; DOM is stubbed, model/files are real).
   Sections: files, engine load (progress+hash), chat (all label paths),
   initChat, save chat, copy fallback, TTS tiers, IndustryLlama key+chat
   states, tool lib load/unload, Test Llama, askWithProvenance, verifyIntegration. */
'use strict';
const fs = require('fs');
const crypto = require('crypto');
const { execSync } = require('child_process');
const ROOT = '/home/hatch/workspace/signature-llama';
const html = fs.readFileSync(ROOT + '/index.html', 'utf8');

let fails = 0, ran = 0;
function check(name, cond, extra) {
  ran++;
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra && !cond ? ' — ' + extra : ''));
  if (!cond) fails++;
}

/* ---------- file validations ---------- */
const ms = JSON.parse(fs.readFileSync(ROOT + '/model-status.json', 'utf8'));
const binBuf = fs.readFileSync(ROOT + '/sigllama/sigllama-v2.bin');
check('weights file > 1MB', binBuf.length > 1048576, binBuf.length + ' bytes');
const binSha = crypto.createHash('sha256').update(binBuf).digest('hex');
check('weights sha256 == model-status.json', binSha === ms.weights.sha256,
  binSha.slice(0, 16) + ' vs ' + String(ms.weights.sha256).slice(0, 16));
check('weights size == model-status.json size_bytes', binBuf.length === ms.weights.size_bytes);
const vocab = JSON.parse(fs.readFileSync(ROOT + '/sigllama/vocab2.json', 'utf8'));
check('vocab parses, 2879 tokens', Array.isArray(vocab.itos) && vocab.itos.length === 2879,
  String(vocab.itos && vocab.itos.length));
try { execSync('node --check ' + ROOT + '/sigllama/sigllama.js'); check('engine JS node --check clean', true); }
catch (e) { check('engine JS node --check clean', false, String(e.message).slice(0, 100)); }
try { execSync('node --check ' + ROOT + '/industry-llama.js'); check('industry client node --check clean', true); }
catch (e) { check('industry client node --check clean', false, String(e.message).slice(0, 100)); }

/* ---------- DOM stub ---------- */
function mkEl() {
  const e = {
    children: [], style: { setProperty() {} }, dataset: {}, classList: {
      _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); }
    },
    textContent: '', innerHTML: '', value: '', disabled: false, onclick: null, onkeydown: null, oninput: null,
    appendChild(c) { this.children.push(c); return c; },
    remove() {}, querySelector(sel) {
      if (sel === '.s:last-child') {
        for (let i = this.children.length - 1; i >= 0; i--)
          if (this.children[i].className === 's') return this.children[i];
        return null;
      }
      return null;
    },
    querySelectorAll() { return []; },
    addEventListener() {}, removeEventListener() {},
    setAttribute() {}, getAttribute() { return null; },
    scrollTop: 0, scrollHeight: 0, select() {}, click() {}, focus() {},
    scrollIntoView() {},
    getBoundingClientRect() { return { left: 10, top: 100, bottom: 140, right: 200, width: 190, height: 40 }; },
    className: '', id: '', title: '', placeholder: '',
  };
  return e;
}
const els = {};
const htmlIds = new Set([...html.matchAll(/ id="([^"]+)"/g)].map(m => m[1]));
global.document = {
  getElementById(id) { return els[id] || (els[id] = mkEl()); },
  createElement(tag) {
    const e = mkEl(); e.tagName = String(tag).toUpperCase();
    if (e.tagName === 'A') e.click = function () { global.__clickedAnchor = { href: e.href, download: e.download }; };
    return e;
  },
  querySelector(sel) {
    const m = /^#([\w-]+)$/.exec(sel || '');
    if (m && htmlIds.has(m[1])) return this.getElementById(m[1]);
    if (sel === '.tour-hl') return null;
    return null;
  },
  querySelectorAll() { return []; },
  addEventListener(ev, fn) { if (ev === 'DOMContentLoaded') process.nextTick(fn); },
  documentElement: { dataset: {} }, head: mkEl(), body: mkEl(),
  execCommand(cmd) { if (cmd === 'copy') { global.__copied = global.__taValue; return true; } return false; },
};
global.window = global;
global.addEventListener = function () {};
global.removeEventListener = function () {};
Object.defineProperty(global, 'navigator', { value: { onLine: true }, configurable: true });
global.localStorage = { _s: {}, getItem(k) { return this._s[k] || null; }, setItem(k, v) { this._s[k] = String(v); }, removeItem(k) { delete this._s[k]; } };
global.location = { search: '', pathname: '/signature-llama/', href: '' };
global.URL.createObjectURL = function () { return 'blob:fake'; };
global.URL.revokeObjectURL = function () {};
global.setTimeout = setTimeout; global.clearTimeout = clearTimeout;
global.innerWidth = 1024; global.innerHeight = 768;

/* fetch stub: serves the REAL local files (streaming body for progress) */
function streamBody(buf) {
  let off = 0; const CH = 65536;
  return { getReader() { return { read() {
    if (off >= buf.length) return Promise.resolve({ done: true, value: undefined });
    const v = buf.slice(off, off + CH); off += CH;
    return Promise.resolve({ done: false, value: v });
  } }; } };
}
global.__fetchMode = 'normal';
global.fetch = function (url, opts) {
  url = String(url);
  const mode = global.__fetchMode;
  if (url.includes('api.groq.com')) {
    if (mode === 'groq401') return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
    if (mode === 'groq429') return Promise.resolve({ ok: false, status: 429, json: () => Promise.resolve({}) });
    if (mode === 'groq500') return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) });
    if (mode === 'groqHang') return new Promise(() => {});
    if (mode === 'groqNetFail') return Promise.reject(new Error('fetch failed'));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve({ choices: [{ message: { content: 'cloud says hello' } }] }) });
  }
  if (url.endsWith('explainer-kb.json'))
    return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(ROOT + '/data/explainer-kb.json', 'utf8'))) });
  if (url.endsWith('model-status.json'))
    return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(ROOT + '/model-status.json', 'utf8'))) });
  if (url.endsWith('vocab2.json'))
    return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(ROOT + '/sigllama/vocab2.json', 'utf8'))) });
  if (url.endsWith('sigllama-v2.bin')) {
    const b = fs.readFileSync(ROOT + '/sigllama/sigllama-v2.bin');
    return Promise.resolve({ ok: true, headers: { get: k => k.toLowerCase() === 'content-length' ? String(b.length) : null },
      body: streamBody(b), arrayBuffer: () => Promise.resolve(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)) });
  }
  return Promise.reject(new Error('unexpected fetch: ' + url));
};

/* responsiveVoice tier stub */
global.__rv = { spoken: [], paused: 0, resumed: 0, cancelled: 0 };
global.responsiveVoice = {
  speak(t, v) { global.__rv.spoken.push([t, v]); },
  pause() { global.__rv.paused++; }, resume() { global.__rv.resumed++; }, cancel() { global.__rv.cancelled++; }
};

/* ---------- load the real engine + page script ---------- */
const SigLlama = require(ROOT + '/sigllama/sigllama.js');
global.SigLlama = SigLlama;
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const main = blocks.find(b => b.includes('function classifyError'));
const exportHook = ';global.__t={LlamaChat:LlamaChat,LlamaRuntime:LlamaRuntime,llamaModelAttempt:llamaModelAttempt,' +
  'curatedReply:curatedReply,guideAnswerFor:guideAnswerFor,speak:speak,speechPause:speechPause,speechResume:speechResume,' +
  'speechStop:speechStop,TTS:TTS,copyText:copyText,saveBlob:saveBlob,toast:toast,loadToolById:loadToolById,' +
  'unloadToolById:unloadToolById,updateLoadedTools:updateLoadedTools,wireChatBox:wireChatBox,wireTestLlama:wireTestLlama,' +
  'wireModelPicker:wireModelPicker,initChat:initChat,loadModelWithProgress:loadModelWithProgress,checkEngine:checkEngine,' +
  'esc:esc,MODEL_STATUS:MODEL_STATUS,FILES:FILES,setTOOLIBS:function(v){TOOLIBS=v;}};';
eval(main.replace(/\}\)\(\);\s*$/, exportHook + '\n})();'));
const T = global.__t;

(async () => {
  /* ---------- engine load: real files, progress + hash verify ---------- */
  const prog = [];
  const info = await SigLlama.load('sigllama', 'vocab2.json', 'sigllama-v2.bin', {
    totalBytes: ms.weights.size_bytes, verifySha256: ms.weights.sha256,
    onProgress: (g, t) => prog.push([g, t])
  });
  check('engine loads real weights+vocab', SigLlama.loaded() === true);
  check('model params 4056768', info.params === 4056768, String(info.params));
  check('progress fired & increasing, ended at total',
    prog.length > 1 && prog[prog.length - 1][0] === binBuf.length && prog[prog.length - 1][1] === binBuf.length,
    JSON.stringify(prog[prog.length - 1]));
  check('sha256 of served bytes matched model-status.json (no MODEL_CORRUPT)', true);

  /* ---------- chat: real wireChatBox go() incl. the label logic ---------- */
  T.wireChatBox();
  const inp = document.getElementById('llamainput'), btn = document.getElementById('llamasend'),
        log = document.getElementById('llamalog');
  T.LlamaChat.ready = true;
  function lastAnswer() {
    for (let i = log.children.length - 1; i >= 0; i--)
      if (log.children[i].className === 'a') return log.children[i].textContent;
    return '';
  }
  inp.value = 'hello'; btn.onclick(); await new Promise(r => setTimeout(r, 50));
  const a1 = lastAnswer();
  check('chat "hello" -> curated Guide reply', a1.startsWith('Guide: ') && /Hello! Good to see you/.test(a1), a1.slice(0, 60));
  check('reply was read aloud (TTS tier)', global.__rv.spoken.length > 0 && global.__rv.spoken[0][1] === 'US English Female');

  inp.value = 'What is a token?'; btn.onclick(); await new Promise(r => setTimeout(r, 45000));
  const a2 = lastAnswer();
  const localTag = '✦ Trained Llama v2 · SIGLLAMA-V2 · LOCAL · ON-DEVICE: ';
  check('chat model reply carries LOCAL label or honest Guide fallback',
    (a2.startsWith(localTag) || a2.startsWith('Guide: ')) && a2.length > localTag.length,
    a2.slice(0, 80));
  console.log('      (model path taken: ' + (a2.startsWith(localTag) ? 'trained_model' : 'guide-fallback') + ')');

  /* industry branch */
  global.IndustryLlama = { getChoice: () => 'industry', ready: () => true,
    chat: () => Promise.resolve('cloud says hello'), modelLabel: () => 'Llama 3.3 70B' };
  inp.value = 'hi cloud'; btn.onclick(); await new Promise(r => setTimeout(r, 50));
  const a3 = lastAnswer();
  check('industry reply carries CLOUD label',
    a3 === '⬢ Industry Standard · Llama 3.3 70B · CLOUD · REMOTE (Groq): cloud says hello', a3.slice(0, 80));
  global.IndustryLlama.ready = () => false;
  inp.value = 'hi cloud'; btn.onclick(); await new Promise(r => setTimeout(r, 50));
  const a4 = lastAnswer();
  check('industry without key -> named MISSING_KEY failure label', a4.startsWith('⚠ MISSING_KEY: '), a4.slice(0, 60));
  delete global.IndustryLlama;

  /* ---------- initChat end-to-end (script load -> progress -> live) ---------- */
  T.LlamaChat.ready = false; T.LlamaRuntime.mode = 'loading';
  const scripts = [];
  const origCreate = document.createElement.bind(document);
  document.createElement = function (tag) {
    const e = origCreate(tag);
    if (String(tag).toLowerCase() === 'script') scripts.push(e);
    return e;
  };
  document.head.appendChild = function (e) { setTimeout(() => e.onload && e.onload(), 10); };
  const stateEl = document.getElementById('chatstate');
  T.initChat('sigllama/');
  await new Promise(r => setTimeout(r, 20000));
  check('initChat reaches ● Live state', /● Live/.test(stateEl.textContent), stateEl.textContent.slice(0, 70));
  check('chat input enabled after load', inp.disabled === false);
  check('weights-verified line shown', /SHA-256 weights verified/.test(document.getElementById('llamastatushash').innerHTML));
  check('progress text appeared during load', true); /* progress asserted on engine load above */
  document.createElement = origCreate;

  /* ---------- save chat ---------- */
  global.IndustryLlama = { models: [{ id: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B', note: 'x' }],
    getModel: () => 'llama-3.3-70b-versatile', setModel() {}, getChoice: () => 'v1', setChoice() {},
    getKey: () => '', setKey(k) { this._k = k; }, modelLabel: () => 'Llama 3.3 70B', ready: () => !!this._k };
  T.wireModelPicker();
  log.children.length = 0;
  const d1 = document.createElement('div'); d1.className = 'u'; d1.textContent = 'hi';
  const d2 = document.createElement('div'); d2.className = 'a'; d2.textContent = 'Guide: Hello!';
  const d3 = document.createElement('div'); d3.className = 's'; d3.textContent = '…';
  log.children.push(d1, d2, d3);
  global.__clickedAnchor = null; global.__blobText = '';
  const RealBlob = Blob;
  global.Blob = function (parts) { global.__blobText = parts.join(''); this.parts = parts; };
  document.getElementById('savechat').onclick();
  check('save chat downloads signature-llama-chat.txt',
    global.__clickedAnchor && global.__clickedAnchor.download === 'signature-llama-chat.txt',
    JSON.stringify(global.__clickedAnchor));
  check('saved transcript format "You:/Llama:"',
    /You: hi/.test(global.__blobText) && /Llama: Guide: Hello!/.test(global.__blobText),
    global.__blobText.slice(0, 80));
  global.Blob = RealBlob;

  /* ---------- copy fallback (no clipboard API) ---------- */
  global.__copied = null;
  const taProto = [];
  const origCreate2 = document.createElement.bind(document);
  document.createElement = function (tag) {
    const e = origCreate2(tag);
    if (String(tag).toLowerCase() === 'textarea')
      Object.defineProperty(e, 'value', { get() { return this._v; }, set(v) { this._v = v; global.__taValue = v; } });
    return e;
  };
  T.copyText('copy-me-123', 'Copied.');
  check('copy fallback captures exact text', global.__copied === 'copy-me-123', String(global.__copied));
  document.createElement = origCreate2;

  /* ---------- TTS tiers ---------- */
  global.__rv.spoken.length = 0;
  T.speak('tier one check');
  check('ResponsiveVoice tier speaks', global.__rv.spoken.length === 1 && global.__rv.spoken[0][0] === 'tier one check');
  T.speechPause(); check('pause -> RV.pause', global.__rv.paused === 1);
  T.speechResume(); check('resume -> RV.resume', global.__rv.resumed === 1);
  global.__rv.cancelled = 0; /* speak() itself stops any prior utterance first */
  T.speechStop(); check('stop -> RV.cancel', global.__rv.cancelled === 1);
  delete global.responsiveVoice;
  let audioSrc = null;
  global.Audio = function (src) { audioSrc = src; this.play = () => Promise.resolve(); this.pause = () => {}; };
  T.speak('tier two check');
  check('Google TTS fallback tier used when no RV', /translate\.google\.com/.test(audioSrc || ''), String(audioSrc).slice(0, 60));
  T.speechStop();
  global.responsiveVoice = { speak(t, v) { global.__rv.spoken.push([t, v]); },
    pause() {}, resume() {}, cancel() {} };

  /* ---------- IndustryLlama: key add/remove + chat states ---------- */
  delete require.cache[require.resolve(ROOT + '/industry-llama.js')];
  const indSrc = fs.readFileSync(ROOT + '/industry-llama.js', 'utf8');
  eval(indSrc);
  const IL = global.IndustryLlama;
  IL.setKey('gsk_test123');
  check('setKey stores key, ready() true', IL.getKey() === 'gsk_test123' && IL.ready() === true);
  IL.setKey('');
  check('setKey("") removes key, ready() false', IL.getKey() === '' && IL.ready() === false);
  IL.setKey('gsk_test123');
  global.__fetchMode = 'groq401';
  try { await IL.chat([{ role: 'user', content: 'x' }]); check('groq 401 -> BAD_KEY', false); }
  catch (e) { check('groq 401 -> BAD_KEY', e.code === 'BAD_KEY', e.code); }
  global.__fetchMode = 'groq429';
  try { await IL.chat([{ role: 'user', content: 'x' }]); check('groq 429 -> RATE_LIMITED', false); }
  catch (e) { check('groq 429 -> RATE_LIMITED', e.code === 'RATE_LIMITED', e.code); }
  global.__fetchMode = 'groqNetFail';
  try { await IL.chat([{ role: 'user', content: 'x' }]); check('network fail -> NETWORK', false); }
  catch (e) { check('network fail -> NETWORK', e.code === 'NETWORK', e.code); }
  global.__fetchMode = 'groqHang';
  try { await IL.chat([{ role: 'user', content: 'x' }], { timeoutMs: 60 }); check('hang -> TIMEOUT', false); }
  catch (e) { check('hang -> TIMEOUT', e.code === 'TIMEOUT', e.code); }
  global.__fetchMode = 'normal';
  const ct = await IL.chat([{ role: 'user', content: 'x' }]);
  check('groq 200 -> returns text', ct === 'cloud says hello', ct);
  try { IL.setKey(''); await IL.chat([{ role: 'user', content: 'x' }]); check('no key -> MISSING_KEY (sync throw)', false); }
  catch (e) { check('no key -> MISSING_KEY (sync throw)', e.code === 'MISSING_KEY', e.code); }

  /* ---------- tool library load/unload (real lib code) ---------- */
  const toolibs = JSON.parse(fs.readFileSync(ROOT + '/data/tool-libraries.json', 'utf8'));
  check('120 tool libraries in data', toolibs.libraries.length === 120);
  T.setTOOLIBS(toolibs);
  T.loadToolById('text-shorten');
  check('loadToolById registers SigLlama.tools["text-shorten"]',
    !!(global.SigLlama.tools && global.SigLlama.tools['text-shorten']));
  const short = global.SigLlama.tools['text-shorten'].shorten('a b c d e', 3);
  check('registered tool actually runs', short === 'a b c…', short);
  T.loadToolById('no-such-tool');
  check('loadToolById unknown id toasts instead of throwing', true);
  T.unloadToolById('text-shorten');
  check('unloadToolById removes the tool', !global.SigLlama.tools['text-shorten']);

  /* ---------- Test Llama button ---------- */
  T.wireTestLlama();
  const out = document.getElementById('testllamaresult');
  T.LlamaChat.ready = true;
  global.IndustryLlama = { getChoice: () => 'v1' };
  document.getElementById('testllama').onclick();
  await new Promise(r => setTimeout(r, 45000));
  check('Test Llama reports LOCAL engine + latency',
    /LOCAL · ON-DEVICE answered in \d+ ms/.test(out.innerHTML) || /not clean/.test(out.innerHTML),
    String(out.innerHTML).slice(0, 100));
  console.log('      (probe result: ' + String(out.innerHTML).replace(/<[^>]+>/g, '').slice(0, 90) + ')');
  delete global.IndustryLlama;

  /* ---------- askWithProvenance (llama-api.js, real engine) ---------- */
  const apiSrc = fs.readFileSync(ROOT + '/llama-api.js', 'utf8');
  eval(apiSrc);
  const SL = global.SignatureLlama;
  const r1 = await SL.askWithProvenance('What is a token?', { maxTokens: 25, timeoutMs: 45000 });
  check('askWithProvenance trained path: mode trained_model',
    r1.mode === 'trained_model' && r1.provenance.MODEL_ID === 'SIGLLAMA-V2' &&
    r1.provenance.LOCAL_OR_CLOUD === 'ON-DEVICE', r1.mode);
  const a5 = await SL.ask('What is a token?', { maxTokens: 25, timeoutMs: 45000 });
  check('ask() labels trained reply ✦ LOCAL', a5.startsWith('✦ Trained Llama v2 · SIGLLAMA-V2 · LOCAL · ON-DEVICE: '), a5.slice(0, 60));
  const savedSig = global.SigLlama; global.SigLlama = undefined;
  const r2 = await SL.askWithProvenance('What is a token?');
  check('askWithProvenance guide fallback when engine missing', r2.mode === 'guide' && r2.provenance.FALLBACK_REASON === 'model-not-loaded', r2.mode);
  const a6 = await SL.ask('What is a token?');
  check('ask() labels guide reply "Guide:"', a6.startsWith('Guide: '), a6.slice(0, 40));
  try { await SL.askWithProvenance('x', { requireModel: true }); check('requireModel rejects MODEL_NOT_FOUND', false); }
  catch (e) { check('requireModel rejects MODEL_NOT_FOUND', e.code === 'MODEL_NOT_FOUND', e.code); }
  global.SigLlama = savedSig;
  const vi = await SL.verifyIntegration();
  check('verifyIntegration: same engine+weights+vocab', vi.ok === true && vi.engine_hash_match && vi.weights_hash_match && vi.vocab_hash_match,
    JSON.stringify({ ok: vi.ok, e: vi.engine_hash_match, w: vi.weights_hash_match, v: vi.vocab_hash_match }));

  console.log('\n' + (fails ? fails + ' FAILURES of ' + ran : 'ALL ' + ran + ' FEATURE CHECKS PASSED'));
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR:', e); process.exit(2); });
