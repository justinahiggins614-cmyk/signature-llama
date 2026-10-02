#!/usr/bin/env python3
"""Build the JAH Network master index (signature-llama hosts it as pure data).

Reads live counts from each site's machine-readable count endpoint/index file
(api.json / stats.json / index .json.gz), never hand-edited numbers.

Outputs:
  network-index.json   - the 9 sites: official name, live URL, record type,
                         live record count, last updated, data/index location
  network-sitemap.xml  - ecosystem sitemap: the 9 site roots + this index file

Run: python3 code/build_network_index.py
"""
import json, os, sys, gzip, io, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)              # ~/workspace/signature-llama
WS = os.path.dirname(REPO)                # ~/workspace
GH = 'https://justinahiggins614-cmyk.github.io'
DATE = __import__('datetime').date.today().isoformat()

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'JAH-Network-Index/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def count_gz_lines(url):
    """Count non-empty lines of a remote .jsonl.gz without writing a file."""
    req = urllib.request.Request(url, headers={'User-Agent': 'JAH-Network-Index/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    n = 0
    with gzip.open(io.BytesIO(data), 'rt') as f:
        for line in f:
            if line.strip():
                n += 1
    return n

def local(path):
    return os.path.join(WS, path)

def local_gz_count(path):
    n = 0
    with gzip.open(path, 'rt') as f:
        for line in f:
            if line.strip():
                n += 1
    return n

sites = []

def add(name, repo, record_type, record_count, count_source, last_updated,
        data_index_url, sitemap_url=None, note=''):
    sites.append({
        'official_name': name,
        'repo': repo,
        'live_url': GH + '/' + repo + '/',
        'record_type': record_type,
        'live_record_count': record_count,
        'count_source': count_source,
        'last_updated': last_updated,
        'data_index_url': data_index_url,
        'sitemap_url': sitemap_url or (GH + '/' + repo + '/sitemap.xml'),
        'note': note,
    })

# 1. The Signature AI Telephone Book
api = fetch_json(GH + '/jah-ai-models/api.json')
add('The Signature AI Telephone Book', 'jah-ai-models', 'AIs',
    {'published_ais': api['records_published_total'],
     'embedded_ais': api['records_embedded'],
     'word_ais': api['wordai_index_records']},
    GH + '/jah-ai-models/api.json', api['records_as_of'],
    GH + '/jah-ai-models/data/index/ai-catalog.json')

# 2. Signature Universal Paradox Immune Calculator
try:
    eq = count_gz_lines(GH + '/jah-calculator/data/index/eq.idx.json.gz')
    src = GH + '/jah-calculator/data/index/eq.idx.json.gz'
except Exception:
    eq = local_gz_count(local('jah-calculator/data/index/eq.idx.json.gz'))
    src = 'local clone fallback'
add('Signature Universal Paradox Immune Calculator', 'jah-calculator', 'equations',
    eq, src, '2026-09-29',
    GH + '/jah-calculator/data/index/eq.idx.json.gz')

# 3. The Signature Dictionary
st = fetch_json(GH + '/jah-dictionary/data/index/stats.json')
add('The Signature Dictionary', 'jah-dictionary', 'dictionary entries',
    {'entries': st['entry_count'], 'headwords': st['words'], 'spec_terms': st['terms']},
    GH + '/jah-dictionary/data/index/stats.json', st['last_updated'],
    GH + '/jah-dictionary/data/index/dict.idx.json.gz')

# 4. JAH Wiki
api = fetch_json(GH + '/jah-wiki/api.json')
bd = api.get('records_breakdown_2026_10_01', {})
add('JAH Wiki', 'jah-wiki', 'encyclopedia articles', api['records_approx'],
    GH + '/jah-wiki/api.json', api['records_as_of'],
    GH + '/jah-wiki/api.json', note='breakdown: %s' % json.dumps(bd))

# 5. JAH-N Wiki
api = fetch_json(GH + '/jah-n-wiki-leaks/api.json')
add('JAH-N Wiki', 'jah-n-wiki-leaks', 'dossiers', api['records_approx'],
    GH + '/jah-n-wiki-leaks/api.json', api['records_as_of'],
    GH + '/jah-n-wiki-leaks/data/patents.idx.json.gz')

# 6. Globally Rejustered Patent Catalog
api = fetch_json(GH + '/cyber-patent-catalog/api.json')
add('Globally Rejustered Patent Catalog', 'cyber-patent-catalog', 'public patent records',
    api['records_approx'], GH + '/cyber-patent-catalog/api.json', api['records_as_of'],
    GH + '/cyber-patent-catalog/data/patents.jsonl')

# 7. Signature Spec Catalog Pending Patents (main + 16 shards)
shards = fetch_json(GH + '/signature-one-archive/data/index/shards.json')['shards']
spec_total = 0
for e in shards:
    url = e['base'] + e['index']
    try:
        spec_total += count_gz_lines(url)
    except Exception:
        repo_name = 'signature-one-archive' if not e['base'] else e['base'].rstrip('/').split('/')[-1]
        spec_total += local_gz_count(local(repo_name + '/' + e['index']))
add('Signature Spec Catalog Pending Patents', 'signature-one-archive', 'draft specs',
    spec_total, GH + '/signature-one-archive/data/index/shards.json', DATE,
    GH + '/signature-one-archive/data/index/shards.json',
    note='main + %d shard repos summed from live index files' % (len(shards) - 1))

# 8. Signature Llama (this repo — read local data files; JS page reads the same source)
terms = len(json.load(open(os.path.join(REPO, 'data', 'llm-dictionary.json')))['terms'])
libs = len(json.load(open(os.path.join(REPO, 'data', 'tool-libraries.json')))['libraries'])
add('Signature Llama: The Fully Cyber Utilizable AI', 'signature-llama',
    'LLM dictionary terms + tool libraries',
    {'dictionary_terms': terms, 'tool_libraries': libs},
    GH + '/signature-llama/data/llm-dictionary.json', DATE,
    GH + '/signature-llama/data/llm-dictionary.json')

# 9. The Signature PC System Depository
pc = fetch_json(GH + '/jah-computer-systems/data/last-updated.json')
add('The Signature PC System Depository', 'jah-computer-systems', 'computer systems',
    pc['recorded'], GH + '/jah-computer-systems/data/last-updated.json', pc['updated'],
    GH + '/jah-computer-systems/data/systems.json')

out = {
    'index_name': 'JAH Network Master Index',
    'hosted_by': 'signature-llama (data files only)',
    'generated': DATE,
    'generated_by': 'code/build_network_index.py — do not hand-edit counts; re-run the script.',
    'sites': sites,
}
open(os.path.join(REPO, 'network-index.json'), 'w').write(json.dumps(out, indent=1) + '\n')

sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.s3.org/2001/XMLSchema">'.replace('s3.org/2001/XMLSchema', 'sitemaps.org/schemas/sitemap/0.9')]
for s in sites:
    sm.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (s['live_url'], DATE))
sm.append('  <url><loc>%s/signature-llama/network-index.json</loc><lastmod>%s</lastmod></url>' % (GH, DATE))
sm.append('  <url><loc>%s/signature-llama/network-sitemap.xml</loc><lastmod>%s</lastmod></url>' % (GH, DATE))
sm.append('</urlset>')
open(os.path.join(REPO, 'network-sitemap.xml'), 'w').write('\n'.join(sm) + '\n')

print('sites:', len(sites))
for s in sites:
    print(' -', s['official_name'][:45], '->', json.dumps(s['live_record_count'])[:60], '(as of %s)' % s['last_updated'])
print('wrote network-index.json, network-sitemap.xml')
