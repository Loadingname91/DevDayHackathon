"""Cross-stitch Chart look: example boards (chart key + Home light + Home dark).

Usage: python gen_xstitch.py <canvas dir>
"""
import os, sys

OUT = sys.argv[1]

# 9x9 cross-stitch motifs, one per app ('#' = a stitched cell)
MOTIF = {
    'Budget': ['.........', '.#######.', '.#.....#.', '.#...####', '.#...#..#', '.#...####', '.#.....#.', '.#######.', '.........'],
    'Groceries': ['##.......', '.#.......', '.#######.', '.#.....#.', '.#.....#.', '.######..', '.........', '..#...#..', '.........'],
    'Calendar': ['..#...#..', '.#######.', '.#######.', '.#.....#.', '.#.#.#.#.', '.#.....#.', '.#.#.#.#.', '.#######.', '.........'],
    'To-dos': ['.........', '........#', '.......#.', '......#..', '#....#...', '.#..#....', '..##.....', '...#.....', '.........'],
    'Workout': ['.........', '.........', '##.....##', '##.....##', '#########', '##.....##', '##.....##', '.........', '.........'],
    'Classes': ['.........', '.###.###.', '.#..#..#.', '.#..#..#.', '.#..#..#.', '.#..#..#.', '.###.###.', '....#....', '.........'],
    'Subscriptions': ['.........', '..####.#.', '.#....##.', '.#...###.', '.#.....#.', '.###...#.', '.##....#.', '.#.####..', '.........'],
}
# app -> (DMC number, floss name, light hex, dark hex)
FLOSS = {
    'Budget': ('3812', 'Sea green', '#1F8A70', '#3FC29F'),
    'Groceries': ('702', 'Kelly green', '#3F8F2F', '#6BC458'),
    'Calendar': ('798', 'Delft blue', '#2F5FB3', '#6E97E6'),
    'To-dos': ('3853', 'Autumn gold', '#D2711F', '#F09A4E'),
    'Workout': ('3837', 'Lavender', '#6C3B8C', '#A877CC'),
    'Classes': ('3845', 'Turquoise', '#0E8C9C', '#3EC3D3'),
    'Subscriptions': ('3607', 'Plum', '#A3307E', '#D865B0'),
}
THEME = {
    'light': dict(ground='#F5F6F3', grid='rgba(30,35,43,0.07)', card='#FFFFFF', line='#DADDE2', ink='#1E232B', sec='#535B69', btn='#1E232B', btnInk='#FFFFFF', gold='#E5A800', key=2),
    'dark': dict(ground='#13151A', grid='rgba(255,255,255,0.055)', card='#1C1F26', line='#2E333D', ink='#ECEEF1', sec='#A6ADB9', btn='#ECEEF1', btnInk='#13151A', gold='#F5C518', key=3),
}
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Azeret+Mono:wght@500&amp;family=Familjen+Grotesk:wght@400;500;600;700&amp;display=swap">'
SANS = "font-family: 'Familjen Grotesk', system-ui, sans-serif;"
MONO = "font-family: 'Azeret Mono', ui-monospace, monospace; font-weight: 500;"


def motif(app, size, theme):
    rows, col = MOTIF[app], FLOSS[app][THEME[theme]['key']]
    s = size / 9.0
    lines = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '#':
                x, y, p = c * s, r * s, s * 0.2
                lines.append('<path d="M%.1f %.1fL%.1f %.1fM%.1f %.1fL%.1f %.1f"></path>' % (x + p, y + p, x + s - p, y + s - p, x + s - p, y + p, x + p, y + s - p))
    return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" aria-hidden="true" style="flex: none;">%s</svg>'
            % (size, size, size, size, col, max(1.2, s * 0.32), ''.join(lines)))


def spool(color):
    return ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">'
            '<path d="M6 3h12M6 21h12M8 3v18M16 3v18M8 8l8 2M8 12l8 2M8 16l8 2"></path></svg>' % color)


def aida(t):
    return ('background-color: %s; background-image: linear-gradient(%s 1px, transparent 1px), linear-gradient(90deg, %s 1px, transparent 1px); background-size: 9px 9px;'
            % (t['ground'], t['grid'], t['grid']))


def page(title, w, h, inner, script, interactive_props='{}'):
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%s</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
%s
<style>
body{margin:0}
a{color:inherit;text-decoration:none}
button{font:inherit;cursor:pointer}
::selection{background:#F5C518;color:#1E232B}
</style>
</helmet>
%s
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":%d,"height":%d}}'>
%s
</script>
</body>
</html>
''' % (title, FONTS, inner, w, h, script)


def home(theme, done_default):
    t = THEME[theme]
    def face(app, before, after, changed):
        f = FLOSS[app]
        notch = ('<sc-if value="{{ done }}" hint-placeholder-val="{{ %s }}"><span style="width: 8px; height: 8px; border-radius: 50%%; background: %s; position: absolute; top: 8px; right: 8px;" aria-label="just changed"></span></sc-if>' % ('true' if done_default else 'false', t['gold'])) if changed else ''
        val = ('{{ f%s }}' % app.replace('-', '')) if changed else before
        return ('<a href="#" style="position: relative; display: flex; align-items: center; gap: 12px; padding: 10px 12px; min-height: 64px; box-sizing: border-box; background: %s; border: 1px solid %s; border-radius: 10px; color: %s;">'
                '%s<span style="display: flex; flex-direction: column; gap: 2px;"><span style="%s font-size: 14px; font-weight: 600;">%s</span>'
                '<span style="%s font-size: 15px; font-variant-numeric: tabular-nums; color: %s;">%s</span></span>%s</a>'
                % (t['card'], t['line'], t['ink'], motif(app, 27, theme), SANS, app, SANS, t['sec'], val, notch))
    apps = (face('Budget', '$412 left', '$376 left', True) + face('Groceries', '12 to buy', '4 to buy', True) +
            face('Calendar', '3 today', '4 today', True) + face('To-dos', '3 today', '', False) +
            face('Workout', 'Pull day 6 pm', '', False) + face('Classes', '2 due', '', False))

    def line(app, text):
        return ('<span style="display: flex; align-items: center; gap: 10px; %s font-size: 15px; color: %s;">%s<span><b style="font-weight: 600;">%s</b> %s</span></span>'
                % (SANS, t['ink'], motif(app, 18, theme), app, text))

    def nxt(time, app, text):
        return ('<span style="display: flex; align-items: center; gap: 12px; min-height: 44px; border-top: 1px solid %s;"><span style="%s font-size: 13px; color: %s; width: 58px;">%s</span>%s<span style="%s font-size: 15px; color: %s;">%s</span></span>'
                % (t['line'], MONO, t['sec'], time, motif(app, 18, theme), SANS, t['ink'], text))

    def pin(app):
        return ('<a href="#" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; min-height: 56px; color: %s; %s font-size: 12px; font-weight: 500;">%s%s</a>'
                % (t['ink'], SANS, motif(app, 22, theme), app))

    card = '''<section style="display: flex; flex-direction: column; gap: 12px; padding: 16px; border-radius: 12px; background: %(card)s; border: 2px {{ edgeStyle }} {{ cardEdge }};">
  <span style="display: flex; justify-content: space-between; align-items: baseline; %(sans)s font-size: 13px; color: %(sec)s;"><span>Corner Market receipt · 5:41 pm</span><span style="%(mono)s font-size: 12px;">$35.83</span></span>
  %(l1)s
  %(l2)s
  %(l3)s
  <sc-if value="{{ notDone }}" hint-placeholder-val="{{ %(nd)s }}">
    <span style="display: flex; gap: 8px; align-items: center;">
      <button onClick="{{ confirm }}" style="flex: 1; min-height: 48px; border: 0; border-radius: 10px; background: %(btn)s; color: %(btnInk)s; %(sans)s font-size: 16px; font-weight: 600;">Add to 3 apps</button>
      <a href="#" style="min-height: 48px; padding: 0 14px; display: flex; align-items: center; %(sans)s font-size: 15px; color: %(ink)s;">Review items</a>
    </span>
  </sc-if>
  <sc-if value="{{ done }}" hint-placeholder-val="{{ %(d)s }}">
    <span style="display: flex; justify-content: space-between; align-items: center; min-height: 48px; %(sans)s font-size: 15px; color: %(ink)s;"><span>Stitched into 3 apps</span><button onClick="{{ undo }}" style="min-height: 44px; padding: 0 12px; border: 1px solid %(line)s; border-radius: 10px; background: transparent; color: %(ink)s; font-size: 15px;">Undo</button></span>
  </sc-if>
</section>''' % dict(t, sans=SANS, mono=MONO, l1=line('Budget', '{{ budgetLine }}'), l2=line('Groceries', '8 bought from Weekly shop'),
                     l3=line('Calendar', 'Grocery trip, today'), nd='false' if done_default else 'true', d='true' if done_default else 'false')

    inner = '''<div style="width: 390px; height: 844px; box-sizing: border-box; position: relative; overflow: hidden; %(aida)s color: %(ink)s; %(sans)s">
<div style="height: 760px; overflow-y: auto; box-sizing: border-box; padding: 20px 16px 24px; display: flex; flex-direction: column; gap: 20px;">
  <span style="display: flex; justify-content: space-between; align-items: center;"><span style="%(mono)s font-size: 12px; color: %(sec)s;">FRI 20 NOV · 5:45 PM</span><a href="#" aria-label="You and settings" style="width: 36px; height: 36px; border-radius: 50%%; border: 1px solid %(line)s; background: %(cardbg)s; display: grid; place-items: center; font-size: 14px; font-weight: 600;">S</a></span>
  <h1 style="margin: 0; font-size: 30px; line-height: 1.12; font-weight: 700; letter-spacing: -0.02em;">{{ status }}</h1>
  %(card)s
  <section style="display: flex; flex-direction: column;">
    <h2 style="margin: 0 0 6px; font-size: 15px; font-weight: 600;">Next up</h2>
    %(n1)s%(n2)s%(n3)s
  </section>
  <section style="display: flex; flex-direction: column; gap: 10px;">
    <h2 style="margin: 0; font-size: 15px; font-weight: 600;">Your apps</h2>
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">%(apps)s</div>
  </section>
</div>
<nav aria-label="Pinned apps" style="position: absolute; left: 0; right: 0; bottom: 0; height: 84px; box-sizing: border-box; padding: 6px 8px 18px; display: flex; align-items: stretch; background: %(cardbg)s; border-top: 1px solid %(line)s;">
  %(pins)s
  <a href="#" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; margin: 2px; border-radius: 10px; background: %(btn)s; color: %(btnInk)s; font-size: 12px; font-weight: 600;">%(spool)sClair</a>
</nav>
</div>''' % dict(aida=aida(t), ink=t['ink'], sans=SANS, mono=MONO, sec=t['sec'], line=t['line'], card=card, cardbg=t['card'],
                 n1=nxt('6:00 PM', 'Workout', 'Pull day'), n2=nxt('9:00 PM', 'To-dos', 'Return library books'), n3=nxt('SUN', 'Subscriptions', 'Spotify renews, $11.99'),
                 apps=apps, pins=''.join(pin(a) for a in ['Budget', 'Groceries', 'Calendar', 'Workout']), btn=t['btn'], btnInk=t['btnInk'], spool=spool(t['btnInk']))
    script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: %s }; }
  renderVals() {
    var d = this.state.done, self = this;
    return {
      done: d, notDone: !d,
      status: d ? '$376 left this month. Pull day at 6 pm.' : '$412 left this month. Pull day at 6 pm.',
      budgetLine: d ? '$35.83 spent, $376 left' : '$412 → $376',
      fBudget: d ? '$376 left' : '$412 left', fGroceries: d ? '4 to buy' : '12 to buy', fCalendar: d ? '4 today' : '3 today',
      edgeStyle: d ? 'solid' : 'dashed',
      cardEdge: d ? '%s' : '%s',
      confirm: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); }
    };
  }
}''' % ('true' if done_default else 'false', t['line'], t['ink'])
    return inner, script


def key():
    t = THEME['light']
    rows = ''.join(
        '<span style="display: grid; grid-template-columns: 44px 1fr 88px 64px 120px; align-items: center; gap: 12px; min-height: 52px; border-top: 1px solid %s;">%s<span style="%s font-size: 16px; font-weight: 600;">%s</span>'
        '<span style="display: flex; gap: 4px;"><span style="width: 36px; height: 24px; border-radius: 4px; background: %s;"></span><span style="width: 36px; height: 24px; border-radius: 4px; background: %s;"></span></span>'
        '<span style="%s font-size: 13px;">DMC %s</span><span style="%s font-size: 14px; color: %s;">%s</span></span>'
        % ('transparent' if i == 0 else t['line'], motif(a, 32, 'light'), SANS, a, f[2], f[3], MONO, f[0], SANS, t['sec'], f[1]) for i, (a, f) in enumerate(FLOSS.items()))
    sw = lambda c, label, ink: '<span style="display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: %s;"><span style="width: 100%%; height: 44px; border-radius: 8px; background: %s; border: 1px solid %s;"></span>%s</span>' % (ink, c, t['line'], label)
    inner = '''<div style="width: 900px; height: 844px; box-sizing: border-box; padding: 48px; %s color: %s; %s display: flex; flex-direction: column; gap: 28px;">
  <h1 style="margin: 0; font-size: 44px; line-height: 1.05; font-weight: 700; letter-spacing: -0.025em;">Chart key</h1>
  <p style="margin: -12px 0 0; font-size: 17px; line-height: 1.5; color: %s; max-width: 640px;">Every app is one floss colour and one stitched motif, used the same way on its patch, its pin, its rows and the thread a change pulls. Light mode is white aida, dark mode is black aida.</p>
  <section style="display: flex; flex-direction: column; background: %s; border: 1px solid %s; border-radius: 12px; padding: 4px 20px;">%s</section>
  <section style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px;">%s%s%s%s%s%s</section>
  <p style="margin: 0; font-size: 15px; color: %s;">Familjen Grotesk for everything you read; Azeret Mono only for times, amounts on receipts and floss numbers. No red: an overspend is cross-hatched, never coloured.</p>
</div>''' % (aida(t), t['ink'], SANS, t['sec'], t['card'], t['line'], rows,
             sw(t['ground'], 'Aida white', t['ink']), sw(t['card'], 'Card', t['ink']), sw(t['ink'], 'Ink', t['ink']),
             sw(t['gold'], 'Just changed', t['ink']), sw(THEME['dark']['ground'], 'Black aida', t['ink']), sw(THEME['dark']['card'], 'Dark card', t['ink']), t['sec'])
    return inner, 'class Component extends DCLogic {\n  renderVals() { return {}; }\n}'


k_inner, k_script = key()
open(os.path.join(OUT, 'XsKey.dc.html'), 'w').write(page('Chart key', 900, 844, k_inner, k_script))
for theme, done in [('light', False), ('dark', True)]:
    inner, script = home(theme, done)
    open(os.path.join(OUT, 'XsHome%s.dc.html' % theme.title()), 'w').write(page('Home, %s' % theme, 390, 844, inner, script))
print('ok')
