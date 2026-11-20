# Demo day: Quilt at Lassonde DevDay

The pitch is on Fri Nov 20, 2026. This is the third version of this guide, written late on Nov 19 (`spec/adr/010-web-only-devday-planner-cut.md`, "Third cut"). The pitch is shaped like a Shark Tank pitch. The screen work is two parts: a short recording of Clair building three apps, then a live run of Clair planning next week's training from everything in the account. The demo clock is pinned at 5:45 pm on Fri 20 Nov.

The app runs as a website on the phone and the laptop. Nothing is built yet, so the live demo is a no-go until the base runs on both. What is still open is in section 6.

## 1. The pitch, beat by beat

Ninety seconds, eight beats. Beats 4 and 5 are the screen; the rest is you talking, with slides behind.

| # | Time | Beat | What is said or shown |
| --- | --- | --- | --- |
| 1 | 0:00-0:10 | Hook | "Hi, we're [name] and [name], and this is Quilt. Hands up if you pay for more than three apps to run your money, your workouts and your to-dos. Keep it up if none of them talk to each other." |
| 2 | 0:10-0:20 | The problem, as a story | "That's Sam, a student here. A budget app, a gym app, a calorie app, a calendar. Four subscriptions, and each one knows a quarter of Sam's week. We asked [N] U students: they pay for [X] apps, about $[Y] a month." Real numbers only. |
| 3 | 0:20-0:28 | What it is | "Quilt is one app where you describe the app you need and Clair, our AI, builds it. Every app it builds is connected to the others." |
| 4 | 0:28-0:40 | **Recorded:** three builds | Play the clip. "We recorded this today, in the real app. Three sentences: a calorie tracker, a running tracker for my 10K, a private cycle tracker. Three working apps." |
| 5 | 0:40-1:10 | **Live:** the planner | Steps 5a to 5f below. |
| 6 | 1:10-1:20 | Why us | "Notion makes you build it yourself. AI app builders make apps that sit alone. Quilt's apps know about each other, and nothing changes without your OK." |
| 7 | 1:20-1:27 | Traction and price | "[N] students joined our waitlist in [D] days. Free to start, $6 a month, $4 for students." |
| 8 | 1:27-1:30 | Close | "Quilt: your life, stitched together." |

Shark Tank pitches usually name an ask. DevDay isn't raising money, so the ask is beat 7's waitlist number, or drop it.

### Beat 4, the recorded builds (12 s)

What it shows: Quilt is an app builder. A sentence becomes a working app, and the app arrives connected.

| Sentence typed to Clair | What Clair builds | What to point at |
| --- | --- | --- |
| "Track what I eat, calories and protein" | Calories: meals, saved foods | The new patch on Home |
| "I'm running a 10K on Sat 12 Dec. Track my runs" | Running: runs and races | The race is already on Calendar |
| "Track my cycle and keep it private" | Cycle: a daily log | "Private: I won't read it unless you turn that on" |

How to record it:

- Record on the second demo workspace, the one in the 8-app "before" state, on the day, after the builds pass their test five times each.
- One take per sentence: type it, the preview draws in, tap **Make it**, the patch sews onto Home. End on the laptop showing three new patches.
- Cut it to about 12 seconds. Speeding it up is fine if the clip says "sped up". Don't cut anything that changes what the app did.
- Put "Recorded today in the real app" on the clip, and say it.
- If the builds aren't working by early afternoon, don't show a clip. Show the Flows prototype (https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne) and call it a prototype.

### Beat 5, Clair plans the week, live (30 s, must work)

What it shows: the apps work together. One sentence makes Clair read nine apps and Sam's Google Calendar and come back with one plan, with a reason for every line.

The setup is real data in the demo account, which has 12 apps. Sam lifts four times a week: Pull day Monday and Friday at 6:00 pm, Leg day Tuesday at 7:00 am, Push day Wednesday at 6:00 pm. Sam is training for a 10K on Sat 12 Dec. Next week is Thanksgiving week, and Sam's Google Calendar has a dentist appointment on Tuesday morning, the drive home on Wednesday evening, Thanksgiving at home until Saturday, and the trip back on Sunday. Google Calendar is connected before the pitch.

| Step | ~Time | Action | What the room sees |
| --- | --- | --- | --- |
| 5a | 0:40 | Phone on Home. Laptop on Calendar, next week | 12 apps. Say: "This is my real account. Next week is Thanksgiving, I've got a dentist appointment and a 10K in three weeks." |
| 5b | 0:44 | Tap **Clair**, type "Plan my training for next week" | "Reading your week…", then "Read 9 apps: Calendar, Classes, To-dos, Workout, Running, Calories, Cycle, Meditation and Groceries." |
| 5c | 0:50 | Clair's card | "Next week's training. 4 lifts (1 kept, 3 moved), 2 runs, 1 recovery to-do, 1 grocery item." Read out two reasons: "Leg day moves to 5 pm because of the dentist. The long run is five and a half miles because my last one was five." |
| 5d | 0:58 | Tap **Add to 5 apps** | Threads run to the apps. Groceries goes 12 → 13 on Home. On the laptop, sessions jump to new times and two runs appear. Say: "Five apps, one tap. Nothing changed until I said OK." |
| 5e | 1:04 | Clair offers "Do this every Sunday at 7 pm?" Tap **Turn on** | Workout's Workflows tab: "Every Sunday at 7:00 pm, plan next week's training", on. Say: "And now it does this every week." |
| 5f | 1:10 | | Move to beat 6. Undo is for questions. |

The plan Clair must produce, every time:

| When | What | Change | Reason shown |
| --- | --- | --- | --- |
| Mon 23 Nov 6:00 pm | Pull day | kept | Free after CS 3500 (Classes) |
| Tue 24 Nov 7:00 am → 5:00 pm | Leg day | moved | Dentist at 7:30 am (Google Calendar). Also: shortest session; energy 2 logged on day 1 of your last 3 cycles (Cycle) |
| Wed 25 Nov 6:00 pm → 7:00 am | Push day | moved | Drive home at 5:00 pm (Google Calendar) |
| Thu 26 Nov 8:00 am | Easy run, 3 mi | new | Away from the gym; a run goes anywhere |
| Sat 28 Nov 9:00 am | Long run, 5.5 mi | new | 10K on Sat 12 Dec; last long run 5 mi (Running) |
| Fri 27 Nov → Sun 29 Nov 4:00 pm | Pull day | moved | Back on campus Sun 12:00 pm (Google Calendar) |
| Tue 24 Nov 9:30 pm | To-do: 10 min body scan | new | After Leg day; 3 sessions logged this week (Meditation) |
| Weekly shop | Oats | new | Oatmeal 3 of 5 mornings; not on your list (Calories) |

The card also says: "Mon to Thu you logged 1,650 to 1,970 calories a day (target 2,200)." It states the numbers and stops there.

**The planner is built in four steps, and you demo the highest one that works every time.** Run the sentence ten times against a fresh reset; all ten must match.

| Step | The card | Button |
| --- | --- | --- |
| 1 | The four lifts, kept or moved | Add to 2 apps |
| 2 | Plus the two runs | Add to 3 apps |
| 3 | Plus the Cycle line on Leg day and the calorie sentence | Add to 3 apps |
| 4 | Plus the body scan to-do and Oats | Add to 5 apps |

If you demo a lower step, change the words in 5b to 5d to match what is on screen. Credits go from 32 to 31.

If Clair hasn't proposed anything after 12 s, "Use sample" appears and replays a recorded run, marked "sample". Say that it's a recording.

### For questions, if built

- **Appointments.** Type "Am I due for any appointments?" → "Haircut is due. You go about every 5 weeks. The last was Sat 17 Oct." → Haircut, Sat 21 Nov 2:00 pm, reminder the day before → **Add to Calendar** → rule "Every Sunday at 7:00 pm, check for appointments that are due".
- **A rule in words.** Type "When I add an exam, add a study to-do two days before" → Clair sets up the rule → add an exam → the to-do appears.
- **The grocery receipt.** Photo → "Add to 3 apps" → Budget $412 → $376 → Undo.

### What to say if asked

- **"Is the cycle data safe?"** A new Cycle app is private: Clair can't read it until you switch that on. In this demo account it's on. Nothing is encrypted yet; that comes before real users.
- **"Is it giving health advice?"** No. It moves sessions around your calendar and repeats your own numbers back. It doesn't tell you what to eat or how hard to train.
- **"Did it really build those apps?"** Yes, that clip is the real app, recorded today. The account in the live demo has the same three apps with weeks of data in them.
- **"What's next?"** Meals from a photo, health data from the phone, reminders as phone notifications, a native app.

## 2. The devices

- **Phone:** the website in Chrome, opened from its Home screen icon so it runs full screen, signed in to the demo account. There is no APK.
- **Laptop:** the same website, joined to the demo account with the 6-digit join code (email and password as the fallback), open on Calendar, next week. It also plays the clip.
- **Google account:** one demo Google account, added as a test user on the Google Cloud project, whose main calendar holds exactly the four events below and nothing else between Fri 13 Nov and Tue 19 Jan.

| Event | When |
| --- | --- |
| Dentist | Tue 24 Nov, 7:30 to 8:30 am |
| Drive home for Thanksgiving | Wed 25 Nov, 5:00 to 9:00 pm |
| Thanksgiving at home | Thu 26 to Sat 28 Nov, all day |
| Back to campus | Sun 29 Nov, 12:00 to 1:00 pm |

## 3. What's in the demo account

Twelve apps. The numbers on Home at 5:45 pm:

| App | Home shows | App | Home shows |
| --- | --- | --- | --- |
| Budget | $412 left | Workout | 3 this week |
| Groceries | 12 to buy | Subscriptions | $38.46 a month |
| Calendar | 3 today | Calories | 1,140 today |
| To-dos | 2 today | Running | 7 mi this week |
| Classes | 2 due this week | Meditation | 25 min this week |
| Notes | 3 this week | Cycle | last period started Tue 27 Oct |

Calories, Running, Cycle and Meditation are simple logs. You can add a record by hand or by typing to Clair ("had a chicken burrito, about 700 calories"; "ran 3 miles in 29 minutes"). There are no photo meals, calorie estimates, pace, charts, timer or cycle predictions in the app yet.

## 4. Before the pitch

- Tonight: create the Google Cloud project, turn on the Calendar API, set the consent screen to testing with the demo Google account as a test user, and make the four events.
- Tomorrow, by early afternoon: record the three builds (beat 4) and cut the clip.
- Connect Google Calendar in the demo account (Calendar → Add Google Calendar) well before the pitch. Don't do the Google sign-in on stage.
- Reset the demo workspace (`POST /dev/reset`), then check Home shows 12 apps with the numbers above and Calendar shows the four "from Google" events.
- Run the planner sentence ten times on fresh resets and decide which step you're demoing.
- Run "Use sample" once and dismiss it.
- Five minutes before, warm the server: open Home and run one Clair turn on each device, then reset again.
- Check live sync: confirm something on the phone and watch the laptop.
- Phone on the hotspot, not the venue Wi-Fi, unless the venue Wi-Fi has been tested.
- Laptop: the clip queued, then Calendar on next week. Phone on Home.

## 5. Backup plan

In order of preference:

1. **"Use sample" in the real app.** It appears after 12 s and replays the recorded planner run with the same screens.
2. **A lower planner step.** If the full plan isn't steady, demo the step that is.
3. **Google is down or sign-in fails.** Reset with the seeded copies of the four events (`DEMO_GCAL_FIXTURE=1`). The screens look the same. Say the calendar events are seeded if asked.
4. **No clip.** Show the Flows prototype for beat 4 and say it is a prototype.
5. **The rule doesn't work.** Skip step 5e.
6. **The recorded video** of beat 5, made after the feature freeze. It doesn't exist yet.
7. **The base only.** Type "spent $12 on lunch" → card → Add → $412 → $400 on both devices → Undo.
8. **Prototypes.** `design/prototypes/quilt-home.html` and the canvas boards (https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P) still show the grocery receipt flow and 8 apps. Use them only to show the look.

There are no design boards for the planner card, the "from Google" rows, the offer card, the Workflows tab or the four new apps. They are built in code from the existing styles.

## 6. Still open

### Must do before the pitch

1. **Build the base tonight** and run it on the phone's browser and the laptop: sign-in, 12 apps, Home, a typed sentence to a card, confirm, undo, live sync (`spec/backend.md` §13, T1 to T4). Go/no-go at 10:00 on Nov 20.
2. **Reach the safe point first tomorrow:** planner step 1 and the Sunday rule, on seeded Google events. Then the builds and the clip, then planner steps 2 to 4, then Google sign-in, then the rest (`spec/backend.md` §13, D1 to D10).
3. **Record the fallback run and the backup video** after the feature freeze, two hours before the pitch.
4. **Make the deck** for the slide beats, with real survey and waitlist numbers.
5. **Decide what to tell the organisers.** The DevDay application described the receipt as the feature built on the day.

### Things to be honest about

- This is more than two people are likely to finish in a day. The order above is built so that stopping anywhere still leaves a working demo.
- The clip is a recording, and the account in the live demo is not the one in the clip.
- The rule's Sunday run is not scheduled unless that job gets built; Run now is what works.
- Quilt reads Google Calendar and doesn't write to it, so the plan doesn't appear in Google.
- The connection works only for Google accounts we list as test users.
- Nothing is encrypted yet, including cycle data and the stored Google token.
- The planner works on next week in this account. It hasn't been tested on other people's data.
