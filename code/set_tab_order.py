#!/usr/bin/env python3
"""Tab order + Best-of-the-Best pop-open fix for signature-llama.

New tab order: Main | Versions | Compiler | 1 Million Archive | Best of the Best
(archive tab labeled "1 Million Archive" per his order).
Also: archive.html Best-of-the-Best <details> pops open by default.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABS = [
    ('index.html', '&#127968; Main'),
    ('versions.html', '&#128230; Versions'),
    ('compiler.html', '&#9881;&#65039; Compiler'),
    ('archive.html', '&#128449; 1 Million Archive'),
    ('showcase.html', '&#9733; Best of the Best'),
]


def tabbar(active):
    parts = ['<nav class="jah-tabs" aria-label="Llama pages">']
    for href, label in TABS:
        cls = 'tablink on' if href == active else 'tablink'
        aria = ' aria-current="page"' if href == active else ''
        parts.append('<a class="%s" href="%s"%s>%s</a>' % (cls, href, aria, label))
    parts.append('</nav>')
    return ''.join(parts)


def main():
    for page, _ in TABS:
        p = os.path.join(ROOT, page)
        html = open(p, encoding='utf-8').read()
        new = tabbar(page)
        html2, n = re.subn(r'<nav class="jah-tabs" aria-label="Llama pages">.*?</nav>',
                           new, html, count=1, flags=re.S)
        assert n == 1, 'tab bar not found once in ' + page
        open(p, 'w', encoding='utf-8').write(html2)
        print('tab order set:', page)

    # archive.html: Best of the Best pops open by default
    ap = os.path.join(ROOT, 'archive.html')
    a = open(ap, encoding='utf-8').read()
    old = "'<details><summary>\\uD83D\\uDC49 Pop open: what it does, implications, stats</summary>'"
    new = ("'<details open><summary>\\u2B50 The full picture: what it does, implications, stats</summary>'")
    assert old in a, 'bestpin details markup not found'
    a = a.replace(old, new, 1)
    open(ap, 'w', encoding='utf-8').write(a)
    print('archive.html: Best of the Best now pops open by default')


if __name__ == '__main__':
    main()
