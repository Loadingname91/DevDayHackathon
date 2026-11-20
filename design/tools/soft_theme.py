"""Soft Quilt skin for the Screens boards (decided Nov 19: light = Mint air).

The boards were authored in Quilter's Workbench tokens. retheme() rewrites one board's HTML to the
Soft Quilt look: Mint air gradient ground, frosted white cards, pastel app dyes, ink pill buttons,
a frosted pinned bar and Figtree. gen_all.page() calls it on every generated board.

The boards that are not generated (Main, Groceries, Budget, Calendar, Spool) are converted in place:
  python3 design/tools/soft_theme.py design/canvas Main Groceries Budget Calendar Spool
Running it twice is safe: the old values it looks for are gone after the first pass.
"""
import os, re, sys

GROUND_V1 = ('background-color: #EEF6F1; background-image: radial-gradient(75% 46% at 100% 0%, #C9F0DE 0%, transparent 72%), '
             'radial-gradient(75% 46% at 0% 22%, #DDEBFF 0%, transparent 72%), radial-gradient(75% 46% at 100% 60%, #FFF0C4 0%, transparent 72%), '
             'radial-gradient(75% 46% at 0% 100%, #CFEFF0 0%, transparent 72%);')
# the ground is kept faint (blobs at half strength) so the app patches carry the colour
GROUND = ('background-color: #EEF6F1; background-image: radial-gradient(75% 46% at 100% 0%, rgba(201,240,222,0.5) 0%, transparent 72%), '
          'radial-gradient(75% 46% at 0% 22%, rgba(221,235,255,0.5) 0%, transparent 72%), radial-gradient(75% 46% at 100% 60%, rgba(255,240,196,0.5) 0%, transparent 72%), '
          'radial-gradient(75% 46% at 0% 100%, rgba(207,239,240,0.5) 0%, transparent 72%);')
# second pass (Nov 19, later): deeper patch dyes so the apps stand out against the fainter ground
TUNE = {'CFF2E1': 'B5EBD0', 'FFDCCA': 'FFC8AC', 'D5E4FF': 'BDD5FF', 'FFEFB8': 'FFE48F', 'FFD5E3': 'FFBFD4', 'E0D8FF': 'CFC3FF', 'CDEEF3': 'B1E5EE', 'F1E6D6': 'EAD8BD', 'DDEBC8': 'CDE2AC'}
INK, SEC, THREAD = '#221F3A', '#5B5775', '#B4B0CC'

HEX = {
    # chrome
    'F4EEE1': 'EEF6F1', '2A2119': '221F3A', '1F180D': '221F3A', '665847': '5B5775', 'BFAE90': 'B4B0CC', 'FFFDF8': 'FFFFFF',
    'EEE6D6': 'E3EFE8', 'F3ECDD': 'EAF3EE', 'FBF6EC': 'F6FAF8', 'F7F1E6': 'EAF3EE', 'DCCFB6': 'C9C6DC',
    # accents: denim becomes a clearer blue for links and Clair's chalk; mustard becomes ink
    '3557A6': '2F56B0', '22396F': '263F8C', '1F6B5E': '1C6F52', 'E3A72F': '221F3A',
    # app dyes -> Soft Quilt pastels (same app keeps one colour everywhere)
    'D3ECE7': 'CFF2E1', 'DDEBD2': 'FFDCCA', 'DCE4F3': 'D5E4FF', 'FBEBC4': 'FFEFB8', 'F8DCC2': 'FFD5E3', 'E7EBC2': 'E0D8FF',
    'EADCF0': 'CDEEF3', 'F3DCE0': 'F1E6D6',
}

ST = ('.st{background-color:rgba(255,255,255,.78);border-radius:16px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.95),0 12px 28px -16px rgba(20,30,40,.32);'
      'transition:outline-color var(--t-state) var(--ease);outline:1.5px solid transparent;outline-offset:-7px}')
ST_BASTED = '.st.basted{outline:1.5px dashed rgba(34,31,58,.42)}'
EXTRA = ('.qp{border-radius:16px;box-shadow:0 12px 28px -18px rgba(20,30,40,.4)}\n'
         'body{font-variant-numeric:tabular-nums}\n::selection{background:#C9F0DE;color:#221F3A}\n'
         'a:focus-visible,button:focus-visible{outline:3px solid #2F56B0;outline-offset:3px}\n')
BAR_SKIN = ('height: 62px; display: flex; gap: 6px; padding: 6px; box-sizing: border-box; border-radius: 26PX; background: rgba(255,255,255,0.72); '
            'border: 1px solid rgba(255,255,255,0.95); -webkit-backdrop-filter: blur(18px) saturate(1.4); backdrop-filter: blur(18px) saturate(1.4); '
            'box-shadow: 0 14px 30px -12px rgba(20,30,40,0.4);')
RADIUS = {'8': '12', '12': '16', '16': '22'}


def _hex(m):
    return '#' + HEX.get(m.group(1).upper(), m.group(1))


def tune(t):
    # safe to run again: the first-pass values it looks for are gone afterwards
    t = t.replace(GROUND_V1, GROUND)
    t = re.sub(r'#([0-9A-Fa-f]{6})\b', lambda m: '#' + TUNE.get(m.group(1).upper(), m.group(1)), t)
    t = t.replace('border: 1.5px dashed rgba(34,31,58,0.3); border-radius: 11px;', 'border: 1.5px dashed rgba(34,31,58,0.45); border-radius: 11px;')
    return t.replace('.qp{border-radius:16px;box-shadow:0 12px 28px -18px rgba(20,30,40,.4)}', '.qp{border-radius:16px;box-shadow:0 12px 26px -14px rgba(20,30,40,.45)}')


def retheme(t):
    if 'family=Figtree' in t:
        return tune(t)
    # type: one family, tabular figures instead of the mono
    t = re.sub(r'family=Bricolage\+Grotesque[^"\']*?display=swap', 'family=Figtree:wght@400..800&amp;display=swap', t)
    t = t.replace('Bricolage Grotesque', 'Figtree').replace('Hanken Grotesk', 'Figtree').replace('DM Mono', 'Figtree')
    t = re.sub(r"(Figtree\\*'), ?monospace", r'\1, system-ui, sans-serif', t)
    t = t.replace('font-weight: 800', 'font-weight: 700').replace('font-weight:800', 'font-weight:700')
    # ground
    t = re.sub(r'overflow: hidden; background: #F4EEE1;', 'overflow: hidden; ' + GROUND, t, flags=re.I)
    t = re.sub(r'(<div style="width: 1280px; height: 800px;[^"]*?)background: #F4EEE1;', lambda m: m.group(1) + GROUND, t, flags=re.I)
    # cards: solid edge when saved, dashed while waiting for OK
    t = re.sub(r'\.st\.basted\{[^}]*\}', ST_BASTED, t)
    seen = []
    t = re.sub(r'\.st\{[^}]*\}', lambda m: ST if not seen and not seen.append(1) else '', t)
    # the apps grid: separate rounded patches instead of one pieced block
    t = re.sub(r'(grid-template-columns: repeat\(6, minmax\(0, 1fr\)\);[^"]*?) border-radius: \d+px; overflow: (?:hidden|clip);', r'\1 gap: 6px;', t)
    t = t.replace('.num{font-variant-numeric:tabular-nums}', '.num{font-variant-numeric:tabular-nums}\n' + EXTRA.rstrip('\n'), 1)
    t = t.replace('.pb,.rw,.st{transition:none}', '.pb,.rw,.st{transition:none}')
    # pinned bar: frosted, separate rounded pins, ink Clair pill
    t = t.replace('height: 62px; display: flex; border-radius: 16px; box-shadow: 0 8px 22px -14px rgba(42,33,25,0.55);', BAR_SKIN)
    t = t.replace('border-radius: 16px 0 0 16px;', 'border-radius: 20PX;').replace('border-left: 1.5px dashed rgba(42,33,25,0.4);', 'border-radius: 20PX;')
    t = t.replace('box-shadow: inset 0 -3px 0 #3557A6;', 'box-shadow: inset 0 0 0 2px #221F3A;')
    t = t.replace('background: #2A2119; color: #FBF6EC; border-radius: 0 16px 16px 0;', 'background: #221F3A; color: #FFFFFF; border-radius: 20PX;')
    # patches: rounded, with the running stitch set in from the edge
    t = t.replace('inset: 3px; border: 1.5px dashed rgba(42,33,25,0.28); border-radius: 8px;', 'inset: 6px; border: 1.5px dashed rgba(34,31,58,0.3); border-radius: 11PX;')
    # buttons: ink pills; the "just changed" tag: an ink pill
    t = re.sub(r'background: #3557A6; color: #(?:FFFFFF|FFFDF8|FBF6EC)', 'background: #221F3A; color: #FFFFFF', t, flags=re.I)
    t = re.sub(r'(<(?:a|button)\b[^>]*class="btn[^>]*?border-radius: )(?:12|10|14)px', r'\g<1>99PX', t)
    t = re.sub(r'background: #E3A72F; color: #(?:1F180D|2A2119); border-radius: 4px', 'background: #221F3A; color: #FFFFFF; border-radius: 99PX', t, flags=re.I)
    t = re.sub(r'background: #E3A72F;(\s*)color: #(?:1F180D|2A2119)', r'background: #221F3A;\1color: #FFFFFF', t, flags=re.I)
    # the old stitch tone was sometimes used for text; text gets a tone that passes 4.5:1
    t = re.sub(r'(?<![-\w])color: ?#BFAE90', 'color: #6F6B8A', t, flags=re.I)
    # colours
    t = re.sub(r'#([0-9A-Fa-f]{6})\b', _hex, t)
    t = t.replace('rgba(42,33,25,', 'rgba(34,31,58,').replace('rgba(42, 33, 25,', 'rgba(34, 31, 58,')
    # rounder corners everywhere else
    t = re.sub(r'border-radius: ?[^;\'"}]+', lambda m: re.sub(r'\b(8|12|16)px', lambda k: RADIUS[k.group(1)] + 'px', m.group(0)), t)
    return tune(t.replace('PX', 'px'))


if __name__ == '__main__':
    for name in sys.argv[2:]:
        p = os.path.join(sys.argv[1], name + '.dc.html')
        src = open(p).read()
        open(p, 'w').write(retheme(src))
    print('rethemed', sys.argv[2:])
