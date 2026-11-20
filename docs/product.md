# Quilt: the product in plain words

Written late on Thu 19 Nov 2026. This is the short version of what we're building. The requirements are in `spec/prd.md`, and the longer overview with every app and plan is at https://claude.ai/artifact/6TXLXKTmxbqjt3kv8bbgRP.

## What it is

Quilt is a personal app builder. You describe the app you need, and Clair, Quilt's AI, builds it from a small set of blocks. Every app is connected to your other apps and your calendar from the moment it exists. It runs on your phone and your laptop, and both stay in sync.

Three things make it different from a notes app or an AI app builder:

- **Apps know about each other.** A grocery trip shows up in your budget. A class, a workout and a dentist appointment all sit on one calendar.
- **Clair uses all of it.** Ask Clair to plan something and it reads the apps that matter before it answers, and it tells you which ones it read.
- **Nothing changes without your OK.** Clair shows you what it wants to change as a card. You tap once to accept and once to undo.

## Who it's for

Students first: people managing money, classes, food and workouts on their own, across apps that don't share anything. Later, anyone whose life admin is scattered the same way.

## The apps

Quilt starts you with ready-made apps and builds any other app you describe. In the demo account, Clair built Calories, Running, Cycle, Notes and Subscriptions from one sentence each.

| App | What it's for | Tabs |
| --- | --- | --- |
| Budget | Spending against a monthly amount, with limits per category | Overview, Spending, Categories |
| Groceries | Shopping lists, trips, and what you usually buy | List, Trips |
| Calendar | Every date from every app, plus your Google Calendar | Today, Week, Events |
| To-dos | Tasks with a due date, a place and repeats | Today, All, Done |
| Classes | Class times, assignments and exams | Schedule, Due, Exams |
| Notes | A folder of notes per class | Notebooks, All notes |
| Workout | Planned sessions, routines and logged sets | Today, Log, History, Progress, Routines |
| Subscriptions | What you pay each month and when it renews | Subscriptions, Renewals |
| Calories | Meals with calories and protein, saved foods, an optional daily target | Today, Log, Foods |
| Meditation | Sessions with minutes, kind, and mood before and after | Sessions, This week |
| Running | Runs with distance and time, and the races you're training for | This week, Log, Races |
| Cycle | A daily log and when each cycle started. Clair can't read it unless you switch that on | Log, Cycles |

Any app that has rules also gets a Workflows tab.

## How you put things in

Type it, say it, take a photo, or drop in a file. Clair works out which apps it belongs in and shows you one card. For the hackathon, typing is what works; photos come second.

## Rules and automations

A rule is a sentence: "Every Sunday at 7 pm, plan next week's training" or "When I add an exam, add a study to-do two days before". You describe it and Clair sets it up. Rules can run on a schedule or when something is added or changed, and they can add things to other apps or ask Clair to work something out. Anything Clair decides still waits for your OK.

This is the part we're building at the hackathon.

## What Clair can do with connected data

The example we're demoing: "Plan my training for next week." Clair reads nine apps, including your Google Calendar, your runs, what you ate and, if you've shared it, your cycle log. It comes back with one plan:

- the gym sessions that clash with something are moved, and the ones that don't are left alone;
- two runs are added on the days you're away from the gym, sized from your last long run and your race date;
- a short recovery session goes on the evening of the hardest day;
- one thing you keep eating but haven't got on your list goes on the shopping list.

Every line has its reason and the app it came from. Clair repeats your own numbers back ("you logged 1,650 to 1,970 calories a day") and doesn't judge them.

Also in the hackathon build: appointment reminders. Calendar events can be marked doctor, dentist or barber. Clair sees three haircuts five weeks apart, tells you the next one is due, and offers to add it at a free time with a reminder the day before. It never books anything.

The same idea, later:

- Plan dinners from what's in Groceries, what's left in Budget and which nights are busy.
- Lighten workouts in exam week and suggest a short meditation the night before.
- Pull your own logs together before a doctor's visit.

Clair reports your own numbers and proposes changes to plans. It doesn't give medical or diet advice.

## Free and paid

Prices are decided as a plan, not yet charged.

| | Free | Plus | Pro |
| --- | --- | --- | --- |
| Price | $0 | $6 a month, or $4 for students | $12 a month |
| Apps | Up to 5 | Unlimited | Unlimited |
| Sync, connections between apps, import and export | Yes | Yes | Yes |
| Clair | 50 credits a month | 1,000 credits, voice, questions across apps | 4,000 credits |
| Rules | Connections between apps | 10 rules, Clair's own pattern checks with a monthly cap | Unlimited, plus sending and outside triggers |
| Outside data | Google Calendar | Health data from the phone | Bank feeds and other connectors |

Import from Notion, Apple Notes, Google Docs and Obsidian, and full export, are free on every plan.

## What's next after the hackathon

| Next | What it adds |
| --- | --- |
| Calories, deeper | Meals from a photo, calorie estimates you can correct, a trends chart |
| Health data | Workouts, heart rate, sleep and steps from the phone, Android first |
| Reminders that reach you | Phone notifications for the reminders Clair sets |
| Meditation, deeper | A timer, and minutes from other apps |
| Cycle, deeper | A prediction shown in the app, as a range from your own history |
| The planner going further | How you slept, changing the routine itself, and planning meals, not just the shopping list |
| Native phone app | Needed for health data, notifications and widgets |
| Encryption | Nothing is encrypted yet; it comes before real users' sensitive data |

One question is still open on Calories: whether it sets a daily target for you. The big calorie apps do. MyFitnessPal asks your height, weight, age, sex, activity level and how fast you want to gain or lose, then works out a daily number ([how it calculates goals](https://support.myfitnesspal.com/hc/en-us/articles/360032625391-How-does-MyFitnessPal-calculate-my-initial-goals)). Cronometer works its energy target out from your weight goal ([Cronometer targets](https://support.cronometer.com/hc/en-us/articles/33113157685652)). MacroFactor starts from an estimate and then adjusts it from what you log and how your weight moves ([MacroFactor](https://help.macrofactorapp.com/en/articles/222-how-does-macrofactor-make-adjustments-for-a-weight-gain-or-weight-loss-goal)). Our suggestion is to offer the same setup on first open with a clear "Just log" option, so nobody gets a target they didn't ask for.

## What we're building at the hackathon

- **Tonight:** the core. Apps drawn from blocks (12 of them, including simple Calories, Running, Cycle and Meditation apps), Home, Clair turning a typed sentence into a card, OK and Undo, phone and laptop in sync. It runs as a website on both; the phone opens it from its Home screen.
- **Tomorrow:** the workflow engine, with the training planner as its first rule and the appointment check as its second; Clair building three apps from three sentences, which we record; and Google Calendar connected so Clair plans around real events.

The demo script is `docs/demo-day.md`.
