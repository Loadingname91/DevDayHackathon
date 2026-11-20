# Who builds what: frontend on mock data, backend behind the contract

Decided late Nov 19 ([ADR-011](adr/011-frontend-on-mocks-ownership-split.md)). Read this before `spec/backend.md` §13: it says which half of that table is yours and how the two halves meet.

## 1. Owners

| Side | Owner | §13 column | Code | Specs they own |
| --- | --- | --- | --- | --- |
| **Frontend** | Hitesh (git user `hiteshbalegar`) | B: client | `web/`, the Vercel project for the site | `spec/ui-tech-plan.md`, `design/` |
| **Backend** | Hitesh's teammate | A: API and Clair | `api/`, the Supabase project (schema, RLS, seed), the Google Cloud project, the Railway service and its env vars | `spec/backend.md`, `spec/clair-agent.md`, `spec/workflows.md` |

**Which side is this session?** If `git config user.name` is `hiteshbalegar`, you are on the frontend. Otherwise you are on the backend. If the person you are working with says otherwise, they win.

**Rules for both sides.**

- Write code only in your own folder. Read the other side's code freely; don't edit it. If it looks wrong, say so to your person and add a line to the log in section 7.
- The frontend does not wait for the backend. It builds every screen against mock data (section 3) and switches to the live API one route at a time (section 5).
- The backend does not build UI, and does not shape a response to suit a mock. The contract (section 2) is what both sides build to.
- Shared files, changed by either side with a log line: the contract sections named in section 2, `CLAUDE.md`, and the canonical demo facts.
- Commit or push only when your person asks.

## 2. The contract (the seam)

The contract is these sections, and nothing else:

| What | Where |
| --- | --- |
| Endpoints, requests, responses, status codes | `spec/backend.md` §10 |
| Command result on every write: `{change_set_id, server_seq, blocks[], faces{}, warnings[]}` | `spec/backend.md` §10, §5 |
| `AppSpec`, blocks, `Row`, `Patch`, `Dated` | `spec/ui-tech-plan.md` §3 |
| `ChangeSet` (the `Proposal` shape) and `Card` | `spec/ui-tech-plan.md` §4, `spec/backend.md` §10 |
| Clair's turn request and SSE events (`status`, `understood`, `question`, `note`, `proposal`, `offer`, `text_delta`, `done`) | `spec/clair-agent.md` §2 |
| `/sync` | `spec/backend.md` §7 |
| Rule shape (`workflows[]`) | `spec/workflows.md`, "Engine v1" |
| Every value on screen | `spec/backend.md` §2.2 and §2.3 (the seed) |

Where `spec/ui-tech-plan.md` §3 and `spec/backend.md` disagree, `backend.md` wins. §3 lists the known differences in its first paragraph (select options as `{id, label, hint?}`, the slug is `key`, `_via`, `position`, the `relation`, `formula` and `repeat` field types).

**Types.** The end state is unchanged: Pydantic models → OpenAPI → `openapi-typescript` → `web/src/api/types.ts`. Until the API publishes OpenAPI, the frontend writes `web/src/api/types.ts` by hand from the sections above. When the generated file replaces it, every compile error is a contract difference: fix the code or log the difference, never cast it away.

**Backend's first deliverable is the models, not the handlers.** Write the Pydantic models for the base routes (`/me`, `/home`, `/apps`, `/apps/{id}`, the command result, `ChangeSet`, `/sync`, the SSE event payloads) and commit the OpenAPI output as `api/openapi.json` before the handlers work. That one file unblocks the frontend's generated types.

**Changing the contract.** Either side may need to. Do all three in one commit: edit the spec section, add a line to the log in section 7, and tell your person so they can tell the other. A shape that changed in code but not in the spec is a bug.

## 3. Mock data (frontend)

The frontend ships a mock transport inside the web app. One device, state in memory, reset on reload.

```
web/src/api/client.ts        one request function and one SSE reader; every screen calls these
web/src/mocks/handler.ts     answers the same paths as spec/backend.md §10 from fixtures
web/src/mocks/fixtures/      one JSON file per response or scripted run
web/src/mocks/scenarios.ts   named scenarios: which fixtures answer, in what order, with what delays
```

- `VITE_API=mock` sends every route to the mock handler. `VITE_API=live` sends every route to `VITE_API_BASE`, except the routes listed in `VITE_MOCK_ROUTES` (comma-separated path prefixes, such as `/clair,/connect`). That list is how the switch to live happens one route at a time.
- In mock mode there is no Supabase sign-in and no Realtime; `/me` is a fixture.
- **Fixtures are recorded server answers, not a second server.** A fixture holds the finished response: faces as the strings the server would send, `lines`, `targets`, `deltas`, `actions`. The mock never evaluates a formula, expands a stitch, computes a date or works out "today". Confirm and Undo swap between a "before" and an "after" fixture. If a screen needs a value no fixture holds, add a fixture; don't compute it in the client.
- **Every fixture value comes from the seed** (`spec/backend.md` §2.2 and §2.3) at `DEMO_NOW`, Fri 20 Nov 2026 5:45 pm America/Denver. If the live API and a fixture disagree, the seed decides which is wrong.
- Clair runs are scripted SSE: a list of events with delays, replayed by the mock SSE reader (`status` at once, then `understood`, `proposal`, `done`).
- **Any screen showing mock data carries a visible "mock data" mark.** The demo deployment runs `VITE_API=live` with `VITE_MOCK_ROUTES` empty. Mock data is never shown on stage as the product. The stage fallback is the server's "Use sample" (`fixture: "planner"`), which is a different thing: a recorded run replayed through the real pipeline and marked "sample".
- Mocks can't prove two-device sync, the join code, undo's exact restore, or run timing. Those count only on the live API.

**Scenarios to mock, in build order.** The backend may read these fixtures as example responses and should say so in the log if its real response differs.

| Scenario | Covers | Source of the values |
| --- | --- | --- |
| `seed` | `/me`, `/home`, `/apps`, `/apps/{id}` for all 12 apps; next week in Calendar with the four "from Google" events | `backend.md` §2.2, §2.3 |
| `before` | The 8-app state for the recorded clip | `backend.md` §2.3 |
| `lunch` | "spent $12 on lunch" → one Budget card → Add → $412 → $400 → Undo | `backend.md` §13 base cut line |
| `planner-r1`, `planner-r4` | The understanding line, the card, Review items with reasons and "also" lines, confirm, Groceries 12 → 13 at rung 4 | `clair-agent.md` §12.9, `backend.md` §2.3 |
| `offer` | "Do this every Sunday at 7 pm?" → Turn on → Workout's Workflows tab; Run now; switch off | `workflows.md`, `backend.md` §10 |
| `build-calories`, `build-running`, `build-cycle` | The three sentence builds: chalk, basted preview, Make it, the new patch on Home | `clair-agent.md` §12.11 |
| `google` | Not connected → connected row → Refresh; denied | `backend.md` §8a |
| `appointments` | "Haircut is due" card → Add to Calendar → the second rule | `clair-agent.md` §12.10 |
| `exam-rule` | The rule card; an exam with its "by rule ›" to-do | `workflows.md` steps 3 and 4 |
| `receipt` | Only if D10 is reached | `backend.md` §2.2, `clair-agent.md` §12.1 |
| `errors` | Confirm fails (frayed edge), `409` on a second confirm, a status past 6 s, no card after 12 s → "Use sample", stream closes before `done` | `backend.md` §10, §11; `clair-agent.md` §2, §15 |

## 4. What each side owes the other

**Backend → frontend**

| When | What |
| --- | --- |
| First | `api/openapi.json` for the base routes (section 2) |
| T1 | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE` (the Railway URL); the demo account's email and password; whether Clair's events arrive as SSE or need the polling fallback (`backend.md` §10, "Hosting") |
| Each step of §13 | A line in the log saying which routes are now live on the deployment |
| Any time | A log line when a real response differs from a fixture |

**Frontend → backend**

| When | What |
| --- | --- |
| T1 | The site's URL on Vercel, which the API needs as `WEB_ORIGIN` (CORS, and the redirect back after Google sign-in). There is no `/api` rewrite: the site calls the Railway URL directly (ADR-012) |
| As built | The fixtures in `web/src/mocks/fixtures/`, as worked examples of each response |
| Any time | A log line when a screen needs a field the contract doesn't have |

The client sends a `run_id` (a UUID it makes) with every Clair turn, and `{fixture: "planner"}` for "Use sample" (`clair-agent.md` §2). Both are already in the contract.

## 5. Switching from mock to live

Do it in this order. After each switch, load the screen on the live route and compare it with the mock; a difference is a contract bug for the log.

| Switch | Needs from the backend (`backend.md` §13) | Remove from `VITE_MOCK_ROUTES` |
| --- | --- | --- |
| 1 | T2: `/health`, JWT check, `/apps`, `/apps/{id}`; demo sign-in | `/me`, `/apps` |
| 2 | T3: `/home`, `/sync`, change sets (confirm, undo, dismiss), Realtime | `/home`, `/sync`, `/change-sets`, `/join-codes` |
| 3 | T4: the Clair loop for one sentence | `/clair` for typed turns |
| 4 | D1, D2: planner rung 1, workflows endpoints, the `offer` event | `/apps/*/workflows` |
| 5 | D3 to D9, as each lands | `/connect`, then nothing left |

**The base cut line and the 10:00 go/no-go on Nov 20 are judged on the live API with `VITE_MOCK_ROUTES` covering nothing the cut line touches.** A screen that works only on mocks is not done. `check.py`, the two-device check and the safe point (`backend.md` §13) are live-only by definition.

## 6. Stories by side

`spec/prd-stories.md` holds the criteria. This table says who builds which half.

| Story | Frontend builds | Backend builds |
| --- | --- | --- |
| US-5 Home | Home, the bar, the cache | `/home`, faces, Next up |
| US-17 Twelve apps | `AppView`, the six blocks, the Add form | The four new specs, seed rows, `/apps/{id}` |
| US-8 Typed note (base: "spent $12 on lunch") | Clair sheet, status, understood, `ProposalCard` | Clair loop, `propose_changes`, the basted change set |
| US-3 Confirm | Confirm flow, `threadPull`, `roll`, "just changed" | Command service, confirm, `deltas`, final `faces` |
| US-7 Undo | Undo toast, the reversal | Undo as an exact inverse |
| US-4 Laptop | Laptop layout, Realtime catch-up, the join code screen | `events`, `/sync`, join codes |
| US-13 Planner | The planner card, Review items (read-only), "Use sample" | The brief, the planning check, `move_occurrence`, AB-11, `fixture: "planner"` |
| US-14 Sunday rule | `OfferCard`, the `Workflows` block and tab | `workflows[]`, the three endpoints, the `offer` event, Run now |
| US-6 Three builds (recorded) | The Build flow, the patch sewing onto Home, cutting the clip | `propose_app`, spec validation and retry, the "before" state, AB-1b |
| US-12 Google Calendar | `ConnectGoogle`, "from Google" rows, all-day events | OAuth, sync, the read-only guard |
| US-16 Appointment check | The card on Calendar (reuses the offer card) | `get_gaps`, the prompt section, AB-12 |
| US-15 Described rule | The rule card, "by rule ›", the run line | `row_added` / `field_changed` + `write_row`, guards, `propose_workflow` |
| US-1, US-2 Receipt (D10 only) | Photo chip, downscale, the receipt card | Upload, the receipt prompt, `fixture: "receipt"` |

Known gap: the criteria of US-3, US-4 and US-7 are still written around the receipt. For the base, read them with the lunch sentence: one app, "Add to Budget", $412 → $400.

## 7. Contract and hand-off log

Newest first. One line each: date and time, side, what changed or went live, the spec section edited.

| When | Side | What | Spec |
| --- | --- | --- | --- |
| Nov 19, late | Owner | API moves from Vercel functions to one always-on FastAPI server on Railway; the site stays on Vercel and calls it cross-origin | ADR-012, `backend.md` §1, §10, §13 |
| Nov 19, late | Frontend | Split decided; frontend builds on mocks first | ADR-011, this file |
