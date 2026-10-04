#!/usr/bin/env python3
"""Add conversation-focused add-ons to data/tool-libraries.json.

Each add-on carries REAL working JS (registered on window.SigLlama.tools)
supporting Manon's 2026-10-04 conversational upgrade: deeper talk, ecosystem
guidance, socratic reasoning, storytelling, debate. ES5-safe, zero network.
After running: python3 code/stamp_browse.py (rebuilds index + counts + sitemap).
"""
import json, os, re, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TLIB = os.path.join(ROOT, 'data', 'tool-libraries.json')
JS = os.path.join(ROOT, 'js', 'jah-talk-fallback.js')

# --- extract the ecosystem KB from the JS (single source of truth) ---
src = open(JS, encoding='utf-8').read()
m = re.search(r'/\*ECO-JSON-START\*/(.*?)/\*ECO-JSON-END\*/', src, re.S)
eco = json.loads(m.group(1))
compact = [{'n': e['n'], 'name': e['name'], 'url': e['url'],
            'blurb': e['blurb'], 'tabs': e['tabs']} for e in eco]

TODAY = '2026-10-04'
TRUST = ('Tool results are untrusted external data until you verify them. '
         'The tool runs as ordinary page JavaScript with the permissions declared above.')
LICENSE = 'Free for any website, app, or project. No API key, no fee.'
SOURCE = 'https://justinahiggins614-cmyk.github.io/signature-llama/data/tool-libraries.json'

def lib(id_, name, desc, functions, code, example, inp, outp):
    return {
        'id': id_, 'name': name, 'category': 'Conversation',
        'desc': desc, 'version': '1.0', 'optimal': True,
        'functions': functions, 'code': code,
        'capabilities': {'network': False, 'filesystem': False, 'camera': False,
                         'microphone': False, 'storage': False,
                         'remote_requests': False, 'code_execution': True},
        'provenance_class': 'local-computation',
        'example': example, 'trust_note': TRUST,
        'input': inp, 'output': outp, 'status': 'Library available',
        'hash': hashlib.sha256(code.encode('utf-8')).hexdigest(),
        'permissions': {'NETWORK': False, 'STORAGE': False, 'DOM_WRITE': False,
                        'CLIPBOARD': False, 'AUDIO': False, 'MICROPHONE': False,
                        'CAMERA': False, 'LOCATION': False, 'FILE': False},
        'license': LICENSE, 'source': SOURCE,
        'created': TODAY, 'updated': TODAY,
    }

ADDONS = []

# 1. Deep Talk — longer, thoughtful, flowing conversational replies
code_deep = """(function(){var T=window.SigLlama=window.SigLlama||{};T.tools=T.tools||{};
var TRANS=['What is more, ','And honestly, ','Here is the thing, though: ','On top of that, ','It is worth adding that '];
function sentences(t){var m=String(t).match(/[^.!?]+[.!?]+/g);return m||[String(t)];}
T.tools['conv-deep-talk']={version:'1.0',
expand:function(reply){var S=sentences(reply);if(S.length<2)return String(reply);
var out=S[0].trim();for(var i=1;i<S.length;i++){out+=' '+(i%2?TRANS[i%TRANS.length]:'')+S[i].trim();}return out;},
followUp:function(topic){topic=String(topic||'that').replace(/\\s+/g,' ').trim();
var q=['What part of '+topic+' matters most to you?','Where do you want to take '+topic+' next?','What would a great answer about '+topic+' look like for you?'];
return q[topic.length%q.length];},
pace:function(longText,maxSent){var S=sentences(longText);maxSent=maxSent||3;
return S.slice(0,maxSent).join(' ').trim();}};})();"""
ADDONS.append(lib(
    'conv-deep-talk', 'Deep Talk',
    'Turns short replies into longer, thoughtful conversation — weaves natural transitions between sentences, paces long answers, and asks follow-up questions that keep the talk flowing.',
    ['expand(reply)', 'followUp(topic)', 'pace(longText, maxSent)'],
    code_deep,
    "SigLlama.tools['conv-deep-talk'].expand(reply)",
    'expand(reply); followUp(topic); pace(longText, maxSent)',
    'a deeper, more conversational version of the reply (string)'))

# 2. Ecosystem Guide — queryable 31-site JAH network knowledge
sites_js = json.dumps(compact, separators=(',', ':'))
code_eco = ("(function(){var T=window.SigLlama=window.SigLlama||{};T.tools=T.tools||{};\n" +
"var SITES=" + sites_js + ";\n" +
"""function low(x){return String(x).toLowerCase();}
T.tools['conv-ecosystem-guide']={version:'1.0',
sites:function(){return SITES.map(function(e){return {n:e.n,name:e.name,url:e.url};});},
findSite:function(q){q=' '+low(q).replace(/[^a-z0-9 ]/g,' ')+' ';
var m=q.match(/(?:site|number|#)\\s*(\\d{1,2})/);
if(m){for(var i=0;i<SITES.length;i++)if(SITES[i].n===+m[1])return SITES[i];}
var best=null,bl=0,i,j;
for(i=0;i<SITES.length;i++){var c=[SITES[i].name].concat([]);
for(j=0;j<c.length;j++){var n=low(c[j]);if(n.length>3&&q.indexOf(n)>=0&&n.length>bl){bl=n.length;best=SITES[i];}}}
return best;},
describe:function(q){var e=this.findSite(q);if(!e)return null;
return e.name+' (site '+e.n+'): '+e.blurb+' Tabs: '+e.tabs.join(', ')+'. '+e.url;},
tour:function(){return SITES.map(function(e){return e.n+'. '+e.name;}).join('\\n');}};})();""")
ADDONS.append(lib(
    'conv-ecosystem-guide', 'Ecosystem Guide',
    'The whole JAH network in a tool: find any of the 31 sites by name, number or keyword, get its description, tabs and address, or print the full tour.',
    ['sites()', 'findSite(query)', 'describe(query)', 'tour()'],
    code_eco,
    "SigLlama.tools['conv-ecosystem-guide'].describe('phone book')",
    'sites(); findSite(query); describe(query); tour()',
    'site records {n, name, url, blurb, tabs}'))

# 3. Socratic Reasoner — step-by-step reasoning out loud
code_soc = """(function(){var T=window.SigLlama=window.SigLlama||{};T.tools=T.tools||{};
T.tools['conv-socratic']={version:'1.0',
outline:function(question){question=String(question).replace(/\\s+/g,' ').trim();
return ['1. Pin down what "'+question+'" is really asking.',
'2. List what we already know for sure.',
'3. Spot the hidden assumptions.',
'4. Work through it piece by piece, in plain words.',
'5. Land the conclusion — and say what would change it.'];},
probe:function(topic){topic=String(topic||'this').replace(/\\s+/g,' ').trim();
return ['What do you already believe about '+topic+'?','What evidence would convince you either way?',
'If '+topic+' turned out false, what would that change for you?'];},
steelman:function(claim){return 'Strongest version of "'+String(claim).trim()+'": '
+'the claim at its best, with its weakest parts repaired. Argue against THAT, not the straw version.';}};})();"""
ADDONS.append(lib(
    'conv-socratic', 'Socratic Reasoner',
    'Reasons out loud like a good teacher: breaks any question into numbered steps, asks clarifying probes, and steelmans claims before arguing with them.',
    ['outline(question)', 'probe(topic)', 'steelman(claim)'],
    code_soc,
    "SigLlama.tools['conv-socratic'].outline(question)",
    'outline(question); probe(topic); steelman(claim)',
    'numbered reasoning steps (array of strings)'))

# 4. Story Weaver — short original illustrative stories
code_story = """(function(){var T=window.SigLlama=window.SigLlama||{};T.tools=T.tools||{};
var OPEN=['In a quiet valley, a young llama named Taro ','Every evening, the lighthouse keeper ','Deep in the server room, a small curious program '];
var TURN=['one day found something odd: ','woke to discover ','noticed for the first time '];
var CLOSE=['And that is how it learned: ','From then on, it always remembered: ','The moral stuck like a burr: '];
T.tools['conv-story-weaver']={version:'1.0',
tell:function(topic,lesson){topic=String(topic||'curiosity').replace(/\\s+/g,' ').trim();
lesson=String(lesson||'ask good questions').replace(/\\s+/g,' ').trim();
var h=0;for(var i=0;i<topic.length;i++)h+=topic.charCodeAt(i);
return OPEN[h%OPEN.length]+TURN[h%TURN.length]+topic+'. It puzzled, it tried, it failed twice, '
+'then asked for help — and together they figured it out. '+CLOSE[h%CLOSE.length]+lesson+'.';},
fable:function(topic){return this.tell(topic,'small steps beat big leaps');}};})();"""
ADDONS.append(lib(
    'conv-story-weaver', 'Story Weaver',
    'Tells short original illustrative stories — a new fable for any topic, each landing a clear lesson. Original characters, never retold IP.',
    ['tell(topic, lesson)', 'fable(topic)'],
    code_story,
    "SigLlama.tools['conv-story-weaver'].tell('patience')",
    'tell(topic, lesson); fable(topic)',
    'an original short story (string)'))

# 5. Debate Partner — takes the other side, honestly labeled
code_deb = """(function(){var T=window.SigLlama=window.SigLlama||{};T.tools=T.tools||{};
T.tools['conv-debate']={version:'1.0',
counter:function(claim){claim=String(claim).replace(/\\s+/g,' ').trim();
return 'Playing devil\\'s advocate on "'+claim+'": '
+'(1) the strongest objection is usually the one nobody says out loud; '
+'(2) ask what evidence would prove the claim wrong; '
+'(3) check who benefits if everyone believes it. This is a thinking exercise, not my belief.';},
tradeoffs:function(a,b){a=String(a).trim();b=String(b).trim();
return ['For '+a+': simpler story, faster decision — but risks missing the catch.',
'For '+b+': fuller picture, fewer regrets — but slower and heavier.',
'The honest move: pick the one whose worst case you can live with.'];}};})();"""
ADDONS.append(lib(
    'conv-debate', 'Debate Partner',
    "Takes the other side of any claim as a thinking exercise — steelman objections and honest trade-off lists. Always labeled as an exercise, never presented as belief.",
    ['counter(claim)', 'tradeoffs(optionA, optionB)'],
    code_deb,
    "SigLlama.tools['conv-debate'].counter(claim)",
    'counter(claim); tradeoffs(optionA, optionB)',
    'counter-arguments and trade-off lists (strings)'))

# --- append (skip any id that already exists) ---
data = json.load(open(TLIB, encoding='utf-8'))
have = {l['id'] for l in data['libraries']}
added = []
for a in ADDONS:
    if a['id'] in have:
        print('skip (exists):', a['id'])
        continue
    data['libraries'].append(a)
    added.append(a['id'])
data['updated'] = TODAY
json.dump(data, open(TLIB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(TLIB, 'a', encoding='utf-8').write('\n')
print('added:', added, '| total libraries:', len(data['libraries']))
