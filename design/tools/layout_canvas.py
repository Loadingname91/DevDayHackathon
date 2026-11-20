import json, os, sys
p = os.path.join(sys.argv[1], 'canvas.json')
c = json.load(open(p))
b = c['boards']
rows = [
    (1340, 'Home and finding your apps', [('Main', 'Home: the evening check-in waits in the queue'), ('Tabs', 'Your apps (swipe up from any app)'), ('Search', 'Search (pull down anywhere; scoped to Budget)'), ('You', 'You: activity, credits, privacy'), ('Rule', 'Reminder from something Clair noticed')]),
    (2640, 'Clair: tell, talk, ask, share', [('ClairSheet', 'Tap Clair: tell Clair anything'), ('ClairTalk', 'Hold Clair: talk, release to send'), ('ClairResult', 'Tell and ask: nothing saves before OK'), ('ClairAsk', 'Ask: your data vs a general answer'), ('ClairPhoto', 'A photo and a question: answer, not a log'), ('ClairShare', 'Share a file into Quilt'), ('ClairFridge', 'Fridge photo: a menu question; picks become notes'), ('ClairNotes', 'Settings: what Clair remembers')]),
    (3940, 'Demo path: one receipt updates three apps', [('Groceries', 'Groceries'), ('Receipt', 'Review receipt'), ('Budget', 'Budget'), ('Calendar', 'Calendar: dates from every app'), ('EditItem', 'Edit an item')]),
    (5240, 'Clair builds an app', [('Build', 'New app 1 · describe'), ('Preview', 'New app 2 · pick a layout'), ('Arrange', 'New app 3 · arrange'), ('Connect', 'New app 4 · connect and add'), ('Empty', 'New app 5 · ready'), ('Clair', 'Clair chat')]),
    (6540, 'Apps made from blocks', [('Workout', 'Workout: an app with 5 tabs'), ('Session', 'Log a set'), ('Todos', 'To-dos')]),
    (9240, 'First open: onboarding', [('OnWelcome', '1.3 Welcome: guest, no sign-up'), ('OnSlips', '2.1 What slips for you?'), ('OnMaking', '2.2 Starter apps, instant; pins fill'),
        ('OnHome', '3.1 First prompt on Home'), ('OnSheet', '3.2 Clair sheet, new user'), ('OnCamera', '3.3 Camera asked just in time'),
        ('OnCheckin', '5.1 Day-1 evening check-in'), ('OnKeep', '6.1 Keep your quilt'), ('OnDevice', '6.4 Add a device: join code'),
        ('OnLaptop', '6.5 Laptop joins with the code', 1280, 800), ('Welcome', '2.4 Skipped picks: day-one Home'), ('OnOffline', 'No connection on first open')]),
]
order = ['DesignSystem.dc.html', 'Spool.dc.html']
for y, _, items in rows:
    x = 0
    for name, title, *size in items:
        w, h = size or (390, 844)
        key = name + '.dc.html'
        entry = b.get(key, {})
        entry.update({'x': x, 'y': y, 'w': w, 'h': h, 'title': title, 'is_interactive': True, 'radius': 28 if w == 390 else 18})
        x += w + 80
        b[key] = entry
        order.append(key)
b['Laptop.dc.html'] = {'x': 0, 'y': 7840, 'w': 1280, 'h': 800, 'title': 'Laptop: apps | app | detail', 'is_interactive': True, 'radius': 18}
order.append('Laptop.dc.html')
order = ['Main.dc.html'] + [k for k in order if k != 'Main.dc.html']
assert set(order) == set(b.keys()), set(b.keys()) ^ set(order)
c['order'] = order
n = c['notes']
for k in [k for k in n if k.startswith('row') and k != 'row0']: del n[k]
for r, (y, t, items) in enumerate(rows, 1):
    n['row' + str(r)] = {'x': 0, 'y': y - 300, 'text': t, 'kind': 'title1', 'maxW': max(1800, sum((it[2] if len(it) > 2 else 390) + 80 for it in items) - 80)}
n['row' + str(len(rows) + 1)] = {'x': 0, 'y': 7540, 'text': 'Laptop: the same apps, wider', 'kind': 'title1', 'maxW': 1800}
n['onboarding'] = {'x': -620, 'y': 9240, 'w': 480, 'size': 'm', 'fill': 'teal', 'text': (
    "First open (docs/onboarding.md). Press Play on Welcome and tap through.\n\n"
    "Welcome > Start > What slips? (pick Money, Groceries, To-dos) > Make my apps > starter apps appear, pins fill (Calendar last) > Open Home > "
    "Clair button > Photo > camera pre-prompt > Continue > Review receipt (row 3: the first basted card) > Add to 3 apps (the first stitched moment).\n\n"
    "Evening: check-in > Review > Remind me. Then Keep your quilt > Continue with Google > Add a device (code 482 913) > the laptop: type 482913 to join, anything else shows the error.\n\n"
    "Branches: Skip on What slips? goes to the skipped-picks Home (the old Day one board, updated: no name, first prompt). "
    "Not now on the camera ask shows the camera-off line. No connection on first open: Try again.")}
n['screens']['text'] = ("Every screen is in Soft Quilt, light mode on Mint air (restyled Nov 19). Dark mode and the ground picker are on the page \"Look: Soft Quilt\".\n\n"
    "Row 1 · Home and finding: Home, Your apps, Search, You, Reminder.\n"
    "Row 2 · Clair: tap the Clair button, hold it to talk, tell and ask, data vs general questions, a photo with a question, share a file in, a fridge photo that asks what's low, what Clair remembers.\n"
    "Row 3 · Demo path: Groceries, Review receipt, Budget, Calendar, Edit an item.\n"
    "Row 4 · Clair builds an app: describe, pick a layout, arrange, connect and add, ready; Clair chat.\n"
    "Row 5 · Apps made from blocks: Workout (5 tabs), Log a set, To-dos.\n"
    "Row 6 · Laptop.\n"
    "Row 7 · First open: onboarding, Welcome to second device.\n\n"
    "The main button is Clair: one place to put anything in or ask anything, and it can land in several apps. A receipt is one example. Search is pull-down.\n\n"
    "Words: Clair builds “apps”; sections inside an app are “tabs”. Buttons say what happens.")
n['flows']['text'] = ("Click paths (press Play on any board)\n\n"
    "Demo: Home > Clair > Photo > Review receipt > Add to 3 apps > See Budget ($412 → $376) > Calendar.\n\n"
    "Clair: Home > Clair > “Spent $12 on lunch” > Add to 3 apps; the same sheet answers “Can I afford $60 concert tickets?” from Budget. Hold Clair to talk. File > a shared syllabus > Add to 2 apps.\n\n"
    "Photo and ask: a photo with a question gets an answer, not a log (Clair offers “Log these items or just answer?”); receipts still go to Review receipt. Data answers cite your apps; general answers say so and offer a tracker.\n\n"
    "Coming back: Home > Show 3 more > Clair's evening check-in > Review > Update 3 apps.\n\n"
    "Build: Your apps > New app > Build it > pick a layout > Arrange or Use this layout > Add to my apps > ready.\n\n"
    "Everywhere: the pinned bar (Budget, Groceries, Calendar, To-dos) and the Clair button.")
n['flows']['y'] = 3940
n['links'] = {'x': -620, 'y': 6540, 'w': 480, 'size': 'm', 'fill': 'yellow', 'text': (
    "Live versions and docs (Nov 19)\n\n"
    "Motion catalogue: every animation, named and playable, with a reduced-motion switch: claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC\n\n"
    "Home prototype (demo start state, Clair sheet, thread pull): claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV\n\n"
    "Flows prototype (build an app, swipe rows, sheets, pull to search, Just used on the bar): claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne\n\n"
    "Docs in the repo: docs/prd.md, docs/ui-tech-plan.md, docs/demo-readiness.md")}
json.dump(c, open(p, 'w'), ensure_ascii=False)
print('boards', len(b), 'order', len(order))
