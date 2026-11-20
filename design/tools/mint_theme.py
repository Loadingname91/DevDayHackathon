"""Mint colours for the canvas boards (picked Nov 20, spec/adr/013-mint-one-family-palette.md).

The boards were drawn in Soft Quilt's Nov 19 colours (Mint air light, Denim dusk dark, nine
unrelated pastel dyes). mint() rewrites one board's HTML to the Mint palette the client uses
(web/src/styles/tokens.css): a plain mint ground, ink and greys tinted to the ground's hue, and the
nine dyes as one family from pear through teal to blue. Layout, copy and behaviour are untouched.

soft_theme.retheme() and gen_soft.py call it, so regenerated boards come out in Mint. To convert
boards already on disk (running it twice is safe: the old values are gone after the first pass):
  python3 design/tools/mint_theme.py design/canvas Main Budget ...
The record boards SqGrounds and SqAppearance keep the Nov 19 grounds on purpose.
"""
import math, os, re, sys

NH = 172  # the neutral hue the ground, ink and greys take


def ok(L, C, h):
    """OKLCH to #RRGGBB, clipped to sRGB (same values as tokens.css)."""
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    f = lambda x: max(0.0, min(1.0, 1.055 * x ** (1 / 2.4) - 0.055 if x > 0.0031308 else 12.92 * x))
    return '#%02X%02X%02X' % tuple(round(f(x) * 255) for x in rgb)


def rgb(hex6):
    h = hex6.lstrip('#')
    return '%d,%d,%d' % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# dye: (hue, light lightness, chroma, dark lightness), as in tokens.css
DYES = {'sage': (165, .87, .065, .42), 'apricot': (152, .94, .05, .33), 'chambray': (222, .9, .05, .38),
        'butter': (135, .95, .05, .32), 'blush': (205, .94, .05, .33), 'lavender': (240, .86, .06, .43),
        'sea glass': (195, .88, .05, .4), 'linen': (172, .93, .03, .34), 'pear': (142, .9, .05, .38)}


def dye(name):
    h, l, c, dl = DYES[name]
    return dict(fill=ok(l, c, h), deep=ok(.44, .1, h), dfill=ok(dl, c * 1.1, h), ddeep=ok(.86, .08, h))


# Nov 19 dye values: light fill, light deep, dark fill, dark deep
OLD_DYES = {'sage': ('B5EBD0', '1C6F52', '23604D', '9BE8C6'), 'apricot': ('FFC8AC', 'A8481B', '74402A', 'FFC2A3'),
            'chambray': ('BDD5FF', '2B58B8', '2C4A8F', 'AFC9FF'), 'butter': ('FFE48F', '7D5B00', '655216', 'FFE082'),
            'blush': ('FFBFD4', 'A52E62', '742E52', 'FFB3CF'), 'lavender': ('CFC3FF', '5340BE', '463D9C', 'C9BEFF'),
            'sea glass': ('B1E5EE', '146E7F', '1F5E6B', '9FE3EE'), 'linen': ('EAD8BD', '75552A', '594A34', 'E8D3B3'),
            'pear': ('CDE2AC', '4A661B', '44591F', 'CBE3A2')}

INK, INK_D = ok(.24, .03, NH), ok(.95, .01, NH)
CARD_D = ok(.25, .024, NH)
ACCENT = ok(.45, .1, 185)  # links, focus, switches, Clair's chalk: a clear teal that passes 4.5:1 on the ground
HEX = {
    # light chrome
    'EEF6F1': ok(.966, .016, NH), '221F3A': INK, '5B5775': ok(.46, .03, NH), '6F6B8A': ok(.48, .03, NH),
    'B4B0CC': ok(.76, .02, NH), 'C9C6DC': ok(.84, .015, NH), 'E3EFE8': ok(.92, .014, NH), 'EAF3EE': ok(.94, .012, NH),
    'F6FAF8': ok(.98, .006, NH), 'C9F0DE': ok(.9, .045, 180),
    # accents (were blue)
    '2F56B0': ACCENT, '263F8C': ok(.4, .09, 190),
    # dark chrome (Denim dusk)
    '121A2C': ok(.19, .024, NH), 'F3F1FB': INK_D, 'BBB7D8': ok(.78, .025, NH), '24213A': CARD_D, '1B1930': ok(.2, .02, NH),
}
for name, olds in OLD_DYES.items():
    d = dye(name)
    for old, new in zip(olds, (d['fill'], d['deep'], d['dfill'], d['ddeep'])):
        HEX.setdefault(old, new)

RGBA = {'34,31,58': rgb(INK), '34, 31, 58': rgb(INK).replace(',', ', '), '243,241,251': rgb(INK_D), '30,32,54': rgb(CARD_D),
        '53,87,166': rgb(ACCENT), '30,25,70': '10,40,34', '20,30,40': '10,40,34'}
GRADIENT = re.compile(r'\s*background-image:\s*radial-gradient\([^;"]*?;')


def mint(t):
    t = GRADIENT.sub('', t)  # the ground is plain now
    t = re.sub(r'#([0-9A-Fa-f]{6})\b', lambda m: HEX.get(m.group(1).upper(), '#' + m.group(1)).replace('##', '#'), t)
    for old, new in RGBA.items():
        t = t.replace('rgba(%s,' % old, 'rgba(%s,' % new)
    return t


HEX = {k: (v if v.startswith('#') else '#' + v) for k, v in HEX.items()}

if __name__ == '__main__':
    for name in sys.argv[2:]:
        p = os.path.join(sys.argv[1], name if name.endswith('.html') else name + '.dc.html')
        open(p, 'w').write(mint(open(p).read()))
    print('mint', len(sys.argv) - 2)


# ---------------------------------------------------------------- the palette board (SqMint)
APPS = [('Budget', 'sage'), ('Groceries', 'apricot'), ('Calendar', 'chambray'), ('To-dos', 'butter'), ('Workout', 'blush'),
        ('Classes', 'lavender'), ('Subscriptions', 'sea glass'), ('Notes', 'linen'), ('Calories', 'pear')]


def board():
    """1280 x 640: the Mint palette in light and dark, every app's patch and the chrome tokens."""
    def side(dark):
        g, ink, sec = (HEX['121A2C'], INK_D, HEX['BBB7D8']) if dark else (HEX['EEF6F1'], INK, HEX['5B5775'])
        card = CARD_D if dark else ok(.995, .003, NH)
        cta, cta_ink = (INK_D, HEX['1B1930']) if dark else (INK, ok(.985, .004, NH))
        patches = ''.join(
            '<span style="display: flex; flex-direction: column; justify-content: space-between; gap: 8px; min-height: 92px; padding: 12px; border-radius: 18px; '
            'background: %s; color: %s; outline: 1.5px dashed %sBF; outline-offset: -5px;"><b style="font-size: 13px; font-weight: 600;">%s</b>'
            '<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-size: 12px; font-weight: 700; color: %s;">%s</span>'
            '<span style="font-size: 11px; color: %s;">%s · %s</span></span></span>'
            % ((d := dye(dn))['dfill' if dark else 'fill'], ink, d['ddeep' if dark else 'deep'], app, d['ddeep' if dark else 'deep'], dn, ink,
               d['dfill' if dark else 'fill'], d['ddeep' if dark else 'deep'])
            for app, dn in APPS)
        chip = lambda label, val: ('<span style="display: flex; align-items: center; gap: 8px; font-size: 12px;"><span style="width: 22px; height: 22px; border-radius: 7px; '
                                   'background: %s; box-shadow: inset 0 0 0 1px %s33;"></span><span><b style="font-weight: 600;">%s</b> %s</span></span>' % (val, ink, label, val))
        chrome = ''.join(chip(a, b) for a, b in [('Ground', g), ('Card', card), ('Ink', ink), ('Secondary', sec), ('Button', cta), ('Accent', ok(.84, .09, 185) if dark else ACCENT)])
        return ('<div style="display: flex; flex-direction: column; gap: 16px; padding: 24px; border-radius: 28px; background: %s; color: %s;">'
                '<span style="display: flex; justify-content: space-between; align-items: center; gap: 12px;"><h2 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">%s</h2>'
                '<span style="min-height: 36px; padding: 0 16px; display: flex; align-items: center; border-radius: 99px; background: %s; color: %s; font-size: 13px; font-weight: 700;">Add to 3 apps</span></span>'
                '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px;">%s</div>'
                '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 12px; color: %s;">%s</div></div>'
                % (g, ink, 'Dark' if dark else 'Light', cta, cta_ink, patches, sec, chrome))
    inner = ('<div style="width: 1280px; height: 640px; box-sizing: border-box; padding: 28px; background: #E4E8E6; color: %s; font-family: \'Figtree\', system-ui, sans-serif; '
             'font-variant-numeric: tabular-nums; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px;">%s%s</div>' % (INK, side(False), side(True)))
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>Mint palette</title>\n<script src="./support.js"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400..800&amp;display=swap">\n<style>body{margin:0}</style>\n</helmet>\n%s\n</x-dc>\n'
            '<script type="text/x-dc" data-dc-script data-props=\'{"$preview":{"width":1280,"height":640}}\'>\nclass Component extends DCLogic { renderVals() { return {}; } }\n</script>\n</body>\n</html>\n' % inner)
