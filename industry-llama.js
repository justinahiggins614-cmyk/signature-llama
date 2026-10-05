/* ============================================================
 * IndustryLlama — the "Llama · Industry Standard" engine client.
 * Signature Llama: The Fully Cyber Utilizable AI
 * Independent project by Justin Addam Higgins. Not affiliated with Meta.
 *
 * What it is: a tiny client for a REAL full-scale Llama served by a
 * cloud inference provider (Groq) over its OpenAI-compatible API.
 * The user pastes their own FREE API key once; the key is kept in the
 * browser's localStorage and is only ever sent to api.groq.com.
 * No key ever touches our servers (there are none — static hosting).
 *
 * Any Signature site on the same origin
 * (justinahiggins614-cmyk.github.io) can include this file and call:
 *
 *   IndustryLlama.ready()            // true when a key is saved
 *   IndustryLlama.chat(messages)    // messages: [{role, content}...]
 *                                    // -> Promise<string> (assistant text)
 *
 * chat() throws Errors with a .code: MISSING_KEY | BAD_KEY |
 * RATE_LIMITED | NETWORK | BAD_RESPONSE. Show e.message to the user.
 * License: free for any website, app, or project.
 * ============================================================ */
(function () {
  'use strict';
  /* Profile-aware storage: public (signed-out) behaves exactly as before;
     signed-in profiles get their own namespaced keys. Guard keeps this working
     even when signin.js is not loaded. */
  var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage;
  var ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions';
  var KEY_STORE = 'sigllama_industry_key';
  var MODEL_STORE = 'sigllama_industry_model';
  var CHOICE_STORE = 'sigllama_model_choice'; /* 'v1' | 'industry' */

  var MODELS = [
    { id: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B', note: 'the workhorse — fast, strong, 128k context' },
    { id: 'meta-llama/llama-4-maverick-17b-128e-instruct', label: 'Llama 4 Maverick', note: 'newest generation, 128k context' },
    { id: 'meta-llama/llama-4-scout-17b-16e-instruct', label: 'Llama 4 Scout', note: 'long-context specialist' }
  ];
  var DEFAULT_MODEL = MODELS[0].id;

  function lsGet(k) { try { return PS.get(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { PS.set(k, v); } catch (e) {} }
  function lsDel(k) { try { PS.remove(k); } catch (e) {} }

  function err(code, message) { var e = new Error(message); e.code = code; return e; }

  var api = {
    models: MODELS,
    endpoint: ENDPOINT,
    getKey: function () { return lsGet(KEY_STORE) || ''; },
    setKey: function (k) {
      k = String(k || '').trim();
      if (!k) { lsDel(KEY_STORE); return; }
      lsSet(KEY_STORE, k);
    },
    getModel: function () {
      var m = lsGet(MODEL_STORE) || DEFAULT_MODEL;
      for (var i = 0; i < MODELS.length; i++) if (MODELS[i].id === m) return m;
      return DEFAULT_MODEL;
    },
    setModel: function (id) { lsSet(MODEL_STORE, id); },
    modelLabel: function () {
      var m = api.getModel();
      for (var i = 0; i < MODELS.length; i++) if (MODELS[i].id === m) return MODELS[i].label;
      return m;
    },
    getChoice: function () { return lsGet(CHOICE_STORE) || 'v1'; },
    setChoice: function (c) { lsSet(CHOICE_STORE, c === 'industry' ? 'industry' : 'v1'); },
    ready: function () { return !!api.getKey(); },
    /* messages: [{role:'system'|'user'|'assistant', content}] — opts: {maxTokens} */
    chat: function (messages, opts) {
      opts = opts || {};
      var key = api.getKey();
      if (!key) throw err('MISSING_KEY', 'No API key saved yet — paste your free key to use Industry Standard mode.');
      var body = {
        model: api.getModel(),
        messages: messages,
        max_tokens: opts.maxTokens || 600,
        temperature: opts.temperature === undefined ? 0.7 : opts.temperature
      };
      var TIMEOUT_MS = opts.timeoutMs || 60000; /* a cloud call never hangs forever */
      var req = fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key },
        body: JSON.stringify(body)
      }).then(function (r) {
        if (r.status === 401) throw err('BAD_KEY', 'That key was rejected (401). Check it at console.groq.com/keys and paste it again.');
        if (r.status === 429) throw err('RATE_LIMITED', 'Rate limit hit (429) — the free tier allows a breather, then try again.');
        if (!r.ok) throw err('BAD_RESPONSE', 'The cloud returned HTTP ' + r.status + ' — try again, or switch back to v1.');
        return r.json();
      }).then(function (j) {
        var t = j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
        t = String(t == null ? '' : t).trim();
        if (!t) throw err('BAD_RESPONSE', 'The cloud answered empty — try again, or switch back to v1.');
        return t;
      }).catch(function (e) {
        if (e && e.code) throw e;
        throw err('NETWORK', 'Could not reach the cloud (' + String((e && e.message) || e).slice(0, 120) + '). Check your connection — v1 still works offline.');
      });
      return Promise.race([
        req,
        new Promise(function (_, rej) {
          setTimeout(function () {
            rej(err('TIMEOUT', 'The cloud did not answer within ' + Math.round(TIMEOUT_MS / 1000) + ' seconds — try again, or switch back to v1.'));
          }, TIMEOUT_MS);
        })
      ]);
    }
  };
  window.IndustryLlama = api;
})();
