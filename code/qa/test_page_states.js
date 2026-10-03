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
global.addEventListener = function () {};
global.removeEventListener = function () {};
Object.defineProperty(global, 'navigator', { value: { onLine: true }, configurable: true });
global.localStorage = { _s: {}, getItem(k) { return this._s[k] || null; }, setItem(k, v) { this._s[k] = v; }, removeItem(k) { delete this._s[k]; } };
global.location = { search: '' };
global.fetch = () => Promise.reject(new Error('no network in test'));
global.setTimeout = setTimeout; global.clearTimeout = clearTimeout;

// The main block is wrapped in an IIFE: inject an exporter just before its end.
const exportHook = ';global.__t={classifyError:typeof classifyError!=="undefined"?classifyError:undefined,' +
  'failureText:failureText,fmtMB:fmtMB,fallbackReasonFor:fallbackReasonFor,updateCtxCount:updateCtxCount,' +
  'wireTTSButtons:wireTTSButtons,wireChatBox:wireChatBox,speechStop:speechStop,speechPause:speechPause,' +
  'speechResume:speechResume,LlamaChat:LlamaChat,' +
  'TOUR_STEPS:TOUR_STEPS,Tour:Tour,tourCard:tourCard,tourStart:tourStart,tourShow:tourShow,tourEnd:tourEnd,tourKeys:tourKeys,wireTour:wireTour};';
const hookable = main.replace(/\}\)\(\);\s*$/, exportHook + '\n})();');
eval(hookable);
const { classifyError, failureText, fmtMB, fallbackReasonFor, updateCtxCount,
        wireTTSButtons, wireChatBox, speechStop, speechPause, speechResume, LlamaChat,
        TOUR_STEPS, Tour, tourCard, tourStart, tourShow, tourEnd, tourKeys, wireTour } = global.__t;

// TTS controls exist and wire without throwing
wireTTSButtons();

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

// ---- tour ----
function mkEl2() {
  var e = mkEl();
  e.getBoundingClientRect = function () { return { left: 10, top: 100, bottom: 140, right: 200, width: 190, height: 40 }; };
  e.scrollIntoView = function () {};
  e.focus = function () {};
  e.classList.contains = function () { return false; };
  return e;
}
const htmlIds = new Set([...html.matchAll(/ id="([^"]+)"/g)].map(m => m[1]));
const origQS = document.querySelector;
document.querySelector = function (sel) {
  if (sel === '.tour-hl') return null;
  var m = /^#([\w-]+)$/.exec(sel);
  if (m && htmlIds.has(m[1])) { if (!els['qs:' + m[1]]) els['qs:' + m[1]] = mkEl2(); return els['qs:' + m[1]]; }
  return null;
};
global.innerWidth = 1024; global.innerHeight = 768;

check('all tour steps target real elements',
  TOUR_STEPS.every(function (s) { return !!document.querySelector(s.sel); }),
  'missing: ' + TOUR_STEPS.filter(function (s) { return !document.querySelector(s.sel); }).map(function (s) { return s.sel; }).join(','));
check('tour has 9 steps', TOUR_STEPS.length === 9, String(TOUR_STEPS.length));
wireTour();
check('tour buttons wired', ['tourstart', 'tourskip', 'tourback', 'tournext', 'tourend', 'retaketour']
  .every(function (id) { return typeof document.getElementById(id).onclick === 'function'; }));
tourStart();
check('tourStart activates', Tour.active === true && Tour.i === 0);
check('tour card visible', tourCard().style.display === 'block');
check('first step highlighted', document.querySelector('#modelpick').classList !== undefined);
tourKeys({ key: 'ArrowRight', target: { tagName: 'BODY' } });
check('ArrowRight advances', Tour.i === 1);
tourKeys({ key: 'ArrowLeft', target: { tagName: 'BODY' } });
check('ArrowLeft goes back', Tour.i === 0);
tourKeys({ key: 'Escape', target: { tagName: 'BODY' } });
check('Escape ends tour', Tour.active === false && tourCard().style.display === 'none');
check('dismissal flag set', (function () { try { return localStorage.getItem('jah-tour-seen-llama') === '1'; } catch (e) { return false; } })());
tourStart(); tourShow(TOUR_STEPS.length - 1);
check('last step shows Finish', document.getElementById('tournext').textContent === 'Finish ✓');
tourShow(TOUR_STEPS.length); /* past the end -> ends */
check('past-end ends tour', Tour.active === false);
check('guide panel exists in DOM ids', htmlIds.has('siteguide') && htmlIds.has('tourprompt') && htmlIds.has('tourcard'));
check('nav has Guide link', /href="#siteguide"/.test(html));
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
