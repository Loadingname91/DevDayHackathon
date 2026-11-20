"""Soft Quilt look option: pastel patches on a soft gradient ground (after the Lumo reference),
kept in Quilt's voice: stitched patch edges, basted card, spool for Clair, no red.

Decided Nov 19: light = Mint air, dark = Denim dusk. Colours replaced Nov 20 by Mint (mint_theme.py, ADR-013).
Boards: Home light (before), Home dark (after), Clair builds Car light and dark, Grounds (the 6 tried).

Usage: python gen_soft.py <canvas dir> [<static preview dir>]
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mint_theme import mint  # Nov 20: boards are written in the Mint colours (ADR-013); SqGrounds stays a record

OUT = sys.argv[1]
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None

FONTS = 'https://fonts.googleapis.com/css2?family=Figtree:wght@400..800&amp;display=swap'

ICON = {
    'Budget': 'M3 7h15a3 3 0 0 1 3 3v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 7l2-3h12M16 13h2',
    'Groceries': 'M3 4h2l2 11h11l2-8H6M9 20h.01M17 20h.01',
    'Calendar': 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
    'To-dos': 'M4 12l5 5L20 6',
    'Workout': 'M3 9v6M6 7v10M18 7v10M21 9v6M6 12h12',
    'Classes': 'M4 5h6a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H4zM20 5h-6a2 2 0 0 0-2 2v12a2 2 0 0 1 2-2h6z',
    'Subscriptions': 'M4 12a8 8 0 0 1 14-5l2 2M20 12a8 8 0 0 1-14 5l-2-2M20 4v5h-5M4 20v-5h5',
    'Notes': 'M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h5',
    'Car': 'M5 11l1.6-4.6A2 2 0 0 1 8.5 5h7a2 2 0 0 1 1.9 1.4L19 11M3 11h18v6H3zM7 17v2M17 17v2M7 14h.01M17 14h.01',
    'spool': 'M6 3h12M6 21h12M8 3v18M16 3v18M8 8l8 2M8 12l8 2M8 16l8 2',
    'arrow': 'M5 12h14M13 6l6 6-6 6',
    'back': 'M15 5l-7 7 7 7',
    'camera': 'M4 8h3l2-3h6l2 3h3v11H4zM12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z',
    'mic': 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3',
}

# app: (light fill, light deep, dark fill, dark bright)
APP = {
    'Budget': ('#B5EBD0', '#1C6F52', '#23604D', '#9BE8C6'),
    'Groceries': ('#FFC8AC', '#A8481B', '#74402A', '#FFC2A3'),
    'Calendar': ('#BDD5FF', '#2B58B8', '#2C4A8F', '#AFC9FF'),
    'To-dos': ('#FFE48F', '#7D5B00', '#655216', '#FFE082'),
    'Workout': ('#FFBFD4', '#A52E62', '#742E52', '#FFB3CF'),
    'Classes': ('#CFC3FF', '#5340BE', '#463D9C', '#C9BEFF'),
    'Subscriptions': ('#B1E5EE', '#146E7F', '#1F5E6B', '#9FE3EE'),
    'Notes': ('#EAD8BD', '#75552A', '#594A34', '#E8D3B3'),
    'Car': ('#CDE2AC', '#4A661B', '#44591F', '#CBE3A2'),
}

GROUNDS = {
    'Lilac haze': dict(mode='light', base='#F3EEF8', blobs=[('100% 0%', '#D9CFFF'), ('0% 20%', '#FFE1D2'), ('100% 58%', '#CFF1E4'), ('0% 100%', '#DCE6FF')],
                       note='The reference, warmed: lilac and mint with a peach corner.'),
    'Peach morning': dict(mode='light', base='#FBF1EA', blobs=[('100% 0%', '#FFD9C4'), ('0% 22%', '#FFEFC2'), ('100% 60%', '#F6D6E6'), ('0% 100%', '#E3DAFF')],
                          note='Warmest. Closest to "hand-made, not a cold system".'),
    'Mint air': dict(mode='light', base='#EEF6F1', blobs=[('100% 0%', '#C9F0DE'), ('0% 22%', '#DDEBFF'), ('100% 60%', '#FFF0C4'), ('0% 100%', '#CFEFF0')],
                     note='Chosen for light mode. Fresh and calm.'),
    'Plain muslin': dict(mode='light', base='#F6F1EA', blobs=[],
                         note='No gradient at all. The plain look, done well; best in daylight.'),
    'Midnight': dict(mode='dark', base='#171529', blobs=[('100% 0%', '#3A2F7A'), ('0% 22%', '#532B45'), ('100% 60%', '#1D4A4D'), ('0% 100%', '#27336B')],
                     note='Dark. The patches glow; the ground stays quiet.'),
    'Denim dusk': dict(mode='dark', base='#121A2C', blobs=[('100% 0%', '#27407F'), ('0% 22%', '#2B2F66'), ('100% 60%', '#17464A'), ('0% 100%', '#3B2A55')],
                       note='Chosen for dark mode. Keeps the old denim as a ground.'),
}

MODE = {
    'light': dict(ink='#221F3A', sec='#5B5775', card='rgba(255,255,255,0.68)', cardLine='rgba(255,255,255,0.95)', solid='#FFFFFF',
                  shadow='0 12px 26px -14px rgba(20,30,40,0.42)', cta='#221F3A', ctaInk='#FFFFFF', thread='rgba(34,31,58,0.38)', bar='rgba(255,255,255,0.72)', barShadow='0 14px 30px -12px rgba(30,25,70,0.45)'),
    'dark': dict(ink='#F3F1FB', sec='#BBB7D8', card='rgba(255,255,255,0.08)', cardLine='rgba(255,255,255,0.16)', solid='#24213A',
                 shadow='0 12px 28px -14px rgba(0,0,0,0.6)', cta='#F3F1FB', ctaInk='#1B1930', thread='rgba(243,241,251,0.42)', bar='rgba(30,32,54,0.9)', barShadow='0 14px 30px -12px rgba(0,0,0,0.6)'),
}


def _rgba(hex6, a):
    h = hex6.lstrip('#')
    return 'rgba(%d,%d,%d,%s)' % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ground_css(name):
    # the ground is kept faint (blobs at about half strength) so the app patches carry the colour
    g = GROUNDS[name]
    a = '0.5' if g['mode'] == 'light' else '0.55'
    imgs = ', '.join('radial-gradient(75%% 46%% at %s, %s 0%%, transparent 72%%)' % (pos, _rgba(col, a)) for pos, col in g['blobs'])
    return 'background-color: %s;%s' % (g['base'], (' background-image: %s;' % imgs) if imgs else '')


def app_col(app, mode):
    lf, ld, df, db = APP[app]
    return (lf, ld) if mode == 'light' else (df, db)


def icon(name, size, color, sw=2):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex: none;"><path d="%s"></path></svg>'
            % (size, size, color, sw, ICON[name]))


def cond(name, default, body):
    return '<sc-if value="{{ %s }}" hint-placeholder-val="{{ %s }}">%s</sc-if>' % (name, 'true' if default else 'false', body)


STYLE = '''
body{margin:0}
a{color:inherit;text-decoration:none}
button{font:inherit;cursor:pointer}
.sq{font-family:'Figtree',system-ui,sans-serif;font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased}
.sq *{box-sizing:border-box}
.sq ::selection{background:#C9BEFF;color:#221F3A}
.sq a:focus-visible,.sq button:focus-visible{outline:3px solid #5340BE;outline-offset:3px}
.sq .scroll{scrollbar-width:none}
.sq .scroll::-webkit-scrollbar{display:none}
.sq button{transition:transform 120ms cubic-bezier(.16,1,.3,1)}
.sq button:active{transform:scale(0.97)}
@media (prefers-reduced-motion: reduce){.sq button{transition:none}}
'''


def page(title, w, h, inner, script):
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
<link rel="stylesheet" href="%s">
<style>%s</style>
</helmet>
%s
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":%d,"height":%d}}'>
%s
</script>
</body>
</html>
''' % (title, FONTS, STYLE, inner, w, h, script)


def home_script(done):
    return '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: %s }; }
  renderVals() {
    var d = this.state.done, self = this;
    return {
      done: d, notDone: !d,
      money: d ? '$376' : '$412',
      budgetLine: d ? '$35.83 spent, $376 left' : '$412 → $376',
      fBudget: d ? '$376' : '$412', fGroceries: d ? '4' : '12', fCalendar: d ? '4' : '3',
      okHead: d ? 'Added just now' : 'Needs your OK',
      edgeStyle: d ? 'solid' : 'dashed',
      confirm: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); }
    };
  }
}''' % ('true' if done else 'false')


def home_vals(done):
    return dict(money='$376' if done else '$412', budgetLine='$35.83 spent, $376 left' if done else '$412 → $376',
                fBudget='$376' if done else '$412', fGroceries='4' if done else '12', fCalendar='4' if done else '3',
                okHead='Added just now' if done else 'Needs your OK', edgeStyle='solid' if done else 'dashed',
                done=done, notDone=not done)


def tile(app, mode, m, span, face, unit, big=False, changed=False, done=False):
    fill, deep = app_col(app, mode)
    tag = cond('done', done, '<span style="padding: 3px 8px; border-radius: 99px; background: %s; color: %s; font-size: 11px; font-weight: 700;">just now</span>' % (deep, '#FFFFFF' if mode == 'light' else fill)) if changed else ''
    return ('<a href="#" style="grid-column: span %d; display: flex; flex-direction: column; justify-content: space-between; gap: 10px; min-height: %dpx; padding: 13px; border-radius: 22px; background: %s; color: %s; outline: 1.5px dashed %s; outline-offset: -6px; box-shadow: %s;">'
            '<span style="display: flex; justify-content: space-between; align-items: center;">%s%s</span>'
            '<span style="display: flex; flex-direction: column; gap: 2px;"><span style="font-size: 13px; font-weight: 600; white-space: nowrap;">%s</span>'
            '<span style="display: flex; align-items: baseline; gap: 5px; flex-wrap: wrap;"><span style="font-size: %dpx; font-weight: 700; letter-spacing: -0.02em; line-height: 1;">%s</span><span style="font-size: 12px; font-weight: 500; color: %s;">%s</span></span></span></a>'
            % (span, 124 if big else 112, fill, m['ink'], deep + 'BF', m['shadow'], icon(app, 22, deep), tag, app, 38 if big else 22, face, m['ink'], unit))


def ok_card(mode, m, done):
    def line(app, text):
        fill, deep = app_col(app, mode)
        return ('<span style="display: flex; align-items: center; gap: 10px; font-size: 15px; line-height: 1.3;"><span style="width: 28px; height: 28px; border-radius: 9px; background: %s; display: grid; place-items: center; flex: none;">%s</span><span><b style="font-weight: 700;">%s</b> %s</span></span>'
                % (fill, icon(app, 16, deep), app, text))
    btns = cond('notDone', not done, '<span style="display: flex; gap: 8px; align-items: center; padding-top: 2px;"><button onClick="{{ confirm }}" style="flex: 1; min-height: 50px; border: 0; border-radius: 99px; background: %s; color: %s; font-size: 16px; font-weight: 700;">Add to 3 apps</button><a href="#" style="min-height: 50px; padding: 0 14px; display: flex; align-items: center; font-size: 15px; font-weight: 600;">Review items</a></span>' % (m['cta'], m['ctaInk']))
    donerow = cond('done', done, '<span style="display: flex; justify-content: space-between; align-items: center; min-height: 50px; font-size: 15px; font-weight: 600;"><span>Added to 3 apps</span><button onClick="{{ undo }}" style="min-height: 44px; padding: 0 18px; border: 1.5px solid %s; border-radius: 99px; background: transparent; color: %s; font-weight: 700;">Undo</button></span>' % (m['ink'], m['ink']))
    return ('<section style="display: flex; flex-direction: column; gap: 10px;"><h2 style="margin: 0; font-size: 15px; font-weight: 700;">{{ okHead }}</h2>'
            '<div style="display: flex; flex-direction: column; gap: 11px; padding: 16px; border-radius: 24px; background: %s; border: 1px solid %s; outline: 1.5px {{ edgeStyle }} %s; outline-offset: -7px; box-shadow: %s;">'
            '<span style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: %s;"><span>Corner Market receipt · 5:41 pm</span><span>$35.83</span></span>%s%s%s%s%s</div></section>'
            % (m['card'], m['cardLine'], m['thread'], m['shadow'], m['sec'],
               line('Budget', '{{ budgetLine }}'), line('Groceries', '8 bought from Weekly shop'), line('Calendar', 'Grocery trip, today'), btns, donerow))


def bar(mode, m):
    # five equal cells: a tile in the app's colour holding the icon, the name under it on the frosted strip
    cell = 'flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border-radius: 20px;'
    tile = 'width: 46px; height: 30px; border-radius: 13px; display: grid; place-items: center;'
    lbl = 'font-size: 13px; font-weight: 600; line-height: 16px; white-space: nowrap;'

    def pin(app):
        fill, deep = app_col(app, mode)
        return ('<a href="#" aria-label="%s" style="%s"><span aria-hidden="true" style="%s background: %s;">%s</span><span style="%s">%s</span></a>'
                % (app, cell, tile, fill, icon(app, 19, deep, 1.8), lbl, app))
    return ('<nav aria-label="Pinned apps and Clair" style="position: absolute; left: 12px; right: 12px; bottom: 16px; height: 64px; padding: 5px 6px; display: flex; border-radius: 26px; background: %s; border: 1px solid %s; -webkit-backdrop-filter: blur(18px) saturate(1.4); backdrop-filter: blur(18px) saturate(1.4); box-shadow: %s;">%s'
            '<a href="#" aria-label="Clair: type, talk or add a photo" style="%s"><span aria-hidden="true" style="%s background: %s;">%s</span><span style="%s font-weight: 700;">Clair</span></a></nav>'
            % (m['bar'], m['cardLine'], m['barShadow'], ''.join(pin(a) for a in ['Budget', 'Groceries', 'Calendar', 'To-dos']), cell, tile, m['cta'], icon('spool', 19, m['ctaInk'], 1.8), lbl))


def home(ground, done):
    mode = GROUNDS[ground]['mode']
    m = MODE[mode]

    def nxt(time, app, text, last=False):
        fill, deep = app_col(app, mode)
        dot = fill if mode == 'light' else deep
        ring = deep if mode == 'light' else fill
        return ('<span style="position: relative; display: flex; align-items: center; gap: 12px; min-height: 44px;">'
                '<span style="width: 16px; height: 16px; border-radius: 50%%; background: %s; border: 2px solid %s; flex: none; position: relative; z-index: 1;"></span>%s'
                '<span style="flex: 1; font-size: 16px;">%s <span style="color: %s; font-size: 14px;">· %s</span></span><span style="font-size: 14px; font-weight: 600; color: %s;">%s</span></span>'
                % (dot, ring, '' if last else '<span aria-hidden="true" style="position: absolute; left: 7px; top: 32px; height: 26px; border-left: 2px dashed %s;"></span>' % m['thread'],
                   text, m['sec'], app, m['sec'], time))

    apps = (tile('Budget', mode, m, 4, '{{ fBudget }}', 'left', True, True, done) + tile('Groceries', mode, m, 2, '{{ fGroceries }}', 'to buy', True, True, done) +
            tile('Calendar', mode, m, 2, '{{ fCalendar }}', 'today', False, True, done) + tile('To-dos', mode, m, 2, '2', 'today') + tile('Workout', mode, m, 2, '3', 'this week') +
            tile('Classes', mode, m, 2, '2', 'due') + tile('Notes', mode, m, 2, '3', 'this week') + tile('Subscriptions', mode, m, 2, '$38.46', 'a month'))

    return '''<div class="sq" style="width: 390px; height: 844px; position: relative; overflow: hidden; %(g)s color: %(ink)s;">
<div class="scroll" style="height: 844px; overflow-y: auto; padding: 18px 16px 104px; display: flex; flex-direction: column; gap: 20px;">
  <span style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: %(sec)s;"><span>Fri 20 Nov · 5:45 pm</span><a href="#" aria-label="You and settings" style="width: 44px; height: 44px; border-radius: 50%%; background: %(card)s; border: 1px solid %(cardLine)s; color: %(ink)s; display: grid; place-items: center; font-size: 15px; font-weight: 700;">S</a></span>
  <h1 style="margin: -6px 0 0; font-size: 31px; font-weight: 700; line-height: 1.12; letter-spacing: -0.025em; text-wrap: balance;">{{ money }} left this month. Pull day at 6 pm.</h1>
  <a href="#" style="display: flex; align-items: center; gap: 10px; min-height: 54px; padding: 0 8px 0 16px; border-radius: 99px; background: %(card)s; border: 1px solid %(cardLine)s; box-shadow: %(shadow)s;">%(spool)s<span style="flex: 1; font-size: 15px; color: %(sec)s;">Describe an app. Clair builds it.</span><span style="width: 38px; height: 38px; border-radius: 50%%; background: %(cta)s; display: grid; place-items: center;">%(arrow)s</span></a>
  %(ok)s
  <section style="display: flex; flex-direction: column;"><h2 style="margin: 0 0 4px; font-size: 15px; font-weight: 700;">Next up</h2>%(n1)s%(n2)s%(n3)s</section>
  <section style="display: flex; flex-direction: column; gap: 10px;"><h2 style="margin: 0; font-size: 15px; font-weight: 700;">Your apps</h2>
    <div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px;">%(apps)s</div></section>
</div>
%(bar)s
</div>''' % dict(m, g=ground_css(ground), spool=icon('spool', 20, m['ink']), arrow=icon('arrow', 18, m['ctaInk']), ok=ok_card(mode, m, done),
                 n1=nxt('6:00 pm', 'Workout', 'Pull day'), n2=nxt('8:00 pm', 'To-dos', 'Take out recycling'), n3=nxt('9:00 pm', 'To-dos', 'Return library books', True),
                 apps=apps, bar=bar(mode, m))


# ---------------------------------------------------------------- Clair builds Car
def clair_script():
    return '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: false }; }
  renderVals() {
    var d = this.state.done, self = this;
    return {
      done: d, notDone: !d,
      credits: d ? '22 credits' : '32 credits',
      cardHead: d ? 'Car is in your apps' : 'Make a Car app?',
      edgeStyle: d ? 'solid' : 'dashed',
      confirm: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); }
    };
  }
}'''


def clair(ground):
    mode = GROUNDS[ground]['mode']
    m = MODE[mode]

    def line(app, text):
        fill, deep = app_col(app, mode)
        return ('<span style="display: flex; align-items: flex-start; gap: 10px; font-size: 15px; line-height: 1.35;"><span style="width: 28px; height: 28px; border-radius: 9px; background: %s; display: grid; place-items: center; flex: none;">%s</span><span style="padding-top: 3px;"><b style="font-weight: 700;">%s</b> %s</span></span>'
                % (fill, icon(app, 16, deep), app, text))

    photo = ('<span aria-label="Photo of a car maintenance card" role="img" style="width: 168px; padding: 12px 12px 14px; border-radius: 6px; background: #FFFDF6; color: #2B2A33; display: flex; flex-direction: column; gap: 5px; font-size: 9.5px; line-height: 1.25; transform: rotate(-2deg); box-shadow: 0 6px 14px -6px rgba(0,0,0,0.4);">'
             '<b style="font-size: 11px; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase;">Maintenance schedule</b>'
             '<span>Oil and filter: every 5,000 mi or 6 months</span><span>Tire rotation: every 7,500 mi</span><span>Engine air filter: every 15,000 mi</span>'
             '<span style="border-top: 1px solid #C9C4B4; padding-top: 5px;">Next oil change: 12/05/2026 or 62,500 mi</span></span>')

    return '''<div class="sq" style="width: 390px; height: 844px; position: relative; overflow: hidden; %(g)s color: %(ink)s;">
<header style="display: flex; align-items: center; gap: 10px; padding: 16px 16px 8px;">
  <a href="#" aria-label="Back" style="width: 44px; height: 44px; border-radius: 50%%; background: %(card)s; border: 1px solid %(cardLine)s; display: grid; place-items: center;">%(back)s</a>
  <span style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 7px; font-size: 17px; font-weight: 700;">%(spool)sClair</span>
  <span style="min-height: 32px; padding: 0 12px; display: flex; align-items: center; border-radius: 99px; background: %(card)s; border: 1px solid %(cardLine)s; font-size: 13px; font-weight: 600;">{{ credits }}</span>
</header>
<div class="scroll" style="height: 692px; overflow-y: auto; padding: 14px 16px 24px; display: flex; flex-direction: column; gap: 14px;">
  <div style="align-self: flex-end; max-width: 250px; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; padding: 16px 16px 14px; border-radius: 24px 24px 6px 24px; background: %(userFill)s;">%(photo)s<span style="font-size: 16px;">make this an app</span></div>
  <p style="margin: 6px 0 0; max-width: 300px; font-size: 16px; line-height: 1.45;">From your maintenance card: 3 services. I can connect it to Calendar and Budget.</p>
  <div style="display: flex; flex-direction: column; gap: 12px; padding: 18px 16px 16px; border-radius: 24px; background: %(card)s; border: 1px solid %(cardLine)s; outline: 1.5px {{ edgeStyle }} %(thread)s; outline-offset: -7px; box-shadow: %(shadow)s;">
    <h2 style="margin: 0; font-size: 19px; font-weight: 700; letter-spacing: -0.01em;">{{ cardHead }}</h2>
    %(l1)s%(l2)s%(l3)s
    %(btns)s
    %(donerow)s
  </div>
  %(after)s
</div>
<div style="position: absolute; left: 12px; right: 12px; bottom: 16px; min-height: 60px; padding: 6px 6px 6px 18px; display: flex; align-items: center; gap: 6px; border-radius: 99px; background: %(bar)s; border: 1px solid %(cardLine)s; -webkit-backdrop-filter: blur(18px) saturate(1.4); backdrop-filter: blur(18px) saturate(1.4); box-shadow: %(barShadow)s;">
  <span style="flex: 1; font-size: 15px; color: %(sec)s;">Tell Clair anything</span>
  <a href="#" aria-label="Photo" style="width: 46px; height: 46px; border-radius: 50%%; display: grid; place-items: center;">%(cam)s</a>
  <a href="#" aria-label="Hold to talk" style="width: 46px; height: 46px; border-radius: 50%%; background: %(cta)s; display: grid; place-items: center;">%(mic)s</a>
</div>
</div>''' % dict(m, g=ground_css(ground), back=icon('back', 20, m['ink']), spool=icon('spool', 20, m['ink']), photo=photo,
                 userFill=app_col('Classes', mode)[0],
                 l1=line('Car', 'new app · Services and Log<br>next: Oil and filter, Sat 5 Dec'), l2=line('Calendar', 'Oil change · Sat 5 Dec'), l3=line('Budget', 'service costs go to Transport'),
                 btns=cond('notDone', True, '<span style="display: flex; gap: 8px; align-items: center; padding-top: 2px;"><button onClick="{{ confirm }}" style="flex: 1; min-height: 50px; border: 0; border-radius: 99px; background: %s; color: %s; font-size: 16px; font-weight: 700;">Make it</button><a href="#" style="min-height: 50px; padding: 0 16px; display: flex; align-items: center; font-size: 15px; font-weight: 600;">Preview</a></span>' % (m['cta'], m['ctaInk'])),
                 donerow=cond('done', False, '<span style="display: flex; justify-content: space-between; align-items: center; min-height: 50px; font-size: 15px; font-weight: 600;"><span>9 apps now</span><button onClick="{{ undo }}" style="min-height: 44px; padding: 0 18px; border: 1.5px solid %s; border-radius: 99px; background: transparent; color: %s; font-weight: 700;">Undo</button></span>' % (m['ink'], m['ink'])),
                 after=cond('done', False, '<p style="margin: 0; max-width: 300px; font-size: 16px; line-height: 1.45;">Done. Snap a service receipt any time and I will log it here and in Budget.</p>'),
                 cam=icon('camera', 22, m['ink']), mic=icon('mic', 21, m['ctaInk']))


CLAIR_VALS = dict(done=False, notDone=True, credits='32 credits', cardHead='Make a Car app?', edgeStyle='dashed')


# ---------------------------------------------------------------- Grounds
def grounds():
    def swatch(name):
        g = GROUNDS[name]
        mode = g['mode']
        m = MODE[mode]

        def mini(app, face, unit):
            fill, deep = app_col(app, mode)
            return ('<span style="flex: 1; display: flex; flex-direction: column; gap: 14px; padding: 12px; border-radius: 18px; background: %s; outline: 1.5px dashed %s; outline-offset: -5px;">%s'
                    '<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-size: 12px; font-weight: 600;">%s</span><span style="font-size: 18px; font-weight: 700; letter-spacing: -0.02em;">%s <span style="font-size: 11px; font-weight: 500;">%s</span></span></span></span>'
                    % (fill, deep + 'BF', icon(app, 18, deep), app, face, unit))
        return ('<div style="display: flex; flex-direction: column; gap: 14px; padding: 22px 20px 20px; border-radius: 28px; %s color: %s; box-shadow: 0 16px 34px -18px rgba(30,25,70,0.45);">'
                '<span style="display: flex; flex-direction: column; gap: 4px;"><h2 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">%s</h2><span style="font-size: 14px; line-height: 1.4; color: %s; min-height: 40px;">%s</span></span>'
                '<span style="display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 14px 14px 14px 16px; border-radius: 20px; background: %s; border: 1px solid %s; box-shadow: %s;"><span style="font-size: 17px; font-weight: 700; letter-spacing: -0.015em;">$412 left this month.</span>'
                '<span style="min-height: 36px; padding: 0 14px; display: flex; align-items: center; border-radius: 99px; background: %s; color: %s; font-size: 13px; font-weight: 700;">Add</span></span>'
                '<span style="display: flex; gap: 8px;">%s%s%s</span></div>'
                % (ground_css(name), m['ink'], name, m['sec'], g['note'], m['card'], m['cardLine'], m['shadow'], m['cta'], m['ctaInk'],
                   mini('Budget', '$412', 'left'), mini('Groceries', '12', 'to buy'), mini('Classes', '2', 'due')))

    return '''<div class="sq" style="width: 1280px; height: 640px; padding: 36px; background: #E9E7EF; color: #221F3A; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-rows: 1fr; gap: 24px;">%s</div>''' % ''.join(swatch(n) for n in GROUNDS)


def staticize(html, vals):
    def sub_if(mo):
        return mo.group(2) if vals.get(mo.group(1)) else ''
    html = re.sub(r'<sc-if value="\{\{ (\w+) \}\}"[^>]*>(.*?)</sc-if>', sub_if, html, flags=re.S)
    html = re.sub(r'\{\{ (\w+) \}\}', lambda mo: str(vals.get(mo.group(1), '')), html)
    return html.replace(' onClick="', ' data-on="')


BOARDS = [
    ('SqHomeLight', 'Home, Mint air', 390, 844, home('Mint air', False), home_script(False), home_vals(False)),
    ('SqHomeDark', 'Home, Denim dusk', 390, 844, home('Denim dusk', True), home_script(True), home_vals(True)),
    ('SqClair', 'Clair builds Car, Mint air', 390, 844, clair('Mint air'), clair_script(), CLAIR_VALS),
    ('SqClairDark', 'Clair builds Car, Denim dusk', 390, 844, clair('Denim dusk'), clair_script(), CLAIR_VALS),
    ('SqGrounds', 'Grounds', 1280, 640, grounds(), 'class Component extends DCLogic { renderVals() { return {}; } }', {}),
]

for name, title, w, h, inner, script, vals in BOARDS:
    html = page(title, w, h, inner, script)
    open(os.path.join(OUT, name + '.dc.html'), 'w').write(html if name == 'SqGrounds' else mint(html))
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        open(os.path.join(PREVIEW, name + '.html'), 'w').write(
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title><link rel="stylesheet" href="%s"><style>%s</style></head><body>%s</body></html>'
            % (title, FONTS.replace('&amp;', '&'), STYLE, staticize(inner, vals)))

# register the page, boards and notes in canvas.json (safe to run again)
import json
cp = os.path.join(OUT, 'canvas.json')
c = json.load(open(cp))
if not any(pg['id'] == 'look-soft' for pg in c['pages']):
    c['pages'].append({'id': 'look-soft', 'name': 'Look: Soft Quilt'})
PLACE = [('SqHomeLight', 0, 0, 'Light: Mint air (tap Add to 3 apps)', True), ('SqHomeDark', 470, 0, 'Dark: Denim dusk (after the receipt)', True),
         ('SqClair', 940, 0, 'Clair builds Car, light (tap Make it)', True), ('SqClairDark', 1410, 0, 'Clair builds Car, dark (tap Make it)', True),
         ('SqGrounds', 0, 1300, 'The six grounds tried. Chosen: Mint air and Denim dusk', False)]
# the Appearance board is written by gen_soft_themes.py; it is placed here so one file owns the page layout
if 'SqAppearance.dc.html' not in c['boards'] and os.path.exists(os.path.join(OUT, 'SqAppearance.dc.html')):
    c['boards']['SqAppearance.dc.html'] = {'x': 1880, 'y': 0, 'w': 390, 'h': 844, 'title': 'You, Appearance (tap a background or Light / Dark)', 'page': 'look-soft', 'radius': 28, 'is_interactive': True}
    c['order'].append('SqAppearance.dc.html')
c['boards'].pop('SqHomePeach.dc.html', None)
c['order'] = [o for o in c['order'] if o != 'SqHomePeach.dc.html']
for (name, title, w, h, _i, _s, _v), (n2, x, y, bt, inter) in zip(BOARDS, PLACE):
    e = c['boards'].get(name + '.dc.html')
    if e is None:  # new board; an existing one keeps the frame it has on the live canvas
        e = {'x': x, 'y': y, 'w': w, 'h': h, 'page': 'look-soft', 'radius': 28 if w == 390 else 20}
        if inter:
            e['is_interactive'] = True
        c['boards'][name + '.dc.html'] = e
    e['title'] = bt
    if w == 390:
        e['x'] = x
    if name + '.dc.html' not in c['order']:
        c['order'].append(name + '.dc.html')
_n = {}
_n['title_sq'] = {'x': 0, 'y': -300, 'text': 'The look: Soft Quilt', 'kind': 'title1', 'maxW': 1800, 'page': 'look-soft'}
_n['sq_note'] = {'x': 0, 'y': 964, 'w': 860, 'size': 'm', 'fill': 'blue', 'page': 'look-soft', 'text': (
    'Soft Quilt: the Lumo reference in Quilt\u2019s voice (warm, hand-made, calm, plain words, no red). '
    'Each app is a pastel patch with a running-stitch edge on a soft gradient ground. A change waiting for your OK has a dashed edge; once added the edge is solid. '
    'Frost is used only where content scrolls under it (the pinned bar, Clair\u2019s field). Clair is the spool, never a sparkle. Figtree throughout.\n\n'
    'What it keeps from the old look: patches, stitches, the basted card, the thread in Next up, the pinned bar.\n'
    'What it drops: muslin and denim chrome, woven prints, the mustard tag (now a small \u201cjust now\u201d pill in the app\u2019s own colour).')}
_n['sq_decide'] = {'x': 940, 'y': 964, 'w': 860, 'size': 'm', 'fill': 'green', 'page': 'look-soft', 'text': (
    'Decided Thu 19 Nov\n\nLight mode: Mint air.\nDark mode: Denim dusk.\n\n'
    'People can pick another ground in You, Appearance (free). The Screens page is restyled to this look in Mint air; the old design-system board is kept as a record.')}
_n['screens'] = {'text': c['notes'].get('screens', {}).get('text', '').replace("Every screen is in Quilter's Workbench (Nov 19).", 'Every screen is in Soft Quilt, light mode on Mint air (restyled Nov 19). Dark mode and the ground picker are on the page "Look: Soft Quilt".')}
_n['row0'] = {'text': "Old design system: Quilter's Workbench (superseded by Soft Quilt)"}
for k, v in _n.items():
    if k in c['notes']:
        c['notes'][k]['text'] = v['text']
        if 'fill' in v:
            c['notes'][k]['fill'] = v['fill']
    else:
        c['notes'][k] = v
json.dump(c, open(cp, 'w'), ensure_ascii=False)
print('ok', len(BOARDS))
