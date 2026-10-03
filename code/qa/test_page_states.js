/* Page-level unit tests: classifyError, failureText, fmtMB, updateCtxCount, TTS wiring.
   Loads the page's main inline <script> block with a minimal DOM stub. */
'use strict';
const fs = require('fs');
const html = fs.readFileSync('/home/hatch/workspace/signature-llama/index.html', 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const main = blocks.find(b => b.includes('function classifyError'));
if (!main) { console.log('FAIL: main script block not found'); process.exit(1); }

// ---- minimal DOM stub ----
function mkEl() {
  return {
    children: [], style: {}, dataset: {}, classList: { add() {}, remove() {} },
    textContent: '', innerHTML: '', value: '', disabled: false,
    appendChild(c) { this.children.push(c); return c; },
    remove() {}, querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, setAttribute() {}, getAttribute() { return null; },
    scrollTop: 0, scrollHeight: 0, onclick: null, onkeydown: null, select() {},
    className: '', id: '', title: '', placeholder: '',
  };
}
const els = {};
global.document = {
  getElementById(id) { return els[id] || (els[id] = mkEl()); },
  createElement() { return mkEl(); },
  querySelectorAll() { return []; },
  addEventListener(ev, fn) { if (ev === 'DOMContentLoaded') process.nextTick(fn); },
  documentElement: { dataset: {} }, head: mkEl(), body: mkEl(),
};
global.window = global;
Object.defineProperty(global, 'navigator', { value: { onLine: true }, configurable: true });
global.localStorage = { _s: {}, getItem(k) { return this._s[k] || null; }, setItem(k, v) { this._s[k] = v; }, removeItem(k) { delete this._s[k]; } };
global.location = { search: '' };
global.fetch = () => Promise.reject(new Error('no network in test'));
global.setTimeout = setTimeout; global.clearTimeout = clearTimeout;

// The main block is wrapped in an IIFE: inject an exporter just before its end.
const exportHook = ';global.__t={classifyError:typeof classifyError!=="undefined"?classifyError:undefined,' +
  'failureText:failureText,fmtMB:fmtMB,fallbackReasonFor:fallbackReasonFor,updateCtxCount:updateCtxCount,' +
  'wireTTSButtons:wireTTSButtons,wireChatBox:wireChatBox,speechStop:speechStop,speechPause:speechPause,' +
  'speechResume:speechResume,LlamaChat:LlamaChat};';
const hookable = main.replace(/\}\)\(\);\s*$/, exportHook + '\n})();');
eval(hookable);
const { classifyError, failureText, fmtMB, fallbackReasonFor, updateCtxCount,
        wireTTSButtons, wireChatBox, speechStop, speechPause, speechResume, LlamaChat } = global.__t;

let fails = 0;
function check(name, cond, extra) {
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra && !cond ? ' — ' + extra : ''));
  if (!cond) fails++;
}

// classifyError coverage for the new verify path
check('sha mismatch -> MODEL_CORRUPT',
  classifyError(new Error('MODEL_CORRUPT: sha256 mismatch'), 'generate') === 'MODEL_CORRUPT');
check('OOM -> OUT_OF_MEMORY',
  classifyError(new Error('out of memory'), 'generate') === 'OUT_OF_MEMORY');
check('404 vocab -> MODEL_NOT_FOUND',
  classifyError(new Error('vocab2.json not found at x'), 'generate') === 'MODEL_NOT_FOUND');
check('bad magic -> MODEL_CORRUPT',
  classifyError(new Error('bad magic'), 'generate') === 'MODEL_CORRUPT');
check('script load fail -> ENGINE_LOAD_FAILED',
  classifyError(new Error('sigllama.js fetch failed'), 'script') === 'ENGINE_LOAD_FAILED');
check('failureText names the code',
  failureText('MODEL_CORRUPT').startsWith('MODEL_CORRUPT — '));
check('fallbackReasonFor(MODEL_CORRUPT)', fallbackReasonFor('MODEL_CORRUPT') === 'corrupted-weights');
check('fmtMB', fmtMB(4137675) === '3.9');

// updateCtxCount
LlamaChat.history = ['Human: ' + 'word '.repeat(50) + '\nLlama:'];
updateCtxCount();
check('ctxcount shows 52 words', document.getElementById('ctxcount').textContent === '52',
  'got ' + document.getElementById('ctxcount').textContent);
LlamaChat.history = ['Human: ' + 'word '.repeat(120) + '\nLlama:'];
updateCtxCount();
check('ctxcount caps at 96', document.getElementById('ctxcount').textContent === '96',
  'got ' + document.getElementById('ctxcount').textContent);
check('ctxfull shown when over', document.getElementById('ctxfull').style.display === 'inline');
LlamaChat.history = ['Human: hi\nLlama:'];
updateCtxCount();
check('ctxfull hidden when under', document.getElementById('ctxfull').style.display === 'none');

// TTS controls exist and wire without throwing
wireTTSButtons();
check('tts buttons wired', ['ttsplay', 'ttspause', 'ttsresume', 'ttsstop'].every(id => {
  const b = document.getElementById(id); return b && typeof b.onclick === 'function';
}));
check('speechStop/Pause/Resume are functions',
  typeof speechStop === 'function' && typeof speechPause === 'function' && typeof speechResume === 'function');

// wireChatBox: Enter key triggers go; go() calls LlamaChat.send
wireChatBox();
const inp = document.getElementById('llamainput');
check('Enter key wired on input', typeof inp.onkeydown === 'function');

console.log(fails ? fails + ' FAILURES' : 'ALL PAGE-LEVEL TESTS PASSED');
process.exit(fails ? 1 : 0);
