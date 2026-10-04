#!/usr/bin/env python3
"""Signature Llama -- Offline Static (thumbdrive edition, v2.0.0)

The best version. Runs fully client-side on any static page -- no network, ever.

Single file, standard library only. Copy to any USB stick and run:
    python3 llama-thumbdrive-offline-static.py
No install, no network needed (Offline Static). Other variants use the
network only for their documented route, with offline fallback.
Independent project by Justin Addam Higgins. Not affiliated with Meta.
"""
import getpass, hashlib, json, os, re, time, urllib.request

VARIANT_ID = 'offline-static'
VARIANT_NAME = 'Offline Static'

ECOSYSTEM_JSON = '[{"n": 1, "repo": "signature-math", "url": "https://justinahiggins614-cmyk.github.io/signature-math/", "name": "Signature Math", "blurb": "his deterministic math grid foundation — the math everything else in the network is built on.", "tabs": ["Math Grid", "Proofs", "Signature Mark"], "aliases": ["math", "math grid"]}, {"n": 2, "repo": "jah-calculator", "url": "https://justinahiggins614-cmyk.github.io/jah-calculator/", "name": "Signature Universal Paradox Immune Calculator", "blurb": "a safe hand-written calculator with paradox checking, project simulation and a lab — no eval, real answers.", "tabs": ["Basic", "Scientific", "Ask Anything", "Paradox Check", "Project", "Simulate", "Lab"], "aliases": ["calculator", "paradox calculator"]}, {"n": 3, "repo": "jah-dictionary", "url": "https://justinahiggins614-cmyk.github.io/jah-dictionary/", "name": "The Signature Dictionary", "blurb": "255,611 entries of original definitions with a personal AI teacher, read-aloud, copy and download.", "tabs": ["Search", "A–Z", "Word AI", "1 Million Archive"], "aliases": ["dictionary"]}, {"n": 4, "repo": "jah-wiki", "url": "https://justinahiggins614-cmyk.github.io/jah-wiki/", "name": "JAH Wiki", "blurb": "the Wikipedia-like encyclopedia over ALL the network\'s data — articles with analysis lenses, demos and working code.", "tabs": ["Search", "Random Article", "A–Z", "Article Pages"], "aliases": ["wiki", "jah wiki", "encyclopedia"]}, {"n": 5, "repo": "jah-n-wiki-leaks", "url": "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/", "name": "JAH-N Wiki", "blurb": "the classified-dossier archive — every spec and patent as a signed-off dossier, marching to a million files.", "tabs": ["Dossiers", "Search", "AI Disc", "Thumbdrive"], "aliases": ["jah-n", "wiki leaks", "leaks", "dossier", "dossiers"]}, {"n": 6, "repo": "signature-llama", "url": "https://justinahiggins614-cmyk.github.io/signature-llama/", "name": "Signature Llama", "blurb": "the fully cyber utilizable AI — this site: chat, four downloadable versions, a compiler and the archive.", "tabs": ["Main", "Versions", "Compiler", "1 Million Archive", "Best of the Best"], "aliases": ["llama", "signature llama", "this site", "here"]}, {"n": 7, "repo": "jah-ai-models", "url": "https://justinahiggins614-cmyk.github.io/jah-ai-models/", "name": "The Signature AI Phone Book", "blurb": "the Yellow Pages of AI — dial any AI by number, three-way calling, 243 domain AIs and a million hybrids.", "tabs": ["Dial Pad", "A–Z Directory", "Mix Lab", "Persona Archive"], "aliases": ["phone book", "telephone book", "ai phone", "yellow pages", "dial"]}, {"n": 8, "repo": "cyber-patent-catalog", "url": "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/", "name": "Globally Rejustered Patent Catalog", "blurb": "real harvested public patent records, every 30 minutes, full records listed and searchable.", "tabs": ["Search", "Filter Pills", "Patent Records"], "aliases": ["patent catalog", "patents", "public patents"]}, {"n": 9, "repo": "signature-one-archive", "url": "https://justinahiggins614-cmyk.github.io/signature-one-archive/specs.html", "name": "Signature Spec Catalog Pending Patents", "blurb": "his own original draft specs marching to a million — 24 group cards, lens tabs and an academy.", "tabs": ["Group Cards", "Spec Lenses", "Academy", "Search"], "aliases": ["spec catalog", "specs", "spec archive", "pending patents"]}, {"n": 10, "repo": "jah-computer-systems", "url": "https://justinahiggins614-cmyk.github.io/jah-computer-systems/", "name": "The Signature PC System Depository", "blurb": "every computer system from historic to predicted, marching to a million PCs, each with demos.", "tabs": ["Categories", "System Files", "Simulators"], "aliases": ["pc", "computer", "computers", "pc depository"]}, {"n": 11, "repo": "signature-books", "url": "https://justinahiggins614-cmyk.github.io/signature-books/", "name": "The Signature Book Depository", "blurb": "3,000 finished original books plus Signature Magazines and a library, all readable on-site.", "tabs": ["Books", "Magazines", "Library"], "aliases": ["books", "book depository", "library", "magazines"]}, {"n": 12, "repo": "signature-comics", "url": "https://justinahiggins614-cmyk.github.io/signature-comics/", "name": "The Signature Comic Store", "blurb": "the original Signature comics universe — his own characters and series.", "tabs": ["Comics", "Series"], "aliases": ["comics", "comic store"]}, {"n": 13, "repo": "signature-newspapers", "url": "https://justinahiggins614-cmyk.github.io/signature-newspapers/", "name": "The Signature Global Newspaper Archive", "blurb": "the ecosystem\'s own news wire — real events from his own sites each day, never invented, with audio read-aloud.", "tabs": ["Editions", "Audio Reader"], "aliases": ["newspaper", "newspapers", "news"]}, {"n": 14, "repo": "signature-backend", "url": "https://justinahiggins614-cmyk.github.io/signature-backend/", "name": "The Signature AI Mix and Match Generator", "blurb": "mix-and-match phone-book AI models, kid-simple — name it, get its full build with real downloads.", "tabs": ["Mixes", "Generate", "Gene Boxes", "The Opperater"], "aliases": ["mix and match", "mix lab generator", "mad scientist", "gene"]}, {"n": 15, "repo": "signature-boundless-generators", "url": "https://justinahiggins614-cmyk.github.io/signature-boundless-generators/", "name": "The Signature Boundless Generator Archive", "blurb": "a generator for every field — jets, food, cars, toys and more — with exact-recreation build packages.", "tabs": ["Generators", "Universal Solver"], "aliases": ["generators", "boundless"]}, {"n": 16, "repo": "signature-ai-mixlab", "url": "https://justinahiggins614-cmyk.github.io/signature-ai-mixlab/", "name": "The Signature AI Mix Lab", "blurb": "the phone book\'s hybrid forge as its own site — a million deterministic AI hybrids, computed on demand.", "tabs": ["Forge", "A–Z Hybrids"], "aliases": ["mix lab", "hybrids", "mixlab"]}, {"n": 17, "repo": "signature-ai-olypics", "url": "https://justinahiggins614-cmyk.github.io/signature-ai-olypics/", "name": "AI Olympics", "blurb": "the battle dome — Signature AIs vs industry-style replicas vs hybrids, with medal charts and weekly games.", "tabs": ["Events", "Medal Charts", "Weekly Games"], "aliases": ["olympics", "oly pics", "battle", "games"]}, {"n": 18, "repo": "signature-chip-maker", "url": "https://justinahiggins614-cmyk.github.io/signature-chip-maker/", "name": "The Signature Computer Chip Maker and Archive", "blurb": "chip-design generator for any chip type, a million designs, full specs with SVG circuit-board images.", "tabs": ["Designer", "Archive"], "aliases": ["chip", "chips", "chip maker"]}, {"n": 19, "repo": "signature-app-archive", "url": "https://justinahiggins614-cmyk.github.io/signature-app-archive/", "name": "The Signature App Archive", "blurb": "Signature versions of every phone and PC app — a million apps, each working on-site or downloadable.", "tabs": ["Apps A–Z", "Downloads"], "aliases": ["apps", "app archive", "applications"]}, {"n": 20, "repo": "signature-ai-robot-matcher", "url": "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/", "name": "The Signature AI Robot Matcher", "blurb": "matches Signature AIs with their best-fit robot bodies — a million documented pairs with full specs.", "tabs": ["Pairs", "Mix-and-Match"], "aliases": ["robot", "robots", "robot matcher"]}, {"n": 21, "repo": "signature-experiment-solver", "url": "https://justinahiggins614-cmyk.github.io/signature-experiment-solver/", "name": "The Signature Experiment Solver", "blurb": "enter any experiment and it runs full-scale in a visible Universal Matrix — steps, findings, conclusion.", "tabs": ["Solver", "A–Z Solver Types"], "aliases": ["experiment", "experiments", "solver"]}, {"n": 22, "repo": "signature-ai-image-video-maker", "url": "https://justinahiggins614-cmyk.github.io/signature-ai-image-video-maker/", "name": "Signature AI Pixel", "blurb": "free and unlimited client-side image and video generation, powered by his AI.", "tabs": ["Image Maker", "Video Maker", "Catalog"], "aliases": ["pixel", "image maker", "video maker", "images", "pictures"]}, {"n": 23, "repo": "signature-ai-song-maker", "url": "https://justinahiggins614-cmyk.github.io/signature-ai-song-maker/", "name": "Signature Music Studio", "blurb": "a full music studio — beat maker, vocal synth, album maker and an archive of ready-to-play songs.", "tabs": ["Studio Stages", "Song Archive", "Album Maker"], "aliases": ["music", "music studio", "songs", "song maker"]}, {"n": 24, "repo": "signature-fixit", "url": "https://justinahiggins614-cmyk.github.io/signature-fixit/", "name": "The Signature Mr Fix-It", "blurb": "describe any problem — photo or video upload — and get step-by-step fixes with images and graphs.", "tabs": ["Fix Finder", "Photo/Video Upload", "Fix Archive"], "aliases": ["fix", "fixit", "fix-it", "mr fix", "repair"]}, {"n": 25, "repo": "signature-university", "url": "https://justinahiggins614-cmyk.github.io/signature-university/", "name": "The Signature University", "blurb": "courses across the whole ecosystem — learn every site and skill, track by track.", "tabs": ["Courses", "Tracks"], "aliases": ["university", "college", "school", "courses"]}, {"n": 26, "repo": "signature-cyber-mega-mall", "url": "https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/", "name": "The Signature Cyber Mega-Mall", "blurb": "the software mall — an \'80s \'90s mall experience with a map, stores and customizable products.", "tabs": ["Mall Map", "Stores", "Products"], "aliases": ["mega mall", "mall", "cyber mall", "store", "shop"]}, {"n": 27, "repo": "signature-3d-print", "url": "https://justinahiggins614-cmyk.github.io/signature-3d-print/", "name": "The Signature 3D Print Mega Mall", "blurb": "3D-printable keepsake emblems for specs and patents — STL/OBJ/3MF with real slicer profiles.", "tabs": ["Departments", "Models"], "aliases": ["3d print", "3d", "printing"]}, {"n": 28, "repo": "signature-earth", "url": "https://justinahiggins614-cmyk.github.io/signature-earth/", "name": "Signature Earth", "blurb": "his own planet explorer — an interactive 3D globe with a real gazetteer.", "tabs": ["Globe", "Gazetteer"], "aliases": ["earth", "planet", "globe", "world"]}, {"n": 29, "repo": "signature-flight-school", "url": "https://justinahiggins614-cmyk.github.io/signature-flight-school/", "name": "The Signature Flight School", "blurb": "pick any plane or jet, fly with an AI instructor — real sim, device-local pilot hours.", "tabs": ["Aircraft", "Sim", "AI Instructor"], "aliases": ["flight", "flight school", "flying", "planes", "pilot"]}, {"n": 30, "repo": "signature-game-store", "url": "https://justinahiggins614-cmyk.github.io/signature-game-store/", "name": "The Signature Game Store", "blurb": "playable games from 1970s arcade-style to modern combat-style, each with cover, play and download.", "tabs": ["Games", "Play", "Download"], "aliases": ["game store", "games", "gaming", "arcade"]}, {"n": 31, "repo": "signature-website-creator", "url": "https://justinahiggins614-cmyk.github.io/signature-website-creator/", "name": "Signature Website Creator", "blurb": "an AI website builder — describe the site you want and get a real one, with live-view editing.", "tabs": ["Builder", "1 Million Website Options", "Mirror a Website"], "aliases": ["website creator", "website builder", "make a website", "build a site", "mirror"]}]'

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
    return json.loads(ECOSYSTEM_JSON)


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


_ECO = ECO

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
            ECO = _ECO
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


if __name__ == "__main__":
    llama = Llama(variant=VARIANT_ID, name='Signature Llama',
                  description='The fully cyber utilizable AI.',
                  abilities=['chat in natural flowing sentences', 'explain AI terms in plain words', 'point you around all 31 JAH network sites', 'describe its files, tools and versions'],
                  domain='conversation')
    chat_loop(llama)
