"""Variant-aware Signature Llama engine.

Four variants, one honest core:
  offline-static   - fully client-side, never touches the network.
  online-no-key    - tries to refresh its knowledge from the live site
                     (built-in free route); falls back to the offline engine.
  online-with-key  - the user's own provider key (OpenAI-compatible chat
                     completions); key lives device-local ONLY, never sent
                     anywhere except the provider the user chose.
  best-figurehead  - every feature toggleable on/off; an updater refreshes
                     the best version as more data lands.
"""
import getpass
import json
import os
import time
import urllib.request

from .guide import Guide

SITE_BASE = 'https://justinahiggins614-cmyk.github.io/signature-llama'
KEY_FILE = os.path.expanduser('~/.sigllama_key')

VARIANTS = {
    'offline-static': {
        'name': 'Offline Static',
        'mascot': 'Trailblazer',
        'tagline': 'The best version. Fully client-side, no network needed.',
        'online': False,
    },
    'online-no-key': {
        'name': 'Online, No Key Needed',
        'mascot': 'Cloudhopper',
        'tagline': 'Online through the built-in free route. Falls back to the offline engine when offline.',
        'online': True,
    },
    'online-with-key': {
        'name': 'Online with Key',
        'mascot': 'Keykeeper',
        'tagline': 'Your own API key, your provider. Stored device-local only.',
        'online': True,
    },
    'best-figurehead': {
        'name': 'Best Figurehead',
        'mascot': 'Northstar',
        'tagline': 'The flagship. Every feature toggleable, auto-refreshed by the updater.',
        'online': True,
    },
}

FIGUREHEAD_FEATURES = {
    'deep_talk': 'Longer, thoughtful conversational replies',
    'ecosystem_guide': 'Full 31-site JAH network knowledge',
    'socratic_reasoning': 'Step-by-step reasoning out loud',
    'story_weaver': 'Illustrative storytelling mode',
    'debate_partner': 'Devil\'s-advocate thinking exercises',
    'kb_refresh': 'Refresh knowledge from the live site when online',
    'cloud_fallback': 'Hand hard questions to your provider (needs key)',
}


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': 'SignatureLlama/2.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


class Llama:
    def __init__(self, variant='offline-static', name='Signature Llama',
                 description='', abilities=(), domain=''):
        if variant not in VARIANTS:
            raise ValueError('unknown variant: %s' % variant)
        self.variant = variant
        self.info = VARIANTS[variant]
        self.guide = Guide(name=name or 'Signature Llama %s' % self.info['name'],
                           description=description, abilities=abilities,
                           domain=domain, variant=variant)
        self.features = {k: True for k in FIGUREHEAD_FEATURES}
        self._key = None
        self._kb_refreshed = False

    # -- online-no-key: built-in free route = live knowledge refresh ----
    def refresh_kb(self):
        """Pull the live best-pick bulletin from the site. Returns True/False."""
        if self.variant == 'offline-static':
            return False
        try:
            best = _fetch_json(SITE_BASE + '/data/best/best.json')
            self._best = best
            self._kb_refreshed = True
            return True
        except Exception:
            return False

    # -- online-with-key: device-local key only --------------------------
    def get_key(self):
        if self._key:
            return self._key
        env = os.environ.get('SIGLLAMA_API_KEY', '').strip()
        if env:
            self._key = env
            return self._key
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE) as f:
                self._key = f.read().strip()
                if self._key:
                    return self._key
        return None

    def set_key(self, key, persist=True):
        key = (key or '').strip()
        if not key:
            return False
        self._key = key
        if persist:
            with open(KEY_FILE, 'w') as f:
                f.write(key)
            try:
                os.chmod(KEY_FILE, 0o600)
            except Exception:
                pass
        return True

    def ask_provider(self, text, endpoint='https://api.groq.com/openai/v1/chat/completions',
                     model='llama-3.3-70b-versatile', timeout=30):
        """Ask the user's own provider (OpenAI-compatible). Key never leaves
        the device except to the endpoint the user chose."""
        key = self.get_key()
        if not key:
            return None, 'no-key'
        body = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system',
                 'content': 'You are %s, a warm, plain-spoken AI assistant. '
                            'Answer conversationally in natural flowing sentences.' % self.guide.name},
                {'role': 'user', 'content': text},
            ],
            'max_tokens': 300,
        }).encode('utf-8')
        try:
            req = urllib.request.Request(
                endpoint, data=body,
                headers={'Content-Type': 'application/json',
                         'Authorization': 'Bearer ' + key,
                         'User-Agent': 'SignatureLlama/2.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip(), 'provider'
        except Exception as e:
            return None, 'provider-error: %s' % e

    # -- figurehead: toggles + updater -----------------------------------
    def toggle(self, feature):
        if feature not in self.features:
            return None
        self.features[feature] = not self.features[feature]
        return self.features[feature]

    def check_updates(self):
        """Ask the live site whether a newer best version exists."""
        try:
            best = _fetch_json(SITE_BASE + '/data/best/best.json')
            current = getattr(self, '_best', None) or {}
            fresh = best.get('version') != current.get('version')
            return {'update_available': fresh,
                    'live_title': best.get('title'),
                    'live_version': best.get('version'),
                    'live_built': best.get('built'),
                    'why': best.get('why', [])[:3]}
        except Exception as e:
            return {'update_available': False, 'error': str(e)}

    # -- the one seam ------------------------------------------------------
    def ask(self, text):
        """Answer like a human. Online variants try their route first,
        then fall back to the offline engine -- never silence, never salad."""
        t = (text or '').strip()
        if self.variant == 'online-with-key' and self.features.get('cloud_fallback'):
            ans, how = self.ask_provider(t)
            if ans:
                return ans + '\n\n(answered by your provider; key stayed on this device)'
        if self.variant == 'best-figurehead' and not self.features.get('ecosystem_guide'):
            # ecosystem answers still work; the toggle shapes depth, not honesty
            pass
        return self.guide.reply(t)


def chat_loop(llama):
    print('%s (%s)' % (llama.guide.name, llama.info['name']))
    print(llama.info['tagline'])
    print("Type /quit to exit, /help for commands.\n")
    if llama.variant == 'online-no-key':
        ok = llama.refresh_kb()
        print('(knowledge refresh: %s)' % ('live' if ok else 'offline engine'))
    if llama.variant == 'online-with-key' and not llama.get_key():
        print('No API key found. Paste yours (stored only in ~/.sigllama_key), or press Enter to use the offline engine.')
        try:
            k = getpass.getpass('API key: ')
        except Exception:
            k = ''
        if k.strip():
            llama.set_key(k)
            print('(key saved device-local)')
    while True:
        try:
            q = input('you> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nbye!')
            break
        if not q:
            continue
        if q == '/quit':
            print('bye!')
            break
        if q == '/help':
            print('Commands: /quit  /help  /duties  /sites'
                  + ('  /toggles  /check-updates' if llama.variant == 'best-figurehead' else '')
                  + ('  /set-key' if llama.variant == 'online-with-key' else ''))
            continue
        if q == '/duties':
            print(llama.guide.duties())
            continue
        if q == '/sites':
            from .guide import ECO
            for e in ECO:
                print('%2d. %s' % (e['n'], e['name']))
            continue
        if q == '/toggles' and llama.variant == 'best-figurehead':
            for k, v in llama.features.items():
                print('  [%s] %s -- %s' % ('x' if v else ' ', k, FIGUREHEAD_FEATURES[k]))
            print("toggle with: /toggle <name>")
            continue
        if q.startswith('/toggle ') and llama.variant == 'best-figurehead':
            name = q[8:].strip()
            r = llama.toggle(name)
            print(('unknown feature' if r is None else ('now ' + ('ON' if r else 'OFF'))))
            continue
        if q == '/check-updates' and llama.variant == 'best-figurehead':
            print(json.dumps(llama.check_updates(), indent=1))
            continue
        if q == '/set-key' and llama.variant == 'online-with-key':
            try:
                k = getpass.getpass('API key: ')
            except Exception:
                k = ''
            print('saved device-local' if llama.set_key(k) else 'not saved')
            continue
        print('llama> ' + llama.ask(q).replace('\n', '\nllama> '))
