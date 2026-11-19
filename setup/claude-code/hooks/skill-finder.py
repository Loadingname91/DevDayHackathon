#!/usr/bin/env python3
"""UserPromptSubmit hook: find installed skills relevant to the prompt and remind Claude to use them.

Scans ~/.claude/skills/*/SKILL.md and SKILL.md files of *enabled* plugins in ~/.claude/plugins/cache,
scores each by word overlap between the prompt and the skill's name + description, and injects the
top matches as additionalContext. Always exits 0 so it can never block a prompt.
ponytail: plain keyword overlap, no embeddings; good enough to surface candidates, Claude decides.
"""
import glob, json, os, re, sys

HOME = os.path.expanduser('~/.claude')
STOP = set('a an and are as at be but by can do does for from get has have how i if in into is it its me my of on or our should so that the their them then there these this to use used uses using was we what when where which who why will with you your yes no not just also any all more most some such than very want wanna make please help need like'.split())


def words(text):
    return {w for w in re.findall(r'[a-z][a-z0-9-]{2,}', text.lower()) if w not in STOP}


def front(path):
    try:
        head = open(path, encoding='utf-8', errors='ignore').read(4000)
    except OSError:
        return None, ''
    m = re.match(r'---\s*\n(.*?)\n---', head, re.S)
    if not m:
        return None, ''
    fm = m.group(1)
    name = re.search(r'^name:\s*(.+)$', fm, re.M)
    desc = re.search(r'^description:\s*(.*(?:\n[ \t]+.*)*)', fm, re.M)
    d = re.sub(r'\s+', ' ', desc.group(1)).strip(' >|-"\'') if desc else ''
    return (name.group(1).strip().strip('"\'') if name else None), d


def skills():
    out = {}
    for p in glob.glob(os.path.join(HOME, 'skills', '*', 'SKILL.md')):
        n, d = front(p)
        if n:
            out[n] = d
    try:
        enabled = json.load(open(os.path.join(HOME, 'settings.json'))).get('enabledPlugins', {})
    except Exception:
        enabled = {}
    for key, on in enabled.items():
        if on is not True or '@' not in key:
            continue
        plugin, market = key.split('@', 1)
        for p in glob.glob(os.path.join(HOME, 'plugins', 'cache', market, plugin, '*', '**', 'SKILL.md'), recursive=True):
            n, d = front(p)
            if n:
                out.setdefault(f'{plugin}:{n}', d)
    return out


def main():
    try:
        prompt = json.load(sys.stdin).get('prompt', '')
    except Exception:
        prompt = ''
    pw = words(prompt)
    if len(pw) < 2:
        return
    scored = []
    for name, desc in skills().items():
        nw = words(name.replace(':', ' ').replace('-', ' '))
        score = 3 * len(pw & nw) + len(pw & words(desc))
        if score >= 3:
            scored.append((score, name, desc))
    scored.sort(reverse=True)
    top = scored[:8]
    lines = ['Skill check (pre-hook): before answering, look at the available skills list and invoke any skill that fits this message with the Skill tool (plugin skills use plugin:skill names). Keyword matches for this prompt:']
    lines += [f'- {n}: {d[:160]}' for _, n, d in top] or ['- (no strong keyword match; still scan the list)']
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': '\n'.join(lines)}}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass
