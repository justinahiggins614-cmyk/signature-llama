#!/usr/bin/env python3
"""Move THE JAH NETWORK nav to the bottom of every page (above footer, one
instance per page) and apply label renames:
  "5 Wiki Leaks" -> "5 JAH-N Wiki Leaks"   (ordered 2026-10-04)
  "14 The Signature AI Mad Scientist Creation Lab" -> "14 The Signature AI Mix and Match Generator"
  (his 2026-10-04 standing rename order: never "mad scientist" anywhere visible)
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ['index.html', 'archive.html', 'compiler.html', 'showcase.html',
         'browse.html', '404.html', 'versions.html']


def renamed(nav):
    nav = nav.replace('>5 Wiki Leaks<', '>5 JAH-N Wiki Leaks<')
    nav = nav.replace('>14 The Signature AI Mad Scientist Creation Lab<',
                      '>14 The Signature AI Mix and Match Generator<')
    return nav


def main():
    # canonical nav source: index.html (already bottom-placed), renamed
    index = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<div class="jahnet">.*?</div>', index, re.S)
    assert m, 'no jahnet nav in index.html'
    canon = renamed(m.group(0))
    # sanity: one instance in index already at bottom
    assert index.count('<div class="jahnet">') == 1

    for page in PAGES:
        p = os.path.join(ROOT, page)
        if not os.path.exists(p):
            print('skip (missing):', page)
            continue
        html = open(p, encoding='utf-8').read()
        navs = re.findall(r'<div class="jahnet">.*?</div>', html, re.S)
        if page == 'index.html':
            html = html.replace(navs[0], canon, 1)
            open(p, 'w', encoding='utf-8').write(html)
            print('index.html: renamed in place (already at bottom)')
            continue
        # remove every existing instance
        html2 = re.sub(r'<div class="jahnet">.*?</div>\n?', '', html, flags=re.S)
        removed = len(navs)
        # insert one instance directly above the footer (or above </body>)
        marker = None
        for cand in ('<div class="footer">', '<footer'):
            if cand in html2:
                marker = cand
                break
        insertion = '<!-- THE JAH NETWORK: one instance per page, bottom, above footer -->\n' + canon + '\n'
        if marker:
            html2 = html2.replace(marker, insertion + marker, 1)
            where = 'above footer'
        else:
            html2 = html2.replace('</body>', insertion + '</body>', 1)
            where = 'above </body>'
        open(p, 'w', encoding='utf-8').write(html2)
        n = html2.count('<div class="jahnet">')
        print('%s: removed %d, now %d instance(s), %s' % (page, removed, n, where))
        assert n == 1, 'expected exactly one nav on ' + page


if __name__ == '__main__':
    main()
