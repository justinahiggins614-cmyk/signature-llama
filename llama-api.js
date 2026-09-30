/* ============================================================
 * SignatureLlama.ask(question) — the on-demand Signature Llama API.
 * Signature Llama: The Fully Cyber Utilizable AI
 * Independent model by Justin Addam Higgins. Not affiliated with Meta.
 *
 * Usage — paste into any web page, no keys, no setup:
 *
 *   <script src="https://justinahiggins614-cmyk.github.io/signature-llama/llama-api.js"></script>
 *   <script>
 *     SignatureLlama.ask("What is a token?").then(function(answer){
 *       console.log(answer);
 *     });
 *   </script>
 *
 * SignatureLlama.ask(question) returns a Promise of a string.
 * Before the trained model publishes it answers from the on-site
 * knowledge base; once the live model is present on the page it
 * answers with the trained Llama automatically.
 * License: free for any website, app, or project. No API key, no fee.
 * ============================================================ */
(function () {
  'use strict';
  var SITE = 'https://justinahiggins614-cmyk.github.io/signature-llama/';
  var STOP = { the:1, a:1, an:1, of:1, to:1, is:1, it:1, in:1, and:1,
    what:1, how:1, does:1, do:1, for:1, with:1, on:1, by:1, i:1, you:1,
    me:1, my:1, this:1, that:1, tell:1, about:1, please:1, can:1, explain:1 };
  var kbCache = null;

  function words(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/).filter(function (w) { return w && !STOP[w]; });
  }
  function fetchKB() {
    if (kbCache) return Promise.resolve(kbCache);
    return fetch(SITE + 'data/explainer-kb.json').then(function (r) { return r.json(); })
      .then(function (j) { kbCache = j.entries || j; return kbCache; })
      .catch(function () { kbCache = []; return kbCache; });
  }
  function answerFromKB(question, kb) {
    var ws = words(question), best = null, bestScore = 0;
    kb.forEach(function (e) {
      var hay = (e.title + ' ' + (e.kw || []).join(' ') + ' ' + e.text).toLowerCase();
      var score = 0;
      ws.forEach(function (w) {
        if (hay.indexOf(w) >= 0) score += ((e.kw || []).indexOf(w) >= 0 ? 3 : 1);
      });
      if (score > bestScore) { bestScore = score; best = e; }
    });
    if (best && bestScore >= 2) return best.title + ': ' + best.text;
    return 'I can explain Signature Llama itself, or any of its files, ' +
      'libraries, and tools — try asking what sigllama.js does, what the ' +
      'quantizer is for, or how to use the model in your own page. ' +
      'See ' + SITE + '#guide for everything the on-site guide knows.';
  }
  window.SignatureLlama = window.SignatureLlama || {};
  window.SignatureLlama.version = '1.0';
  window.SignatureLlama.site = SITE;
  /* ask(question) -> Promise<string> */
  window.SignatureLlama.ask = function (question) {
    try {
      if (window.SigLlama && SigLlama.loaded && SigLlama.loaded()) {
        return SigLlama.generate(
          'You are the Signature Llama on-site guide. Explain clearly and briefly: ' + question,
          { maxTokens: 140, temperature: 0.7, topK: 40, stopAtEos: true });
      }
    } catch (e) { /* fall through to the knowledge base */ }
    return fetchKB().then(function (kb) { return answerFromKB(question, kb); });
  };
})();
