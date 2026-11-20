"""Soft Quilt: the "You > Appearance" board, where people pick Light / Dark / Match phone and a ground per mode.

Decided Nov 19: grounds are user-pickable and free on every plan. Defaults: light = Mint air, dark = Denim dusk.
Writes SqAppearance.dc.html only. It does not touch canvas.json; register the board separately (390 x 844, interactive).

Tokens (GROUNDS, MODE, APP, ICON, STYLE, page(), icon(), cond(), staticize()) come from gen_soft.py: this file
execs the part of its source above the line that starts with "BOARDS = [", so none of its file writing runs.

Usage: python gen_soft_themes.py <canvas dir> [<static preview dir>]
"""
import json, os, sys

OUT = sys.argv[1]
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None


def load_soft():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gen_soft.py')).read()
    cut = src.index('\nBOARDS = [')
    ns = {'__name__': 'gen_soft_tokens'}
    saved = sys.argv
    sys.argv = ['gen_soft.py', OUT]  # gen_soft reads sys.argv[1] at the top; no preview dir
    try:
        exec(compile(src[:cut], 'gen_soft.py', 'exec'), ns)
    finally:
        sys.argv = saved
    return ns


S = load_soft()
GROUNDS, MODE, APP, ICON = S['GROUNDS'], S['MODE'], S['APP'], S['ICON']
icon, cond, page, staticize, app_col = S['icon'], S['cond'], S['page'], S['staticize'], S['app_col']
ICON['check'] = 'M5 12.5l4.5 4.5L19 7'  # same mark as To-dos, a little rounder at this size

# short id used in hole names -> ground name
IDS = [('Lilac', 'Lilac haze'), ('Peach', 'Peach morning'), ('Mint', 'Mint air'), ('Muslin', 'Plain muslin'),
       ('Midnight', 'Midnight'), ('Denim', 'Denim dusk')]
DEFAULT = dict(mode='match', light='Mint', dark='Denim')
SAMPLE = [('Budget', '$412', 'left'), ('Groceries', '12', 'to buy'), ('Classes', '2', 'due')]
MODE_KEYS = ['ink', 'sec', 'card', 'cardLine', 'shadow', 'cta', 'ctaInk', 'thread']
MODES = [('Light', 'light', 'Light'), ('Dark', 'dark', 'Dark'), ('Match', 'match', 'Match phone')]
MODE_NOTE = dict(match='Follows your phone. Showing light now.', light='Always light.', dark='Always dark.')


def ground_image(name):
    b = GROUNDS[name]['blobs']
    return ', '.join('radial-gradient(75%% 46%% at %s, %s 0%%, transparent 72%%)' % x for x in b) if b else 'none'


def tokens():
    """Everything renderVals() needs, as plain data."""
    return dict(
        grounds={i: dict(mode=GROUNDS[n]['mode'], base=GROUNDS[n]['base'], image=ground_image(n)) for i, n in IDS},
        mode={k: {t: MODE[k][t] for t in MODE_KEYS} for k in MODE},
        app={a: dict(light=list(app_col(a, 'light')), dark=list(app_col(a, 'dark'))) for a, _f, _u in SAMPLE},
        note=MODE_NOTE)


def vals(st):
    """Python mirror of renderVals(), for the static preview."""
    t = tokens()
    shown = 'dark' if st['mode'] == 'dark' else 'light'
    g = t['grounds'][st[shown]]
    m = t['mode'][shown]
    v = dict(m, groundBase=g['base'], groundImage=g['image'], modeNote=t['note'][st['mode']])
    for a, _f, _u in SAMPLE:
        fill, deep = t['app'][a][shown]
        v['fill' + a], v['deep' + a], v['edge' + a] = fill, deep, deep + '8C'
    for i, _n in IDS:
        on = st[t['grounds'][i]['mode']] == i
        v['sel' + i], v['ring' + i], v['pressed' + i] = on, (m['ink'] if on else 'transparent'), ('true' if on else 'false')
    for key, mid, _l in MODES:
        on = st['mode'] == mid
        v['is' + key], v['bg' + key], v['ink' + key] = on, (m['cta'] if on else 'transparent'), (m['ctaInk'] if on else m['ink'])
        v['pressedMode' + key] = 'true' if on else 'false'
    return v


def script():
    return '''class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = %(state)s;
    this.T = %(tokens)s;
  }
  renderVals() {
    var s = this.state, T = this.T, self = this;
    var shown = s.mode === 'dark' ? 'dark' : 'light';  // Match phone shows light on this board
    var g = T.grounds[s[shown]], m = T.mode[shown];
    var v = { groundBase: g.base, groundImage: g.image, modeNote: T.note[s.mode] };
    Object.keys(m).forEach(function (k) { v[k] = m[k]; });
    Object.keys(T.app).forEach(function (a) {
      var c = T.app[a][shown];
      v['fill' + a] = c[0]; v['deep' + a] = c[1]; v['edge' + a] = c[1] + '8C';
    });
    Object.keys(T.grounds).forEach(function (id) {
      var gm = T.grounds[id].mode, on = s[gm] === id;
      v['sel' + id] = on;
      v['ring' + id] = on ? m.ink : 'transparent';
      v['pressed' + id] = on ? 'true' : 'false';
      v['pick' + id] = function () { var n = {}; n[gm] = id; self.setState(n); };
    });
    [['Light', 'light'], ['Dark', 'dark'], ['Match', 'match']].forEach(function (p) {
      var on = s.mode === p[1];
      v['is' + p[0]] = on;
      v['bg' + p[0]] = on ? m.cta : 'transparent';
      v['ink' + p[0]] = on ? m.ctaInk : m.ink;
      v['pressedMode' + p[0]] = on ? 'true' : 'false';
      v['set' + p[0]] = function () { self.setState({ mode: p[1] }); };
    });
    return v;
  }
}''' % dict(state=json.dumps(DEFAULT), tokens=json.dumps(tokens(), indent=1))


def hicon(name, size, hole, sw=2):
    """An icon whose stroke is a hole (follows the mode)."""
    return icon(name, size, '{{ %s }}' % hole, sw)


def swatch(i, name):
    g = GROUNDS[name]
    gm = g['mode']
    m = MODE[gm]

    def patch(app):
        fill, deep = app_col(app, gm)
        return '<span style="width: 26px; height: 26px; border-radius: 8px; background: %s; outline: 1.5px dashed %s; outline-offset: -4px;"></span>' % (fill, deep + '8C')
    check = cond('sel' + i, DEFAULT[gm] == i,
                 '<span style="position: absolute; top: 9px; right: 9px; width: 24px; height: 24px; border-radius: 50%%; background: %s; display: grid; place-items: center;">%s</span>'
                 % (m['cta'], icon('check', 15, m['ctaInk'], 2.6)))
    return ('<button onClick="{{ pick%(i)s }}" aria-pressed="{{ pressed%(i)s }}" style="display: block; padding: 3px; border: 2.5px solid {{ ring%(i)s }}; border-radius: 24px; background: transparent; text-align: left;">'
            '<span style="position: relative; display: flex; flex-direction: column; justify-content: space-between; height: 80px; padding: 10px 11px 10px; border-radius: 17px; background-color: %(base)s; background-image: %(img)s; color: %(ink)s; box-shadow: inset 0 0 0 1px %(line)s;">'
            '<span style="display: flex; gap: 5px;">%(p1)s%(p2)s</span>'
            '<span style="font-size: 14px; font-weight: 700; white-space: nowrap;">%(name)s</span>%(check)s</span></button>'
            % dict(i=i, base=g['base'], img=ground_image(name), ink=m['ink'],
                   line='rgba(34,31,58,0.12)' if gm == 'light' else 'rgba(255,255,255,0.16)',
                   p1=patch('Budget'), p2=patch('Groceries'), name=name, check=check))


def mode_btn(key, label):
    return ('<button onClick="{{ set%(k)s }}" aria-pressed="{{ pressedMode%(k)s }}" style="flex: %(fx)s; min-height: 46px; padding: 0 4px; display: flex; align-items: center; justify-content: center; gap: 4px; border: 0; border-radius: 99px; background: {{ bg%(k)s }}; color: {{ ink%(k)s }}; font-size: 14px; font-weight: 700; white-space: nowrap;">%(c)s%(l)s</button>'
            % dict(k=key, l=label, fx='1.4' if key == 'Match' else '1', c=cond('is' + key, DEFAULT['mode'] == key.lower(), hicon('check', 15, 'ink' + key, 2.6))))


def mini(app, face, unit):
    return ('<span style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; padding: 11px 12px; border-radius: 18px; background: {{ fill%(a)s }}; outline: 1.5px dashed {{ edge%(a)s }}; outline-offset: -5px;">%(ic)s'
            '<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-size: 13px; font-weight: 600;">%(a)s</span><span style="font-size: 18px; font-weight: 700; letter-spacing: -0.02em; white-space: nowrap;">%(f)s <span style="font-size: 12px; font-weight: 500;">%(u)s</span></span></span></span>'
            % dict(a=app, f=face, u=unit, ic=hicon(app, 18, 'deep' + app)))


def appearance():
    h2 = 'margin: 0; font-size: 15px; font-weight: 700;'
    hint = 'font-size: 13px; font-weight: 500; color: {{ sec }};'
    grid = 'display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px;'
    light = ''.join(swatch(i, n) for i, n in IDS if GROUNDS[n]['mode'] == 'light')
    dark = ''.join(swatch(i, n) for i, n in IDS if GROUNDS[n]['mode'] == 'dark')
    return '''<div class="sq" style="width: 390px; height: 844px; position: relative; overflow: hidden; background-color: {{ groundBase }}; background-image: {{ groundImage }}; color: {{ ink }};">
<div class="scroll" style="height: 844px; overflow-y: auto; padding: 16px 16px 24px; display: flex; flex-direction: column; gap: 20px;">
  <header style="display: flex; align-items: center; gap: 12px;">
    <a href="#" aria-label="Back to You" style="width: 44px; height: 44px; border-radius: 50%%; background: {{ card }}; border: 1px solid {{ cardLine }}; display: grid; place-items: center; flex: none;">%(back)s</a>
    <h1 style="margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.02em;">Appearance</h1>
  </header>
  <section aria-label="How Quilt looks now" style="display: flex; flex-direction: column; gap: 8px;">
    <div style="padding: 13px 16px; border-radius: 20px; background: {{ card }}; border: 1px solid {{ cardLine }}; box-shadow: {{ shadow }}; font-size: 18px; font-weight: 700; letter-spacing: -0.015em;">$412 left this month.</div>
    <div style="display: flex; gap: 8px;">%(minis)s</div>
  </section>
  <section style="display: flex; flex-direction: column; gap: 7px;">
    <h2 style="%(h2)s">Light or dark</h2>
    <div style="display: flex; gap: 4px; padding: 4px; border-radius: 99px; background: {{ card }}; border: 1px solid {{ cardLine }};">%(modes)s</div>
    <span style="%(hint)s">{{ modeNote }}</span>
  </section>
  <section style="display: flex; flex-direction: column; gap: 7px;">
    <span style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;"><h2 style="%(h2)s">Light background</h2><span style="%(hint)s">Used when Quilt is light</span></span>
    <div style="%(grid)s">%(light)s</div>
  </section>
  <section style="display: flex; flex-direction: column; gap: 7px;">
    <span style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;"><h2 style="%(h2)s">Dark background</h2><span style="%(hint)s">Used when Quilt is dark</span></span>
    <div style="%(grid)s">%(dark)s</div>
  </section>
  <p style="margin: 0; font-size: 14px; line-height: 1.4; color: {{ sec }};">Free on every plan. Your choice applies on every device you sign in on.</p>
</div>
</div>''' % dict(back=hicon('back', 20, 'ink'), minis=''.join(mini(*s) for s in SAMPLE), h2=h2, hint=hint, grid=grid,
                 modes=''.join(mode_btn(k, l) for k, _m, l in MODES), light=light, dark=dark)


NAME, TITLE, W, H = 'SqAppearance', 'You, Appearance', 390, 844
inner = appearance()
open(os.path.join(OUT, NAME + '.dc.html'), 'w').write(page(TITLE, W, H, inner, script()))

if PREVIEW:
    os.makedirs(PREVIEW, exist_ok=True)
    states = [('', DEFAULT), ('-dark', dict(DEFAULT, mode='dark')), ('-peach', dict(DEFAULT, mode='light', light='Peach')),
              ('-midnight', dict(DEFAULT, mode='dark', dark='Midnight')), ('-muslin', dict(DEFAULT, mode='light', light='Muslin'))]
    for suffix, st in states:
        open(os.path.join(PREVIEW, NAME + suffix + '.html'), 'w').write(
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title><link rel="stylesheet" href="%s"><style>%s</style></head><body>%s</body></html>'
            % (TITLE, S['FONTS'].replace('&amp;', '&'), S['STYLE'], staticize(inner, vals(st))))
print('ok', NAME, W, H)
