"""Gen Z look options: Colour Blocks and Sticker Lid, Home in dark and light.

Usage: python gen_looks.py <canvas dir>
"""
import os, sys

OUT = sys.argv[1]

ICON = {  # 24px line icons
    'Budget': 'M3 7h15a3 3 0 0 1 3 3v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 7l2-3h12M16 13h2',
    'Groceries': 'M3 4h2l2 11h11l2-8H6M9 20h.01M17 20h.01',
    'Calendar': 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
    'To-dos': 'M4 12l5 5L20 6',
    'Workout': 'M3 9v6M6 7v10M18 7v10M21 9v6M6 12h12',
    'Classes': 'M4 5h6a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H4zM20 5h-6a2 2 0 0 0-2 2v12a2 2 0 0 1 2-2h6z',
    'Subscriptions': 'M4 12a8 8 0 0 1 14-5l2 2M20 12a8 8 0 0 1-14 5l-2-2M20 4v5h-5M4 20v-5h5',
}


def icon(app, size, color, sw=2.2):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex: none;"><path d="%s"></path></svg>'
            % (size, size, color, sw, ICON[app]))


def spool(color):
    return ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
            '<path d="M6 3h12M6 21h12M8 3v18M16 3v18M8 8l8 2M8 12l8 2M8 16l8 2"></path></svg>' % color)


def page(title, w, h, fonts, inner, script):
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
<style>
body{margin:0}
a{color:inherit;text-decoration:none}
button{font:inherit;cursor:pointer}
</style>
</helmet>
%s
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":%d,"height":%d}}'>
%s
</script>
</body>
</html>
''' % (title, fonts, inner, w, h, script)


def script(done):
    return '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: %s }; }
  renderVals() {
    var d = this.state.done, self = this;
    return {
      done: d, notDone: !d,
      money: d ? '$376' : '$412',
      budgetLine: d ? '$35.83 spent, $376 left' : '$412 → $376',
      fBudget: d ? '$376' : '$412', fGroceries: d ? '4' : '12', fCalendar: d ? '4' : '3',
      edgeStyle: d ? 'solid' : 'dashed',
      lift: d ? 'rotate(0deg)' : 'rotate(-1.5deg) translateY(-3px)',
      confirm: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); }
    };
  }
}''' % ('true' if done else 'false')


def cond(name, default, body):
    return '<sc-if value="{{ %s }}" hint-placeholder-val="{{ %s }}">%s</sc-if>' % (name, 'true' if default else 'false', body)


# ---------------------------------------------------------------- Colour Blocks
CB_FONTS = 'https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&amp;display=swap'
CB_SANS = "font-family: 'Archivo', system-ui, sans-serif;"
CB_APP = {  # block colour, ink on block
    'Budget': ('#C6F432', '#111113'), 'Groceries': ('#FF7A1A', '#111113'), 'Calendar': ('#2E4BFF', '#FFFFFF'),
    'To-dos': ('#FFD23F', '#111113'), 'Workout': ('#FF5CA8', '#111113'), 'Classes': ('#B79CFF', '#111113'), 'Subscriptions': ('#45C4FF', '#111113'),
}
CB_THEME = {
    'dark': dict(ground='#0E0E10', ink='#F4F4F1', sec='#A6A6AD', card='#1C1C20', line='#2C2C31'),
    'light': dict(ground='#FFFFFF', ink='#111113', sec='#56565E', card='#F1F1F3', line='#DEDEE3'),
}


def cb_home(theme, done):
    t = CB_THEME[theme]

    def block(app, span, label, face_hole, face_static, unit, changed):
        bg, ink = CB_APP[app]
        face = face_hole or face_static
        tag = cond('done', done, '<span style="align-self: flex-start; padding: 3px 8px; border-radius: 99px; background: %s; color: %s; font-size: 11px; font-weight: 700; letter-spacing: 0.02em;">just now</span>' % (ink, bg)) if changed else ''
        return ('<a href="#" style="position: relative; grid-column: %s; display: flex; flex-direction: column; justify-content: space-between; gap: 8px; padding: 14px; min-height: %dpx; box-sizing: border-box; border-radius: 18px; background: %s; color: %s; outline: 2px dashed %s; outline-offset: -7px;">'
                '<span style="display: flex; flex-direction: column; gap: 6px;"><span style="display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700;">%s%s</span>%s</span>'
                '<span style="display: flex; align-items: baseline; gap: 6px;"><span style="font-size: %dpx; font-weight: 900; font-stretch: 112%%; letter-spacing: -0.03em; line-height: 0.9; font-variant-numeric: tabular-nums;">%s</span><span style="font-size: 14px; font-weight: 600;">%s</span></span></a>'
                % (span, 132 if 'span 4' in span or 'span 6' in span else 112, bg, ink, 'rgba(0,0,0,0.28)' if ink != '#FFFFFF' else 'rgba(255,255,255,0.5)',
                   icon(app, 18, ink), app, tag, 44 if 'span 4' in span else 32, face, unit))

    apps = (block('Budget', 'span 4', '', '{{ fBudget }}', '', 'left', True) + block('Groceries', 'span 2', '', '{{ fGroceries }}', '', 'to buy', True) +
            block('Calendar', 'span 2', '', '{{ fCalendar }}', '', 'today', True) + block('To-dos', 'span 2', '', '', '3', 'today', False) +
            block('Workout', 'span 2', '', '', '6pm', 'pull', False) + block('Classes', 'span 3', '', '', '2', 'due', False) +
            block('Subscriptions', 'span 3', '', '', '$38', 'a month', False))

    def line(app, text):
        bg, _ = CB_APP[app]
        return '<span style="display: flex; align-items: center; gap: 10px; font-size: 15px;"><span style="width: 14px; height: 14px; border-radius: 4px; background: %s; flex: none;"></span><span><b>%s</b> %s</span></span>' % (bg, app, text)

    def nxt(time, app, text):
        bg, ink = CB_APP[app]
        return ('<span style="display: flex; align-items: center; gap: 12px; min-height: 44px;"><span style="min-width: 64px; padding: 4px 8px; box-sizing: border-box; border-radius: 8px; background: %s; color: %s; font-size: 13px; font-weight: 800; text-align: center;">%s</span><span style="font-size: 16px;">%s</span></span>'
                % (bg, ink, time, text))

    def pin(app):
        bg, ink = CB_APP[app]
        return ('<a href="#" aria-label="%s" style="flex: 1; display: grid; place-items: center; margin: 3px; border-radius: 14px; background: %s;">%s</a>' % (app, bg, icon(app, 22, ink)))

    inner = '''<div style="width: 390px; height: 844px; box-sizing: border-box; position: relative; overflow: hidden; background: %(ground)s; color: %(ink)s; %(sans)s">
<div style="height: 752px; overflow-y: auto; box-sizing: border-box; padding: 18px 16px 24px; display: flex; flex-direction: column; gap: 18px;">
  <span style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: %(sec)s;"><span>Fri 20 Nov · 5:45 pm</span><a href="#" aria-label="You and settings" style="width: 36px; height: 36px; border-radius: 50%%; background: %(card)s; color: %(ink)s; display: grid; place-items: center; font-weight: 800;">S</a></span>
  <h1 style="margin: 0; display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 92px; font-weight: 900; font-stretch: 118%%; letter-spacing: -0.045em; line-height: 0.82;">{{ money }}</span><span style="font-size: 20px; font-weight: 600; line-height: 1.25; letter-spacing: -0.01em;">left this month. Pull day at 6 pm.</span></h1>
  <section style="display: flex; flex-direction: column; gap: 12px; padding: 16px; border-radius: 20px; background: %(card)s; outline: 2px {{ edgeStyle }} %(ink)s; outline-offset: -2px;">
    <span style="display: flex; justify-content: space-between; font-size: 13px; color: %(sec)s; font-weight: 600;"><span>Corner Market receipt · 5:41 pm</span><span>$35.83</span></span>
    %(l1)s%(l2)s%(l3)s
    %(btns)s
    %(donerow)s
  </section>
  <section style="display: flex; flex-direction: column; gap: 4px;"><h2 style="margin: 0 0 4px; font-size: 15px; font-weight: 800;">Next up</h2>%(n1)s%(n2)s%(n3)s</section>
  <section style="display: flex; flex-direction: column; gap: 10px;"><h2 style="margin: 0; font-size: 15px; font-weight: 800;">Your apps</h2>
    <div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 6px;">%(apps)s</div></section>
</div>
<nav aria-label="Pinned apps" style="position: absolute; left: 12px; right: 12px; bottom: 16px; height: 68px; box-sizing: border-box; padding: 4px; display: flex; border-radius: 22px; background: %(card)s; box-shadow: 0 8px 24px rgba(0,0,0,0.25);">
  %(pins)s
  <a href="#" style="flex: 1.4; display: flex; align-items: center; justify-content: center; gap: 6px; margin: 3px; border-radius: 14px; background: %(ink)s; color: %(ground)s; font-size: 15px; font-weight: 800;">%(spool)sClair</a>
</nav>
</div>''' % dict(t, sans=CB_SANS, l1=line('Budget', '{{ budgetLine }}'), l2=line('Groceries', '8 bought from Weekly shop'), l3=line('Calendar', 'Grocery trip, today'),
                 btns=cond('notDone', not done, '<span style="display: flex; gap: 8px; align-items: center;"><button onClick="{{ confirm }}" style="flex: 1; min-height: 50px; border: 0; border-radius: 99px; background: #C6F432; color: #111113; font-size: 17px; font-weight: 800;">Add to 3 apps</button><a href="#" style="min-height: 50px; padding: 0 12px; display: flex; align-items: center; font-size: 15px; font-weight: 600;">Review</a></span>'),
                 donerow=cond('done', done, '<span style="display: flex; justify-content: space-between; align-items: center; min-height: 50px; font-size: 16px; font-weight: 700;"><span>Added to 3 apps</span><button onClick="{{ undo }}" style="min-height: 44px; padding: 0 16px; border: 2px solid %s; border-radius: 99px; background: transparent; color: %s; font-weight: 700;">Undo</button></span>' % (t['ink'], t['ink'])),
                 n1=nxt('6:00 pm', 'Workout', 'Pull day'), n2=nxt('9:00 pm', 'To-dos', 'Return library books'), n3=nxt('Sun', 'Subscriptions', 'Spotify renews, $11.99'),
                 apps=apps, pins=''.join(pin(a) for a in ['Budget', 'Groceries', 'Calendar', 'Workout']), spool=spool(t['ground']))
    return inner


# ---------------------------------------------------------------- Sticker Lid
SL_FONTS = 'https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&amp;family=Unbounded:wght@600;800&amp;display=swap'
SL_SANS = "font-family: 'Onest', system-ui, sans-serif;"
SL_DISP = "font-family: 'Unbounded', system-ui, sans-serif;"
SL_APP = {  # fill, ink, shape radius, rotation
    'Budget': ('#7CE36C', '#0F1A0C', '22px', '-3deg'), 'Groceries': ('#FF8A3D', '#1E0E02', '999px', '2deg'),
    'Calendar': ('#3D6BFF', '#FFFFFF', '30px', '-1deg'), 'To-dos': ('#FFE14A', '#221C00', '44% 56% 52% 48% / 55% 45% 55% 45%', '3deg'),
    'Workout': ('#FF6FB5', '#2A0618', '16px', '-2deg'), 'Classes': ('#A98BFF', '#160B33', '999px', '1.5deg'), 'Subscriptions': ('#4FD1E8', '#04222A', '26px', '-2.5deg'),
}
SL_THEME = {
    'dark': dict(ground='#24262B', ink='#F3F3F0', sec='#ADB0B8', card='#FFFFFF', cardInk='#141518', line='#3A3D44', shadow='0 3px 8px rgba(0,0,0,0.45)'),
    'light': dict(ground='#DCDEE2', ink='#141518', sec='#4F535C', card='#FFFFFF', cardInk='#141518', line='#C3C6CC', shadow='0 3px 8px rgba(20,21,24,0.22)'),
}


def sl_home(theme, done):
    t = SL_THEME[theme]

    def sticker(app, face, unit, changed):
        fill, ink, rad, rot = SL_APP[app]
        tag = cond('done', done, '<span style="position: absolute; top: -8px; right: -6px; padding: 3px 8px; border-radius: 99px; background: #FFFFFF; color: #141518; border: 2px solid #141518; font-size: 11px; font-weight: 700; transform: rotate(6deg);">new</span>') if changed else ''
        return ('<a href="#" style="position: relative; display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; min-height: 104px; box-sizing: border-box; border-radius: %s; background: %s; color: %s; border: 5px solid #FFFFFF; box-shadow: %s; transform: rotate(%s);">'
                '<span style="display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700;">%s%s</span>'
                '<span style="display: flex; align-items: baseline; gap: 5px;"><span style="%s font-size: 28px; font-weight: 800; letter-spacing: -0.02em; line-height: 1;">%s</span><span style="font-size: 13px; font-weight: 600;">%s</span></span>%s</a>'
                % (rad, fill, ink, t['shadow'], rot, icon(app, 18, ink), app, SL_DISP, face, unit, tag))

    apps = (sticker('Budget', '{{ fBudget }}', 'left', True) + sticker('Groceries', '{{ fGroceries }}', 'to buy', True) +
            sticker('Calendar', '{{ fCalendar }}', 'today', True) + sticker('To-dos', '3', 'today', False) +
            sticker('Workout', '6pm', 'pull day', False) + sticker('Classes', '2', 'due', False))

    def line(app, text):
        fill, ink, _, _ = SL_APP[app]
        return '<span style="display: flex; align-items: center; gap: 10px; font-size: 15px;"><span style="width: 26px; height: 26px; border-radius: 8px; background: %s; display: grid; place-items: center; flex: none;">%s</span><span><b>%s</b> %s</span></span>' % (fill, icon(app, 15, ink), app, text)

    def nxt(time, app, text):
        fill, ink, _, _ = SL_APP[app]
        return ('<span style="display: flex; align-items: center; gap: 12px; min-height: 44px;"><span style="width: 30px; height: 30px; border-radius: 50%%; background: %s; display: grid; place-items: center; flex: none; border: 3px solid #FFFFFF;">%s</span><span style="font-size: 16px; flex: 1;">%s</span><span style="font-size: 14px; font-weight: 600; color: %s;">%s</span></span>'
                % (fill, icon(app, 14, ink), text, t['sec'], time))

    def pin(app):
        fill, ink, _, _ = SL_APP[app]
        return ('<a href="#" aria-label="%s" style="flex: 1; display: grid; place-items: center;"><span style="width: 46px; height: 46px; border-radius: 50%%; background: %s; border: 4px solid #FFFFFF; box-shadow: %s; display: grid; place-items: center;">%s</span></a>'
                % (app, fill, t['shadow'], icon(app, 20, ink)))

    inner = '''<div style="width: 390px; height: 844px; box-sizing: border-box; position: relative; overflow: hidden; background: %(ground)s; color: %(ink)s; %(sans)s">
<div style="height: 756px; overflow-y: auto; box-sizing: border-box; padding: 18px 18px 24px; display: flex; flex-direction: column; gap: 20px;">
  <span style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: %(sec)s;"><span>Fri 20 Nov · 5:45 pm</span><a href="#" aria-label="You and settings" style="width: 38px; height: 38px; border-radius: 50%%; background: #FFFFFF; color: #141518; border: 3px solid #FFFFFF; box-shadow: %(shadow)s; display: grid; place-items: center; font-weight: 700;">S</a></span>
  <h1 style="margin: 0; %(disp)s font-size: 34px; font-weight: 800; line-height: 1.08; letter-spacing: -0.03em;">{{ money }} left this month. Pull day at 6 pm.</h1>
  <section style="display: flex; flex-direction: column; gap: 12px; padding: 16px; border-radius: 22px; background: %(card)s; color: %(cardInk)s; outline: 2px {{ edgeStyle }} %(ink)s; outline-offset: 5px; box-shadow: %(shadow)s; transform: {{ lift }};">
    <span style="display: flex; justify-content: space-between; font-size: 13px; color: #4F535C; font-weight: 600;"><span>Corner Market receipt · 5:41 pm</span><span>$35.83</span></span>
    %(l1)s%(l2)s%(l3)s
    %(btns)s
    %(donerow)s
  </section>
  <section style="display: flex; flex-direction: column;"><h2 style="margin: 0 0 4px; font-size: 15px; font-weight: 700;">Next up</h2>%(n1)s%(n2)s%(n3)s</section>
  <section style="display: flex; flex-direction: column; gap: 14px;"><h2 style="margin: 0; font-size: 15px; font-weight: 700;">Your apps</h2>
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 14px; padding: 4px;">%(apps)s</div></section>
</div>
<nav aria-label="Pinned apps" style="position: absolute; left: 0; right: 0; bottom: 0; height: 88px; box-sizing: border-box; padding: 8px 10px 18px; display: flex; align-items: center; background: %(ground)s; border-top: 1px solid %(line)s;">
  %(pins)s
  <a href="#" style="flex: 1.3; height: 52px; display: flex; align-items: center; justify-content: center; gap: 6px; border-radius: 99px; background: #FFFFFF; color: #141518; border: 3px solid #141518; font-size: 15px; font-weight: 700;">%(spool)sClair</a>
</nav>
</div>''' % dict(t, sans=SL_SANS, disp=SL_DISP, l1=line('Budget', '{{ budgetLine }}'), l2=line('Groceries', '8 bought from Weekly shop'), l3=line('Calendar', 'Grocery trip, today'),
                 btns=cond('notDone', not done, '<span style="display: flex; gap: 8px; align-items: center;"><button onClick="{{ confirm }}" style="flex: 1; min-height: 50px; border: 0; border-radius: 99px; background: #141518; color: #FFFFFF; font-size: 16px; font-weight: 700;">Add to 3 apps</button><a href="#" style="min-height: 50px; padding: 0 12px; display: flex; align-items: center; font-size: 15px; font-weight: 600;">Review</a></span>'),
                 donerow=cond('done', done, '<span style="display: flex; justify-content: space-between; align-items: center; min-height: 50px; font-size: 16px; font-weight: 700;"><span>Added to 3 apps</span><button onClick="{{ undo }}" style="min-height: 44px; padding: 0 16px; border: 2px solid #141518; border-radius: 99px; background: transparent; color: #141518; font-weight: 700;">Undo</button></span>'),
                 n1=nxt('6:00 pm', 'Workout', 'Pull day'), n2=nxt('9:00 pm', 'To-dos', 'Return library books'), n3=nxt('Sun', 'Subscriptions', 'Spotify renews, $11.99'),
                 apps=apps, pins=''.join(pin(a) for a in ['Budget', 'Groceries', 'Calendar', 'Workout']), spool=spool('#141518'))
    return inner


for name, fn, fonts in [('Cb', cb_home, CB_FONTS), ('Sl', sl_home, SL_FONTS)]:
    for theme, done in [('dark', False), ('light', True)]:
        open(os.path.join(OUT, '%sHome%s.dc.html' % (name, theme.title())), 'w').write(
            page('Home, %s' % theme, 390, 844, fonts, fn(theme, done), script(done)))
print('ok')
