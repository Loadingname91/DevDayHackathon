// Hand-written from spec/backend.md §10, §7, spec/ui-tech-plan.md §3 and §4 and
// spec/clair-agent.md §2, until api/openapi.json exists (spec/split.md §2).
// When the generated file replaces this one, every compile error is a contract
// difference: fix the code or log it in spec/split.md §7. Never cast it away.
//
// Fields marked "assumed" are not in the contract yet; each has a line in the log.

export type Dye = 'butter' | 'sage' | 'sea glass' | 'apricot' | 'chambray' | 'lavender' | 'pear' | 'blush' | 'linen';
export type CollectionRef = string; // "groceries/items" or "*dated"
export type Scalar = string | number | boolean;

export type Option = { id: string; label: string; hint?: string; limit?: number };
export type Field = {
  key: string;
  label: string;
  type: 'text' | 'number' | 'money' | 'date' | 'datetime' | 'bool' | 'select' | 'relation' | 'formula' | 'repeat';
  options?: Option[];
  required?: boolean;
  target?: CollectionRef; // relation
  unit?: string; // assumed: display hint for number fields ("mi", "min")
  unitFirst?: boolean; // assumed: "energy 2" rather than "2 energy"
};
export type Collection = {
  key: string;
  name: string;
  fields: Field[];
  titleField: string;
  dateField?: string;
  amountField?: string;
  calendar?: boolean;
  label?: string;
};

// `within`: "today", "week", "past", "future", "7d" (next 7 days), "-7d" (last 7 days), counted from server_now. `empty`: no value.
export type Filter = { field: string; op: 'eq' | 'ne' | 'lt' | 'gt' | 'within' | 'empty'; value: Scalar };
export type Query = { agg: string; from: CollectionRef; field?: string; where?: Filter[]; window?: 'today' | 'week' | 'month' | 'all' };
export type Term = number | Query | { setting: string };
export type Value = Term | { minus: [Term, Term] };
export type Format = 'money' | 'count' | 'number' | 'duration' | 'text';

export type ViewBase = {
  id: string;
  source: CollectionRef;
  fields?: string[];
  where?: Filter[];
  sort?: { field: string; dir: 'asc' | 'desc' };
  group?: string;
  swipe?: { right?: 'complete'; left?: 'delete' };
  switch?: string;
  addAt?: 'start' | 'end';
  label?: string; // section label above the card
  limit?: number; // show the first N, then "Show all N"
  due?: string; // a date field shown as a relative tag ("in 2 days", "Overdue · 2 days")
};
export type TextBlock = { kind: 'text'; id: string; text: string };
export type MetricBlock = { kind: 'metric'; id: string; label: string; value: Value; format: Format; compare?: Value };
export type ProgressBlock = { kind: 'progress'; id: string; label: string; value: Value; target: Value; format: Format };
export type ListBlock = { kind: 'list'; add?: boolean /* Nov 20: a trailing "Add a <row>" row; on by default when `source` is this app's collection, `false` opts out */ } & ViewBase;
export type TableBlock = { kind: 'table' } & ViewBase;
export type CalendarBlock = { kind: 'calendar'; window?: 'today' | 'week' } & ViewBase; // window: assumed
export type FormBlock = { kind: 'form'; id: string; collection: CollectionRef; fields: string[]; submit: string };
export type ChartBlock = { kind: 'chart'; id: string; type: 'bar' | 'line'; from: CollectionRef; x: string; y: Query; window: 'week' | 'month' };
export type WorkflowsBlock = { kind: 'workflows'; id: string };

// ---- instruments (Nov 20): blocks that do the app's job, so an app is more than a list and a form.
// Numbers they show come from the server in `values[block.id]`; the client lays out and formats.
/** A hero figure with its bar: "$412 left of $1,200", "11 days to go". */
export type GaugeBlock = { kind: 'gauge'; id: string; label: string; value: Value; target: Value; format: Format; link?: { app: string; text: string } };
/** One bar per option of a select field: Budget's "Where it went". */
export type BarsBlock = { kind: 'bars'; id: string; label: string; from: CollectionRef; by: string; value: Query };
/** A goal ring: Calories today against the target. */
export type RingBlock = { kind: 'ring'; id: string; label: string; value: Value; target: Value; format: Format };
/** Days to a dated row: the race, the next exam, the next renewal. */
export type CountdownBlock = { kind: 'countdown'; id: string; source: CollectionRef };
/** Mon to Sun, one cell per day with that day's figure. History, not a streak. */
export type StripBlock = { kind: 'strip'; id: string; label: string; value: Query };
/** Tap a saved row to log it again: Calories' foods into meals. */
export type PicksBlock = { kind: 'picks'; id: string; label: string; from: CollectionRef; log: CollectionRef; fields: string[] };
/** Rows to tick, in sections. Tap the circle or swipe right to complete, swipe left to delete, tap the row to edit. */
export type ChecklistBlock = {
  kind: 'checklist'; id: string; source: CollectionRef; fields?: string[]; switch?: string; due?: string;
  /** Sections, in order. Label tokens: {today} "Fri 20 Nov", {n} rows in it, {option} the picked switch option. */
  groups: { label: string; where: Filter[]; done?: boolean; collapsed?: boolean }[];
  add?: { placeholder: string; set?: Record<string, Scalar>; pinned?: boolean };
  swipe?: { right?: 'complete'; left?: 'delete' };
};
/** Dates from every app as a day timeline, a week (day strip and agenda) or a month grid. */
export type DaysBlock = { kind: 'days'; id: string; source: CollectionRef; views: ('day' | 'week' | 'month')[]; view: 'day' | 'week' | 'month'; apps?: string[] };
/** Next session and the guided log behind it: Workout's "Start pull day" → Log a set. */
export type NextBlock = { kind: 'next'; id: string; source: CollectionRef; log: CollectionRef; fields: string[] };
/** A timer that logs a row when it ends. countdown: Meditation. stopwatch: a run (asks `after` fields at the end). */
export type TimerBlock = {
  kind: 'timer'; id: string; label: string; mode: 'countdown' | 'stopwatch'; log: CollectionRef; minutesField: string;
  kindField?: string; presets?: number[]; moodFields?: [string, string]; after?: string[]; set?: Record<string, Scalar>;
};
/** A month of days to log into: Cycle. Tap a day to log or change it. */
export type MonthBlock = { kind: 'month'; id: string; source: CollectionRef; dateField: string; mark: string; fields: string[] };
export type LeafBlock = TextBlock | MetricBlock | ProgressBlock | ListBlock | TableBlock | CalendarBlock | FormBlock | ChartBlock | WorkflowsBlock
  | GaugeBlock | BarsBlock | RingBlock | CountdownBlock | StripBlock | PicksBlock | ChecklistBlock | DaysBlock | NextBlock | TimerBlock | MonthBlock;
export type PageBlock = { kind: 'page'; id: string; title: string; children: LeafBlock[] };

export type Trigger =
  | { kind: 'schedule'; rule: string; at: string }
  | { kind: 'row_added'; collection: CollectionRef; where?: Filter[] }
  | { kind: 'field_changed'; collection: CollectionRef; field: string; to: Scalar; where?: Filter[] };
export type Action =
  | { kind: 'ask_clair'; text: string }
  | { kind: 'write_row'; collection: CollectionRef; map: Record<string, unknown> };
export type Workflow = { id: string; sentence: string; on: boolean; trigger: Trigger; action: Action; runs?: string; next_run?: string };

export type Stitch = { from: CollectionRef; to: CollectionRef; map: { to: string; from?: string; const?: Scalar }[]; where?: Filter[] };
export type AppSpec = {
  v: 1;
  id: string;
  key: string;
  name: string;
  icon: string;
  dye: Dye;
  print?: 'solid' | 'gingham' | 'stripe' | 'dot';
  private?: boolean;
  settings?: Record<string, Scalar>;
  collections: Collection[];
  tabs: PageBlock[];
  face: { value: Value; format: Format; label: string; status?: boolean };
  stitches?: Stitch[];
  workflows?: Workflow[];
};

// A record as the API sends it: a block (backend.md §2.2).
export type Rec = { id: string; position: string; version: number; properties: Record<string, unknown>; example?: boolean /* assumed: build preview rows */ };
// A row of the virtual *dated source (backend.md §3, §8a).
export type DatedRow = {
  at: string; // date or datetime
  title: string;
  sub: string;
  app: string;
  record_id: string;
  occurrence?: string;
  ends?: string;
  all_day?: boolean;
  source?: string; // "google"
  changed?: boolean; // assumed: "just changed" on a row
};

export type Face = { text: string; label: string; value?: number };
// assumed: the server sends each metric and progress block's computed value, since all formulas run in Python.
export type BlockValue = {
  text?: string; sub?: string; target?: string; pct?: number; over?: string; over_pct?: number; title?: string; unit?: string; note?: string;
  /** bars */ rows?: { label: string; text: string; pct?: number; over_pct?: number; note?: string }[];
  /** strip */ days?: { dow: string; text?: string; on?: boolean; today?: boolean }[];
  /** next */ eyebrow?: string; meta?: string; action?: string; record_id?: string; occurrence?: string; rest?: number;
  steps?: { id: string; name: string; plan: string; sets: number; reps: number; weight: number; unit: string; best?: { reps: number; weight: number; text: string } }[];
  link?: string;
};

export type Patch = { id: string; key: string; name: string; icon: string; dye: Dye; print?: string; face: Face; changed: boolean; lastOpened: string; pinned: boolean; isNew?: boolean };
export type Connection = { provider: 'google'; account_email: string; last_synced_at: string; needs_reconnect: boolean };

export type RowOp =
  | { op: 'insert'; ref: CollectionRef; values: Record<string, unknown>; reason?: string; reason_source?: string; also?: string; also_source?: string }
  | { op: 'update'; rowId: string; values: Record<string, unknown>; reason?: string; also?: string }
  | { op: 'delete'; rowId: string; reason?: string }
  | { op: 'move_occurrence'; record_id: string; occurrence: string; fields: { key: string; value: string }[]; reason?: string; also?: string }
  | { op: 'keep'; record_id: string; occurrence: string; reason?: string }; // assumed: clair-agent.md §12.9 writes {keep: true}

export type ChangeSetStatus = 'basted' | 'stitched' | 'undone' | 'dismissed';
export type CardLine = { apps: string[]; what: string; val: string; sub?: string };
// assumed: Review items rows as the server words them (clair-agent.md §12.9 shows the text, not a shape).
export type ReviewRow = { title: string; when: string; change: 'kept' | 'moved' | 'new' | 'changed' | 'removed'; reason?: string; source?: string; also?: string; also_source?: string; app: string };
export type ChangeSet = {
  id: string;
  status: ChangeSetStatus;
  source: { kind: string; label: string; at: string };
  mode?: 'live' | 'fixture';
  title: string;
  summary?: string;
  ops: RowOp[];
  lines: CardLine[];
  expanded: RowOp[];
  targets: string[];
  deltas: { app: string; before: string; after: string }[];
  actions: { primary: string; secondary?: string };
  review?: ReviewRow[];
  /** assumed: what the card proposes. "app" carries `preview` (propose_app), "rule" carries `rule` (propose_workflow). */
  kind?: 'records' | 'app' | 'rule';
  preview?: AppResponse;
  rule?: Omit<Workflow, 'id' | 'on'> & { app: string };
  flagged?: boolean;
  version?: number;
};
export type Card =
  | { kind: 'change_set'; change_set: ChangeSet }
  | { kind: 'checkin'; id: string; title: string; items: { text: string; app: string }[]; change_set?: ChangeSet }
  | { kind: 'keep' };

export type CommandResult = { change_set_id: string; server_seq: number; blocks: Rec[]; faces: Record<string, Face>; warnings: unknown[] };

export type Me = {
  user: { id: string; display_name: string; email?: string };
  is_anonymous: boolean;
  workspace: { id: string; tz: string; epoch: number; settings: { pins: string[]; credits_monthly: number; notes_enabled: boolean } };
  credits: { granted: number; spent: number; left: number; resets?: string };
  server_now: string;
};
export type Home = { greeting: string; status: string; needsOk: Card[]; nextUp: DatedRow[]; noticed?: unknown; apps: Patch[]; seq: number; server_now?: string };
export type AppResponse = {
  spec: AppSpec;
  data: Record<CollectionRef, (Rec | DatedRow)[]>;
  faces: Record<string, Face>;
  values?: Record<string, BlockValue>;
  /** assumed: the app's status sentence, written by the server; **bold** marks the figures */
  status?: string;
  seq: number;
  server_now?: string;
};
export type SyncResponse = { seq: number; epoch: number; server_now: string; blocks: unknown[]; change_sets: ChangeSet[]; faces: Record<string, Face>; touched_apps: string[] };

// ---- Clair (clair-agent.md §2)
/** What Sam picked on one question. `other`: typed under Other, or into the field of the picked option that takes a value. */
export type Choice = { choices: string[]; other?: string };
/** The answer to a `question` event (clair-agent.md §2, §11). A card of questions sends `answers`; one question (the fridge) sends `choices`. */
export type Answer = {
  question_id: string;
  answers?: Record<string, Choice>;
  /** "Skip, use your best guess": Clair decides, sets no number for Sam, and the plan says what it picked */
  skip?: boolean;
  choices?: string[];
  other?: string;
};
export type TurnRequest =
  | { thread_id?: string; run_id?: string; text?: string; transcript?: string; voice?: boolean; images?: string[]; files?: string[]; context?: { app: string; collection?: string; record_id?: string } }
  | { fixture: 'planner' | 'receipt'; run_id?: string }
  | { answer: Answer; thread_id?: string; run_id?: string };
export type Offer = { kind: 'workflow'; app: string; sentence: string; trigger: Trigger; action: Action; prompt?: string };
/** An option on a question card. `input`: picking it shows a field ("Set a number"); single-select questions only. */
export type AskOption = { label: string; description?: string; input?: { placeholder: string; numeric?: boolean } };
/** One question on a card: 2 to 4 options, and an Other row unless `other` is false. */
export type AskQuestion = { id: string; header: string; text: string; options: AskOption[]; multi: boolean; other?: boolean };
export type Question =
  /** a card of 1 to 3 questions, asked before a build (clair-agent.md §7 rule 7); `plan_after`: a `plan` follows the answer */
  | { id: string; questions: AskQuestion[]; plan_after?: boolean; expires_at?: string }
  /** one question with up to 8 options (the fridge) */
  | { id: string; text: string; options: { id: string; label: string; hint?: string }[]; multi: boolean; expires_at?: string };
/** What Clair will build, in plain words, before the Build preview (clair-agent.md §2, §11). */
export type Plan = {
  title: string;
  new_app?: { key: string; name: string; icon: string; dye: Dye };
  /** `app`: the app the line is about (its dye dot), the new app or an existing one */
  lines: { app?: string; text: string }[];
  private?: boolean;
};
export type ClairEvent =
  | { event: 'status'; data: { text: string } }
  | { event: 'understood'; data: { kind: string; summary: string; items?: string[] } }
  | { event: 'question'; data: Question }
  | { event: 'plan'; data: Plan }
  | { event: 'note'; data: { text: string } }
  | { event: 'proposal'; data: { change_set: ChangeSet } }
  | { event: 'offer'; data: Offer }
  | { event: 'text_delta'; data: { text: string } }
  | { event: 'done'; data: { status: 'complete' | 'awaiting_input' | 'error'; sources: string[]; spoken?: string; message?: string } };
