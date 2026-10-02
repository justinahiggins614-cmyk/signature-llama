#!/usr/bin/env python3
"""Regenerate sitemap.xml for signature-llama.

Includes: core pages/data files, every LLM-dictionary term (?term= URL),
every tool library (?toollib= URL), and the single-page section anchors
(#model, #chat, #developers, ...). GitHub Pages serves the page for every
query string, so all listed URLs return HTTP 200.

Run: python3 code/build_sitemap.py
"""
import json, os, urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASE = 'https://justinahiggins614-cmyk.github.io/signature-llama'
DATE = date.today().isoformat()

terms = json.load(open(os.path.join(REPO, 'data', 'llm-dictionary.json')))['terms']
libs = json.load(open(os.path.join(REPO, 'data', 'tool-libraries.json')))['libraries']

sections = ['phonebook', 'model', 'chat', 'creations', 'downloads', 'compatibility',
            'developers', 'ai-access', 'guide', 'inventory', 'dictionary', 'toollib',
            'facts', 'methodology']

core = [
    '', '/llms.txt', '/llama-manifest.json', '/model-status.json', '/llama-api.js',
    '/industry-llama.js', '/network-index.json', '/network-sitemap.xml',
    '/data/llm-dictionary.json', '/data/explainer-kb.json', '/data/tool-libraries.json',
    '/sigllama/sigllama.js', '/sigllama/vocab.json',
    '/patch/signature-llama-patch-v1.zip',
]

urls = []
for p in core:
    urls.append((BASE + p if p else BASE + '/', DATE, 'weekly'))
for s in sections:
    urls.append((BASE + '/#' + s, DATE, 'monthly'))
for t in terms:
    urls.append((BASE + '/?term=' + urllib.parse.quote(t['t'], safe=''), DATE, 'monthly'))
for l in libs:
    urls.append((BASE + '/?toollib=' + urllib.parse.quote(l['id'], safe=''), DATE, 'monthly'))

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, lastmod, changefreq in urls:
    loc = loc.replace('&', '&amp;').replace('<', '&lt;')
    lines.append('  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq></url>'
                 % (loc, lastmod, changefreq))
lines.append('</urlset>')
open(os.path.join(REPO, 'sitemap.xml'), 'w').write('\n'.join(lines) + '\n')
print('wrote sitemap.xml with %d urls (%d terms, %d libraries, %d sections)'
      % (len(urls), len(terms), len(libs), len(sections)))
