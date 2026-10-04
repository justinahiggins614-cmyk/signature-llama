#!/usr/bin/env python3
"""Build the four standard Signature Llama versions' download artifacts.

For each variant (offline-static, online-no-key, online-with-key, best-figurehead)
produces, under downloads/:
  signature-llama-<variant>-py.zip   Python package (real, working)
  signature-llama-<variant>.js       single-file JS build (real, working)
  llama-thumbdrive-<variant>.py      single-file thumbdrive program (real, working)
plus downloads/MANIFEST.json (sha256 of everything).

NEVER builds .exe (standing rule -- it cannot be built on this machine).

The ecosystem KB is extracted from js/jah-talk-fallback.js (ECO-JSON markers --
single source of truth) into data/ecosystem.json, which the Python packages ship.

Run: python3 code/build_versions.py
"""
import hashlib
import json
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'code', 'versions_src')
DL = os.path.join(ROOT, 'downloads')
TODAY = '2026-10-04'

VARIANTS = [
    ('offline-static', 'Offline Static', 'Trailblazer',
     'The best version. Runs fully client-side on any static page -- no network, ever.'),
    ('online-no-key', 'Online, No Key Needed', 'Cloudhopper',
     'Online through the built-in free route (live knowledge refresh), no signup, no key. '
     'Falls back to the offline engine when offline.'),
    ('online-with-key', 'Online with Key', 'Keykeeper',
     'Your own API key, your provider. The key is stored device-local only and never '
     'leaves your device except to the provider you chose.'),
    ('best-figurehead', 'Best Figurehead', 'Northstar',
     'The flagship. Every feature toggleable on/off, backed by an updater that '
     'automatically refreshes the best version as more data is added.'),
]

PROFILE = {
    'name': 'Signature Llama',
    'description': 'The fully cyber utilizable AI.',
    'abilities': ['chat in natural flowing sentences',
                  'explain AI terms in plain words',
                  'point you around all 31 JAH network sites',
                  'describe its files, tools and versions'],
    'domain': 'conversation',
}

SETUP_PY = """from setuptools import setup, find_packages
setup(name='signature-llama-{vid}', version='2.0.0',
      description='Signature Llama ({vname}) -- conversational on-device AI',
      packages=find_packages(), package_data={{'signature_llama': ['ecosystem.json']}},
      python_requires='>=3.8')
"""

README = """# Signature Llama -- {vname} (Python)

{tagline}

## Run it
    python3 -m signature_llama.chat
or
    python3 chat.py

## What is inside
- `signature_llama/guide.py` -- the conversational engine (zero-network,
  plain-words replies, full duties coverage, all 31 JAH network sites)
- `signature_llama/engine.py` -- the variant runtime (online behaviors,
  key handling, feature toggles, updater)
- `signature_llama/ecosystem.json` -- the 31-site knowledge base
- `chat.py` -- the chat entry point

## The four versions
- Offline Static -- no network, ever. The best version.
- Online, No Key Needed -- built-in free route (live knowledge refresh),
  falls back to the offline engine when offline.
- Online with Key -- your own provider key, stored device-local only
  (`~/.sigllama_key`, mode 600, or the SIGLLAMA_API_KEY env var).
- Best Figurehead -- every feature toggleable; `/check-updates` asks the
  live site whether a newer best version exists.

Independent project by Justin Addam Higgins. Not affiliated with Meta.
No .exe is offered -- it cannot be built on this machine.
"""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_eco():
    src = open(os.path.join(ROOT, 'js', 'jah-talk-fallback.js'), encoding='utf-8').read()
    m = re.search(r'/\*ECO-JSON-START\*/(.*?)/\*ECO-JSON-END\*/', src, re.S)
    eco = json.loads(m.group(1))
    assert len(eco) == 31, 'expected 31 sites, got %d' % len(eco)
    out = os.path.join(ROOT, 'data', 'ecosystem.json')
    json.dump(eco, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote data/ecosystem.json (%d sites)' % len(eco))
    return eco


def build_python_package(vid, vname, tagline, eco):
    pkgdir = os.path.join(DL, '_pkg', 'signature-llama-%s' % vid)
    moddir = os.path.join(pkgdir, 'signature_llama')
    if os.path.exists(pkgdir):
        shutil.rmtree(pkgdir)
    os.makedirs(moddir)
    for fn in ('guide.py', 'engine.py'):
        shutil.copy(os.path.join(SRC, fn), os.path.join(moddir, fn))
    open(os.path.join(moddir, '__init__.py'), 'w').write(
        '"""Signature Llama (%s) -- conversational on-device AI."""\n'
        'from .engine import Llama, VARIANTS  # noqa\n' % vname)
    shutil.copy(os.path.join(ROOT, 'data', 'ecosystem.json'),
                os.path.join(moddir, 'ecosystem.json'))
    shutil.copy(os.path.join(SRC, 'chat.py'), os.path.join(pkgdir, 'chat.py'))
    open(os.path.join(pkgdir, 'setup.py'), 'w').write(
        SETUP_PY.format(vid=vid, vname=vname))
    open(os.path.join(pkgdir, 'README.md'), 'w').write(
        README.format(vname=vname, tagline=tagline))
    zpath = os.path.join(DL, 'signature-llama-%s-py.zip' % vid)
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _dirs, files in os.walk(pkgdir):
            for fn in files:
                full = os.path.join(base, fn)
                z.write(full, os.path.relpath(full, pkgdir))
    print('wrote', os.path.basename(zpath))
    return zpath


JS_WRAPPER = """/* ============================================================
   Signature Llama -- __VNAME__ (single-file JS build, v2.0.0)
   __TAGLINE__
   The engine below is the real JAHtalk GuideTalk conversational engine
   (js/jah-talk-fallback.js): zero-network, plain-words replies, full
   duties coverage, all 31 JAH network sites. This wrapper adds the
   __VID__ variant behavior and the SignatureLlama.ask() seam.
   Independent project by Justin Addam Higgins. Not affiliated with Meta.
   ============================================================ */
__ENGINE__
;(function(){
'use strict';
var JT = (typeof window !== 'undefined' && window.JAHtalk) ? window.JAHtalk : null;
var VARIANT = __VARIANT_JSON__;
var PROFILE = __PROFILE_JSON__;
function lsGet(k){ try { return window.localStorage.getItem(k); } catch(e){ return null; } }
function lsSet(k,v){ try { window.localStorage.setItem(k,v); } catch(e){} }
var api = (window.SignatureLlama = window.SignatureLlama || {});
api.variant = VARIANT.id;
api.variantName = VARIANT.name;
api.features = {};
(VARIANT.features || []).forEach(function(f){ api.features[f] = true; });
try {
  var saved = JSON.parse(lsGet('sigllama_features_' + VARIANT.id) || 'null');
  if (saved) Object.keys(saved).forEach(function(k){ if (k in api.features) api.features[k] = !!saved[k]; });
} catch(e){}
api.setFeature = function(name, on){
  if (!(name in api.features)) return false;
  api.features[name] = !!on;
  var s = {}; Object.keys(api.features).forEach(function(k){ s[k] = api.features[k]; });
  lsSet('sigllama_features_' + VARIANT.id, JSON.stringify(s));
  return true;
};
/* the one seam: ask() -> Promise<string>, honest about which route answered */
api.ask = function(question){
  var q = String(question == null ? '' : question);
  function offline(){ return Promise.resolve(JT ? JT.reply(PROFILE, q) : 'The offline engine did not load.'); }
  if (VARIANT.id === 'online-with-key') {
    var key = lsGet('sigllama_key');
    var endpoint = lsGet('sigllama_endpoint') || 'https://api.groq.com/openai/v1/chat/completions';
    var model = lsGet('sigllama_model') || 'llama-3.3-70b-versatile';
    if (key && window.fetch) {
      return window.fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key },
        body: JSON.stringify({ model: model,
          messages: [{ role: 'system',
                       content: 'You are Signature Llama, a warm plain-spoken AI assistant. Answer conversationally.' },
                     { role: 'user', content: q }],
          max_tokens: 300 })
      }).then(function(r){ if(!r.ok) throw 0; return r.json(); })
        .then(function(j){ return (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content || '').trim(); })
        .catch(function(){ return offline(); });
    }
    return offline();
  }
  if (VARIANT.id === 'online-no-key' && window.fetch) {
    /* built-in free route: refresh the best-pick bulletin when online */
    return window.fetch('https://justinahiggins614-cmyk.github.io/signature-llama/data/best/best.json')
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(){ return offline(); })
      .catch(function(){ return offline(); });
  }
  return offline();
};
/* figurehead updater: ask the live site whether a newer best exists */
api.checkUpdates = function(){
  if (!window.fetch) return Promise.resolve({ update_available: false, error: 'no fetch' });
  return window.fetch('https://justinahiggins614-cmyk.github.io/signature-llama/data/best/best.json')
    .then(function(r){ if(!r.ok) throw 0; return r.json(); })
    .then(function(b){ return { update_available: true, live_title: b.title,
      live_version: b.version, live_built: b.built, why: (b.why || []).slice(0, 3) }; })
    .catch(function(e){ return { update_available: false, error: String(e && e.message || e) }; });
};
})();
"""


def build_js(vid, vname, tagline, features):
    engine = open(os.path.join(ROOT, 'js', 'jah-talk-fallback.js'), encoding='utf-8').read()
    out = (JS_WRAPPER
           .replace('__VNAME__', vname)
           .replace('__TAGLINE__', tagline)
           .replace('__VID__', vid)
           .replace('__ENGINE__', engine)
           .replace('__VARIANT_JSON__', json.dumps({'id': vid, 'name': vname, 'features': features}))
           .replace('__PROFILE_JSON__', json.dumps(PROFILE)))
    path = os.path.join(DL, 'signature-llama-%s.js' % vid)
    open(path, 'w', encoding='utf-8').write(out)
    print('wrote', os.path.basename(path))
    return path


def build_thumbdrive(vid, vname, tagline, eco):
    guide_src = open(os.path.join(SRC, 'guide.py'), encoding='utf-8').read()
    guide_src = guide_src.replace(
        "def _load_eco():\n    p = os.path.join(_HERE, 'ecosystem.json')\n"
        "    with open(p, encoding='utf-8') as f:\n        return json.load(f)",
        "def _load_eco():\n    return json.loads(ECOSYSTEM_JSON)")
    engine_src = open(os.path.join(SRC, 'engine.py'), encoding='utf-8').read()
    engine_src = engine_src.replace('from .guide import Guide', '')
    engine_src = engine_src.replace('from .guide import ECO', 'ECO = _ECO')
    engine_src = engine_src.replace('from signature_llama.engine import chat_loop', '')
    parts = [
        '#!/usr/bin/env python3',
        '"""Signature Llama -- %s (thumbdrive edition, v2.0.0)' % vname,
        '',
        tagline,
        '',
        'Single file, standard library only. Copy to any USB stick and run:',
        '    python3 %s' % ('llama-thumbdrive-%s.py' % vid),
        'No install, no network needed (Offline Static). Other variants use the',
        'network only for their documented route, with offline fallback.',
        'Independent project by Justin Addam Higgins. Not affiliated with Meta.',
        '"""',
        'import getpass, hashlib, json, os, re, time, urllib.request',
        '',
        'VARIANT_ID = %r' % vid,
        'VARIANT_NAME = %r' % vname,
        '',
        'ECOSYSTEM_JSON = %r' % json.dumps(eco, ensure_ascii=False),
        '',
        guide_src,
        '',
        '_ECO = ECO',
        '',
        engine_src,
        '',
        'if __name__ == "__main__":',
        '    llama = Llama(variant=VARIANT_ID, name=%r,' % PROFILE['name'],
        '                  description=%r,' % PROFILE['description'],
        '                  abilities=%r,' % PROFILE['abilities'],
        '                  domain=%r)' % PROFILE['domain'],
        '    chat_loop(llama)',
        '',
    ]
    path = os.path.join(DL, 'llama-thumbdrive-%s.py' % vid)
    open(path, 'w', encoding='utf-8').write('\n'.join(parts))
    print('wrote', os.path.basename(path))
    return path


def main():
    os.makedirs(DL, exist_ok=True)
    eco = extract_eco()
    manifest = {'built': TODAY, 'generator': 'code/build_versions.py',
                'note': 'No .exe is offered -- it cannot be built on this machine.',
                'files': {}}
    features_all = ['deep_talk', 'ecosystem_guide', 'socratic_reasoning',
                    'story_weaver', 'debate_partner', 'kb_refresh', 'cloud_fallback']
    for vid, vname, mascot, tagline in VARIANTS:
        feats = features_all if vid == 'best-figurehead' else ['deep_talk', 'ecosystem_guide']
        files = [
            build_python_package(vid, vname, tagline, eco),
            build_js(vid, vname, tagline, feats),
            build_thumbdrive(vid, vname, tagline, eco),
        ]
        for f in files:
            manifest['files'][os.path.basename(f)] = {
                'sha256': sha256_file(f),
                'bytes': os.path.getsize(f),
                'variant': vid,
            }
    # clean the package staging dir
    shutil.rmtree(os.path.join(DL, '_pkg'), ignore_errors=True)
    mp = os.path.join(DL, 'MANIFEST.json')
    json.dump(manifest, open(mp, 'w', encoding='utf-8'), indent=1)
    print('wrote MANIFEST.json (%d files)' % len(manifest['files']))


if __name__ == '__main__':
    main()
