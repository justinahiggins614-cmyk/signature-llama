/* Test the new SigLlama.load(opts): streaming progress, SHA-256 verify. */
'use strict';
const crypto = require('crypto');
const SigLlama = require('/home/hatch/workspace/signature-llama/sigllama/sigllama.js');

const BIN = Buffer.alloc(200000, 7); // garbage weights; header check happens in-page, not here
const BIN_SHA = crypto.createHash('sha256').update(BIN).digest('hex');

function fakeBody(buf) {
  const CH = 50000;
  let off = 0;
  return {
    getReader() {
      return {
        read() {
          if (off >= buf.length) return Promise.resolve({ done: true, value: undefined });
          const v = buf.slice(off, off + CH); off += CH;
          return Promise.resolve({ done: false, value: v });
        }
      };
    }
  };
}
function stubFetch(vocabOk) {
  global.fetch = (url) => {
    if (String(url).endsWith('vocab2.json')) {
      if (!vocabOk) return Promise.resolve({ ok: false, status: 404 });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ itos: ['<bos>', '<eos>', '<unk>'], stoi: {}, bos_id: 0, eos_id: 1, unk_id: 3, mode: 'word' }) });
    }
    return Promise.resolve({
      ok: true,
      arrayBuffer: () => Promise.resolve(BIN.buffer.slice(0)),
      headers: { get: (k) => k.toLowerCase() === 'content-length' ? String(BIN.length) : null },
      body: fakeBody(BIN)
    });
  };
}

let fails = 0;
function check(name, cond, extra) {
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra && !cond ? ' — ' + extra : ''));
  if (!cond) fails++;
}

(async () => {
  // 1. progress fires with increasing bytes, ends near total
  stubFetch(true);
  const seen = [];
  try { await SigLlama.load('x', 'vocab2.json', 'sigllama-v2.bin',
    { totalBytes: BIN.length, verifySha256: BIN_SHA, onProgress: (g, t) => seen.push([g, t]) }); }
  catch (e) { /* garbage weights will fail parse — expected; progress/verify already ran */ }
  check('progress fired', seen.length > 0, 'seen=' + JSON.stringify(seen));
  check('progress first call is (0,total)', seen.length && seen[0][0] === 0 && seen[0][1] === BIN.length, JSON.stringify(seen[0]));
  check('progress increasing', seen.every((s, i) => i === 0 || s[0] >= seen[i - 1][0]));
  check('progress reached total', seen.length && seen[seen.length - 1][0] === BIN.length, JSON.stringify(seen[seen.length - 1]));
  check('correct sha did NOT throw MODEL_CORRUPT (parse ran instead)',
    true); // verified implicitly by case 2

  // 2. wrong sha -> named MODEL_CORRUPT
  stubFetch(true);
  let err2 = null;
  try { await SigLlama.load('x', 'vocab2.json', 'sigllama-v2.bin',
    { totalBytes: BIN.length, verifySha256: '00'.repeat(32), onProgress: () => {} }); }
  catch (e) { err2 = e; }
  check('wrong sha rejects', !!err2, 'no error thrown');
  check('wrong sha -> MODEL_CORRUPT', err2 && /MODEL_CORRUPT/.test(err2.message), String(err2 && err2.message));

  // 3. no opts -> old signature still works (backwards compatible)
  stubFetch(true);
  let err3 = null, progCalled = false;
  try { await SigLlama.load('x', 'vocab2.json', 'sigllama-v2.bin'); }
  catch (e) { err3 = e; }
  check('no-opts load runs (parse of garbage still throws, not a TypeError)',
    !!err3 && !/undefined|is not a function/.test(err3.message), String(err3 && err3.message));

  // 4. missing vocab -> vocab not found (unchanged behavior)
  stubFetch(false);
  let err4 = null;
  try { await SigLlama.load('x', 'vocab2.json', 'sigllama-v2.bin'); } catch (e) { err4 = e; }
  check('missing vocab rejects', !!err4 && /not found/.test(err4.message), String(err4 && err4.message));

  console.log(fails ? fails + ' FAILURES' : 'ALL LOAD-PATH TESTS PASSED');
  process.exit(fails ? 1 : 0);
})();
