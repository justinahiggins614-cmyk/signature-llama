"""Signature Llama conversational guide engine (Python port of js/jah-talk-fallback.js).

Zero-network rule-based talker: warm, plain-words conversation, full duties
coverage, and built-in knowledge of all 31 JAH network sites. Never word salad,
never templated word blocks — genuinely responsive replies.
"""
import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_eco():
    p = os.path.join(_HERE, 'ecosystem.json')
    with open(p, encoding='utf-8') as f:
        return json.load(f)


ECO = _load_eco()

CONCEPTS = [
    (('token', 'tokens', 'tokenize'),
     'A token is a chunk of text the AI reads at a time -- sometimes a whole word, '
     'sometimes just part of one. Models count tokens the way you would count words, roughly.'),
    (('large language model', 'llm'),
     'A large language model is an AI trained on huge piles of text so it can predict what words '
     'come next -- and that turns out to be enough to chat, explain, write and reason.'),
    (('neural network',),
     'A neural network is layers of tiny math units that learn patterns from examples. '
     'Every modern AI, including this one, is one of these under the hood.'),
    (('transformer',),
     'The transformer is the architecture behind nearly every modern AI -- it reads whole sentences '
     'at once and learns which words matter to which other words.'),
    (('prompt',),
     'A prompt is the text you give an AI -- your question or instruction. Better prompts get better '
     'answers: say what you want, give context, be specific.'),
    (('api key',),
     'An API key is a secret string that lets a program use an online AI service. Yours stays on '
     'your device -- never paste it anywhere public.'),
    (('quantization', 'quantize', 'quantized'),
     'Quantization shrinks an AI model by rounding its numbers. The model gets much smaller and '
     'faster with barely any quality loss.'),
    (('embedding',),
     'An embedding turns a word or sentence into numbers capturing its meaning -- similar meanings '
     'get similar numbers, so the AI can do math on meaning.'),
    (('context window',),
     'The context window is how much text an AI keeps in mind at once. This build remembers the '
     'recent conversation, not a whole book.'),
    (('machine learning',),
     'Machine learning is teaching computers by example instead of explicit rules -- the computer '
     'finds the patterns itself.'),
    (('parameter', 'parameters'),
     'Parameters are the learned numbers inside an AI. This build is small and fast; the giant '
     'cloud models have billions.'),
]

JOKES = [
    'Okay, one llama joke: why did the llama bring a ladder to the chat? It heard the '
    'conversation was going to the next level. I will see myself out.',
    'Here is one: what do you call a llama that codes? A "drama-llama" in production. '
    'I am funnier with real questions, I promise.',
    'A llama walks into a library and asks for books on paranoia. The librarian whispers, '
    '"They are right behind you." Anyway -- what can I actually help with?',
]

PROFANE = re.compile(r'\b(fuck|shit|bitch|asshole|dick|cunt|whore|slut)\b', re.I)


def _pick(key, options, salt=''):
    h = int(hashlib.md5((key + '|' + salt).encode('utf-8')).hexdigest(), 16)
    return options[h % len(options)]


def _has(t, phrase):
    return (' ' + phrase + ' ') in (' ' + re.sub(r'[^a-z0-9 ]', ' ', t.lower()) + ' ')


class Guide:
    """Conversational guide bound to one AI profile."""

    def __init__(self, name='Signature Llama', description='', abilities=(),
                 domain='', variant='offline-static'):
        self.name = name
        self.description = description
        self.abilities = [a.strip() for a in abilities if a.strip()]
        self.domain = domain
        self.variant = variant

    # -- profile helpers ------------------------------------------------
    def _purpose(self):
        if self.description:
            m = re.match(r'[^.!?]+[.!?]', self.description.strip())
            return (m.group(0).strip() if m else self.description.strip()[:160])
        if self.domain:
            return 'I work in %s -- ask me anything there.' % self.domain
        return 'I am here to help, plain and simple.'

    def _offer(self, text):
        if not self.abilities:
            return 'answering your questions in plain words'
        tw = set(re.findall(r'[a-z]{4,}', text.lower()))
        best, best_score = None, 0
        for a in self.abilities:
            aw = set(re.findall(r'[a-z]{4,}', a.lower()))
            score = len(tw & aw)
            if score > best_score:
                best, best_score = a, score
        a = (best or self.abilities[0]).rstrip('.')
        return a[0].lower() + a[1:]

    def _summary(self):
        abs_ = [a.rstrip('.') for a in self.abilities[:3]]
        abs_ = [a[0].lower() + a[1:] for a in abs_]
        if not abs_:
            return 'chatting and answering questions'
        if len(abs_) == 1:
            return abs_[0]
        return ', '.join(abs_[:-1]) + ' and ' + abs_[-1]

    # -- intents ---------------------------------------------------------
    def greet(self):
        return _pick(self.name, [
            'Hey there! I am %s. %s What can I do for you today?' % (self.name, self._purpose()),
            'Hello! %s here -- %s How can I help?' % (self.name, self._purpose()),
        ], 'greet')

    def duties(self):
        purp = self._purpose().rstrip('.')
        purp = (purp[0].lower() + purp[1:]) if purp else purp
        lines = [_pick(self.name, [
            'Happy to lay it out -- here is what I am built for.',
            'Good question. Here is my whole job, in plain words.',
        ], 'duties-open') + ' I am %s, %s.' % (self.name, purp)]
        if self.abilities:
            lines.append('')
            lines.append(_pick(self.name, [
                'Day to day, my duties break down like this:',
                'In practice, that means:',
            ], 'duties-list'))
            for i, a in enumerate(self.abilities[:8], 1):
                lines.append('  %d) %s.' % (i, a.rstrip('.')))
        if self.domain:
            lines.append('')
            lines.append('%s is my home turf -- bring me anything from that world.' % self.domain)
        lines.append('')
        lines.append('And I know all 31 sites in the JAH network -- what each does and where '
                     'everything lives -- so ask if you ever need a tour guide. What shall we start with?')
        return '\n'.join(lines)

    # -- ecosystem -------------------------------------------------------
    @staticmethod
    def find_site(q):
        t = ' ' + re.sub(r'[^a-z0-9 ]', ' ', q.lower()) + ' '
        m = re.search(r'(?:site|number|#)\s*(\d{1,2})', t)
        if m:
            for e in ECO:
                if e['n'] == int(m.group(1)):
                    return e
        best, best_len = None, 0
        for e in ECO:
            for cand in [e['name'], e['repo']] + e.get('aliases', []):
                c = re.sub(r'[^a-z0-9 ]', ' ', cand.lower()).strip()
                if len(c) > 2 and (' ' + c + ' ') in t and len(c) > best_len:
                    best_len, best = len(c), e
        if best:
            return best
        ws = [w for w in re.findall(r'[a-z]{5,}', q.lower())]
        b2, b2s = None, 0
        for e in ECO:
            hay = (e['name'] + ' ' + e['blurb'] + ' ' + ' '.join(e['tabs'])).lower()
            sc = sum(1 for w in ws if w in hay)
            if sc > b2s:
                b2s, b2 = sc, e
        return b2 if b2s >= 2 else None

    def _site_answer(self, site, q):
        tabs = ', '.join(site['tabs'])
        blurb = site['blurb']
        blurb = blurb[0].upper() + blurb[1:]
        opener = _pick(q, [
            'Oh, I know that one well.',
            'Good pick -- I know exactly where that lives.',
            'Yep, that is one of ours.',
        ], 'site')
        follow = _pick(q, [
            ' What are you hoping to do there? I can point you at the right tab.',
            ' Anything specific you are after on it?',
        ], 'site-follow')
        return ('%s %s is site %d in the JAH network. %s Over there you will find %s -- '
                'the address is %s.%s' % (opener, site['name'], site['n'], blurb, tabs,
                                          site['url'], follow))

    def _ecosystem_answer(self, q):
        return (_pick(q, [
            'The JAH network is 31 sites, all built by Justin Addam Higgins -- the math grid, the '
            'calculator, the dictionary, the encyclopedia, the dossier archive, the Signature Llama, '
            'the AI phone book, the patent and spec catalogs, and plenty more: a book depository, a '
            'comics store, a news wire, a chip maker, a music studio, a flight school, even his own '
            'planet explorer. ',
        ], 'eco') + _pick(q, [
            'Tell me what you are trying to do and I will point you at the right site and the right tab.',
            'Give me a topic -- math, words, patents, music, games, anything -- and I will tell you '
            'exactly where it lives.',
        ], 'eco-follow'))

    def _versions_answer(self, q):
        return (_pick(q, [
            'The Llama comes in four versions, and the Versions tab on the Signature Llama site lays '
            'them all out with downloads. Short version: Offline Static runs with no internet at all. '
            'Online No-Key uses the built-in free route and falls back to the offline engine when you '
            'lose connection. Online With Key runs on your own API key, which never leaves your device. '
            'And the Best Figurehead is the flagship -- every feature toggleable, with an updater that '
            'refreshes it as new data lands.',
        ], 'ver') + ' ' + _pick(q, [
            'Which sounds like you? Tell me how you plan to use it and I will call the pick.',
            'What matters more to you -- privacy, power, or convenience? I can match you up.',
        ], 'ver-follow'))

    def _concept(self, q):
        m = re.match(r"^(?:what is|what's|whats|define|explain|meaning of|who is)\s+"
                     r'(?:a |an |the )?(.+?)\s*\??$', q.strip().lower())
        if not m:
            return None
        want = ' ' + re.sub(r'[^a-z0-9 ]', ' ', m.group(1)) + ' '
        for keys, text in CONCEPTS:
            for k in keys:
                if (' ' + k + ' ') in want:
                    return text
        return None

    def _open_answer(self, raw, q):
        words = raw.strip().split()
        topic = ' '.join(words[:7]) if len(words) <= 7 else ''
        about = ' about ' + topic if topic else ''
        offer = self._offer(q)
        summ = self._summary()
        if q.strip().endswith('?'):
            return _pick(q, [
                'Good question%s -- and I would rather be straight with you than make something up. '
                'What I can tell you for sure: I am %s, and my strong suits are %s. If your question '
                'touches any of that, ask it in plain words and I will go as deep as I can. And if it '
                'is about another corner of the network, name the topic -- I know all 31 sites and '
                'where everything lives.' % (about, self.name, summ),
                'I want to give you a real answer%s, not a guess. Here is what is true: %s The most '
                'useful thing I can do right now is %s -- want to try that angle? Or tell me a little '
                'more about what you are after and I will meet you there.' % (about, self._purpose(), offer),
            ], 'open-q')
        return _pick(q, [
            'I am with you%s. Here is what I can genuinely do with that: %s. Give me a bit more '
            'detail and I will run with it -- the more specific you are, the more useful I get.'
            % (' on ' + topic if topic else '', offer),
            'Say more -- I am listening. Meanwhile, know that I am %s, good for %s, and I can '
            'tour-guide you through all 31 network sites if that is what you need.' % (self.name, summ),
        ], 'open-s')

    # -- main entry ------------------------------------------------------
    def reply(self, text):
        raw = (text or '').strip()
        t = raw.lower()
        if not t:
            return self.greet()
        if re.match(r'^(bye|goodbye|good ?night|see you|later|gtg|cya)\b', t):
            return _pick(t, ['Goodbye for now -- I will be right here when you need me.',
                             'See you soon! It was good talking with you.'], 'bye')
        if _has(t, 'thank'):
            return _pick(t, ['You are very welcome -- that is what I am here for.',
                             'Anytime. Happy to help.'], 'thanks')
        if re.match(r'^(hi|hii+|hey|hello|yo|howdy|good\s?(morning|afternoon|evening|day)|greetings|sup|hiya)\b', t):
            return _pick(t, [
                'Hey! Good to hear from you. I am %s -- %s What is on your mind?' % (self.name, self._purpose()),
                'Hello there! %s at your service. %s' % (self.name, self._purpose()),
            ], 'hello')
        if re.search(r'who (made|created|built|trained) you|your (maker|creator)|who is (manon|justin)', t):
            return _pick(t, [
                'Justin Addam Higgins made me -- one of his Signature AIs, part of a 31-site network '
                'he built himself.',
                'I was made by Justin Addam Higgins, from scratch. The whole JAH network is his build.',
            ], 'maker')
        if re.search(r'who are you|your name|what is your name|introduce yourself|about yourself|what model are you|what are you', t):
            return ('I am %s. %s If you want the full rundown, just ask me about my duties.'
                    % (self.name, self._purpose()))
        if _has(t, 'how are you') or _has(t, "how's it going"):
            return ('Doing well, thanks for asking! I am %s, ready to work. %s What shall we dig into?'
                    % (self.name, self._purpose()))
        if PROFANE.search(t):
            return ('Ha -- I will let that one slide. I am built to be useful, so let us aim that energy '
                    'somewhere good. What do you actually need?')
        if _has(t, 'joke') or _has(t, 'make me laugh') or _has(t, 'funny'):
            return _pick(t, JOKES, 'joke')
        site = self.find_site(t)
        site_sig = bool(re.search(r'site|website|page|tab|where|take me|open|visit|tell me about', t))
        if site and (site_sig or _has(t, 'how do i') or _has(t, 'how can i')):
            return self._site_answer(site, t)
        if re.search(r'all (the )?sites|the network|jah network|ecosystem|how many sites|site list|full tour|what sites', t):
            return self._ecosystem_answer(t)
        if re.search(r'how do i|how can i|where do i|where can i|take me to|show me how|how to use|get started', t):
            if site:
                return self._site_answer(site, t)
            return ('Here is how I would tackle that: I am best at %s. Walk me through what you are '
                    'trying to do, step by step, and I will guide you through each part.'
                    % self._offer(t))
        if re.search(r'which version|what version|versions|figurehead|best version|api key|no key|offline|online', t):
            return self._versions_answer(t)
        if re.search(r'what are your duties|what is your duty|what do you do|what can you do|your duties|'
                     r'your job|your role|your abilities|help me|^help$|what are you for|what are you good at', t):
            return self.duties()
        concept = self._concept(t)
        if concept:
            return concept + ' ' + _pick(t, ['Want me to go deeper on any part of that?',
                                             'I can also tie it to what I do here -- just ask.'], 'concept')
        if re.search(r'what do you think|your opinion|should i|which is better|do you believe|predict', t):
            return ('Straight answer: I do not have real opinions the way people do -- I am a guide, not '
                    'a person. But I can lay out the trade-offs honestly so you can decide. What are the '
                    'options you are weighing?')
        return self._open_answer(raw, t)
