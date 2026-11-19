import os, re, sys, json

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&amp;family=DM+Mono:wght@400;500&amp;family=Hanken+Grotesk:wght@400;500;600;700&amp;display=swap">'
META = ('<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">\n'
        '<meta name="theme-color" content="#F4EEE1"><meta name="color-scheme" content="light">')
STITCH = 'linear-gradient(90deg,{c} {p}%,transparent 0),linear-gradient(90deg,{c} {p}%,transparent 0),linear-gradient(0deg,{c} {p}%,transparent 0),linear-gradient(0deg,{c} {p}%,transparent 0)'
CSS = ('<style>\n'
       ':root{--ease:cubic-bezier(.16,1,.3,1);--ease-thread:cubic-bezier(.45,0,.15,1);--t-fb:120ms;--t-state:220ms;--t-layout:350ms;--t-focal:600ms;--t-state-out:140ms;--t-layout-out:220ms;--t-focal-out:360ms}\n'
       'html{-webkit-tap-highlight-color:transparent;-webkit-text-size-adjust:100%}\nhtml,body{overscroll-behavior:none}\nbody{margin:0}\n'
       'a{color:#2A2119;text-decoration:none}\n@media (hover:hover) and (pointer:fine){a:hover{color:#665847}a.lk:hover{color:#3557A6}}\n'
       'button{font:inherit;cursor:pointer;color:inherit}\nbutton,a,[role="button"]{touch-action:manipulation}\ninput,textarea,select{font-size:16px}\n'
       '.pb,.qp,.chip,.grip,.swrow{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}\n'
       '.chips{overscroll-behavior-x:contain;scroll-snap-type:x proximity;scroll-padding-inline:16px}\n.chips>*{scroll-snap-align:start}\n'
       '.btn,.chip,.qp{transition:transform var(--t-fb) var(--ease)}\n.btn:active,.chip:active{transform:scale(.97)}\n.qp:active{transform:scale(.98)}\n'
       '.pb{transition:box-shadow var(--t-fb) var(--ease)}\n.pb:active{box-shadow:inset 0 0 0 100px rgba(42,33,25,.07)!important}\n'
       '.rw{transition:background-color var(--t-fb) var(--ease)}\n.rw:active{background-color:#F7F1E6!important}\n'
       '.scr{-webkit-mask-image:linear-gradient(to bottom,#000 calc(100% - 24px),transparent);mask-image:linear-gradient(to bottom,#000 calc(100% - 24px),transparent)}\n'
       ".lk{font:600 15px 'Hanken Grotesk',system-ui,sans-serif;color:#22396F;text-decoration:none;min-height:44px;min-width:44px;justify-content:center;display:inline-flex;align-items:center;gap:4px}\n"
       '.num{font-variant-numeric:tabular-nums}\n'
       '.st{background-color:#FFFDF8;border-radius:16px;background-image:' + STITCH.format(c='#BFAE90', p=58) + ';background-size:7px 1.5px,7px 1.5px,1.5px 7px,1.5px 7px;background-position:0 5px,0 calc(100% - 5px),5px 0,calc(100% - 5px) 0;background-repeat:repeat-x,repeat-x,repeat-y,repeat-y;transition:background-size var(--t-state) var(--ease)}\n'
       '.st.basted{background-image:' + STITCH.format(c='#665847', p=62) + ';background-size:20px 1.5px,20px 1.5px,1.5px 20px,1.5px 20px;transition-duration:var(--t-state-out)}\n'
       '.chalk{position:relative;background:rgba(53,87,166,0.06);border-radius:16px;outline:2px dotted rgba(53,87,166,0.7);outline-offset:-3px}\n'
       '@media (prefers-reduced-motion:reduce){.btn,.chip,.qp,.pb,.rw,.st{transition:none}.btn:active,.chip:active,.qp:active{transform:none}}\n'
       '</style>')

# Section A spacing / radius / type-floor scale, applied to every generated board.
GAP = {'3': '4', '5': '4', '6': '8', '10': '12', '13': '12', '14': '16', '18': '16', '22': '24'}
RAD = {'3': '4', '5': '4', '7': '8', '9': '12', '10': '12', '11': '12', '14': '16', '999': '4'}
def _px(m, table): return re.sub(r'\b(\d+)px', lambda k: table.get(k.group(1), k.group(1)) + 'px', m.group(0))
def _fs(m):
    v = float(m.group(1))
    v = 13 if v < 13 else round(v + 0.01) if v != int(v) else int(v)
    return 'font-size: ' + str(int(v)) + 'px'
def norm(t):
    t = re.sub(r'(?<![\w-])(?:gap|padding(?:-top|-bottom|-left|-right)?): [^;\'"]+', lambda m: _px(m, GAP), t)
    t = re.sub(r'border-radius: [^;\'"]+', lambda m: _px(m, RAD), t)
    return re.sub(r'font-size: ([\d.]+)px', _fs, t)

def page(title, body, script='class Component extends DCLogic {\n  renderVals() { return {}; }\n}', w=390, h=844, css=''):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n' + META + '\n<title>' + title + '</title>\n<script src="./support.js"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n'
            + FONTS + '\n' + CSS + ('\n<style>\n' + css + '\n</style>' if css else '') + '\n</helmet>\n' + norm(body) + '\n</x-dc>\n<script type="text/x-dc" data-dc-script data-props=\'{"$preview":{"width":' + str(w) + ',"height":' + str(h) + '}}\'>\n'
            + norm(script) + '\n</script>\n</body>\n</html>\n')

I = {
    'wallet': 'M3 7h18v12H3zM3 10h18M16 15h2', 'cart': 'M3 4h2l2.2 10.5h10.6L20 7H6.2M9 19.5h.01M17 19.5h.01', 'cal': 'M4 6h16v14H4zM4 10h16M9 3v4M15 3v4',
    'check': 'M5 12.5l4.5 4.5L19 7', 'lift': 'M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10', 'book': 'M5 5h12v15H7a2 2 0 0 1-2-2zM5 18a2 2 0 0 1 2-2h10',
    'repeat': 'M17 3l3 3-3 3M4 12V9a3 3 0 0 1 3-3h13M7 21l-3-3 3-3M20 12v3a3 3 0 0 1-3 3H4', 'plus': 'M12 5v14M5 12h14', 'search': 'M11 5a6 6 0 1 0 0 12a6 6 0 1 0 0-12M20 20l-4.5-4.5',
    'cam': 'M4 8h3l2-3h6l2 3h3v11H4zM12 9.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7', 'back': 'M15 5l-7 7 7 7', 'x': 'M6 6l12 12M18 6L6 18', 'grip': 'M9 6h.01M15 6h.01M9 12h.01M15 12h.01M9 18h.01M15 18h.01',
    'rip': 'M4 20l9-9M13 11l3-7 4 4-7 3M7 14l3 3', 'send': 'M12 19V5M6 11l6-6 6 6', 'user': 'M12 5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7M5 20c1.2-3.6 4-5 7-5s5.8 1.4 7 5',
    'import': 'M12 4v11M7 10l5 5 5-5M5 20h14', 'type': 'M5 7V5h14v2M12 5v14M9 19h6', 'trash': 'M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13', 'note': 'M6 4h12v16H6zM9 9h6M9 13h6M9 17h3',
    'layout': 'M4 4h16v6H4zM4 14h7v6H4zM15 14h5v6h-5z', 'mic': 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21',
    'clip': 'M19.5 11.5l-7.8 7.8a4.6 4.6 0 0 1-6.5-6.5l8.2-8.2a3.1 3.1 0 0 1 4.4 4.4l-8 8a1.5 1.5 0 0 1-2.2-2.2l7.3-7.3', 'doc': 'M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6',
    # Clair button mark: a FACELESS spool (two flanges, barrel, thread tail). A mark, not the character.
    'spool': 'M5 3h14v3.5H5zM5 17.5h14V21H5zM7.5 6.5v11M16.5 6.5v11M7.5 11l9-2M7.5 15l9-2M7.5 15.5C4.8 16 3.2 18 2.2 21.5', 'link': 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
}
DYE = {'Budget': '#D3ECE7', 'Groceries': '#DDEBD2', 'Calendar': '#DCE4F3', 'To-dos': '#FBEBC4', 'Workout': '#F8DCC2', 'Classes': '#E7EBC2', 'Subscriptions': '#EADCF0', 'Meals': '#F3DCE0'}
HREF = {'Budget': 'Budget.dc.html', 'Groceries': 'Groceries.dc.html', 'Calendar': 'Calendar.dc.html', 'To-dos': 'Todos.dc.html', 'Workout': 'Workout.dc.html', 'Classes': 'Preview.dc.html', 'Subscriptions': 'Budget.dc.html', 'Meals': 'Groceries.dc.html'}
ICON = {'Budget': 'wallet', 'Groceries': 'cart', 'Calendar': 'cal', 'To-dos': 'check', 'Workout': 'lift', 'Classes': 'book', 'Subscriptions': 'repeat', 'Meals': 'cart'}

def svg(name, size=18, color='currentColor', sw='1.8'):
    return ('<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 24 24" fill="none" stroke="' + color + '" stroke-width="' + sw
            + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + I[name] + '"></path></svg>')
# Tailor's chalk: the small "from Clair" mark on cards (a spool only appears once per screen, never as a card mark).
def chalk_icon(size=16):
    return ('<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 24 24" aria-hidden="true" style="flex: none;"><path d="M12 4.5 L20.5 18.5 H3.5 Z" fill="rgba(53,87,166,.16)" stroke="#3557A6" stroke-width="1.8" stroke-linejoin="round"></path>'
            '<path d="M8 15.5h8" stroke="#3557A6" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="1 3"></path></svg>')

# Clair, sizes 30 / 44 / 96 only. Small sizes (<=44) get heavier lines, bigger eyes, no barrel band, and a cue outside the barrel.
def spool(expr, size=44):
    assert size in (30, 44, 96), size
    sm = size <= 44
    o, fw, er = ('2.6', '2.6', 3.2) if sm else ('1.6', '1.8', 2.3)
    W, K = '#FFFFFF', '#2A2119'
    P = lambda d, fill='none': '<path d="' + d + '" fill="' + fill + '" stroke="' + W + '" stroke-width="' + fw + '" stroke-linecap="round" stroke-linejoin="round"></path>'
    eyes = lambda dx=0, dy=0: ''.join('<circle cx="' + str(x + dx) + '" cy="' + str(26 + dy) + '" r="' + str(er) + '" fill="' + W + '"></circle>' for x in (23, 33))
    happy = P('M20.5 27 q2.5 -3.5 5 0 M30.5 27 q2.5 -3.5 5 0')
    tail, face, extra = 'M14 38 C8 40 5 43 0 45', '', ''
    if expr == 'hello': face = eyes() + P('M24 31 q4 3 8 0')
    if expr == 'working': face = eyes(1.5, 1.5) + '<ellipse cx="29.5" cy="33" rx="1.8" ry="1.5" fill="' + W + '"></ellipse>'
    if expr == 'thinking':
        face = eyes(1.5, -2) + P('M26 33 h5')
        extra = '<circle cx="50" cy="8" r="1.8" fill="' + K + '"></circle><circle cx="55" cy="2" r="2.2" fill="' + K + '"></circle><circle cx="61" cy="-5" r="2.6" fill="' + K + '"></circle>'
    if expr == 'waiting':
        face = eyes() + P('M20.5 21 q2.5 -2 5 0 M30.5 21 q2.5 -2 5 0') + P('M25 31.5 q3 2 6 0')
        extra = ('<path d="M41 9 L55 -5 L57 -7 L55 -3 Z" fill="#C9CCD1" stroke="' + K + '" stroke-width="1.2" stroke-linejoin="round"></path>'
                 '<path d="M54 -4 C60 -3 62 3 58 9" fill="none" stroke="#E3A72F" stroke-width="1.5" stroke-linecap="round"></path>')
    if expr == 'stitched':
        face = happy + P('M23.5 30.5 q4.5 4.5 9 0')
        if sm: extra = '<path d="M46 2l3 3 6-7" fill="none" stroke="' + K + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></path>'
    if expr == 'proud':
        face = happy + '<circle cx="18.5" cy="31" r="2.1" fill="#F8DCC2"></circle><circle cx="37.5" cy="31" r="2.1" fill="#F8DCC2"></circle><path d="M23 30 q5 6.5 10 0 z" fill="' + W + '"></path>'
        if sm: extra = '<path d="M50 -1v10M45 4h10" stroke="#E3A72F" stroke-width="2.4" stroke-linecap="round"></path>'
    if expr == 'oops':
        face = eyes(0, 1) + P('M20.5 22.5 L25.5 20.5 M30.5 20.5 L35.5 22.5') + P('M23.5 33.5 q1.5 -1.6 3 0 t3 0 t3 0')
        tail = 'M14 40 l-4 1.5 l2 3 l-4.5 1 l2 3 l-5 1'
    if expr == 'sleepy':
        face = P('M20.5 26 q2.5 2 5 0 M30.5 26 q2.5 2 5 0') + P('M26 32.5 q2 1.2 4 0')
        extra = '<path d="M47 1h5l-5 6h5M55 -7h4l-4 5h4" fill="none" stroke="' + K + '" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>'
    assert face, expr
    band = '' if sm else '<path d="M14 18.5h28M14 38h28" stroke="#FFFFFF" stroke-opacity=".28" stroke-width="1.4"></path>'
    return ('<svg class="sp" width="' + str(size) + '" height="' + str(round(size * 70 / 68)) + '" viewBox="-6 -10 68 70" aria-hidden="true" style="flex: none; overflow: visible;">'
            '<path d="' + tail + '" fill="none" stroke="' + K + '" stroke-width="' + o + '" stroke-linecap="round" stroke-linejoin="round"></path>'
            '<rect x="10" y="6" width="36" height="8" rx="3" fill="#D9B98F" stroke="' + K + '" stroke-width="' + o + '"></rect>'
            '<rect x="14" y="14" width="28" height="28" fill="#3557A6" stroke="' + K + '" stroke-width="' + o + '"></rect>' + band +
            '<rect x="10" y="42" width="36" height="8" rx="3" fill="#D9B98F" stroke="' + K + '" stroke-width="' + o + '"></rect>' + face + extra + '</svg>')

def trk(px): return '-0.035em' if px >= 40 else '-0.025em' if px >= 28 else '-0.015em' if px >= 20 else '-0.005em'
def disp(px, extra=''):
    return "font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: " + str(px) + 'px; letter-spacing: ' + trk(px) + ';' + extra
NUM = ' font-variant-numeric: tabular-nums;'
NB = '&nbsp;'
LBL = "font-family: 'Hanken Grotesk', system-ui, sans-serif; font-size: 13px; font-weight: 600; letter-spacing: 0; color: #665847;"
CLAIR = 'font-size: 15px; font-weight: 500; color: #22396F;'

ROOT = '<div style="width: 390px; height: 844px; position: relative; overflow: hidden; background: #F4EEE1; color: #2A2119; font-family: \'Hanken Grotesk\', system-ui, sans-serif;">'
def scroller(bottom=96):
    return '  <div class="scr" style="position: absolute; inset: 0 0 ' + str(bottom) + 'px 0; overflow-y: auto; padding: 44px 16px 24px; box-sizing: border-box; display: grid; grid-template-columns: minmax(0, 1fr); align-content: start; gap: 16px;">'
def back(href, label):
    return '    <a href="' + href + '" aria-label="' + label + '" style="width: 44px; height: 44px; margin-left: -12px; display: grid; place-items: center;">' + svg('back', 22, '#2A2119') + '</a>'
def topbar(href, label, mid='', right=''):
    # mid: plain text, or h1mid(text) when the screen has no big title of its own.
    return ('    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 44px;"><a href="' + href + '" aria-label="' + label
            + '" style="width: 44px; height: 44px; margin-left: -12px; display: grid; place-items: center;">' + svg('back', 22, '#2A2119') + '</a>'
            + (mid if not mid or mid.startswith('<') else '<b style="font-size: 15px; font-weight: 600;">' + mid + '</b>')
            + (right or '<span style="width: 44px;"></span>') + '</div>')
def h1mid(text): return '<h1 style="margin: 0; ' + disp(17) + '">' + text + '</h1>'
def title(app, text=None, extra=''):
    return ('    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;"><span style="width: 36px; height: 36px; border-radius: 8px; background: ' + DYE[app]
            + '; display: grid; place-items: center; flex: none;">' + svg(ICON[app], 18, '#2A2119') + '</span><h1 style="margin: 0; ' + disp(28) + ' line-height: 1.05;">'
            + (text or app) + '</h1>' + extra + '</div>')
def h1(text, size=28):
    return '    <h1 style="margin: 0; ' + disp(size) + ' line-height: 1.05;">' + text + '</h1>'
def sect(text, right=''):
    return ('    <div style="display: flex; justify-content: space-between; gap: 8px; ' + LBL + '"><span>' + text + '</span>'
            + ('<span style="font-weight: 500;">' + right + '</span>' if right else '') + '</div>')
def link(label, href, nav=True, extra=''):
    return '<a class="lk" href="' + href + '"' + (' style="' + extra + '"' if extra else '') + '>' + label + ('<span aria-hidden="true">›</span>' if nav else '') + '</a>'
BTN = 'min-height: 48px; padding: 0 20px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-weight: 600; font-size: 16px; '
BTN2 = 'border: 0; background: transparent; box-shadow: inset 0 0 0 1.5px #BFAE90; color: #2A2119;'
def btn(label, href=None, primary=True, onclick=None):
    st = BTN + ('border: 0; background: #3557A6; color: #FFFFFF;' if primary else BTN2)
    if href: return '<a class="btn" href="' + href + '" style="' + st + '">' + label + '</a>'
    return '<button class="btn" type="button"' + (' onClick="{{ ' + onclick + ' }}"' if onclick else '') + ' style="' + st + '">' + label + '</button>'
SEP = ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;'
ROWT = 'font-size: 16px; font-weight: 500; color: #2A2119;'
ROWM = 'font-size: 13px; color: #665847;'
def row(main, sub='', right='', first=False, href=None, extra=''):
    st = 'display: flex; align-items: center; gap: 12px; min-height: 56px;' + ('' if first else SEP) + extra
    inner = ('<span style="flex: 1; display: flex; flex-direction: column; min-width: 0;"><span style="' + ROWT + '">' + main + '</span>'
             + ('<span style="' + ROWM + '">' + sub + '</span>' if sub else '') + '</span>' + right)
    if href: return '<a class="rw" href="' + href + '" style="' + st + '">' + inner + '</a>'
    return '<div style="' + st + '">' + inner + '</div>'
def tag(t='just changed'):
    return '<span style="font-size: 13px; font-weight: 600; padding: 2px 8px; background: #E3A72F; color: #1F180D; border-radius: 4px; white-space: nowrap;">' + t + '</span>'
def dot(app):
    return '<span aria-hidden="true" style="flex: none; width: 10px; height: 10px; border-radius: 50%; background: ' + DYE[app] + '; box-shadow: inset 0 0 0 1.5px rgba(42,33,25,0.45);"></span>'
PINS = ['Budget', 'Groceries', 'Calendar', 'To-dos']
BAR = 'position: absolute; left: 12px; right: 12px; bottom: max(18px, env(safe-area-inset-bottom, 0px)); height: 62px; display: flex; border-radius: 16px; box-shadow: 0 8px 22px -14px rgba(42,33,25,0.55);'
BARLBL = 'font-size: 13px; font-weight: 600; letter-spacing: 0; white-space: nowrap;'
# The Clair button (pinned bar, right cell). Tap = Clair sheet; hold 450ms = talk. Canvas stills route <a> only, so it stays an <a role="button">.
CLAIR_ARIA = 'Clair: type, talk or add a photo. Hold to talk'
def clairbtn(held=False):
    fill = '<span aria-hidden="true" style="position: absolute; inset: 0; background: rgba(251,246,236,0.22);"></span>' if held else ''
    return ('    <a class="pb" role="button" href="' + ('ClairResult.dc.html' if held else 'ClairSheet.dc.html') + '" aria-label="' + CLAIR_ARIA + '"' + (' aria-pressed="true"' if held else '')
            + ' style="position: relative; overflow: hidden; flex: 0 0 64px; background: #2A2119; color: #FBF6EC; border-radius: 0 16px 16px 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;">'
            + fill + svg('spool', 20, '#FBF6EC') + '<span style="' + BARLBL + ' color: #FBF6EC;">Clair</span></a>')
def bar(active=None, held=False, extra='', pins=PINS):
    out = ['  <nav aria-label="Pinned apps and Clair" style="' + BAR + extra + '">']
    for i, n in enumerate(pins):
        st = ('flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; background: ' + DYE[n] + '; '
              + ('border-radius: 16px 0 0 16px;' if i == 0 else 'border-left: 1.5px dashed rgba(42,33,25,0.4);') + (' box-shadow: inset 0 -3px 0 #3557A6;' if n == active else ''))
        out.append('    <a class="pb" href="' + HREF[n] + '" aria-label="' + n + '"' + (' aria-current="page"' if n == active else '') + ' style="' + st + '">' + svg(ICON[n]) + '<span style="' + BARLBL + '">' + n + '</span></a>')
    out.append(clairbtn(held))
    out.append('  </nav>')
    return '\n'.join(out)
def patch(app, face, span='grid-column: span 2;', big=False, href=None):
    return ('<a class="qp" href="' + (href or HREF[app]) + '" aria-label="' + app + ', ' + face + '" style="position: relative; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-start; padding: 12px; box-sizing: border-box; overflow: hidden; background: '
            + DYE.get(app, '#FFFDF8') + '; ' + span + '"><span aria-hidden="true" style="position: absolute; inset: 3px; border: 1.5px dashed rgba(42,33,25,0.28); border-radius: 8px;"></span>'
            + '<span style="position: relative; display: flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600;">' + svg(ICON.get(app, 'plus'), 16) + app + '</span>'
            + '<span style="position: relative; ' + disp(26 if big else 15, NUM) + ' line-height: 1; white-space: nowrap;">' + face + '</span></a>')
def card(inner, cls='st', extra=''):
    return '    <section class="' + cls + '" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;' + extra + '">' + inner + '</section>'
CLOSE = '\n</div>'
files = {}

# ---------- Tabs -> Your apps / Just used ----------
body = ROOT + '\n' + scroller() + '\n' + back('Main.dc.html', 'Back to Home') + '\n' + h1('Your apps') + '\n' + \
    '    <p style="margin: 0; font-size: 15px;">Swipe up on the bar from inside any app to get here. Just used first, then everything.</p>\n' + \
    sect('Just used') + '\n    <div class="chips" style="display: flex; gap: 8px; overflow-x: auto; margin: 0 -16px; padding: 2px 16px 4px; scrollbar-width: none;">' + \
    ''.join('<a class="chip" href="' + HREF[n] + '" style="flex: none; width: 92px; height: 88px; border-radius: 16px; background: ' + DYE[n] + '; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; box-sizing: border-box; font-size: 13px; font-weight: 600;">' + svg(ICON[n]) + '<span style="display: flex; flex-direction: column;">' + n + '<span style="font-size: 13px; font-weight: 400; color: #665847;">' + ago + '</span></span></a>'
            for n, ago in [('Groceries', '2' + NB + 'min'), ('Budget', '20' + NB + 'min'), ('Workout', '1' + NB + 'hour'), ('To-dos', '3' + NB + 'hours'), ('Calendar', 'Today'), ('Classes', 'Yesterday')]) + '</div>\n' + \
    '    <a href="Search.dc.html" style="display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 16px; color: #665847;">' + svg('search', 16) + 'Find an app</a>\n' + \
    sect('All apps · 7', 'Most used first') + '\n    <div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); grid-auto-rows: 58px; border-radius: 16px; overflow: hidden;">' + \
    patch('Budget', '$376 left', 'grid-column: span 4; grid-row: span 2;', True) + patch('Groceries', '4 to buy', 'grid-column: span 2;') + patch('Calendar', '4 today', 'grid-column: span 2;') + \
    patch('To-dos', '3 today', 'grid-column: span 3;') + patch('Workout', 'Pull day 6' + NB + 'pm', 'grid-column: span 3;') + patch('Classes', '2 due') + patch('Subscriptions', '$38 a month') + \
    '<a href="Build.dc.html" style="grid-column: span 2; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 4px; font-size: 13px; font-weight: 600; color: #22396F;">' + svg('plus') + 'New app</a></div>\n  </div>\n' + bar() + CLOSE
files['Tabs'] = page('Your apps', body)

# ---------- Search ----------
body = ROOT + '\n' + scroller() + '''
    <h1 style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); margin: 0;">Search</h1>
    <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;"><label style="flex: 1; display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 2px #3557A6;">''' + svg('search', 16) + '''<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0);">Search</span><input type="search" enterkeyhint="search" autocapitalize="none" value="coffee" style="flex: 1; min-width: 0; border: 0; background: transparent; font: inherit; font-size: 16px; color: #2A2119; outline: none;"></label>''' + link('Cancel', 'Budget.dc.html', False, 'padding: 0 4px;') + '''</div>
    <div class="chips" style="display: flex; gap: 6px; overflow-x: auto; margin: 0 -16px; padding: 0 16px; scrollbar-width: none;">
      <sc-if value="{{ scoped }}" hint-placeholder-val="{{ true }}"><button class="chip" type="button" onClick="{{ widen }}" style="flex: none; min-height: 44px; padding: 0 12px; border-radius: 12px; border: 0; background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #3557A6; font-size: 14px; display: flex; align-items: center; gap: 6px;">in Budget ''' + svg('x', 14) + '''</button></sc-if>
      <sc-for list="{{ chips }}" as="c" hint-placeholder-count="3"><button class="chip" type="button" onClick="{{ c.pick }}" aria-pressed="{{ c.on }}" style="{{ c.style }}">{{ c.label }}</button></sc-for>
    </div>
''' + card('<span style="display: flex; align-items: center; gap: 8px;">' + chalk_icon() + '<b style="font-size: 16px;' + NUM + '">$16.60 on coffee in October</b></span><span style="' + CLAIR + '">3 visits: Blue Copper twice, Starbucks once. From Budget.</span>', 'chalk') + '\n' + \
    sect('{{ budgetHead }}') + '''
    <section class="st" style="padding: 4px 14px;">
      <sc-for list="{{ rows }}" as="r" hint-placeholder-count="3"><div style="{{ r.style }}"><span style="flex: 1; display: flex; flex-direction: column;"><span style="''' + ROWT + '''">{{ r.t }}</span><span style="''' + ROWM + '''">{{ r.s }}</span></span><span style="font-family: 'DM Mono', monospace; font-size: 14px;''' + NUM + '''">{{ r.v }}</span></div></sc-for>
    </section>
    <sc-if value="{{ scoped }}" hint-placeholder-val="{{ true }}"><button class="btn" type="button" onClick="{{ widen }}" style="min-height: 48px; border-radius: 12px; border: 0; background: transparent; box-shadow: inset 0 0 0 1.5px #BFAE90; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; font-weight: 600; font-size: 16px;">Everywhere else (3)''' + svg('back', 18).replace('M15 5l-7 7 7 7', 'M9 6l6 6-6 6') + '''</button></sc-if>
    <sc-if value="{{ wide }}" hint-placeholder-val="{{ false }}">
''' + sect('Elsewhere') + '\n    <section class="st" style="padding: 4px 14px;">' + row('Coffee beans', 'Groceries · bought today', '', True, 'Groceries.dc.html') + row('Buy coffee filters', 'To-dos · this week', '', False, 'Todos.dc.html') + row('Coffee with Maya', 'Calendar · Sat 21 Nov, 10' + NB + 'am', '', False, 'Calendar.dc.html') + '''</section>
    </sc-if>
  </div>
''' + bar('Budget') + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { scoped: true, month: 'Oct' }; }
  renderVals() {
    var self = this, st = this.state;
    var all = [['Blue Copper', 'Eating out · Oct 3', '$5.25', 'Oct'], ['Blue Copper', 'Eating out · Oct 11', '$5.25', 'Oct'], ['Starbucks', 'Eating out · Oct 19', '$6.10', 'Oct'], ['Blue Copper', 'Eating out · Nov 6', '$5.25', 'Nov']];
    var rows = all.filter(function (r) { return !st.month || r[3] === st.month; }).map(function (r, i) {
      return { t: r[0], s: r[1], v: r[2], style: 'display: flex; align-items: center; gap: 12px; min-height: 56px;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : '') };
    });
    var chips = st.scoped ? ['Oct', 'Nov', 'Eating out'].map(function (m) {
      var on = st.month === m;
      return { label: m, on: on ? 'true' : 'false', pick: function () { self.setState({ month: on ? null : m }); },
        style: 'flex: none; min-height: 44px; padding: 0 12px; border-radius: 12px; border: 0; font-size: 14px; ' + (on ? 'background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #3557A6;' : 'background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90;') };
    }) : [];
    return { scoped: st.scoped, wide: !st.scoped, chips: chips, rows: rows, budgetHead: 'Budget · ' + rows.length,
      widen: function () { self.setState({ scoped: false, month: null }); } };
  }
}'''
files['Search'] = page('Search', body, script)

# ---------- Welcome -> Day one, skipped picks (onboarding 2.4): starter tiles plus the first prompt ----------
body = ROOT + '\n' + scroller() + '''
    <div style="display: flex; align-items: center; justify-content: space-between; min-height: 44px;"><span style="display: flex; gap: 8px; align-items: center; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 17px;"><svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="9" height="9" rx="2" fill="#E3A72F"></rect><rect x="12" y="1" width="9" height="9" rx="2" fill="#5B7DB1"></rect><rect x="1" y="12" width="9" height="9" rx="2" fill="#8DB580"></rect><rect x="12" y="12" width="9" height="9" rx="2" fill="#9C6BA8"></rect></svg>quilt</span></div>
    <header style="display: flex; flex-direction: column; gap: 4px;"><h1 style="margin: 0; ''' + disp(30) + ''' line-height: 1.05;">Afternoon.</h1><p style="margin: 0; font-size: 17px; line-height: 1.35;">Nothing logged yet. Add a receipt or tell Clair something.</p></header>
    <p style="margin: 0; font-size: 16px; line-height: 1.45;">No apps yet. Say what you want to keep track of, or start from one of these.</p>
    <a href="Build.dc.html" style="display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 6px 0 14px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 16px; color: #665847;">Track my subscriptions and…<span style="margin-left: auto; width: 40px; height: 40px; border-radius: 10px; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">''' + svg('send') + '''</span></a>
''' + sect('Or start from one of these') + '''
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; border-radius: 16px; overflow: hidden;">''' + \
    ''.join('<a class="qp" href="Preview.dc.html" style="min-height: 84px; padding: 12px; box-sizing: border-box; background: ' + DYE[a] + '; display: flex; flex-direction: column; justify-content: space-between; position: relative;"><span aria-hidden="true" style="position: absolute; inset: 3px; border: 1.5px dashed rgba(42,33,25,0.28); border-radius: 7px;"></span><span style="position: relative; display: flex; gap: 5px; align-items: center; font-size: 12.5px; font-weight: 600;">' + svg(ICON[a], 16) + a + '</span><span style="position: relative; font-size: 12.5px; color: #665847;">' + why + '</span></a>'
            for a, why in [('Subscriptions', 'the money you forget'), ('Groceries', 'from a receipt photo'), ('Classes', 'every due date'), ('Workout', 'sets, reps, PRs')]) + '''</div>
  </div>
  <nav aria-label="Clair" style="''' + BAR + '''"><span style="flex: 1; background: #FFFDF8; border-radius: 16px 0 0 16px; display: grid; place-items: center; padding: 0 12px; font-size: 13px; color: #665847; text-align: center;">Your most-used apps get pinned here</span>''' + clairbtn().strip() + '</nav>' + CLOSE
files['Welcome'] = page('Day one, skipped picks', body)

# ---------- Empty -> new app ready ----------
body = ROOT + '\n' + scroller() + '\n' + topbar('Tabs.dc.html', 'Back to your apps', '', '<a href="Rule.dc.html" aria-label="App menu" style="width: 44px; height: 44px; display: grid; place-items: center; font-weight: 800; letter-spacing: 2px;">···</a>') + '\n' + \
    title('Subscriptions', None, tag('new')) + '\n' + \
    '    <span style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 13px; color: #665847;">Connected to <span style="display: inline-flex; gap: 5px; align-items: center;">' + dot('Calendar') + 'Calendar</span><span style="display: inline-flex; gap: 5px; align-items: center;">' + dot('Budget') + 'Budget</span></span>\n' + \
    card('<span style="align-self: center;">' + spool('hello', 96) + '</span><b style="' + disp(20) + ' text-align: center;">Subscriptions is ready</b><p style="margin: 0; font-size: 15px; text-align: center;">Add your first one. The fastest way is usually a photo of the bill or email.</p>', 'st', ' align-items: stretch; padding: 22px 16px;') + '\n' + \
    '    <div style="display: grid; gap: 8px;">' + btn(svg('cam') + 'Tell Clair or add a photo', 'ClairSheet.dc.html', False) + btn(svg('type') + 'Type one in', 'Preview.dc.html', False) + btn(svg('import') + 'Bring 4 in from Budget', 'Budget.dc.html', False) + '</div>\n  </div>\n' + bar() + CLOSE
files['Empty'] = page('New app ready', body)

# ---------- Clair chat ----------
body = ROOT + '''
  <header style="position: absolute; top: 0; left: 0; right: 0; z-index: 2; padding: 40px 16px 10px; box-sizing: border-box; display: flex; align-items: center; gap: 10px; background: #F4EEE1; background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1.5px; background-repeat: repeat-x; background-position: 0 100%;">
    <a href="Main.dc.html" aria-label="Back to Home" style="width: 44px; height: 44px; margin-left: -12px; display: grid; place-items: center;">''' + svg('back', 22, '#2A2119') + '''</a>''' + spool('hello', 44) + '''
    <span style="flex: 1; display: flex; flex-direction: column;"><h1 style="margin: 0; ''' + disp(17) + '''">Ask Clair</h1><span style="font-size: 13px; color: #665847;">Answers from your apps only</span></span>
    ''' + link('<span class="num">32</span> credits', 'You.dc.html') + '''
  </header>
  <div class="scr" style="position: absolute; top: 100px; left: 0; right: 0; bottom: 150px; overflow-y: auto; padding: 16px 16px 24px; box-sizing: border-box; display: grid; grid-template-columns: minmax(0, 1fr); align-content: start; gap: 12px;">
    <div style="justify-self: end; max-width: 85%; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #EEE6D6; font-size: 16px;">How much did I spend on food this week?</div>
    <p style="margin: 0; font-size: 16px; line-height: 1.5;"><b>$71.20.</b> $35.83 on groceries and $35.37 eating out. You're on pace for your $200 grocery budget.</p>
    ''' + link('From Budget · 6 rows', 'Budget.dc.html', True, 'justify-self: start; margin-top: -8px;') + '''
    <div style="justify-self: end; max-width: 85%; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #EEE6D6; font-size: 16px;">add oat milk to groceries</div>
    <sc-if value="{{ pending }}" hint-placeholder-val="{{ true }}">
      <section class="st basted" style="padding: 14px; display: flex; flex-direction: column; gap: 8px;"><span style="''' + LBL + '''">Waiting for your OK · Groceries</span><span style="font-size: 16px;">Add <b>Oat milk</b>, 1 carton, to your list?</span><div style="display: flex; gap: 8px;">''' + btn('Add to Groceries', None, True, 'add') + '''</div></section>
    </sc-if>
    <sc-if value="{{ added }}" hint-placeholder-val="{{ false }}">
      <section class="st" style="padding: 12px 14px; display: flex; align-items: center; gap: 10px;">''' + svg('check', 18, '#1F6B5E', '2.2') + '''<span style="flex: 1; font-size: 16px;">Added Oat milk to Groceries.</span>''' + btn('Undo', None, False, 'undo') + '''</section>
    </sc-if>
  </div>
  <div style="position: absolute; left: 0; right: 0; bottom: 96px; padding: 8px 16px 0; box-sizing: border-box; display: flex; flex-direction: column; gap: 8px; background: #F4EEE1;">
    <div class="chips" style="display: flex; gap: 6px; overflow-x: auto; margin: 0 -16px; padding: 0 16px; scrollbar-width: none;">''' + \
    ''.join('<a class="chip" href="' + h + '" style="flex: none; min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; display: flex; align-items: center; font-size: 14px;">' + t + '</a>' for t, h in [('build a classes app', 'Build.dc.html'), ("what's due this week?", 'Calendar.dc.html'), ('scan a receipt', 'Receipt.dc.html')]) + '''</div>
  </div>
''' + bar() + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { added: false }; }
  renderVals() {
    var self = this;
    return { pending: !this.state.added, added: this.state.added, add: function () { self.setState({ added: true }); }, undo: function () { self.setState({ added: false }); } };
  }
}'''
files['Clair'] = page('Ask Clair', body, script)

# ---------- Build -> Describe ----------
body = ROOT + '\n' + scroller(20) + '\n' + topbar('Tabs.dc.html', 'Back to your apps', 'New app') + '\n' + \
    '    <div style="display: flex; gap: 12px; align-items: center;">' + spool('hello', 44) + h1('What do you want to keep track of?', 24).strip() + '</div>\n' + \
    '''    <label style="display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #665847;">Say it the way you'd tell a friend<textarea rows="3" enterkeyhint="send" style="border: 0; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 12px; font: inherit; font-size: 16px; line-height: 1.45; color: #2A2119; resize: none;">Track my subscriptions and warn me before they renew</textarea></label>
    <div class="chips" style="display: flex; gap: 6px; overflow-x: auto; margin: 0 -16px; padding: 0 16px; scrollbar-width: none;">''' + \
    ''.join('<span class="chip" style="flex: none; min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; display: flex; align-items: center; font-size: 14px;">' + t + '</span>' for t in ['log my lifts and PRs', 'plan meals from my pantry', 'track internship applications']) + '</div>\n' + \
    '    ' + btn('Build it', 'Preview.dc.html') + '\n' + sect('Or start from one of these', 'Skips to preview') + '\n' + \
    '    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">' + \
    ''.join('<a class="qp" href="Preview.dc.html" style="min-height: 84px; border-radius: 16px; background: ' + DYE[a] + '; display: flex; flex-direction: column; justify-content: space-between; padding: 12px;">' + svg(ICON[a]) + '<span style="display: flex; flex-direction: column;"><b style="font-size: 15px;">' + n + '</b><span style="font-size: 12.5px; color: #665847;">' + b + '</span></span></a>'
            for a, n, b in [('Subscriptions', 'Subscriptions', '4 blocks'), ('Workout', 'Lift log', '5 blocks'), ('Meals', 'Meal plan', '4 blocks'), ('Calendar', 'Job hunt', '4 blocks')]) + '</div>\n  </div>' + CLOSE
files['Build'] = page('New app: describe', body)

# ---------- Preview -> Clair built it, pick a layout ----------
LAY = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { i: 0 }; }
  renderVals() {
    var self = this, st = this.state;
    var names = ['List first', 'Calendar first', 'Summary first'];
    var list = { k: 'Renewals', kind: 'list' }, total = { k: 'Monthly total', kind: 'total' }, cal = { k: 'Renewal dates', kind: 'cal' }, cap = { k: 'Under your $40 cap', kind: 'cap' };
    var orders = [[list, total, cal], [cal, list, total], [total, cap, list]];
    var pieces = orders[st.i].map(function (p) { return { k: p.k, isList: p.kind === 'list', isTotal: p.kind === 'total', isCal: p.kind === 'cal', isCap: p.kind === 'cap' }; });
    var subs = [['Spotify', 'renews Sun 22 Nov', '$11.99'], ['Hulu', 'not opened in 45 days', '$9.99'], ['Adobe CC, student', 'renews Thu 3 Dec', '$13.49'], ['iCloud 50 GB', 'renews Wed 9 Dec', '$2.99']].map(function (s, j) {
      return { n: s[0], w: s[1], p: s[2], style: 'display: flex; align-items: center; gap: 10px; min-height: 52px;' + (j ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : '') };
    });
    var days = [['F', '20'], ['S', '21'], ['S', '22'], ['M', '23'], ['T', '24'], ['W', '25'], ['T', '26']].map(function (d) { return { d: d[0], n: d[1], style: 'display: flex; flex-direction: column; align-items: center; padding: 6px 0; border-radius: 8px; font-size: 13px; font-variant-numeric: tabular-nums; ' + (d[1] === '22' ? 'background: #3557A6; color: #FFFFFF;' : 'background: #F3ECDD; color: #665847;') }; });
    return { name: names[st.i], pieces: pieces, subs: subs, days: days,
      dots: names.map(function (n, j) { return { style: 'width: 7px; height: 7px; border-radius: 50%; background: ' + (j === st.i ? '#2A2119' : '#BFAE90') + ';' }; }),
      prev: function () { self.setState({ i: (st.i + 2) % 3 }); }, next: function () { self.setState({ i: (st.i + 1) % 3 }); } };
  }
}'''
chev_r = svg('back').replace('M15 5l-7 7 7 7', 'M9 6l6 6-6 6')
body = ROOT + '\n' + scroller(100) + '\n' + topbar('Build.dc.html', 'Back to describe', 'Preview') + '''
    <div style="display: flex; gap: 12px; align-items: center; ''' + CLAIR + '''">''' + spool('waiting', 30) + '''Built 4 pieces. Here are 3 layouts.</div>
    <div class="st" role="group" aria-label="Layouts" style="display: flex; align-items: center; justify-content: space-between; padding: 4px;">
      <button type="button" onClick="{{ prev }}" aria-label="Previous layout" style="width: 44px; height: 44px; border: 0; background: transparent; display: grid; place-items: center;">''' + svg('back') + '''</button>
      <span style="display: flex; flex-direction: column; align-items: center; gap: 4px;"><b style="font-size: 15px;">{{ name }}</b><span style="display: flex; gap: 5px;"><sc-for list="{{ dots }}" as="d" hint-placeholder-count="3"><i style="{{ d.style }}"></i></sc-for></span></span>
      <button type="button" onClick="{{ next }}" aria-label="Next layout" style="width: 44px; height: 44px; border: 0; background: transparent; display: grid; place-items: center;">''' + chev_r + '''</button>
    </div>
''' + title('Subscriptions') + '''
    <p style="margin: 0; font-size: 12.5px; color: #665847;">Example rows · cleared when you add it, unless you keep them</p>
    <sc-for list="{{ pieces }}" as="p" hint-placeholder-count="3">
      <section class="st" style="padding: 12px 14px; display: flex; flex-direction: column; gap: 8px;">
        <span style="''' + LBL + '''">{{ p.k }}</span>
        <sc-if value="{{ p.isList }}" hint-placeholder-val="{{ true }}"><div><sc-for list="{{ subs }}" as="s" hint-placeholder-count="4"><div style="{{ s.style }}"><span style="flex: 1; display: flex; flex-direction: column;"><span style="''' + ROWT + '''">{{ s.n }}</span><span style="''' + ROWM + '''">{{ s.w }}</span></span><span style="font-size: 13px; color: #665847; padding: 2px 8px; border-radius: 4px; box-shadow: inset 0 0 0 1px #BFAE90;">example</span><span style="font-family: 'DM Mono', monospace; font-size: 14px;">{{ s.p }}</span></div></sc-for></div></sc-if>
        <sc-if value="{{ p.isTotal }}" hint-placeholder-val="{{ false }}"><div style="display: flex; align-items: baseline; gap: 8px;"><span style="''' + disp(34, NUM) + '''">$38.46</span><span style="font-size: 12.5px; color: #665847;">a month · 4 subscriptions</span></div></sc-if>
        <sc-if value="{{ p.isCal }}" hint-placeholder-val="{{ false }}"><div style="display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px;"><sc-for list="{{ days }}" as="d" hint-placeholder-count="7"><span style="{{ d.style }}">{{ d.d }}<b>{{ d.n }}</b></span></sc-for></div></sc-if>
        <sc-if value="{{ p.isCap }}" hint-placeholder-val="{{ false }}"><div style="height: 8px; border-radius: 4px; background: #EEE6D6; overflow: hidden;"><div style="width: 96%; height: 100%; background: #1F6B5E;"></div></div><span style="font-size: 12.5px; color: #665847;">$38.46 of $40 · 96%</span></sc-if>
      </section>
    </sc-for>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 30px; display: grid; grid-template-columns: 1fr 1.4fr; gap: 8px;">''' + btn(svg('layout') + 'Arrange', 'Arrange.dc.html', False) + btn('Use this layout', 'Connect.dc.html') + '</div>' + CLOSE
files['Preview'] = page('New app: preview', body, LAY)

# ---------- Arrange (new) ----------
body = ROOT + '\n' + scroller(20) + '\n' + topbar('Preview.dc.html', 'Back to preview', h1mid('Arrange'), link('Done', 'Connect.dc.html', False, 'padding: 0 4px;')) + '''
    <p style="margin: 0; font-size: 12.5px; color: #665847;">Drag the grip to reorder. The rows are examples.</p>
    <sc-for list="{{ pieces }}" as="p" hint-placeholder-count="4">
      <section class="st" style="padding: 8px 8px 10px; display: flex; flex-direction: column; gap: 6px;">
        <div style="display: flex; align-items: center; gap: 6px;">
          <span class="grip" aria-hidden="true" style="width: 44px; height: 44px; display: grid; place-items: center; color: #665847;">''' + svg('grip') + '''</span>
          <span style="flex: 1; display: flex; align-items: center; gap: 8px;"><span style="{{ p.mark }}"></span><b style="font-size: 16px;">{{ p.name }}</b></span>
          <button type="button" onClick="{{ p.rip }}" aria-label="Remove {{ p.name }}" style="width: 44px; height: 44px; border: 0; background: transparent; display: grid; place-items: center;">''' + svg('rip') + '''</button>
        </div>
        <sc-if value="{{ p.isList }}" hint-placeholder-val="{{ false }}"><div role="group" aria-label="View type" style="display: inline-flex; align-self: flex-start; margin-left: 50px; border-radius: 9px; box-shadow: inset 0 0 0 1.5px #BFAE90; overflow: hidden;"><sc-for list="{{ views }}" as="v" hint-placeholder-count="3"><button type="button" onClick="{{ v.pick }}" aria-pressed="{{ v.on }}" style="{{ v.style }}">{{ v.label }}</button></sc-for></div></sc-if>
        <span style="margin-left: 50px; font-size: 12.5px; color: #665847;">{{ p.desc }}</span>
      </section>
    </sc-for>
    <sc-if value="{{ ripped }}" hint-placeholder-val="{{ false }}"><div role="status" style="display: flex; align-items: center; gap: 10px; padding: 8px 8px 8px 14px; border-radius: 12px; background: #2A2119; color: #FBF6EC; font-size: 15px;">Removed a piece.<button type="button" onClick="{{ undo }}" style="margin-left: auto; min-height: 44px; padding: 0 12px; border-radius: 9px; border: 1.5px solid rgba(251,246,236,0.5); background: transparent; color: #FBF6EC; font-weight: 600;">Undo</button></div></sc-if>
    ''' + btn(svg('plus') + 'Add a block', None, False) + '''
    <div class="chalk" style="display: flex; align-items: center; gap: 8px; padding: 6px 6px 6px 14px;"><span style="flex: 1; ''' + CLAIR + '''">Tell Clair: put the total on top</span><span style="width: 44px; height: 44px; border-radius: 10px; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">''' + svg('send') + '''</span></div>
  </div>''' + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { gone: {}, view: 'list' }; }
  renderVals() {
    var self = this, st = this.state;
    var mk = function (c) { return 'width: 18px; height: 18px; border-radius: 4px; background: ' + c + '; box-shadow: inset 0 0 0 1.3px #2A2119;'; };
    var all = [['Renewals', '#E3A72F', 'Spotify, Hulu, Adobe, iCloud', true], ['Monthly total', '#D3ECE7', '$38.46 a month', false], ['Renewal dates', '#DCE4F3', 'Sun 22: Spotify', false], ['Add a subscription', '#DCE4F3', 'name, price, renews on', false]];
    var pieces = all.filter(function (p, i) { return !st.gone[i]; }).map(function (p) {
      var i = all.indexOf(p);
      return { name: p[0], mark: mk(p[1]), desc: p[0] === 'Renewals' ? 'Shown as ' + st.view + ' · ' + p[2] : p[2], isList: p[3],
        rip: function () { var g = Object.assign({}, st.gone); g[i] = true; self.setState({ gone: g, last: i }); } };
    });
    var views = ['list', 'table', 'calendar'].map(function (v) {
      var on = st.view === v;
      return { label: v.charAt(0).toUpperCase() + v.slice(1), on: on ? 'true' : 'false', pick: function () { self.setState({ view: v }); }, style: 'min-height: 44px; min-width: 52px; padding: 0 10px; border: 0; font-size: 12.5px; ' + (on ? 'background: #2A2119; color: #FBF6EC;' : 'background: transparent; color: #665847;') };
    });
    return { pieces: pieces, views: views, ripped: st.last !== undefined && st.gone[st.last],
      undo: function () { var g = Object.assign({}, st.gone); delete g[st.last]; self.setState({ gone: g, last: undefined }); } };
  }
}'''
files['Arrange'] = page('New app: arrange', body, script)

# ---------- Connect & add (new) ----------
body = ROOT + '\n' + scroller(100) + '\n' + topbar('Preview.dc.html', 'Back to preview', h1mid('Add to my apps')) + '\n' + \
    card('<div style="display: flex; gap: 10px; align-items: center;"><span style="width: 48px; height: 48px; border-radius: 12px; background: #EADCF0; display: grid; place-items: center; flex: none;">' + svg('repeat', 22) + '</span><label style="flex: 1; display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; color: #665847;">Name<input value="Subscriptions" autocapitalize="words" enterkeyhint="done" style="min-height: 44px; border: 0; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 0 12px; font: inherit; font-size: 16px; color: #2A2119;"></label></div>'
         + '<div role="radiogroup" aria-label="Colour" style="display: flex; gap: 8px; flex-wrap: wrap;">' + ''.join('<span role="radio" aria-checked="' + ('true' if c == '#EADCF0' else 'false') + '" aria-label="' + n + '" style="width: 32px; height: 32px; border-radius: 50%; background: ' + c + '; box-shadow: ' + ('0 0 0 2px #FFFDF8, 0 0 0 4px #2A2119' if c == '#EADCF0' else 'inset 0 0 0 1px rgba(42,33,25,0.2)') + '; margin: 6px 2px;"></span>' for n, c in [('butter', '#FBEBC4'), ('sage', '#DDEBD2'), ('sea glass', '#D3ECE7'), ('apricot', '#F8DCC2'), ('chambray', '#DCE4F3'), ('lavender', '#EADCF0'), ('pear', '#E7EBC2'), ('blush', '#F3DCE0')]) + '</div>') + '\n' + \
    sect('Connect to your other apps', "Clair's picks") + '''
    <section class="st" style="padding: 4px 6px 4px 14px;">
      <sc-for list="{{ conns }}" as="c" hint-placeholder-count="3">
        <div style="{{ c.row }}"><span style="{{ c.chip }}"></span><span style="flex: 1; display: flex; flex-direction: column;"><span style="''' + ROWT + '''">{{ c.t }}</span><span style="font-size: 12.5px; color: #665847;">{{ c.s }}</span></span>
          <button type="button" role="switch" aria-checked="{{ c.on }}" aria-label="{{ c.t }}" onClick="{{ c.toggle }}" style="{{ c.sw }}"><span style="width: 26px; height: 26px; border-radius: 50%; background: #FFFFFF;"></span></button></div>
      </sc-for>
    </section>
    <label style="display: flex; align-items: center; gap: 10px; min-height: 44px; font-size: 15px;"><input type="checkbox" style="width: 20px; height: 20px; accent-color: #3557A6;"> Keep the example rows</label>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 30px; display: grid; grid-template-columns: 1fr 1.6fr; gap: 8px;">''' + btn('Skip', 'Empty.dc.html', False) + btn('Add to my apps', 'Empty.dc.html') + '</div>' + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { off: { 2: true } }; }
  renderVals() {
    var self = this, st = this.state;
    var conns = [['Renewal dates → Calendar', 'Each renewal shows on its day, 3 days warning', '#DCE4F3'], ['Cost → Budget', 'Counts in Subscriptions ($40 cap)', '#D3ECE7'], ['Unused 30 days → Home', 'Clair suggests cancelling what you don\\u2019t open', '#FBEBC4']].map(function (c, i) {
      var on = !st.off[i];
      return { t: c[0], s: c[1], on: on ? 'true' : 'false', toggle: function () { var o = Object.assign({}, st.off); o[i] = on; self.setState({ off: o }); },
        row: 'display: flex; align-items: center; gap: 10px; min-height: 64px;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : ''),
        chip: 'flex: none; width: 28px; height: 28px; border-radius: 8px; background: ' + c[2] + ';',
        sw: 'flex: none; width: 60px; height: 44px; padding: 9px 4px; border: 0; background: transparent; display: flex; ' + (on ? 'justify-content: flex-end;' : 'justify-content: flex-start;') + ' align-items: center; border-radius: 22px; box-shadow: inset 0 0 0 50px ' + (on ? '#3557A6' : '#BFAE90') + '; background-clip: content-box;' };
    });
    return { conns: conns };
  }
}'''
files['Connect'] = page('New app: connect and add', body, script)

# ---------- Rule -> reminder from an insight ----------
body = ROOT + '\n' + scroller(100) + '\n' + topbar('Main.dc.html', 'Back to Home', h1mid('New reminder')) + '\n' + \
    card('<span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">' + chalk_icon() + 'From what Clair noticed</span><span style="' + CLAIR + '">Weeks you scan grocery receipts, you spend <b>$41 less</b> eating out.</span>', 'chalk') + '\n' + \
    sect('When') + '\n' + card('<b style="font-size: 16px;">After a grocery trip shows up</b><span style="font-size: 12.5px; color: #665847;">A purchase at a grocery store in Budget, or a trip in Calendar</span>') + '\n' + \
    sect('Only if') + '\n' + card('<b style="font-size: 16px;">No receipt was scanned that day</b><span style="font-size: 12.5px; color: #665847;">Groceries has no new items from a photo</span>') + '\n' + \
    sect('Then') + '\n' + card('<b style="font-size: 16px;">Remind me to scan the receipt</b><span style="font-size: 12.5px; color: #665847;">Shows in Needs your OK on Home, once, by 9&nbsp;pm</span>') + '''
    <section class="st" style="padding: 6px 6px 6px 14px; display: flex; align-items: center; gap: 10px; min-height: 60px;"><span style="flex: 1; font-size: 16px;">Reminder is on</span><button type="button" role="switch" aria-checked="{{ onAria }}" aria-label="Reminder on" onClick="{{ toggle }}" style="{{ sw }}"><span style="width: 26px; height: 26px; border-radius: 50%; background: #FFFFFF;"></span></button></section>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 30px; display: grid; grid-template-columns: 1fr 1.6fr; gap: 8px;">''' + btn('Cancel', 'Main.dc.html', False) + btn('Save reminder', 'Main.dc.html') + '</div>' + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { on: true }; }
  renderVals() {
    var self = this, on = this.state.on;
    return { onAria: on ? 'true' : 'false', toggle: function () { self.setState({ on: !on }); },
      sw: 'flex: none; width: 60px; height: 44px; padding: 9px 4px; border: 0; background: transparent; display: flex; ' + (on ? 'justify-content: flex-end;' : 'justify-content: flex-start;') + ' align-items: center; border-radius: 22px; box-shadow: inset 0 0 0 50px ' + (on ? '#3557A6' : '#BFAE90') + '; background-clip: content-box;' };
  }
}'''
files['Rule'] = page('Reminder from an insight', body, script)

# ---------- Workout ----------
body = ROOT + '\n' + scroller() + '\n' + topbar('Main.dc.html', 'Back to Home', '', '<a href="Arrange.dc.html" aria-label="App menu" style="width: 44px; height: 44px; display: grid; place-items: center; font-weight: 800; letter-spacing: 2px;">···</a>') + '\n' + title('Workout') + '''
    <div role="tablist" aria-label="Workout tabs" style="display: flex; gap: 2px; overflow-x: auto; margin: 0 -16px; padding: 0 12px; scrollbar-width: none; background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1.5px; background-repeat: repeat-x; background-position: 0 100%;">
      <sc-for list="{{ tabs }}" as="t" hint-placeholder-count="5"><button type="button" role="tab" aria-selected="{{ t.sel }}" onClick="{{ t.pick }}" style="{{ t.style }}">{{ t.label }}</button></sc-for>
    </div>
    <sc-if value="{{ isToday }}" hint-placeholder-val="{{ true }}">
      <section class="st" style="padding: 14px; display: flex; flex-direction: column; gap: 8px;"><div style="display: flex; justify-content: space-between; font-size: 13px; color: #665847;"><span>Next up · today 6&nbsp;pm</span><span>5 exercises · about 45&nbsp;min</span></div><span style="''' + disp(30) + '''">Pull day</span>''' + btn('Start pull day', 'Session.dc.html') + '''</section>
      <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">''' + ''.join('<section class="st" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 13px; color: #665847;">' + k + '</span><span style="font-family: \'Hanken Grotesk\', sans-serif; font-size: 18px; font-weight: 600; white-space: nowrap;' + NUM + '">' + v + '</span></section>' for k, v in [('Lifted this week', '12,450' + NB + 'lb'), ('New bests', '2')]) + '''</div>
      <section class="st" style="padding: 14px; display: flex; flex-direction: column; gap: 8px;"><div style="display: flex; justify-content: space-between; font-size: 14px;"><b>Sessions this week</b><span style="font-family: 'Hanken Grotesk', sans-serif; font-weight: 600; color: #665847; font-variant-numeric: tabular-nums;">3 of 4</span></div><div style="height: 8px; border-radius: 4px; background: #EEE6D6; overflow: hidden;"><div style="width: 75%; height: 100%; background: #1F6B5E;"></div></div></section>
      <section class="chalk" style="padding: 12px 16px; display: flex; gap: 12px; align-items: center;">''' + chalk_icon() + '''<span style="''' + CLAIR + '''">You did 10 × 120 on lat pulldown last week. Try 125 today.</span></section>
    </sc-if>
    <sc-if value="{{ isOther }}" hint-placeholder-val="{{ false }}">
      <section class="st" style="padding: 18px; display: flex; flex-direction: column; gap: 6px;"><b style="font-size: 16px;">{{ otherTitle }}</b><span style="font-size: 15px;">{{ otherBody }}</span></section>
    </sc-if>
  </div>
''' + bar() + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { tab: 'today' }; }
  renderVals() {
    var self = this, t = this.state.tab;
    var names = ['today', 'log', 'history', 'progress', 'routines'];
    var copy = { log: ['Log', 'Every set you log, newest first.'], history: ['History', '41 sessions since September.'], progress: ['Progress', 'Lat pulldown: 100 → 120 lb in 8 weeks.'], routines: ['Routines', 'Pull, push, legs; Clair can build a new one.'] };
    return { isToday: t === 'today', isOther: t !== 'today', otherTitle: t !== 'today' ? copy[t][0] : '', otherBody: t !== 'today' ? copy[t][1] : '',
      tabs: names.map(function (n) { var on = n === t; return { label: n.charAt(0).toUpperCase() + n.slice(1), sel: on ? 'true' : 'false', pick: function () { self.setState({ tab: n }); },
        style: 'flex: none; min-height: 44px; min-width: 44px; padding: 0 12px; border: 0; border-radius: 0; background: transparent; font-size: 15px; ' + (on ? 'color: #2A2119; font-weight: 600; box-shadow: inset 0 -2.5px 0 #3557A6;' : 'color: #665847;') }; }) };
  }
}'''
files['Workout'] = page('Workout', body, script)

# ---------- Session ----------
body = ROOT + '\n' + scroller(110) + '\n' + topbar('Workout.dc.html', 'Back to Workout', h1mid('Pull day <span class="num">· 18:42</span>'), link('Finish', 'Workout.dc.html', False, 'padding: 0 4px;')) + '''
    <div style="display: flex; justify-content: space-between; font-size: 13px; color: #665847;"><span>Exercise 2 of 5</span><span style="font-family: 'DM Mono', monospace;">27%</span></div>
    <div style="height: 6px; border-radius: 3px; background: #EEE6D6; overflow: hidden;"><div style="width: 27%; height: 100%; background: #1F6B5E;"></div></div>
    <section class="st" style="padding: 14px; display: flex; flex-direction: column; gap: 10px;">
      <div style="display: flex; justify-content: space-between; align-items: baseline;"><b style="''' + disp(22) + '''">Lat pulldown</b><span style="font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: #F8DCC2;''' + NUM + '''">Rest 0:47</span></div>
      <span style="font-size: 13px; color: #665847;''' + NUM + '''">3 × 10 · best 120&nbsp;lb × 10</span>
      <span style="display: flex; gap: 8px; align-items: center; font-size: 15px;">''' + svg('check', 18, '#1F6B5E', '2.2') + '''Set 1 · 12 reps × 110&nbsp;lb</span>
      <span style="font-size: 13px; color: #665847;">Set 2</span>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <sc-for list="{{ steppers }}" as="s" hint-placeholder-count="2">
          <div style="display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 12px; color: #665847;">{{ s.label }}</span><div style="display: flex; align-items: center; justify-content: space-between; border-radius: 12px; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 2px;"><button type="button" onClick="{{ s.down }}" aria-label="Less {{ s.label }}" class="btn" style="width: 44px; height: 44px; border: 0; border-radius: 8px; background: #F3ECDD; font-size: 18px;">−</button><b style="font-family: 'DM Mono', monospace; font-size: 18px;''' + NUM + '''">{{ s.v }}</b><button class="btn" type="button" onClick="{{ s.up }}" aria-label="More {{ s.label }}" style="width: 44px; height: 44px; border: 0; border-radius: 8px; background: #F3ECDD; font-size: 18px;">+</button></div></div>
        </sc-for>
      </div>
      <sc-if value="{{ pr }}" hint-placeholder-val="{{ false }}"><div style="display: flex; gap: 12px; align-items: center; font-size: 15px;">''' + spool('proud', 30) + '''<span><b>New best</b> on lat pulldown. Logged when you finish the set.</span></div></sc-if>
    </section>
''' + sect('Up next') + '\n    <section class="st" style="padding: 4px 14px;">' + row('Seated cable row', '3 × 12 · 100' + NB + 'lb', '', True) + row('Face pulls', '3 × 15 · 40' + NB + 'lb') + '''</section>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 30px; display: grid; grid-template-columns: 1fr 2fr; gap: 8px;">''' + btn('Skip', None, False) + btn('Log set 2') + '</div>' + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { reps: 10, wt: 120 }; }
  renderVals() {
    var self = this, st = this.state;
    return { pr: st.wt > 120 || (st.wt === 120 && st.reps > 10),
      steppers: [
        { label: 'reps', v: st.reps, down: function () { self.setState({ reps: Math.max(1, st.reps - 1) }); }, up: function () { self.setState({ reps: st.reps + 1 }); } },
        { label: 'weight, lb', v: st.wt, down: function () { self.setState({ wt: Math.max(5, st.wt - 5) }); }, up: function () { self.setState({ wt: st.wt + 5 }); } }
      ] };
  }
}'''
files['Session'] = page('Log a set', body, script)

# ---------- To-dos ----------
body = ROOT + '\n' + scroller(150) + '\n' + back('Main.dc.html', 'Back to Home') + '\n' + title('To-dos') + '''
    <p style="margin: 0; font-size: 16px;"><b>{{ left }}</b> left today.</p>
''' + sect('Today · Fri 20 Nov') + '''
    <section class="st" style="padding: 4px 0;">
      <sc-for list="{{ items }}" as="i" hint-placeholder-count="4">
        <button class="rw" type="button" onClick="{{ i.toggle }}" aria-pressed="{{ i.done }}" style="{{ i.style }}"><span aria-hidden="true" style="{{ i.box }}">''' + svg('check', 14, '#FFFFFF', '2.4') + '''</span><span style="flex: 1; display: flex; flex-direction: column; text-align: left;"><span style="{{ i.nameStyle }}">{{ i.t }}</span><span style="font-size: 12px; color: #665847;">{{ i.s }}</span></span><sc-if value="{{ i.late }}" hint-placeholder-val="{{ false }}"><span style="font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: #2A2119; color: #FBF6EC; white-space: nowrap;">Overdue · 2 days</span></sc-if></button>
      </sc-for>
    </section>
''' + sect('This week') + '\n    <section class="st" style="padding: 4px 14px;">' + row('Start CS 3500 project', 'Due Mon 23 Nov · from Classes', '', True, 'Preview.dc.html') + row('Call home', 'Sun 22 Nov') + '''</section>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 96px; display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 4px 0 14px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 16px; color: #665847;">Add a to-do, like "email TA Friday"<span style="margin-left: auto; width: 40px; height: 40px; border-radius: 50%; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">''' + svg('plus') + '''</span></div>
''' + bar('To-dos') + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: { 2: true } }; }
  renderVals() {
    var self = this, st = this.state, left = 0;
    var raw = [['Return library books', 'Marriott Library', true], ['DevDay demo at 3\\u00a0pm', 'Lassonde Studios', false], ['Book flu shot', 'Student health', false], ['Pay Sam back for pizza', '$14 · Budget', false]];
    var items = raw.map(function (r, i) {
      var d = !!st.done[i]; if (!d) left++;
      return { t: r[0], s: r[1], late: r[2] && !d, done: d ? 'true' : 'false', toggle: function () { var o = Object.assign({}, st.done); o[i] = !d; self.setState({ done: o }); },
        style: 'width: 100%; display: flex; align-items: center; gap: 12px; min-height: 56px; padding: 6px 14px; border: 0; background: transparent;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : ''),
        box: 'flex: none; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; ' + (d ? 'background: #1F6B5E;' : 'box-shadow: inset 0 0 0 1.5px #665847;'),
        nameStyle: 'font-size: 16px; font-weight: 500;' + (d ? ' text-decoration: line-through; color: #665847;' : '') };
    });
    return { items: items, left: left };
  }
}'''
files['Todos'] = page('To-dos', body, script)

# ---------- Edit item (new) ----------
body = ROOT + '\n' + scroller() + '\n' + back('Main.dc.html', 'Back to Home') + '\n' + title('Groceries') + '\n' + sect('Bought at Corner Market · 8', 'Swipe or tap') + \
    '\n    <section class="st" style="padding: 4px 14px;">' + ''.join(row(n, s, '', i == 0) for i, (n, s) in enumerate([('Oat milk', '1 carton · from receipt'), ('Eggs', '12'), ('Bananas', '1 bunch'), ('Chicken thighs', '2 lb · use by Tue')])) + '''</section>
  </div>
  <div aria-hidden="true" style="position: absolute; inset: 0; background: rgba(42,33,25,0.32);"></div>
  <section role="dialog" aria-label="Edit item" style="position: absolute; left: 0; right: 0; bottom: 0; background: #F4EEE1; border-radius: 22px 22px 0 0; padding: 12px 16px calc(16px + env(safe-area-inset-bottom, 0px)); display: flex; flex-direction: column; gap: 12px; box-shadow: 0 -10px 30px -18px rgba(42,33,25,0.6);">
    <span aria-hidden="true" style="width: 40px; height: 4px; border-radius: 2px; background: #BFAE90; align-self: center;"></span>
    <h2 style="margin: 0; ''' + disp(20) + '''">Edit item</h2>
''' + ''.join('    <label style="display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; color: #665847;">' + l + '<input value="' + v + '" style="min-height: 44px; border: 0; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 0 12px; font: inherit; font-size: 16px; color: #2A2119;"></label>\n' for l, v in [('Name', 'Oat milk'), ('Amount', '1 carton'), ('Category', 'Dairy')]) + \
    '    <span style="display: flex; gap: 6px; align-items: center; font-size: 12.5px; color: #665847;">' + dot('Budget') + 'From your Corner Market receipt · also in Budget</span>\n' + \
    '    <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 8px;">' + btn(svg('trash') + 'Delete', 'Groceries.dc.html', False) + btn('Save', 'Groceries.dc.html') + '</div>\n  </section>' + CLOSE
files['EditItem'] = page('Edit item', body)

# ---------- You (new) ----------
body = ROOT + '\n' + scroller() + '\n' + topbar('Main.dc.html', 'Back to Home', h1mid('Settings')) + '\n' + sect('What Clair changed', 'All apps') + '''
    <section class="st" style="padding: 4px 14px;">
      <sc-for list="{{ acts }}" as="a" hint-placeholder-count="4"><div style="{{ a.row }}"><span style="flex: 1; display: flex; flex-direction: column;"><span style="{{ a.tStyle }}">{{ a.t }}</span><span style="''' + ROWM + '''">{{ a.s }}</span></span><button class="btn" type="button" onClick="{{ a.flip }}" style="''' + BTN + BTN2 + '''">{{ a.btn }}</button></div></sc-for>
    </section>
''' + sect('Clair credits', 'Free plan') + '\n' + card('<div style="display: flex; align-items: baseline; gap: 8px;"><span style="' + disp(30, NUM) + '">32</span><span style="font-size: 13px; color: #665847;">of 50 left · resets Tue 1 Dec</span></div><div role="meter" aria-valuemin="0" aria-valuemax="50" aria-valuenow="32" aria-label="Clair credits left" style="height: 10px; border-radius: 5px; background: #EEE6D6; overflow: hidden;"><div style="width: 64%; height: 100%; background: #3557A6;"></div></div><span style="font-size: 12.5px; color: #665847;">A chat step is 1, a photo fill 5, building an app 10. At zero, Clair pauses; your apps keep working.</span>') + '\n' + \
    sect('What Clair can read') + '\n' + ''.join('    <label class="st" style="padding: 12px 14px; display: flex; gap: 10px; align-items: flex-start;"><input type="radio" name="read"' + (' checked' if i == 0 else '') + ' style="width: 20px; height: 20px; margin: 2px 0 0; accent-color: #3557A6;"><span style="display: flex; flex-direction: column;"><b style="font-size: 16px; font-weight: 600;">' + t + '</b><span style="font-size: 12.5px; color: #665847;">' + s + '</span></span></label>\n'
    for i, (t, s) in enumerate([('Full help', 'Clair reads your rows to answer and fill apps. Sent to the AI provider only when you ask.'), ('Field names only', 'Clair sees column names, never your values.'), ('Nothing', 'Clair is off. Apps, search and connections still work.')])) + \
    sect('What Clair remembers') + '\n    <section class="st" style="padding: 0 16px;">' + row('3 notes', 'From photos, your apps and what you tell Clair', chev_r, True, 'ClairNotes.dc.html') + '</section>\n' + \
    sect('Your data') + '\n    ' + btn('Export everything (apps + data)', None, False) + '\n    ' + btn('Delete my account', None, False) + '\n  </div>\n' + bar() + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { undone: {} }; }
  renderVals() {
    var self = this, st = this.state;
    var raw = [['Added 8 items from your Corner Market receipt', 'Groceries, Budget, Calendar · 5:41\\u00a0pm'], ['Built the Subscriptions app', 'and connected it to Calendar and Budget · 12:20\\u00a0pm'], ['Set a reminder to cancel Hulu', 'Subscriptions · yesterday'], ['Moved Leg day to 7\\u00a0am', 'Workout · Tue 17 Nov']];
    return { acts: raw.map(function (a, i) {
      var u = !!st.undone[i];
      return { t: a[0], s: u ? 'Undone' : a[1], btn: u ? 'Redo' : 'Undo', tStyle: 'font-size: 16px; font-weight: 500; color: #2A2119;' + (u ? ' text-decoration: line-through; color: #665847;' : ''),
        flip: function () { var o = Object.assign({}, st.undone); o[i] = !u; self.setState({ undone: o }); },
        row: 'display: flex; align-items: center; gap: 10px; min-height: 62px;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : '') };
    }) };
  }
}'''
files['You'] = page('You: activity and settings', body, script)

# ---------- Receipt review (Clair > Photo -> read -> Add to 3 apps) ----------
def flex(html, f): return html.replace('style="', 'style="flex: ' + f + '; ', 1)
body = ROOT + '\n' + scroller(104) + '\n' + back('Groceries.dc.html', 'Back to Groceries') + '''
    <div style="display: flex; gap: 16px; align-items: center;">
      <svg width="54" height="76" viewBox="0 0 44 62" aria-hidden="true" style="flex: none; transform: rotate(-4deg);"><path d="M2 2h40v54l-4-3-4 3-4-3-4 3-4-3-4 3-4-3-4 3-4-3-4 3z" fill="#FFFFFF" stroke="#BFAE90" stroke-width="1.2"></path><path d="M8 10h20M8 16h28M8 21h24M8 26h28M8 31h18M8 36h26M8 44h28" stroke="#665847" stroke-width="1.4" stroke-linecap="round"></path></svg>
      <div style="display: flex; flex-direction: column; gap: 4px;">
        <span style="''' + LBL + '''">Receipt photo · today 5:41&nbsp;pm</span>
        <h1 style="margin: 0; ''' + disp(28) + ''' line-height: 1.05;">Corner Market</h1>
        <span style="font-size: 15px;''' + NUM + '''">{{ count }} of 8 items · {{ total }}</span>
      </div>
    </div>
    <div style="display: flex; gap: 12px; align-items: center; min-height: 44px; ''' + CLAIR + '''">
      <sc-if value="{{ notDone }}" hint-placeholder-val="{{ true }}">''' + spool('waiting', 44) + '''</sc-if><sc-if value="{{ done }}" hint-placeholder-val="{{ false }}">''' + spool('stitched', 44) + '''</sc-if>
      <span>{{ clairLine }}</span>
    </div>
    <section class="{{ listClass }}" aria-label="Items read from the receipt" style="padding: 4px;">
      <sc-for list="{{ items }}" as="i" hint-placeholder-count="8">
        <button class="rw" type="button" onClick="{{ i.toggle }}" aria-pressed="{{ i.on }}" style="{{ i.style }}">
          <span aria-hidden="true" style="{{ i.box }}">''' + svg('check', 14, '#FFFFFF', '2.4') + '''</span>
          <span style="flex: 1; display: flex; flex-direction: column; text-align: left;"><span style="font-size: 16px; font-weight: 500;">{{ i.name }}</span><span style="font-size: 13px; color: #665847;">{{ i.note }}</span></span>
          <span style="font-family: 'DM Mono', monospace; font-size: 14px;''' + NUM + '''">{{ i.price }}</span>
        </button>
      </sc-for>
    </section>
''' + sect('Adding updates 3 apps') + '''
    <section class="st" style="padding: 4px 16px;">
      <sc-for list="{{ effects }}" as="e" hint-placeholder-count="3">
        <a class="rw" href="{{ e.href }}" style="display: flex; align-items: center; gap: 12px; min-height: 56px;">
          <span aria-hidden="true" style="{{ e.dot }}"></span>
          <span style="flex: 1; display: flex; flex-direction: column;"><span style="''' + ROWT + '''">{{ e.app }}</span><span style="''' + ROWM + NUM + '''">{{ e.what }}</span></span>
          <sc-if value="{{ e.changed }}" hint-placeholder-val="{{ false }}">''' + tag() + '''</sc-if>
        </a>
      </sc-for>
    </section>
  </div>
  <div style="position: absolute; left: 16px; right: 16px; bottom: 30px; display: flex; gap: 8px;">
    <sc-if value="{{ notDone }}" hint-placeholder-val="{{ true }}">
      ''' + flex(btn('Not now', 'Main.dc.html', False), '1') + '''
      ''' + flex(btn('Add to 3 apps', None, True, 'add'), '1.6') + '''
    </sc-if>
    <sc-if value="{{ done }}" hint-placeholder-val="{{ false }}">
      ''' + flex(btn('Undo', None, False, 'undo'), '1') + '''
      ''' + flex(btn('See Budget ›', 'Budget.dc.html'), '1.6') + '''
    </sc-if>
  </div>''' + CLOSE
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { off: {}, done: false }; }
  renderVals() {
    var self = this, st = this.state;
    var raw = [['Oat milk', '1 carton', 3.49], ['Eggs, dozen', '12', 4.29], ['Bananas', '1 bunch', 1.87], ['Chicken thighs', '2 lb · use by Tue', 8.62], ['Rice, 5 lb', '1 bag', 6.99], ['Spinach', '1 bag · use by Tue', 3.29], ['Greek yogurt', '32 oz', 4.29], ['Coffee beans', '12 oz', 2.99]];
    var total = 0, count = 0;
    var items = raw.map(function (r, i) {
      var on = !st.off[i];
      if (on) { total += r[2]; count++; }
      return { name: r[0], note: r[1], price: '$' + r[2].toFixed(2), on: on ? 'true' : 'false',
        toggle: function () { if (st.done) return; var o = Object.assign({}, st.off); o[i] = on; self.setState({ off: o }); },
        style: 'width: 100%; display: flex; align-items: center; gap: 12px; min-height: 52px; padding: 6px 12px; border: 0; background: transparent; text-align: left;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : '') + (on ? '' : ' color: #665847;'),
        box: 'flex: none; width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center; ' + (on ? 'background: #1F6B5E;' : 'background: transparent; box-shadow: inset 0 0 0 1.5px #665847;') };
    });
    var left = 412 - total;
    var dot = function (c) { return 'flex: none; width: 12px; height: 12px; border-radius: 50%; background: ' + c + '; box-shadow: inset 0 0 0 1.5px rgba(42,33,25,0.45);'; };
    return {
      items: items, count: count, total: '$' + total.toFixed(2), done: st.done, notDone: !st.done,
      listClass: st.done ? 'st' : 'st basted',
      clairLine: st.done ? 'Added. Groceries, Budget and Calendar are up to date.' : 'I read 8 items. Untick anything wrong, then add.',
      effects: [
        { app: 'Groceries', what: 'Check off ' + count + ' items on your list', href: 'Groceries.dc.html', dot: dot(\'''' + DYE['Groceries'] + '''\'), changed: st.done },
        { app: 'Budget', what: '$412 → $' + Math.round(left) + ' left this month', href: 'Budget.dc.html', dot: dot(\'''' + DYE['Budget'] + '''\'), changed: st.done },
        { app: 'Calendar', what: 'Use the chicken and spinach by Tue 24 Nov', href: 'Calendar.dc.html', dot: dot(\'''' + DYE['Calendar'] + '''\'), changed: st.done }
      ],
      add: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); }
    };
  }
}'''
files['Receipt'] = page('Review receipt', body, script)

# ---------- Clair sheet boards: the sheet over a dimmed Home (Nov 19 decision: the Clair button) ----------
QLOGO = '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="9" height="9" rx="2" fill="#E3A72F"></rect><rect x="12" y="1" width="9" height="9" rx="2" fill="#5B7DB1"></rect><rect x="1" y="12" width="9" height="9" rx="2" fill="#8DB580"></rect><rect x="12" y="12" width="9" height="9" rx="2" fill="#9C6BA8"></rect></svg>'
def backdrop():
    # Home as it sits under the sheet: inert, dimmed by the scrim. Tapping the scrim closes (back to Home).
    return ('  <div aria-hidden="true" inert style="position: absolute; inset: 0; padding: 48px 16px 0; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px;">\n'
            '    <div style="display: flex; align-items: center; justify-content: space-between; min-height: 44px;"><span style="display: flex; gap: 8px; align-items: center; ' + disp(17) + '">' + QLOGO + 'quilt</span>'
            '<span style="width: 44px; height: 44px; border-radius: 50%; background: #F8DCC2; display: grid; place-items: center;">' + svg('user', 18) + '</span></div>\n'
            '    <div style="display: flex; flex-direction: column; gap: 4px;"><span style="' + disp(30) + ' line-height: 1.05;">Evening, Sam.</span><span style="font-size: 17px; line-height: 1.35;"><b class="num">$412</b> left this month. Pull day at <b>6' + NB + 'pm</b>.</span></div>\n'
            + sect('Needs your OK · 4') + '\n'
            + card('<span style="' + LBL + '">From your receipt photo · 5:41' + NB + 'pm</span><div style="display: flex; justify-content: space-between; align-items: baseline;"><b style="font-size: 16px;">Corner Market</b><span style="font-family: \'DM Mono\', monospace; font-size: 15px;' + NUM + '">$35.83</span></div><span style="' + ROWM + '">8 items. Adding updates Groceries, Budget and Calendar.</span>', 'st basted') + '\n'
            + '  </div>\n'
            '  <a href="Main.dc.html" tabindex="-1" aria-hidden="true" style="position: absolute; inset: 0; background: rgba(42,33,25,0.32);"></a>\n')
SHEET_BOTTOM = 'calc(92px + env(safe-area-inset-bottom, 0px))'  # 12px above the pinned bar (bar: bottom 18, height 62)
def sheet(inner, top=None):
    # Floats above the pinned bar, which stays visible above the scrim so confirm threads land on real pins.
    # Rises from the Clair button: transform-origin bottom right (enter T.layout, exit T.layoutOut in the prototypes).
    return ('  <section role="dialog" aria-modal="true" aria-labelledby="sheet-h" style="position: absolute; z-index: 2; left: 12px; right: 12px; bottom: ' + SHEET_BOTTOM + '; ' + ('top: ' + top + ';' if top else 'max-height: calc(100% - 148px);')
            + ' background: #F4EEE1; border-radius: 22px; padding: 8px 16px 16px; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 12px 32px -16px rgba(42,33,25,0.6); transform-origin: 100% 100%;">\n'
            '    <span aria-hidden="true" style="flex: none; width: 40px; height: 4px; border-radius: 4px; background: #BFAE90; align-self: center;"></span>\n' + inner + '\n  </section>\n')
def sheet_head(face, title, sub='', close=True):
    return ('    <div style="flex: none; display: flex; align-items: center; gap: 12px;">' + face
            + '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px;"><h2 id="sheet-h" style="margin: 0; ' + disp(22) + ' line-height: 1.1;">' + title + '</h2>'
            + ('<span style="' + ROWM + '">' + sub + '</span>' if sub else '') + '</span>'
            + ('<a href="Main.dc.html" aria-label="Close" style="flex: none; width: 44px; height: 44px; margin-right: -8px; display: grid; place-items: center;">' + svg('x', 20, '#2A2119') + '</a>' if close else '') + '</div>')
def bubble(t): return '<div style="align-self: flex-end; max-width: 85%; padding: 8px 12px; border-radius: 16px 16px 4px 16px; background: #EEE6D6; font-size: 16px; line-height: 1.4;">' + t + '</div>'
def chipa(label, href, extra=''):
    return '<a class="chip" href="' + href + '" style="min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 15px; font-weight: 600;' + extra + '">' + label + '</a>'
def flexbtn(html, f): return html.replace('style="', 'style="flex: ' + f + '; ', 1)
SWAP = lambda a, b: '<sc-if value="{{ notDone }}" hint-placeholder-val="{{ true }}">' + a + '</sc-if><sc-if value="{{ done }}" hint-placeholder-val="{{ false }}">' + b + '</sc-if>'

# 1 · Start: tap the Clair button
TRY = [('Spent $12 on lunch', 'Log it · Budget', 'ClairResult.dc.html', 'note'), ('Can I afford $60 concert tickets?', 'Ask · from Budget and Calendar', 'ClairResult.dc.html', 'ask'), ('Track my plants', 'Build · a new app', 'Build.dc.html', 'layout')]
I['ask'] = 'M4 5h16v11h-9l-4.5 4v-4H4zM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.4M12 14.2h.01'
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(spool('hello', 44), 'Tell Clair anything', 'Type, talk or add a photo. It can land in several apps.') + '\n'
    '    <div style="flex: none; display: flex; align-items: flex-end; gap: 8px; padding: 4px 4px 4px 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90;">'
    '<textarea rows="2" enterkeyhint="send" aria-label="Tell Clair anything" placeholder="Spent $12 on lunch, gym tomorrow 6' + NB + 'pm…" style="flex: 1; min-width: 0; border: 0; background: transparent; padding: 8px 0; font: inherit; font-size: 16px; line-height: 1.4; color: #2A2119; resize: none; outline: none;"></textarea>'
    '<a href="ClairResult.dc.html" aria-label="Send to Clair" style="flex: none; width: 44px; height: 44px; border-radius: 12px; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">' + svg('send', 20) + '</a></div>\n'
    '    <div style="flex: none; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px;">'
    + ''.join(chipa(svg(ic, 20) + t, h, ' min-height: 48px;') for t, ic, h in [('Talk', 'mic', 'ClairTalk.dc.html'), ('Photo', 'cam', 'Receipt.dc.html'), ('File', 'clip', 'ClairShare.dc.html')]) + '</div>\n'
    + sect('Try this evening', 'Changes through the day') + '\n'
    '    <section class="st" style="flex: none; padding: 4px 16px;">'
    + ''.join('<a class="rw" href="' + h + '" style="display: flex; align-items: center; gap: 12px; min-height: 60px;' + (SEP if i else '') + '"><span aria-hidden="true" style="flex: none; width: 36px; height: 36px; border-radius: 8px; background: #F3ECDD; display: grid; place-items: center;">' + svg(ic, 18) + '</span>'
              '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + '">' + t + '</span><span style="' + ROWM + '">' + s + '</span></span></a>' for i, (t, s, h, ic) in enumerate(TRY)) + '</section>\n'
    '    ' + link('Open chat', 'Clair.dc.html', True, 'align-self: flex-start; margin: -8px 0;')) + bar(extra=' z-index: 3;') + CLOSE)
files['ClairSheet'] = page('Tell Clair anything', body)

# 2 · Talk: hold the Clair button. The waveform IS a running stitch; stitch lengths follow the voice.
WAVE_CSS = ('.wave{display:flex;align-items:center;justify-content:center;gap:6px;height:56px}\n'
            '.wave i{display:block;height:3px;border-radius:2px;background:#2A2119;animation:wv 760ms ease-in-out infinite alternate}\n'
            '.wave i.f{background:#BFAE90;animation:none}\n'
            '@keyframes wv{from{transform:scaleX(.4)}to{transform:scaleX(1)}}\n'
            '@media (prefers-reduced-motion:reduce){.wave i{animation:none}}')
LEN = [4, 8, 14, 20, 12, 26, 18, 10, 22, 28, 14, 8, 16, 10, 6, 4]
wave = ('<div class="wave" aria-hidden="true">' + '<i class="f" style="width: 6px;"></i>' * 2
        + ''.join('<i style="width: ' + str(w) + 'px; animation-delay: -' + str(i * 290 % 760) + 'ms;"></i>' for i, w in enumerate(LEN)) + '<i class="f" style="width: 6px;"></i>' * 2 + '</div>')
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(spool('waiting', 44), 'Listening', 'Hold the Clair button while you talk', False) + '\n'
    '    ' + wave + '\n'
    '    <p aria-live="polite" style="margin: 0; ' + disp(20) + ' font-weight: 700; line-height: 1.3; min-height: 52px;">Spent $12 on lunch, gym tomorrow <span style="color: #665847;">6' + NB + 'pm…</span></p>\n'
    '    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; ' + LBL + '">' + svg('send', 16) + 'Release to send · slide up to cancel</div>') + bar(held=True, extra=' z-index: 3;') + CLOSE)
files['ClairTalk'] = page('Talk to Clair', body, css=WAVE_CSS)

# shared bits for the conversation sheets
def iff(v, html, hint='false'): return '<sc-if value="{{ ' + v + ' }}" hint-placeholder-val="{{ ' + hint + ' }}">' + html + '</sc-if>'
MIC = chipa(svg('mic', 20), 'ClairTalk.dc.html', ' width: 48px; min-height: 48px; padding: 0;').replace('<a ', '<a aria-label="Talk" ', 1)
INPUT = '<input type="text" enterkeyhint="send" aria-label="Tell Clair more" placeholder="Add more or ask…"{v} style="flex: 1; min-width: 0; min-height: 48px; border: 0; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 0 12px; font: inherit; font-size: 16px; color: #2A2119;">'
def composer(attach='', value='', right=MIC):
    return ('    <div style="flex: none; display: flex; flex-direction: column; gap: 8px;">' + attach + '<div style="display: flex; gap: 8px; align-items: center;">'
            + INPUT.replace('{v}', ' value="' + value + '"' if value else '') + right + '</div></div>')
def src_chip(inner, href=None):
    st = 'min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600;'
    return chipa(inner, href, ' font-size: 14px;') if href else '<span style="' + st + '">' + inner + '</span>'
def sources(*chips): return '<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;"><span style="' + ROWM + '">From</span>' + ''.join(chips) + '</div>'
MIXN = "font-family: 'Hanken Grotesk', sans-serif; font-weight: 600;" + NUM  # mixed number+word figures
def fridge(w, h):
    return ('<svg width="' + str(w) + '" height="' + str(h) + '" viewBox="0 0 144 108" aria-hidden="true" style="flex: none; display: block; border-radius: ' + ('12' if w > 60 else '8') + 'px;">'
            '<rect width="144" height="108" fill="#E8EDF3"></rect><path d="M0 40h144M0 76h144" stroke="#BFC8D4" stroke-width="3"></path>'
            '<rect x="12" y="20" width="40" height="18" rx="3" fill="#FFFDF8" stroke="#C9CCD1"></rect><circle cx="20" cy="29" r="4" fill="#F3ECDD"></circle><circle cx="30" cy="29" r="4" fill="#F3ECDD"></circle><circle cx="40" cy="29" r="4" fill="#F3ECDD"></circle>'
            '<path d="M64 38 q4 -22 16 -24 q12 2 14 24z" fill="#8DB580"></path><rect x="104" y="14" width="14" height="24" rx="3" fill="#FFFDF8" stroke="#C9CCD1"></rect>'
            '<rect x="14" y="52" width="30" height="22" rx="3" fill="#F8DCC2"></rect><rect x="54" y="56" width="22" height="18" rx="3" fill="#E3A72F" fill-opacity=".7"></rect><rect x="88" y="48" width="12" height="26" rx="3" fill="#D3ECE7"></rect><rect x="108" y="58" width="24" height="16" rx="3" fill="#F3DCE0"></rect>'
            '<rect x="16" y="86" width="50" height="14" rx="3" fill="#E7EBC2"></rect><rect x="78" y="84" width="40" height="16" rx="3" fill="#FFFDF8" stroke="#C9CCD1"></rect></svg>')

# 3 + 4 · Result: a capture (basted, nothing saves before OK), then a question answered from your apps.
cap1 = ('<section class="{{ cls }}" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;">'
        '<span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">' + dot('Budget') + 'Budget · Eating out<sc-if value="{{ done }}" hint-placeholder-val="{{ false }}"><span style="margin-left: auto;">' + tag() + '</span></sc-if></span>'
        '<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;"><span style="' + ROWT + '">Lunch</span><span style="font-family: \'DM Mono\', monospace; font-size: 15px;' + NUM + '">$12.00</span></div>'
        '<span style="' + ROWM + NUM + '">$376 → $364 left this month</span></section>')
cap2 = ('<section class="{{ cls }}" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;">'
        '<span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">' + dot('Calendar') + dot('Workout') + 'Calendar + Workout<sc-if value="{{ done }}" hint-placeholder-val="{{ false }}"><span style="margin-left: auto;">' + tag() + '</span></sc-if></span>'
        '<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;"><span style="' + ROWT + '">Gym</span><span style="font-family: \'Hanken Grotesk\', sans-serif; font-weight: 600; font-size: 15px;' + NUM + '">6' + NB + 'pm</span></div>'
        '<span style="' + ROWM + '">Sat 21 Nov · a planned session in Workout</span></section>')
answer = ('<section class="chalk" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;">'
          '<p style="margin: 0; font-size: 16px; line-height: 1.45; color: #2A2119;' + NUM + '"><b>Yes.</b> {{ left }} left until 1 Dec; after $60 you\'d have {{ after }}, about {{ perDay }} a day.</p>'
          '<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;"><span style="' + ROWM + '">From</span>' + chipa(dot('Budget') + 'Budget', 'Budget.dc.html', ' font-size: 14px;') + chipa(dot('Calendar') + 'Calendar', 'Calendar.dc.html', ' font-size: 14px;') + '</div>'
          '<sc-if value="{{ notPlanned }}" hint-placeholder-val="{{ true }}">' + btn('Add to Budget as planned', None, False, 'plan') + '</sc-if>'
          '<sc-if value="{{ planned }}" hint-placeholder-val="{{ false }}"><span style="display: flex; align-items: center; gap: 8px; min-height: 48px; font-size: 15px;">' + svg('check', 18, '#1F6B5E', '2.2') + 'Planned in Budget: concert tickets, $60</span></sc-if></section>')
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(SWAP(spool('waiting', 44), spool('stitched', 44)), '{{ head }}') + '\n'
    '    <div class="scr" style="flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 24px; display: flex; flex-direction: column; gap: 12px;">\n'
    '      ' + bubble('spent $12 on lunch, gym tomorrow 6' + NB + 'pm') + '\n'
    '      <span style="' + CLAIR + '">{{ clairLine }}</span>\n'
    '      ' + sect('{{ okLabel }}').strip() + '\n      ' + cap1 + '\n      ' + cap2 + '\n'
    '      <div style="display: flex; gap: 8px; min-height: 48px;">' + SWAP(flexbtn(btn('Edit', None, False), '1') + flexbtn(btn('Add to 3 apps', None, True, 'add'), '1.6'),
                                                                      flexbtn(btn('Undo', None, False, 'undo'), '1') + flexbtn(btn('Back to Home', 'Main.dc.html'), '1.6')) + '</div>\n'
    '      <span aria-hidden="true" style="height: 8px;"></span>\n'
    '      ' + bubble('Can I afford $60 concert tickets?') + '\n      ' + answer + '\n'
    '    </div>\n'
    + composer(), top='56px') + bar(extra=' z-index: 3;') + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { done: false, planned: false }; }
  renderVals() {
    var self = this, st = this.state, left = st.done ? 364 : 376, after = left - 60;
    return { done: st.done, notDone: !st.done, cls: st.done ? 'st' : 'st basted',
      head: st.done ? 'Added to 3 apps' : '2 things, 3 apps',
      clairLine: st.done ? 'Added. Budget, Calendar and Workout are up to date.' : 'I made that into 2 things. Nothing is saved until you OK it.',
      okLabel: st.done ? 'Saved · 3 apps' : 'Waiting for your OK · 3 apps',
      left: '$' + left, after: '$' + after, perDay: '$' + Math.round(after / 11),
      planned: st.planned, notPlanned: !st.planned,
      add: function () { self.setState({ done: true }); },
      undo: function () { self.setState({ done: false }); },
      plan: function () { self.setState({ planned: true }); } };
  }
}'''
files['ClairResult'] = page('Clair: add and ask', body, script)

# 6 · Photo + a question: an answer, not a log. Clair reads the photo AND Groceries.
HAVE = [('Pasta', 'Groceries', True), ('Spinach', 'photo', True), ('Eggs', 'photo', True), ('Olive oil', 'Groceries', True)]  # parmesan: named as missing in the answer and in the action
have = ''.join('<span style="display: flex; align-items: center; gap: 8px; min-height: 24px; font-size: 15px;' + ('' if ok else ' color: #665847;') + '">'
               + (svg('check', 16, '#1F6B5E', '2.4') if ok else '<span aria-hidden="true" style="flex: none; width: 12px; height: 12px; margin: 0 2px; border-radius: 50%; box-shadow: inset 0 0 0 1.5px #665847;"></span>')
               + n + '<span style="margin-left: auto; font-size: 13px; color: #665847;">' + ('from your ' + s if ok else 'missing') + '</span></span>' for n, s, ok in HAVE)
photo_answer = ('<section class="chalk" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;">'
    '<p style="margin: 0; font-size: 16px; line-height: 1.45; color: #2A2119;' + NUM + '"><b>Spinach and egg pasta.</b> You have 4 of 5 things; missing parmesan ($4.29 at Corner Market).</p>'
    '<div style="display: flex; flex-direction: column;">' + have + '</div>'
    + sources(src_chip(svg('cam', 16) + 'Your photo'), src_chip(dot('Groceries') + 'Groceries', 'Groceries.dc.html'))
    + iff('notAdded', '<button type="button" class="btn st basted" onClick="{{ add }}" style="' + BTN + 'border: 0; border-radius: 12px; color: #2A2119; width: 100%;">' + svg('plus', 18) + 'Add parmesan to Groceries</button>', 'true')
    + iff('added', '<span style="display: flex; align-items: center; gap: 8px; min-height: 48px; font-size: 15px;">' + svg('check', 18, '#1F6B5E', '2.2') + '<span style="flex: 1;">Parmesan added to Groceries</span>' + tag() + '<button type="button" class="lk" onClick="{{ undo }}" style="border: 0; background: transparent; padding: 0;">Undo</button></span>')
    + '</section>')
pick = lambda v, label: '<button type="button" class="chip" onClick="{{ ' + v + ' }}" aria-pressed="{{ ' + v + 'On }}" style="{{ ' + v + 'Style }}">' + label + '</button>'
fork = ('<div style="display: flex; flex-direction: column; gap: 8px;"><span style="' + CLAIR + '">Log these items or just answer?</span>'
        '<div role="group" aria-label="What to do with the photo" style="display: flex; gap: 8px;">' + pick('pickLog', 'Log items') + pick('pickAns', 'Just answer') + '</div></div>')
sent = ('<div style="align-self: flex-end; max-width: 85%; display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">' + fridge(96, 72)
        + '<div style="padding: 8px 12px; border-radius: 16px 16px 4px 16px; background: #EEE6D6; font-size: 16px; line-height: 1.4;">What can I make tonight?</div></div>')
chip_att = ('<span style="align-self: flex-start; display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px 4px 4px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 13px; font-weight: 600;">'
            + fridge(32, 32) + 'Fridge photo</span>')
SEND = '<a href="ClairPhoto.dc.html" aria-label="Send to Clair" style="flex: none; width: 48px; height: 48px; border-radius: 12px; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">' + svg('send', 20) + '</a>'
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(iff('compose', spool('hello', 44), 'false') + iff('thinking', spool('thinking', 44)) + iff('waitingFace', spool('waiting', 44), 'true') + iff('added', spool('stitched', 44)), '{{ head }}') + '\n'
    '    <div class="scr" style="flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 24px; display: flex; flex-direction: column; gap: 12px;">\n'
    '      ' + iff('compose', '<span style="' + ROWM + '">Add a photo and ask about it. A receipt still goes to Review receipt.</span>') + '\n'
    '      ' + iff('sent', sent, 'true') + '\n'
    '      ' + iff('thinking', '<span style="' + CLAIR + '">Looking at your photo and Groceries…</span>') + '\n'
    '      ' + iff('answered', fork + iff('isLog', '<div class="st basted" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 16px;">I see 9 items. Review them before anything goes into Groceries.</span>' + link('Review items', 'Receipt.dc.html', True, 'align-self: flex-start;') + '</div>') + iff('isAns', photo_answer, 'true'), 'true') + '\n'
    '    </div>\n'
    + iff('compose', composer(chip_att, 'What can I make tonight?', SEND)) + iff('sent', composer(), 'true'), top='56px') + bar(extra=' z-index: 3;') + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); var self = this; this.state = { phase: 'compose', mode: 'answer', added: false };
    setTimeout(function () { self.setState({ phase: 'thinking' }); }, 900); setTimeout(function () { self.setState({ phase: 'answer' }); }, 2300); }
  renderVals() {
    var self = this, st = this.state, ans = st.phase === 'answer';
    var chip = function (on) { return 'flex: 1; min-height: 44px; padding: 0 12px; border-radius: 12px; border: 0; font-size: 15px; font-weight: 600; ' + (on ? 'background: #2A2119; color: #FBF6EC;' : 'background: #FFFDF8; color: #2A2119; box-shadow: inset 0 0 0 1.5px #BFAE90;'); };
    return { compose: st.phase === 'compose', sent: st.phase !== 'compose', thinking: st.phase === 'thinking', answered: ans,
      waitingFace: ans && !st.added, added: ans && st.added, notAdded: !st.added,
      isLog: st.mode === 'log', isAns: st.mode === 'answer',
      head: st.phase === 'compose' ? 'Tell Clair anything' : st.phase === 'thinking' ? 'Reading your photo' : 'Dinner tonight',
      pickLog: function () { self.setState({ mode: 'log' }); }, pickAns: function () { self.setState({ mode: 'answer' }); },
      pickLogOn: st.mode === 'log' ? 'true' : 'false', pickAnsOn: st.mode === 'answer' ? 'true' : 'false', pickLogStyle: chip(st.mode === 'log'), pickAnsStyle: chip(st.mode === 'answer'),
      add: function () { self.setState({ added: true }); }, undo: function () { self.setState({ added: false }); } };
  }
}'''
files['ClairPhoto'] = page('Clair: photo and a question', body, script)

# 7 · Ask: a question about your data vs a general question, in one conversation.
over = 15 / 165 * 100
data_answer = ('<section class="chalk" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;">'
    '<p style="margin: 0; font-size: 16px; line-height: 1.45; color: #2A2119;' + NUM + '"><b>$165 of $150.</b> $15 over, mostly Blue Copper (4 visits).</p>'
    '<div role="img" aria-label="Eating out: $165 of $150, $15 over" style="height: 8px; border-radius: 4px; background: #EEE6D6; position: relative; overflow: hidden;"><div style="position: absolute; inset: 0 auto 0 0; width: ' + '%.1f' % (100 - over) + '%; background: #1F6B5E;"></div>'
    '<div style="position: absolute; inset: 0 0 0 auto; width: ' + '%.1f' % over + '%; background: repeating-linear-gradient(45deg, #2A2119 0 1.3px, transparent 1.3px 4px), repeating-linear-gradient(-45deg, #2A2119 0 1.3px, transparent 1.3px 4px);"></div></div>'
    '<span style="display: flex; justify-content: space-between; ' + ROWM + '"><span>Eating out · November</span><span style="' + MIXN + '">$15 over</span></span>'
    + sources(src_chip(dot('Budget') + 'Budget', 'Budget.dc.html')) + link('See Eating out', 'Budget.dc.html', True, 'align-self: flex-start; margin: -4px 0;') + '</section>')
general = ('<section style="padding: 12px 16px; border-radius: 16px; background: #FFFDF8; display: flex; flex-direction: column; gap: 8px;">'
    '<span style="display: flex; align-items: center; gap: 8px; ' + ROWM + '">' + svg('book', 16, '#665847') + 'General answer · not from your apps</span>'
    '<p style="margin: 0; font-size: 16px; line-height: 1.45; color: #2A2119;">If you lift a few times a week, a common guide is 1.2 to 1.6' + NB + 'g per kg of body weight. At 70' + NB + 'kg that is about 85 to 110' + NB + 'g a day. With a health condition, ask a doctor first.</p>'
    + link('Track protein in Workout', 'Build.dc.html', True, 'align-self: flex-start; margin: -4px 0;') + '</section>')
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(spool('hello', 44), 'Ask Clair', 'Your apps first; general answers say so') + '\n'
    '    <div class="scr" style="flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 24px; display: flex; flex-direction: column; gap: 12px;">\n'
    '      ' + bubble('How much did I spend on eating out this month?') + '\n      ' + data_answer + '\n'
    '      <span aria-hidden="true" style="height: 4px;"></span>\n'
    '      ' + bubble('How much protein should I eat a day?') + '\n      ' + general + '\n'
    '    </div>\n' + composer(), top='56px') + bar(extra=' z-index: 3;') + CLOSE)
files['ClairAsk'] = page('Ask Clair', body)

# 5 · Shared into Quilt: OS share sheet > Quilt > the Clair sheet with the file attached.
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head('<sc-if value="{{ reading }}" hint-placeholder-val="{{ false }}">' + spool('working', 44) + '</sc-if>' + SWAP(spool('waiting', 44), spool('stitched', 44)), '{{ head }}') + '\n'
    '    <section class="st" style="flex: none; padding: 12px 16px; display: flex; align-items: center; gap: 12px;"><span aria-hidden="true" style="flex: none; width: 40px; height: 48px; border-radius: 4px; background: #F3ECDD; display: grid; place-items: center;">' + svg('doc', 22) + '</span>'
    '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + ' overflow-wrap: anywhere;">Syllabus · ECON 1010.pdf</span><span style="' + ROWM + '">4 pages · shared from Files</span></span></section>\n'
    '    <span style="flex: none; ' + CLAIR + '">{{ line }}</span>\n'
    '    <sc-if value="{{ reading }}" hint-placeholder-val="{{ false }}"><section class="st basted" aria-label="Reading" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 16px;">'
    + '<span style="display: flex; flex-direction: column; gap: 8px;"><i style="display: block; width: 60%; height: 12px; border-radius: 4px; background: #EEE6D6;"></i><i style="display: block; width: 40%; height: 8px; border-radius: 4px; background: #F3ECDD;"></i></span>' * 3 + '</section></sc-if>\n'
    '    <sc-if value="{{ isRead }}" hint-placeholder-val="{{ true }}">\n'
    '    <div class="scr" style="flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 16px; display: flex; flex-direction: column; gap: 8px;">\n'
    '      <span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">{{ okLabel }} ' + dot('Classes') + 'Classes ' + dot('Calendar') + 'Calendar</span>\n'
    '      <section class="{{ cls }}" style="padding: 4px 16px;">'
    '<sc-for list="{{ rows }}" as="r" hint-placeholder-count="3"><div style="{{ r.style }}"><span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + '">{{ r.t }}</span><span style="' + ROWM + NUM + '">{{ r.s }}</span></span><sc-if value="{{ r.exam }}" hint-placeholder-val="{{ false }}"><span style="font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; box-shadow: inset 0 0 0 1px #BFAE90;">Exam</span></sc-if></div></sc-for>'
    '<sc-if value="{{ hasMore }}" hint-placeholder-val="{{ true }}"><button type="button" class="lk" onClick="{{ showMore }}" style="border: 0; background: transparent; padding: 0;' + SEP + ' width: 100%; justify-content: flex-start;">{{ moreLabel }}</button></sc-if></section>\n'
    '    </div>\n'
    '    <div style="flex: none; display: flex; gap: 8px; min-height: 48px;">' + SWAP(flexbtn(btn('Not now', 'Main.dc.html', False), '1') + flexbtn(btn('Add to 2 apps', None, True, 'add'), '1.6'),
                                                                                 flexbtn(btn('Undo', None, False, 'undo'), '1') + flexbtn(btn('See Calendar', 'Calendar.dc.html'), '1.6')) + '</div>\n'
    '    </sc-if>') + bar(extra=' z-index: 3;') + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); var self = this; this.state = { read: false, done: false, more: false }; setTimeout(function () { self.setState({ read: true }); }, 1400); }
  renderVals() {
    var self = this, st = this.state, reading = !st.read;
    var all = [['Problem set 7', 'Due Mon 23 Nov, 11:59\\u00a0pm'], ['Midterm 2', 'Tue 1 Dec, 9:10\\u00a0am · Kendall 104', 1], ['Problem set 8', 'Due Fri 4 Dec, 11:59\\u00a0pm'], ['Reading response', 'Due Mon 7 Dec, 9\\u00a0am'], ['Problem set 9', 'Due Wed 9 Dec, 11:59\\u00a0pm'], ['Term paper', 'Due Fri 11 Dec, 5\\u00a0pm'], ['Review sheet', 'Due Mon 14 Dec, 9\\u00a0am'], ['Final exam', 'Wed 16 Dec, 8\\u00a0am · Kendall 104', 1]];
    var rows = (st.more ? all : all.slice(0, 3)).map(function (r, i) {
      return { t: r[0], s: r[1], exam: !!r[2], style: 'display: flex; align-items: center; gap: 12px; min-height: 56px;' + (i ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : '') };
    });
    return { reading: reading, isRead: !reading, done: st.done, notDone: !reading && !st.done, rows: rows, cls: st.done ? 'st' : 'st basted',
      head: reading ? 'Reading your file' : st.done ? 'Added to 2 apps' : '6 due dates, 2 exams',
      line: reading ? 'Reading 4 pages…' : st.done ? 'Added 8 dates to Classes and Calendar. Each one warns you 3 days ahead.' : 'Found 6 due dates and 2 exams. Add to Classes and Calendar?',
      okLabel: st.done ? 'Saved to' : 'Waiting for your OK ·',
      hasMore: !st.more, moreLabel: 'Show 5 more', showMore: function () { self.setState({ more: true }); },
      add: function () { self.setState({ done: true }); }, undo: function () { self.setState({ done: false }); } };
  }
}'''
files['ClairShare'] = page('Shared with Clair', body, script)

# 8 · Fridge photo: Clair spots what's low and asks a menu question. Picks feed the proposal; "Other" becomes a note Clair remembers.
OPT = ('<sc-for list="{{ opts }}" as="o" hint-placeholder-count="4"><button type="button" class="chip" onClick="{{ o.pick }}" aria-pressed="{{ o.on }}" style="{{ o.style }}">'
       '<span aria-hidden="true" style="{{ o.box }}">' + svg('check', 14, '#FFFFFF', '2.4') + '</span>'
       '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column; text-align: left;"><span style="font-size: 16px; font-weight: 500;">{{ o.n }}</span><span style="' + ROWM + NUM + '">{{ o.d }}</span></span></button></sc-for>')
ask_card = ('<section class="chalk" style="flex: none; padding: 12px 16px; display: flex; flex-direction: column; gap: 12px;">'
    '<p style="margin: 0; font-size: 16px; line-height: 1.45;">Looks like you\'re low on these. Add to Weekly shop?</p>'
    '<div role="group" aria-label="Running low" style="display: flex; flex-direction: column; gap: 8px;">' + OPT + '</div>'
    '<label style="display: flex; flex-direction: column; gap: 4px; ' + LBL + '">Other<input type="text" enterkeyhint="done" value="{{ other }}" onInput="{{ typed }}" placeholder="e.g. stopped buying juice" style="min-height: 48px; border: 0; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; padding: 0 12px; font: inherit; font-size: 16px; font-weight: 400; color: #2A2119;"></label>'
    '<span style="display: flex; align-items: center; gap: 4px; ' + ROWM + '">' + svg('note', 16, '#665847') + 'Clair remembers what you pick</span></section>')
noted_chip = ('<div style="align-self: flex-start; max-width: 100%; box-sizing: border-box; display: inline-flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 13px; font-weight: 600;">'
    + svg('note', 16) + '<span style="min-width: 0;">{{ noteText }}</span>'
    + iff('notDone', '<button type="button" class="lk" onClick="{{ unnote }}" style="flex: none; margin-right: -8px; border: 0; background: transparent; padding: 0 8px;">Undo</button>', 'true') + '</div>')
proposal = ('<section class="{{ cls }}" style="flex: none; padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;">'
    '<span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">' + dot('Groceries') + 'Groceries · Weekly shop</span>'
    '<span style="' + ROWT + '">{{ propTitle }}</span><span style="' + ROWM + '">{{ propSub }}</span>'
    + iff('canConfirm', btn('Add to Groceries', None, True, 'confirm'), 'true')
    + iff('done', '<span style="display: flex; align-items: center; gap: 8px; min-height: 48px; font-size: 15px;">' + svg('check', 18, '#1F6B5E', '2.2') + '<span style="flex: 1;">Saved to Groceries</span><button type="button" class="lk" onClick="{{ undo }}" style="border: 0; background: transparent; padding: 0;">Undo</button></span>'
          + link('See Groceries', 'Groceries.dc.html', True, 'align-self: flex-start; margin: -8px 0;'))
    + '</section>')
add_sel = '<button class="btn" type="button" onClick="{{ answer }}" aria-disabled="{{ noPick }}" style="{{ addStyle }}">Add selected</button>'
# The Groceries pin gets the mustard "just changed" notch (Home's small-patch notch) once the card is stitched; the words stay for screen readers.
SR = 'position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;'
NOTCH = ('<span aria-hidden="true" style="position: absolute; top: 8px; right: 8px; width: 10px; height: 10px; border-radius: 50%; background: #E3A72F; box-shadow: 0 0 0 2px rgba(255,253,248,0.9);"></span>'
         '<span style="' + SR + '">, just changed</span>')
def pin_notch(html, app, cond):
    return html.replace('aria-label="' + app + '" style="', 'aria-label="' + app + '" style="position: relative; ', 1).replace(app + '</span></a>', app + '</span>' + iff(cond, NOTCH) + '</a>', 1)
fbar = pin_notch(bar(extra=' z-index: 3;'), 'Groceries', 'done')
body = (ROOT + '\n' + backdrop() + sheet(
    sheet_head(iff('reading', spool('working', 44)) + iff('waitFace', spool('waiting', 44), 'true') + iff('done', spool('stitched', 44)), '{{ head }}') + '\n'
    '    <div class="scr" style="flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 24px; display: flex; flex-direction: column; gap: 12px;">\n'
    '      <div style="flex: none; display: flex; align-items: center; gap: 12px;">' + fridge(56, 42) + '<span style="' + CLAIR + '">Your fridge. I can see 14 things.</span></div>\n'
    '      ' + iff('reading', '<span style="' + CLAIR + '">Checking it against what you usually buy…</span>') + '\n'
    '      ' + iff('asking', ask_card, 'true') + '\n'
    '      ' + iff('answered', bubble('{{ said }}') + '<span style="' + CLAIR + '">{{ line }}</span>' + iff('noted', noted_chip) + proposal
                  + '<button type="button" class="lk" onClick="{{ restart }}" style="align-self: flex-start; border: 0; background: transparent; padding: 0;">Start over</button>') + '\n'
    '    </div>\n'
    '    ' + iff('asking', '<div style="flex: none; display: flex; gap: 8px;">' + flexbtn(btn('Not now', 'Main.dc.html', False), '1') + flexbtn(add_sel, '1.6') + '</div>', 'true'), top='56px') + fbar + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); var self = this; this.state = { phase: 'reading', picked: {}, other: '', noted: true };
    setTimeout(function () { self.setState({ phase: 'ask' }); }, 1400); }
  renderVals() {
    var self = this, st = this.state, ph = st.phase;
    var LOW = [['Butter', 'you buy every 2 weeks · last 15 days ago'], ['Cheddar', 'usually every week · last 9 days ago'], ['Orange juice', 'every 10 days'], ['Hummus', 'almost empty']];
    var opts = LOW.map(function (r, i) {
      var on = !!st.picked[i];
      return { n: r[0], d: r[1], on: on ? 'true' : 'false',
        pick: function () { var o = Object.assign({}, st.picked); o[i] = !on; self.setState({ picked: o }); },
        style: 'width: 100%; display: flex; align-items: center; gap: 12px; min-height: 60px; padding: 8px 12px; border: 0; border-radius: 12px; ' + (on ? 'background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #3557A6; color: #22396F;' : 'background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; color: #2A2119;'),
        box: 'flex: none; width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center; ' + (on ? 'background: #3557A6;' : 'box-shadow: inset 0 0 0 1.5px #665847;') };
    });
    var names = LOW.filter(function (r, i) { return st.picked[i]; }).map(function (r) { return r[0]; });
    var other = st.other.trim(), none = !names.length && !other;
    // ponytail: a keyword match stands in for Clair reading the "Other" answer
    var juice = /juice/i.test(other), noted = !!other && st.noted, unusual = noted && juice;
    var parts = [];
    if (names.length) parts.push('Add ' + names.length + ' to Weekly shop');
    if (unusual) parts.push('mark orange juice not usual');
    var sub = names.join(', ');
    if (unusual) sub += (sub ? ' · ' : '') + 'orange juice stops showing as low';
    var answered = ph === 'answered' || ph === 'done', done = ph === 'done';
    return { reading: ph === 'reading', asking: ph === 'ask', answered: answered, done: done, notDone: !done, waitFace: ph === 'ask' || ph === 'answered',
      head: { reading: 'Reading your photo', ask: 'Running low', answered: 'Ready to add', done: 'Added to Groceries' }[ph],
      line: done ? 'Added. Groceries is up to date.' : 'Nothing saves until you OK it.',
      opts: opts, other: st.other, noPick: none ? 'true' : 'false',
      addStyle: ''' + json.dumps(BTN + 'border: 0; background: #3557A6; color: #FFFFFF;') + ''' + (none ? ' opacity: 0.45;' : ''),
      said: names.concat(other ? [other] : []).join(', '),
      noted: noted, noteText: juice ? 'Noted: you stopped buying orange juice' : 'Noted: ' + other,
      propTitle: parts.join(' · ') || 'Nothing to change in Groceries', propSub: sub,
      canConfirm: ph === 'answered' && parts.length > 0, cls: done ? 'st' : 'st basted',
      typed: function (e) { self.setState({ other: e.target.value }); },
      answer: function () { if (!none) self.setState({ phase: 'answered', noted: true }); },
      unnote: function () { self.setState({ noted: false }); },
      confirm: function () { self.setState({ phase: 'done' }); },
      undo: function () { self.setState({ phase: 'answered' }); },
      restart: function () { self.setState({ phase: 'ask', picked: {}, other: '', noted: true }); } };
  }
}'''
files['ClairFridge'] = page('Clair: fridge photo', body, script)

# 9 · Settings > What Clair remembers: notes Clair reads before it suggests anything. Delete is ink, never red; undo in a toast.
body = (ROOT + '\n' + scroller() + '\n' + topbar('You.dc.html', 'Back to Settings', h1mid('What Clair remembers')) + '\n'
    '    <p style="margin: 0; font-size: 16px; line-height: 1.45;">Clair reads these before it suggests anything. Facts about your stuff live in your apps.</p>\n'
    '    <button type="button" class="st" role="switch" aria-checked="{{ offA }}" onClick="{{ flip }}" style="width: 100%; min-height: 64px; border: 0; padding: 12px 16px; display: flex; align-items: center; gap: 12px; text-align: left;">'
    '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + '">Turn off notes</span><span style="' + ROWM + '">{{ offSub }}</span></span>'
    '<span aria-hidden="true" style="{{ track }}"><span style="{{ knob }}"></span></span></button>\n'
    + sect('{{ head }}', '{{ headNote }}') + '\n'
    '    ' + iff('hasNotes', '<section class="st" style="padding: 4px 16px;"><sc-for list="{{ notes }}" as="n" hint-placeholder-count="3"><div style="{{ n.row }}">'
        '<span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + '">{{ n.t }}</span><span style="' + ROWM + '">{{ n.s }}</span></span>'
        '<button type="button" onClick="{{ n.del }}" aria-label="{{ n.aria }}" style="flex: none; width: 44px; height: 44px; margin-right: -8px; border: 0; border-radius: 12px; background: transparent; color: #2A2119; display: grid; place-items: center;">' + svg('trash', 20) + '</button></div></sc-for></section>', 'true') + '\n'
    '    ' + iff('none', '<p class="st" style="margin: 0; padding: 16px; font-size: 16px; color: #665847;">Nothing yet. Notes like “stopped buying orange juice” show up here.</p>') + '\n'
    '  </div>\n'
    '  ' + iff('toast', '<div role="status" style="position: absolute; left: 16px; right: 16px; bottom: 92px; z-index: 2; min-height: 52px; padding: 0 8px 0 16px; box-sizing: border-box; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90, 0 8px 22px -14px rgba(42,33,25,0.55); display: flex; align-items: center; gap: 8px;">'
        '<span style="flex: 1; min-width: 0; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Deleted: {{ lastT }}</span>'
        '<button type="button" class="lk" onClick="{{ undoDel }}" style="flex: none; border: 0; background: transparent; padding: 0 8px;">Undo</button></div>') + '\n'
    + bar() + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { gone: {}, last: null, off: false }; }
  renderVals() {
    var self = this, st = this.state;
    var ALL = [['You stopped buying orange juice', 'from a fridge photo, today'], ['Gym is pull day on Saturdays', 'from Workout'], ["Don't suggest snacks", 'you said, Tue 17 Nov']];
    var notes = [];
    ALL.forEach(function (r, i) {
      if (st.gone[i]) return;
      notes.push({ t: r[0], s: r[1], aria: 'Delete note: ' + r[0],
        row: 'display: flex; align-items: center; gap: 12px; min-height: 64px;' + (notes.length ? ' background-image: linear-gradient(90deg, #BFAE90 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x;' : ''),
        del: function () { var g = Object.assign({}, st.gone); g[i] = true; self.setState({ gone: g, last: i });
          setTimeout(function () { if (self.state.last === i) self.setState({ last: null }); }, 6000); } });
    });
    return { notes: notes, hasNotes: notes.length > 0, none: !notes.length,
      head: 'Notes · ' + notes.length, headNote: st.off ? 'Not in use while off' : '',
      offA: st.off ? 'true' : 'false', offSub: st.off ? "Clair isn't reading or adding notes" : 'Clair stops reading and adding notes',
      track: 'flex: none; width: 48px; height: 28px; border-radius: 16px; padding: 2px; box-sizing: border-box; display: flex; ' + (st.off ? 'background: #3557A6; justify-content: flex-end;' : 'background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #665847;'),
      knob: 'width: 24px; height: 24px; border-radius: 12px; ' + (st.off ? 'background: #FFFFFF;' : 'background: #665847; transform: scale(0.75);'),
      flip: function () { self.setState({ off: !st.off }); },
      toast: st.last !== null, lastT: st.last !== null ? ALL[st.last][0] : '',
      undoDel: function () { var g = Object.assign({}, st.gone); delete g[st.last]; self.setState({ gone: g, last: null }); } };
  }
}'''
files['ClairNotes'] = page('What Clair remembers', body, script)

# ---------- First open: onboarding (docs/onboarding.md). Guest, no name. Picks here: Money, Groceries, To-dos -> Budget, Groceries, To-dos + Calendar. ----------
OB_PINS = ['Budget', 'Groceries', 'To-dos', 'Calendar']  # Calendar last (2.3)
def ob_bar(extra=''): return bar(extra=extra, pins=OB_PINS).replace('href="ClairSheet.dc.html"', 'href="OnSheet.dc.html"')
def home_top(greet, status):
    return ('    <div style="display: flex; align-items: center; justify-content: space-between; min-height: 44px;"><span style="display: flex; gap: 8px; align-items: center; ' + disp(17) + '">' + QLOGO + 'quilt</span>'
            '<a href="You.dc.html" aria-label="Profile and settings" style="width: 44px; height: 44px; border-radius: 50%; background: #F8DCC2; display: grid; place-items: center;">' + svg('user', 18) + '</a></div>\n'
            '    <header style="display: flex; flex-direction: column; gap: 4px;"><h1 style="margin: 0; ' + disp(30) + ' line-height: 1.05;">' + greet + '</h1><p style="margin: 0; font-size: 17px; line-height: 1.35;">' + status + '</p></header>\n')
STARTERS = [('Budget', 'Set a monthly amount', 'grid-column: span 6;'), ('Groceries', 'Weekly shop', 'grid-column: span 2;'), ('To-dos', 'Nothing yet', 'grid-column: span 2;'), ('Calendar', 'Nothing yet', 'grid-column: span 2;')]
def starter_grid(anim=False):
    out = ''
    for i, (a, f, sp) in enumerate(STARTERS):
        p = patch(a, f, sp)
        if anim: p = p.replace('class="qp"', 'class="qp mk"', 1).replace('" style="', '" style="animation-delay: ' + str(120 + i * 140) + 'ms; ', 1)
        out += p
    return '    <div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); grid-auto-rows: 72px; min-height: 144px; border-radius: 16px; overflow: hidden;">' + out + '</div>\n'
FIRST = 'Nothing logged yet. Add a receipt or tell Clair something.'
def ob_backdrop():
    return ('  <div aria-hidden="true" inert style="position: absolute; inset: 0; padding: 44px 16px 0; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px;">\n'
            + home_top('Afternoon.', FIRST) + sect('Your apps · 4') + '\n' + starter_grid() + '  </div>\n'
            '  <a href="OnHome.dc.html" tabindex="-1" aria-hidden="true" style="position: absolute; inset: 0; background: rgba(42,33,25,0.32);"></a>\n')
OB_CSS = '.mk{animation:mk var(--t-layout) var(--ease) both}\n@keyframes mk{from{opacity:0;transform:scale(.92)}}\n@media (prefers-reduced-motion:reduce){.mk{animation:none}}'
def center_screen(face, title, line, actions):
    return (ROOT + '\n  <div style="position: absolute; inset: 0; padding: 44px 16px max(24px, env(safe-area-inset-bottom, 0px)); box-sizing: border-box; display: flex; flex-direction: column; gap: 16px;">\n'
            '    <div style="display: flex; align-items: center; min-height: 44px;"><span style="display: flex; gap: 8px; align-items: center; ' + disp(17) + '">' + QLOGO + 'quilt</span></div>\n'
            '    <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 16px;">' + face
            + '<h1 style="margin: 0; ' + disp(30) + ' line-height: 1.1;">' + title + '</h1><p style="margin: 0; font-size: 17px; line-height: 1.45;">' + line + '</p></div>\n'
            '    <div style="display: grid; gap: 8px;">' + actions + '</div>\n  </div>' + CLOSE)

# 1.3 Welcome: guest, no sign-up wall
files['OnWelcome'] = page('Welcome', center_screen(spool('hello', 96), "Hi. I'm Clair. I keep track of the stuff that slips.",
    'Quilt makes small apps for your money, groceries, classes and the rest, and stitches them together. No account needed to start.',
    btn('Start', 'OnSlips.dc.html') + link('I have a quilt · Sign in', 'Main.dc.html', True, 'justify-self: center;')))

# No network on first open (guest sign-in waits)
files['OnOffline'] = page('No connection', center_screen(spool('sleepy', 96), 'Quilt needs a connection to set up.',
    'Nothing is lost. Connect to Wi-Fi or mobile data, then try again.', btn('Try again', 'OnWelcome.dc.html')))

# 2.1 What slips? One question, six chips, nothing preselected.
SLIPS = [('Money', 'wallet'), ('Groceries', 'cart'), ('Classes', 'book'), ('Workouts', 'lift'), ('Subscriptions', 'repeat'), ('To-dos', 'check')]
body = (ROOT + '\n' + scroller(140) + '\n' + topbar('OnWelcome.dc.html', 'Back to Welcome') + '\n'
    '    <div style="display: flex; gap: 12px; align-items: center;">' + spool('hello', 44) + h1('What slips for you?', 28).strip() + '</div>\n'
    '    <div role="group" aria-label="What slips" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">'
    '<sc-for list="{{ chips }}" as="c" hint-placeholder-count="6"><button type="button" class="chip" onClick="{{ c.pick }}" aria-pressed="{{ c.on }}" style="{{ c.style }}">'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex: none;"><path d="{{ c.icon }}"></path></svg>{{ c.n }}</button></sc-for></div>\n'
    '    <p style="margin: 0; font-size: 15px; color: #665847;">Pick any. You can add more later.</p>\n'
    '    ' + iff('some', '<section class="st" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;"><span style="' + LBL + '">Clair makes</span><span style="font-size: 16px; line-height: 1.45;">{{ makes }}</span><span style="' + ROWM + '">Calendar comes with every set, since they all have dates.</span></section>') + '\n'
    '  </div>\n'
    '  <div style="position: absolute; left: 16px; right: 16px; bottom: max(24px, env(safe-area-inset-bottom, 0px)); display: grid; gap: 8px;">'
    + iff('some', btn('Make my apps', 'OnMaking.dc.html')) + iff('none', '<button class="btn" type="button" aria-disabled="true" style="' + BTN + 'border: 0; background: #3557A6; color: #FFFFFF; opacity: 0.45;">Make my apps</button>', 'true')
    + btn('Skip', 'Welcome.dc.html', False) + '</div>' + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { on: {} }; }
  renderVals() {
    var self = this, st = this.state;
    var S = ''' + json.dumps([[n, I[ic]] for n, ic in SLIPS]) + ''';
    var chips = S.map(function (c) {
      var on = !!st.on[c[0]];
      return { n: c[0], icon: c[1], on: on ? 'true' : 'false', pick: function () { var o = Object.assign({}, st.on); o[c[0]] = !on; self.setState({ on: o }); },
        style: 'min-height: 56px; padding: 0 12px; border: 0; border-radius: 12px; display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; ' + (on ? 'background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #3557A6; color: #22396F;' : 'background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; color: #2A2119;') };
    });
    // chip -> template (onboarding.md 2.2): Money and Subscriptions make one app; Calendar always
    var apps = [];
    if (st.on.Money || st.on.Subscriptions) apps.push('Budget & subscriptions');
    [['Groceries', 'Groceries'], ['Classes', 'Classes'], ['Workouts', 'Workout'], ['To-dos', 'To-dos']].forEach(function (m) { if (st.on[m[0]]) apps.push(m[1]); });
    var some = apps.length > 0;
    if (some) apps.push('Calendar');
    return { chips: chips, some: some, none: !some, makes: apps.slice(0, -1).join(', ') + ' and ' + apps[apps.length - 1] };
  }
}'''
files['OnSlips'] = page('What slips for you?', body, script)

# 2.2 Starter apps, instant (templates, no Clair call): patches appear, pins fill.
body = (ROOT + '\n' + scroller() + '\n'
    '    <div style="display: flex; gap: 12px; align-items: center; min-height: 44px; margin-top: 44px;">' + spool('working', 44) + h1('Making your apps', 28).strip() + '</div>\n'
    '    <p style="margin: 0; font-size: 16px; line-height: 1.45;">Budget & subscriptions, Groceries, To-dos and Calendar. They start empty and fill as you tell Clair things.</p>\n'
    '    <div inert>' + starter_grid(True).strip() + '</div>\n'
    '    <div class="mk" style="animation-delay: 760ms; display: grid;">' + btn('Open Home', 'OnHome.dc.html') + '</div>\n'
    '    <p class="mk" style="animation-delay: 760ms; margin: 0; ' + ROWM + '">In the app this takes under a second and goes straight to Home.</p>\n'
    '  </div>\n' + ob_bar(' z-index: 3;').replace('<nav ', '<nav class="mk" ', 1).replace('style="position: absolute; left: 12px;', 'style="animation-delay: 620ms; position: absolute; left: 12px;', 1) + CLOSE)
files['OnMaking'] = page('Making your apps', body, css=OB_CSS)

# 3.1 First prompt on Home: the status line carries it; empty sections hidden; one-time chalk hint at the Clair button.
body = (ROOT + '\n' + scroller() + '\n' + home_top('Afternoon.', FIRST) + sect('Your apps · 4', 'Made from your picks') + '\n' + starter_grid() + '  </div>\n'
    '  ' + iff('hint', '<div class="chalk" role="note" style="position: absolute; left: 16px; right: 12px; bottom: 96px; padding: 12px 8px 12px 16px; box-sizing: border-box; display: flex; align-items: center; gap: 8px; background: #FBF6EC;">'
        + chalk_icon() + '<span style="flex: 1; ' + CLAIR + '">Tap Clair to add a receipt or type. Hold to talk.</span>'
        '<button type="button" class="lk" onClick="{{ hide }}" style="flex: none; border: 0; background: transparent; padding: 0 8px;">Got it</button>'
        '<span aria-hidden="true" style="position: absolute; right: 22px; bottom: -8px; width: 14px; height: 14px; background: #FBF6EC; border-right: 2px dotted rgba(53,87,166,0.7); border-bottom: 2px dotted rgba(53,87,166,0.7); transform: rotate(45deg);"></span></div>', 'true') + '\n'
    + ob_bar() + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { hint: true }; }
  renderVals() { var self = this; return { hint: this.state.hint, hide: function () { self.setState({ hint: false }); } }; }
}'''
files['OnHome'] = page('Day one: first prompt', body, script)

# 3.2 The Clair sheet for a new user: no history, no suggestions from data yet.
body = (ROOT + '\n' + ob_backdrop() + sheet(
    sheet_head(spool('hello', 44), 'Tell Clair anything', 'It can land in several apps at once.') + '\n'
    '    <div style="flex: none; display: flex; align-items: flex-end; gap: 8px; padding: 4px 4px 4px 12px; border-radius: 12px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90;">'
    '<textarea rows="2" enterkeyhint="send" aria-label="Tell Clair anything" placeholder="Spent $12 on lunch, library books due Friday…" style="flex: 1; min-width: 0; border: 0; background: transparent; padding: 8px 0; font: inherit; font-size: 16px; line-height: 1.4; color: #2A2119; resize: none; outline: none;"></textarea>'
    '<a href="ClairResult.dc.html" aria-label="Send to Clair" style="flex: none; width: 44px; height: 44px; border-radius: 12px; background: #3557A6; color: #FFFFFF; display: grid; place-items: center;">' + svg('send', 20) + '</a></div>\n'
    '    <div style="flex: none; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">'
    + chipa(svg('cam', 20) + 'Photo', 'OnCamera.dc.html', ' min-height: 48px;') + chipa(svg('clip', 20) + 'File', 'ClairShare.dc.html', ' min-height: 48px;') + '</div>\n'
    '    <span style="display: flex; align-items: center; gap: 8px; ' + ROWM + '">' + svg('mic', 16, '#665847') + 'Hold the Clair button to talk</span>\n'
    '    <span style="' + ROWM + '">A receipt is a good first one. Clair shows what it read before anything saves.</span>') + ob_bar(' z-index: 3;') + CLOSE)
files['OnSheet'] = page('Day one: tell Clair', body)

# 3.3 Camera, asked just in time: our pre-prompt before the system one. "Not now" shows the camera-off line.
body = (ROOT + '\n' + ob_backdrop() + sheet(
    sheet_head(spool('hello', 44), '{{ head }}', '', False) + '\n'
    '    ' + iff('ask', '<p style="margin: 0; font-size: 16px; line-height: 1.45;">Clair reads the photo you take, like a receipt or a bill. Your phone asks next. Nothing is sent until you take one.</p>'
        '<div style="display: flex; gap: 8px;">' + flexbtn(btn('Not now', None, False, 'deny'), '1') + flexbtn(btn('Continue', 'Receipt.dc.html'), '1.6') + '</div>', 'true') + '\n'
    '    ' + iff('off', '<p style="margin: 0; font-size: 16px; line-height: 1.45;">Camera is off for Quilt. Pick a photo instead, or turn it on in Settings. Nothing was sent.</p>'
        '<div style="display: flex; gap: 8px;">' + flexbtn(btn('Open settings', None, False), '1') + flexbtn(btn('Pick a photo', 'Receipt.dc.html'), '1') + '</div>'
        '<button type="button" class="lk" onClick="{{ again }}" style="align-self: flex-start; border: 0; background: transparent; padding: 0; margin: -8px 0;">Back</button>') + '\n'
    ) + ob_bar(' z-index: 3;') + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { off: false }; }
  renderVals() { var self = this, off = this.state.off;
    return { ask: !off, off: off, head: off ? 'Camera is off' : 'Use your camera?',
      deny: function () { self.setState({ off: true }); }, again: function () { self.setState({ off: false }); } }; }
}'''
files['OnCamera'] = page('Camera, just in time', body, script)

# 5.1 Day-1 evening check-in, built only from Quilt data; then one reminder offer. Keep your quilt waits below.
CI = [('Budget', 'Corner Market · $35.83 added'), ('To-dos', 'Return library books · due tomorrow'), ('Calendar', 'Use the chicken and spinach by Tue')]
body = (ROOT + '\n' + scroller() + '\n' + home_top('Evening.', '<b class="num">$35.83</b> on groceries today. Library books due tomorrow.') + sect('Needs your OK · {{ qn }}') + '\n'
    '    <section class="{{ cls }}" aria-label="Evening check-in from Clair" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;">'
    '<span style="display: flex; align-items: center; gap: 4px; ' + LBL + '">' + chalk_icon(14) + 'Clair · evening check-in</span><b style="font-size: 16px; font-weight: 600;">3 things from today</b>'
    '<div style="display: flex; flex-direction: column;">' + ''.join('<span style="display: flex; align-items: center; gap: 8px; min-height: 32px; font-size: 15px;' + NUM + '">' + dot(a) + '<span style="flex: 1; min-width: 0;">' + t + '</span><span style="' + ROWM + '">' + a + '</span></span>' for a, t in CI) + '</div>'
    + iff('fresh', '<div style="display: flex; gap: 8px;">' + flexbtn(btn('Not now', None, False, 'skip'), '1') + flexbtn(btn('Review', None, True, 'review'), '1.6') + '</div>', 'true')
    + iff('offer', '<span style="' + CLAIR + '">Want a reminder at 8' + NB + 'pm for these?</span><div style="display: flex; gap: 8px;">' + flexbtn(btn('No thanks', None, False, 'noRemind'), '1') + flexbtn(btn('Remind me', None, True, 'remind'), '1.6') + '</div>')
    + iff('answered', '<span style="display: flex; align-items: center; gap: 8px; min-height: 44px; font-size: 15px;">' + svg('check', 18, '#1F6B5E', '2.2') + '<span style="flex: 1;">{{ done }}</span></span>')
    + '</section>\n'
    '    <a class="st rw" href="OnKeep.dc.html" style="padding: 12px 16px; display: flex; align-items: center; gap: 12px;"><span style="flex: 1; min-width: 0; display: flex; flex-direction: column;"><span style="' + ROWT + '">Keep your quilt</span><span style="' + ROWM + '">Right now your apps live only on this phone</span></span>' + chev_r + '</a>\n'
    + sect('Your apps · 4') + '\n' + starter_grid() + '  </div>\n' + ob_bar() + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { step: 'fresh', remind: null }; }
  renderVals() { var self = this, s = this.state.step;
    return { fresh: s === 'fresh', offer: s === 'offer', answered: s === 'done', cls: s === 'fresh' ? 'st basted' : 'st', qn: s === 'done' ? 1 : 2,
      done: this.state.remind ? 'Reminders at 8\\u00a0pm. Your phone asks to allow notifications next.' : 'No reminders. Check-ins still show up here.',
      review: function () { self.setState({ step: 'offer' }); }, skip: function () { self.setState({ step: 'done', remind: false }); },
      remind: function () { self.setState({ step: 'done', remind: true }); }, noRemind: function () { self.setState({ step: 'done', remind: false }); } }; }
}'''
files['OnCheckin'] = page('Day one: evening check-in', body, script)

# 6.1 Keep your quilt: asked after first value, never during the thread pull.
body = (ROOT + '\n' + scroller() + '\n' + home_top('Evening.', '<b class="num">$35.83</b> on groceries today. Library books due tomorrow.') + sect('Needs your OK · {{ qn }}') + '\n'
    '    ' + iff('ask', '<section class="st" style="padding: 16px; display: flex; flex-direction: column; gap: 12px;"><span style="display: flex; align-items: center; gap: 8px; ' + LBL + '">' + QLOGO + 'Your quilt</span>'
        '<b style="' + disp(22) + ' line-height: 1.1;">Keep your quilt</b><p style="margin: 0; font-size: 16px; line-height: 1.45;">Right now your apps live only on this phone. Add Google or an email so you can get them back on any device, like your laptop.</p>'
        + btn('Continue with Google', None, True, 'google') + btn('Use email', None, False, 'email')
        + '<button type="button" class="lk" onClick="{{ notNow }}" style="align-self: center; border: 0; background: transparent; padding: 0; margin: -4px 0;">Not now</button></section>', 'true') + '\n'
    '    ' + iff('kept', '<section class="st" style="padding: 12px 16px; display: flex; flex-direction: column; gap: 8px;"><span style="display: flex; align-items: center; gap: 8px; font-size: 16px;">' + svg('check', 18, '#1F6B5E', '2.2') + '<span style="flex: 1;">{{ keptLine }}</span></span>'
        + link('Add a device', 'OnDevice.dc.html', True, 'align-self: flex-start; margin: -4px 0;') + '</section>') + '\n'
    '    ' + iff('later', '<p style="margin: 0; ' + ROWM + '">Clair asks once more after a few more adds. It stays in Settings any time.</p>') + '\n'
    + sect('Your apps · 4') + '\n' + starter_grid() + '  </div>\n' + ob_bar() + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { s: 'ask' }; }
  renderVals() { var self = this, s = this.state.s;
    return { ask: s === 'ask', kept: s === 'google' || s === 'email', later: s === 'later', qn: s === 'ask' ? 1 : 0,
      keptLine: s === 'email' ? 'Kept. We sent a link to your email to finish.' : 'Kept. Your quilt is saved to sam@gmail.com.',
      google: function () { self.setState({ s: 'google' }); }, email: function () { self.setState({ s: 'email' }); }, notNow: function () { self.setState({ s: 'later' }); } }; }
}'''
files['OnKeep'] = page('Keep your quilt', body, script)

# 6.4 Phone: Settings > Add a device shows a one-time 6-digit code.
body = (ROOT + '\n' + scroller() + '\n' + topbar('You.dc.html', 'Back to Settings', h1mid('Add a device')) + '\n'
    '    <section class="st" style="padding: 16px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;"><span style="font-size: 16px;">Open Quilt on your laptop and enter</span>'
    '<span aria-label="Join code {{ codeAria }}" style="font-family: \'DM Mono\', monospace; font-weight: 500; font-size: 40px; letter-spacing: 0.04em;' + NUM + '">{{ code }}</span>'
    '<span style="' + ROWM + '">The code works once and expires soon.</span></section>\n'
    '    <div style="display: flex; align-items: center; gap: 12px; ' + CLAIR + '">' + spool('waiting', 30) + 'Waiting for your laptop…</div>\n'
    + sect('On the laptop') + '\n'
    '    <ol style="margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 16px; line-height: 1.45;"><li>Open Quilt in a browser.</li><li>Choose “Enter a code from your phone”.</li><li>Type the 6 digits.</li></ol>\n'
    '    <div style="display: grid; gap: 8px;">' + btn('Get a new code', None, False, 'renew') + '</div>\n'
    '    ' + link('See the laptop screen', 'OnLaptop.dc.html', True, 'justify-self: start; margin: -8px 0;') + '\n'
    '  </div>\n' + ob_bar() + CLOSE)
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { n: 0 }; }
  renderVals() { var self = this, c = ['482 913', '730 155'][this.state.n % 2];
    return { code: c, codeAria: c.split('').join(' '), renew: function () { self.setState({ n: self.state.n + 1 }); } }; }
}'''
files['OnDevice'] = page('Add a device', body, script)

# 6.5 Laptop joins: the website's Welcome, six boxes. 482913 joins; anything else clears.
body = ('<div style="width: 1280px; height: 800px; position: relative; overflow: hidden; background: #F4EEE1; color: #2A2119; font-family: \'Hanken Grotesk\', system-ui, sans-serif; display: grid; grid-template-columns: minmax(0, 1fr) 480px minmax(0, 1fr);">\n'
    '  <span style="position: absolute; top: 28px; left: 32px; display: flex; gap: 8px; align-items: center; ' + disp(18) + '">' + QLOGO + 'quilt</span>\n'
    '  <main style="grid-column: 2; align-self: center; display: flex; flex-direction: column; gap: 24px;">\n'
    '    <div style="display: flex; align-items: center; gap: 16px;">' + iff('notJoined', spool('hello', 96), 'true') + iff('joined', spool('stitched', 96)) + '<h1 style="margin: 0; ' + disp(30) + ' line-height: 1.1;">{{ head }}</h1></div>\n'
    '    ' + iff('notJoined', '<section class="st" style="padding: 24px; display: flex; flex-direction: column; gap: 16px;"><label for="jc" style="' + LBL + '">Enter a code from your phone</label>'
        '<div style="position: relative; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px;"><sc-for list="{{ boxes }}" as="b" hint-placeholder-count="6"><span aria-hidden="true" style="{{ b.style }}">{{ b.d }}</span></sc-for>'
        '<input id="jc" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="{{ code }}" onInput="{{ typed }}" style="position: absolute; inset: 0; width: 100%; opacity: 0; border: 0; font-size: 16px; cursor: text;"></div>'
        '<span aria-live="polite" style="{{ msgStyle }}">{{ msg }}</span></section>', 'true') + '\n'
    '    ' + iff('joined', '<p style="margin: 0; font-size: 17px; line-height: 1.45;">The laptop\'s own empty guest quilt is gone. Everything you add here shows on your phone too.</p><div style="display: flex;">' + btn('Open my quilt', 'Laptop.dc.html') + '</div>') + '\n'
    '  </main>\n</div>')
script = '''class Component extends DCLogic {
  constructor(props) { super(props); this.state = { code: '', bad: false, joined: false }; }
  renderVals() {
    var self = this, st = this.state;
    var boxes = [0, 1, 2, 3, 4, 5].map(function (i) { var d = st.code[i] || '', next = i === st.code.length;
      return { d: d, style: 'height: 64px; border-radius: 12px; background: #FFFDF8; display: grid; place-items: center; font-family: \\'DM Mono\\', monospace; font-size: 28px; ' + (next ? 'box-shadow: inset 0 0 0 2px #3557A6;' : 'box-shadow: inset 0 0 0 1.5px #BFAE90;') }; });
    return { boxes: boxes, code: st.code, joined: st.joined, notJoined: !st.joined,
      head: st.joined ? 'Joined. Same quilt as your phone.' : "Hi. I'm Clair. I keep track of the stuff that slips.",
      msg: st.bad ? "That code didn't work. Get a new one on your phone." : 'On your phone: Settings, then Add a device.',
      msgStyle: 'font-size: 15px; ' + (st.bad ? 'font-weight: 600; color: #2A2119;' : 'color: #665847;'),
      typed: function (e) { var v = e.target.value.replace(/\\D/g, '').slice(0, 6);
        if (v.length < 6) return self.setState({ code: v, bad: false });
        if (v === '482913') self.setState({ code: v, joined: true }); else self.setState({ code: '', bad: true }); } };
  }
}'''
files['OnLaptop'] = page('Join from a laptop', body, script, w=1280, h=800)

# ---------- Laptop (new, 1280x800) ----------
side = ''.join('<a href="' + HREF[n] + '" style="display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 8px; border-radius: 10px; font-size: 14px;' + (' background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-weight: 600;' if n == 'Budget' else '') + '"><span style="width: 26px; height: 26px; border-radius: 8px; background: ' + DYE[n] + '; display: grid; place-items: center;">' + svg(ICON[n], 15) + '</span>' + n + (tag() if n == 'Budget' else '') + '</a>' for n in ['Budget', 'Groceries', 'Calendar', 'To-dos', 'Workout', 'Classes', 'Subscriptions'])
body = '''<div style="width: 1280px; height: 800px; display: grid; grid-template-columns: 240px minmax(0, 1fr) 320px; background: #F4EEE1; color: #2A2119; font-family: 'Hanken Grotesk', system-ui, sans-serif; overflow: hidden;">
  <aside aria-label="Apps" style="padding: 22px 14px; display: flex; flex-direction: column; gap: 8px; background-image: linear-gradient(0deg, #DCCFB6 58%, transparent 0); background-size: 1.5px 8px; background-repeat: repeat-y; background-position: 100% 0;">
    <span style="display: flex; gap: 8px; align-items: center; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 18px; padding: 0 6px 6px;"><svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="9" height="9" rx="2" fill="#E3A72F"></rect><rect x="12" y="1" width="9" height="9" rx="2" fill="#5B7DB1"></rect><rect x="1" y="12" width="9" height="9" rx="2" fill="#8DB580"></rect><rect x="12" y="12" width="9" height="9" rx="2" fill="#9C6BA8"></rect></svg>quilt</span>
    <a href="ClairSheet.dc.html" role="button" aria-label="''' + CLAIR_ARIA + '''" style="display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 12px; border-radius: 12px; background: #2A2119; color: #FBF6EC; font-size: 14px; font-weight: 600;">''' + svg('spool', 20, '#FBF6EC') + '''Tell Clair anything</a>
    <a href="Search.dc.html" style="display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 10px; border-radius: 10px; background: #FFFDF8; box-shadow: inset 0 0 0 1.5px #BFAE90; font-size: 13px; color: #665847;">''' + svg('search', 16) + '''Search<span style="margin-left: auto; font-family: 'DM Mono', monospace; font-size: 11px; padding: 1px 6px; border-radius: 5px; background: #EEE6D6;">⌘K</span></a>
    <span style="''' + LBL + ''' padding: 8px 8px 0;">Apps</span>''' + side + '''
    <a href="Build.dc.html" style="display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 8px; font-size: 14px; color: #22396F; font-weight: 600;">''' + svg('plus', 16) + '''New app</a>
    <a href="You.dc.html" style="margin-top: auto; display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 8px; font-size: 13px;"><span style="width: 28px; height: 28px; border-radius: 50%; background: #F8DCC2; display: grid; place-items: center;">''' + svg('user', 15) + '''</span>Sam · 32 credits</a>
  </aside>
  <main style="padding: 26px 30px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; min-width: 0;">
    <div style="display: flex; align-items: center; gap: 10px;"><span style="width: 36px; height: 36px; border-radius: 10px; background: #D3ECE7; display: grid; place-items: center;">''' + svg('wallet') + '''</span><h1 style="margin: 0; ''' + disp(30) + '''">Budget</h1><span style="font-size: 14px; color: #665847;">November</span></div>
    <div style="display: grid; grid-template-columns: 1.1fr 1fr; gap: 16px;">
      <section class="st" style="padding: 18px; display: flex; flex-direction: column; gap: 10px;"><div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;"><span style="''' + disp(46, NUM) + ''' line-height: 1;">$376</span><span style="font-size: 14px; color: #665847;">left of $1,200</span>''' + tag() + '''</div><div style="height: 8px; border-radius: 4px; background: #EEE6D6; overflow: hidden;"><div style="width: 69%; height: 100%; background: #1F6B5E;"></div></div><span style="font-size: 13px; color: #665847;">Was $412 · Corner Market receipt from your phone, 5:41&nbsp;pm</span></section>
      <section class="st" style="padding: 14px 18px; display: flex; flex-direction: column; gap: 8px;">''' + ''.join('<div style="display: flex; justify-content: space-between; font-size: 13.5px;"><span>' + n + '</span><span style="font-family: \'DM Mono\', monospace;">' + v + '</span></div><div style="height: 6px; border-radius: 3px; background: #EEE6D6; position: relative; overflow: hidden;"><div style="position: absolute; inset: 0 auto 0 0; width: ' + w + '%; background: #1F6B5E;"></div>' + ('<div style="position: absolute; inset: 0 0 0 auto; width: 9%; background: repeating-linear-gradient(45deg, #2A2119 0 1.3px, transparent 1.3px 4px), repeating-linear-gradient(-45deg, #2A2119 0 1.3px, transparent 1.3px 4px);"></div>' if o else '') + '</div>' for n, v, w, o in [('Groceries', '$177.83 / $200', '89', 0), ('Eating out', '$165 / $150', '91', 1), ('Transport', '$42 / $80', '52', 0), ('Subscriptions', '$38.46 / $40', '96', 0)]) + '''</section>
    </div>
    <span style="''' + LBL + '''">Recent</span>
    <section class="st" style="padding: 6px;">''' + ''.join('<div style="display: grid; grid-template-columns: minmax(0, 1fr) 210px 90px; gap: 10px; align-items: center; min-height: 48px; padding: 0 12px; border-radius: 10px; font-size: 14px;' + (' background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #3557A6;' if i == 0 else '') + '"><span>' + a + '</span><span style="font-size: 12.5px; color: #665847;">' + b + '</span><span style="text-align: right; font-family: \'DM Mono\', monospace;">' + c + '</span></div>' for i, (a, b, c) in enumerate([('Corner Market', 'Groceries · today 5:41' + NB + 'pm', '$35.83'), ('Union food court', 'Eating out · yesterday', '$11.40'), ('Gas', 'Transport · Tuesday', '$28.00'), ('Spotify', 'Subscriptions · Sun 22 Nov', '$11.99')])) + '''</section>
  </main>
  <aside aria-label="Row detail" style="background: #FFFDF8; padding: 26px 22px; display: flex; flex-direction: column; gap: 12px;">
    <span style="''' + LBL + '''">Detail</span>
    <b style="''' + disp(22) + '''">Corner Market</b><span style="''' + disp(30, NUM) + '''">$35.83</span><span style="font-size: 13px; color: #665847;">Groceries · today 5:41&nbsp;pm · from your receipt photo</span>
    <section class="st" style="padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; font-size: 13.5px;"><span>Oat milk $3.49</span><span>Eggs, dozen $4.29</span><span>Bananas $1.87</span><span>Chicken thighs $8.62</span><span style="color: #665847;">+ 4 more</span></section>
    <span style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 13px; color: #665847;">also in ''' + dot('Groceries') + 'Groceries ' + dot('Calendar') + '''Calendar</span>
    <div style="margin-top: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">''' + btn('Edit', 'EditItem.dc.html', False) + btn(svg('trash', 16) + 'Delete', None, False) + '''</div>
  </aside>
</div>'''
files['Laptop'] = page('Quilt on a laptop', body, w=1280, h=800)

if __name__ == '__main__':
    for name, txt in files.items():
        open(os.path.join(sys.argv[1], name + '.dc.html'), 'w').write(txt)
    print('written', sorted(files))
