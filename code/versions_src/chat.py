"""Signature Llama chat — pick your version, then talk."""
import sys

from signature_llama.engine import Llama, VARIANTS


def main():
    print('Signature Llama — four versions:')
    ids = list(VARIANTS)
    for i, vid in enumerate(ids, 1):
        v = VARIANTS[vid]
        print('  %d) %s -- %s' % (i, v['name'], v['tagline']))
    try:
        choice = input('Pick 1-%d [1]: ' % len(ids)).strip() or '1'
    except (EOFError, KeyboardInterrupt):
        print()
        return
    vid = ids[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(ids) else ids[0]
    llama = Llama(variant=vid,
                  description='The fully cyber utilizable AI -- chat, explain, and guide.',
                  abilities=['chat in natural flowing sentences',
                             'explain what it can do in plain words',
                             'point you around all 31 JAH network sites',
                             'define AI terms simply'],
                  domain='conversation')
    from signature_llama.engine import chat_loop
    chat_loop(llama)


if __name__ == '__main__':
    main()
