"""Render the repo's markdown docs as PAGE artboards for the design canvas.

Usage: python gen_docs.py <repo root> <canvas dir> [heights.json]
Needs the `markdown` package. Writes Doc*.dc.html / Spec*.dc.html into <canvas dir>
and prints the board list as JSON (path, title, page). Heights come from heights.json
(measured by tests/measure_docs.js) or a rough estimate.
"""
import html, json, os, re, sys
import markdown

ROOT, OUT = sys.argv[1], sys.argv[2]
HEIGHTS = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else {}

DOCS = [  # (artboard stem, page, title, sources)
    ('DocPitch', 'docs', 'Pitch: product, MVP and DevDay', ['docs/pitch.md']),
    ('DocDemoDay', 'docs', 'Demo day guide', ['docs/demo-day.md']),
    ('DocOnboarding', 'docs', 'Onboarding journey', ['docs/onboarding.md']),
    ('DocPersona', 'docs', 'First user: Sam', ['docs/research/persona-sam-student.md']),
    ('DocHomeJobs', 'docs', 'What Home is for', ['docs/research/home-jtbd.md']),
    ('DocSetup', 'docs', 'Claude Code on a new device', ['docs/setup-claude-code.md']),
    ('SpecPRD', 'specs', 'PRD', ['spec/prd.md']),
    ('SpecStories', 'specs', 'User stories', ['spec/prd-stories.md']),
    ('SpecBackend', 'specs', 'Backend', ['spec/backend.md']),
    ('SpecClair', 'specs', 'Clair agent loop', ['spec/clair-agent.md']),
    ('SpecUI', 'specs', 'UI tech plan', ['spec/ui-tech-plan.md']),
    ('SpecADRs', 'specs', 'Decision records', sorted('spec/adr/' + f for f in os.listdir(os.path.join(ROOT, 'spec/adr')) if f.endswith('.md'))),
    ('SpecGlossary', 'specs', 'Glossary', ['GLOSSARY.md']),
]
# markdown file name -> artboard, so links between docs keep working on the canvas
MAXH = 7600  # canvas frames top out at 8000 px
LINKS = {}
for stem, _, _, srcs in DOCS:
    first = stem + ('1' if HEIGHTS.get(stem, {}).get('total', 0) > MAXH else '') + '.dc.html'
    for src in srcs:
        LINKS[os.path.basename(src)] = first

CSS = """body{margin:0}
a{color:#2F55C4}a:hover{color:#1A2232}
.doc{font-family:'Hanken Grotesk',system-ui,sans-serif;font-size:17px;line-height:1.6;color:#1A2232}
.doc h1{font-size:40px;line-height:1.15;margin:0 0 24px;letter-spacing:-0.02em}
.doc h2{font-size:28px;line-height:1.2;margin:48px 0 12px;letter-spacing:-0.01em}
.doc h3{font-size:21px;margin:32px 0 8px}
.doc h4{font-size:18px;margin:24px 0 8px}
.doc p,.doc ul,.doc ol{margin:0 0 14px}
.doc li{margin:4px 0}
.doc code{font-family:'DM Mono',ui-monospace,monospace;font-size:0.88em;background:#EEF0F3;padding:1px 5px;border-radius:4px}
.doc pre{background:#EEF0F3;padding:16px;border-radius:8px;overflow-x:auto;font-size:14px;line-height:1.5}
.doc pre code{background:none;padding:0}
.doc .tbl{overflow-x:auto;margin:0 0 18px}
.doc table{border-collapse:collapse;font-size:15px;min-width:100%}
.doc th,.doc td{border-bottom:1px solid #D5D9E0;padding:8px 10px;text-align:left;vertical-align:top}
.doc th{font-weight:700}
.doc blockquote{margin:0 0 14px;padding-left:16px;border-left:3px solid #D5D9E0;color:#4A5366}
.doc hr{border:0;border-top:1px solid #D5D9E0;margin:32px 0}
.doc .src{font-family:'DM Mono',ui-monospace,monospace;font-size:13px;color:#4A5366;margin:0 0 8px}"""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&amp;family=Hanken+Grotesk:wght@400;600;700&amp;display=swap">'


def strip_frontmatter(t):
    return re.sub(r'\A---\n.*?\n---\n', '', t, flags=re.S)


def fix_links(h):
    def sub(m):
        href = m.group(1)
        if href.startswith(('http://', 'https://', '#', 'mailto:')):
            return m.group(0)
        name = os.path.basename(href.split('#')[0])
        return 'href="%s"' % LINKS[name] if name in LINKS else 'href="#"'
    h = re.sub(r'href="([^"]*)"', sub, h)
    return h.replace('<table>', '<div class="tbl"><table>').replace('</table>', '</table></div>')


def body(srcs):
    parts = []
    for s in srcs:
        t = strip_frontmatter(open(os.path.join(ROOT, s), encoding='utf-8').read())
        h = markdown.markdown(t, extensions=['tables', 'fenced_code', 'sane_lists'], output_format='html')
        parts.append('<p class="src">%s</p>\n%s' % (html.escape(s), fix_links(h)))
    out = '\n<hr />\n'.join(parts)
    # the runtime treats {{ }} as holes; docs never mean them that way
    return out.replace('{{', '{&#123;').replace('}}', '&#125;}')


def page(stem, title, inner, h):
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
%s
</style>
</helmet>
<div style="width: 100%%; min-height: %dpx; background: #FFFFFF; box-sizing: border-box;">
<article class="doc" style="box-sizing: border-box; max-width: 920px; margin: 0 auto; padding: 72px 40px 96px;">
%s
</article>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":1280,"height":%d}}'>
class Component extends DCLogic {
  renderVals() { return {}; }
}
</script>
</body>
</html>
''' % (html.escape(title), FONTS, CSS, h, inner, h)


def chunks(stem, inner):
    """Split at top-level h2s so every part fits one frame, using measured offsets."""
    m = HEIGHTS.get(stem)
    if not m or m['total'] <= MAXH:
        return [(inner, int((m['total'] if m else 2000) * 1.04) + 40)]
    pieces = re.split(r'(?=<h[23][ >])', inner)  # pieces[0] = before the first h2
    tops = [0] + m['h2'] + [m['total']]
    out, start = [], 0
    for i in range(1, len(pieces) + 1):
        if tops[i] - tops[start] > MAXH and i - 1 > start:
            out.append((''.join(pieces[start:i - 1]), tops[i - 1] - tops[start]))
            start = i - 1
    out.append((''.join(pieces[start:]), tops[-1] - tops[start]))
    return [(c, min(8000, int(h * 1.04) + 200)) for c, h in out]


boards = []
for stem, pg, title, srcs in DOCS:
    inner = body(srcs)
    parts = chunks(stem, inner)
    for n, (c, h) in enumerate(parts, 1):
        name = stem if len(parts) == 1 else '%s%d' % (stem, n)
        t = title if len(parts) == 1 else '%s (%d of %d)' % (title, n, len(parts))
        open(os.path.join(OUT, name + '.dc.html'), 'w', encoding='utf-8').write(page(name, t, c, h))
        boards.append({'path': name + '.dc.html', 'title': t, 'page': pg, 'h': h, 'doc': stem})
    # plain preview for measuring (same CSS, no runtime)
    prev = '<!doctype html><html><head><meta charset="utf-8">%s<style>%s</style></head><body><div style="width:100%%;background:#fff"><article class="doc" style="box-sizing:border-box;max-width:920px;margin:0 auto;padding:72px 40px 96px;">%s</article></div></body></html>' % (FONTS, CSS, inner)
    os.makedirs(os.path.join(OUT, '..', 'docs-preview'), exist_ok=True)
    open(os.path.join(OUT, '..', 'docs-preview', stem + '.html'), 'w', encoding='utf-8').write(prev)
print(json.dumps(boards))
