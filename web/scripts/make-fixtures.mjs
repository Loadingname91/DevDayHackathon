// Writes the mock fixtures in src/mocks/fixtures/ from the seed tables in
// spec/backend.md §2.2 and §2.3 at DEMO_NOW (Fri 20 Nov 2026, 5:45 pm America/Denver).
//
// Fixtures are recorded server answers (spec/split.md §3). This script only types the
// seed rows out as JSON; every face, total and computed value below is a literal copied
// from the spec, never worked out here. If a value is wrong, the seed decides.
//
// Run: npm run fixtures
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '../src/mocks/fixtures');
mkdirSync(OUT, { recursive: true });
// Files are buffered and written at the end, so the links pass (bottom of the file) can stamp `_links` on the records it names.
const OUTBOX = new Map();
const write = (name, data) => OUTBOX.set(name, data);

const SERVER_NOW = '2026-11-20T17:45:00-07:00';
// MDT until Sun 1 Nov 2026, MST after
const off = (date) => (date < '2026-11-01' ? '-06:00' : '-07:00');
const dt = (date, time) => `${date}T${time}:00${off(date)}`;
const cents = (n) => Math.round(n * 100);
let pos = 0;
const rec = (id, properties) => ({ id, position: 'a' + String(pos++).padStart(3, '0'), version: 1, properties });
let posB = 0; // records added after the first seed (Nov 20, links): 'b000', 'b001'… so the positions of the rows above never move
const recB = (id, properties) => ({ id, position: 'b' + String(posB++).padStart(3, '0'), version: 1, properties });
const page = (id, title, children) => ({ kind: 'page', id, title, children });
const f = (key, label, type, extra = {}) => ({ key, label, type, ...extra });
const opts = (...labels) => labels.map((l) => ({ id: l.toLowerCase().replace(/[^a-z0-9]+/g, '_'), label: l }));

// ------------------------------------------------------------------ app faces (literals from §2.3)
const APPS = [
  // key, name, icon, dye, face text, face label, last opened, pinned
  ['groceries', 'Groceries', 'basket', 'sage', '12', 'to buy', dt('2026-11-20', '17:41'), true],
  ['budget', 'Budget', 'wallet', 'sea glass', '$412', 'left', dt('2026-11-20', '17:30'), true],
  ['calories', 'Calories', 'flame', 'apricot', '1,140', 'today', dt('2026-11-20', '15:40'), false],
  ['calendar', 'Calendar', 'calendar', 'chambray', '3', 'today', dt('2026-11-20', '12:10'), true],
  ['todos', 'To-dos', 'check', 'butter', '2', 'today', dt('2026-11-20', '08:05'), true],
  ['meditation', 'Meditation', 'moon', 'lavender', '25', 'min this week', dt('2026-11-19', '22:45'), false],
  ['workout', 'Workout', 'dumbbell', 'blush', '3', 'this week', dt('2026-11-19', '18:50'), false],
  ['running', 'Running', 'shoe', 'sage', '7', 'mi this week', dt('2026-11-19', '17:15'), false],
  ['notes', 'Notes', 'note', 'linen', '3', 'this week', dt('2026-11-19', '10:30'), false],
  ['classes', 'Classes', 'book', 'chambray', '2', 'due this week', dt('2026-11-19', '09:00'), false],
  ['subscriptions', 'Subscriptions', 'repeat', 'lavender', '$38.46', 'a month', dt('2026-11-15', '12:00'), false],
  ['cycle', 'Cycle', 'drop', 'pear', 'Tue 27 Oct', 'last period started', dt('2026-11-15', '12:00'), false],
];
const NEW_FOUR = ['calories', 'running', 'cycle', 'meditation'];
const patch = ([key, name, icon, dye, text, label, lastOpened, pinned], over = {}) => ({
  id: key, key, name, icon, dye, face: { text, label, ...(over.face || {}) }, changed: !!over.changed, lastOpened, pinned,
});
const PIN_ORDER = ['groceries', 'budget', 'calendar', 'todos'];
const patches = (over = {}, keys = null) =>
  APPS.filter((a) => !keys || keys.includes(a[0])).map((a) => patch(a, over[a[0]]));
const facesOf = (over = {}) => Object.fromEntries(APPS.map((a) => [a[0], { text: a[4], label: a[5], ...(over[a[0]] || {}) }]));
const meta = (key) => { const a = APPS.find((x) => x[0] === key); return { v: 1, id: key, key, name: a[1], icon: a[2], dye: a[3] }; };

// ------------------------------------------------------------------ /me
const me = (creditsLeft) => ({
  user: { id: 'u_sam', display_name: 'Sam', email: 'sam@quilt.demo' },
  is_anonymous: false,
  workspace: { id: 'w_demo', tz: 'America/Denver', epoch: 1, settings: { pins: PIN_ORDER, credits_monthly: 50, notes_enabled: true } },
  credits: { granted: 50, spent: 50 - creditsLeft, left: creditsLeft, resets: '2026-12-01' },
  server_now: SERVER_NOW,
});
write('me', me(32));
write('me.after-clair', me(31));

// ------------------------------------------------------------------ /home
const NEXT_UP = [
  { at: dt('2026-11-20', '18:00'), title: 'Pull day', sub: 'Workout', app: 'workout', record_id: 's_pull', occurrence: '2026-11-20' },
  { at: dt('2026-11-20', '20:00'), title: 'Take out recycling', sub: 'To-dos', app: 'todos', record_id: 't_recycling', occurrence: '2026-11-20' },
  { at: dt('2026-11-20', '21:00'), title: 'Return library books', sub: 'To-dos', app: 'todos', record_id: 't_library' },
];
const home = (status, over = {}, seq = 4100, keys = null) => ({
  greeting: 'Evening, Sam.', status, needsOk: [], nextUp: NEXT_UP, apps: patches(over, keys), seq, server_now: SERVER_NOW,
});
const STATUS = '**$412** left this month. Pull day at **6 pm**.';
write('home', home(STATUS));
write('apps', patches());
const EIGHT = APPS.map((a) => a[0]).filter((k) => !NEW_FOUR.includes(k));
write('home.before', home(STATUS, {}, 4100, EIGHT));
write('apps.before', patches({}, EIGHT));

// ------------------------------------------------------------------ Budget
const CATS = [
  { id: 'c_groceries', label: 'Groceries', limit: 20000 }, { id: 'c_eating_out', label: 'Eating out', limit: 15000 },
  { id: 'c_rent', label: 'Rent' }, { id: 'c_fun', label: 'Fun' },
  { id: 'c_transport', label: 'Transport', limit: 10000 }, { id: 'c_subscriptions', label: 'Subscriptions', limit: 4000 },
];
const cat = (label) => CATS.find((c) => c.label === label).id;
const SPEND = [
  ['01', 'November rent', 'Rent', 380.0], ['01', 'Cafe Rio', 'Eating out', 11.48], ['02', 'Hulu', 'Subscriptions', 9.99, 'subscriptions'],
  ['02', 'Lime scooter', 'Transport', 5.6], ['03', 'Adobe CC, student', 'Subscriptions', 13.49, 'subscriptions'], ['03', 'Blue Copper', 'Eating out', 5.25],
  ['04', 'Chipotle', 'Eating out', 12.35], ['05', "Smith's", 'Groceries', 41.37, 'groceries'], ['06', 'Blue Copper', 'Eating out', 5.25],
  ['07', 'Costa Vida', 'Eating out', 13.2], ['07', 'Megaplex movie', 'Fun', 12.5], ['09', 'Corner Market', 'Groceries', 8.62, 'groceries'],
  ['09', 'iCloud 50 GB', 'Subscriptions', 2.99, 'subscriptions'], ['10', 'Corner Market', 'Groceries', 4.29, 'groceries'], ['10', 'Blue Copper', 'Eating out', 5.25],
  ['11', "Smith's", 'Groceries', 27.15, 'groceries'], ['12', 'Corner Market', 'Groceries', 4.29, 'groceries'], ['12', 'Sushi with Maya', 'Eating out', 22.4],
  ['13', 'Corner Market', 'Groceries', 7.78, 'groceries'], ['13', 'Thai Siam', 'Eating out', 28.0], ['14', "Smith's", 'Groceries', 45.01, 'groceries'],
  ['14', 'Cafe Rio', 'Eating out', 11.48], ['14', 'Lime scooter', 'Transport', 8.4], ['14', 'Thrift shop', 'Fun', 20.03],
  ['15', 'Corner Market', 'Groceries', 3.49, 'groceries'], ['15', 'Bagel Project', 'Eating out', 14.97], ['16', 'Cafe Rio', 'Eating out', 9.62],
  ['17', 'Blue Copper', 'Eating out', 5.25], ['17', 'Gas', 'Transport', 28.0], ['18', 'Taco Bell', 'Eating out', 6.87],
  ['19', 'Union food court', 'Eating out', 11.4], ['19', 'Union vending', 'Eating out', 2.23],
];
const spendRows = SPEND.map(([day, note, c, amount, via], i) =>
  rec('sp_' + String(i + 1).padStart(2, '0'), {
    note, category: cat(c), amount: cents(amount), at: dt('2026-11-' + day, '12:00'), ...(via ? { _via: { app: via } } : {}),
  }));
const LUNCH_ROW = rec('sp_lunch', { note: 'Lunch', category: 'c_eating_out', amount: 1200, at: dt('2026-11-20', '17:45') });
const budgetSpec = {
  ...meta('budget'),
  settings: { limit: 120000 },
  collections: [{
    key: 'spend', name: 'Spending', label: 'Spend', titleField: 'note', dateField: 'at', amountField: 'amount',
    fields: [f('note', 'Note', 'text', { required: true }), f('amount', 'Amount', 'money', { required: true }),
      f('category', 'Category', 'select', { options: CATS }), f('at', 'When', 'datetime', { required: true })],
  }],
  tabs: [
    page('t_overview', 'Overview', [
      { kind: 'metric', id: 'b_left', label: 'Left this month', value: { minus: [{ setting: 'limit' }, { agg: 'sum', from: 'budget/spend', field: 'amount', window: 'month' }] }, format: 'money' },
      { kind: 'progress', id: 'b_spent', label: 'Spent in November', value: { agg: 'sum', from: 'budget/spend', field: 'amount', window: 'month' }, target: { setting: 'limit' }, format: 'money' },
      { kind: 'progress', id: 'b_c_eating', label: 'Eating out', value: 0, target: 15000, format: 'money' },
      { kind: 'progress', id: 'b_c_groceries', label: 'Groceries', value: 0, target: 20000, format: 'money' },
      { kind: 'progress', id: 'b_c_transport', label: 'Transport', value: 0, target: 10000, format: 'money' },
      { kind: 'progress', id: 'b_c_subs', label: 'Subscriptions', value: 0, target: 4000, format: 'money' },
    ]),
    page('t_spending', 'Spending', [
      { kind: 'list', id: 'b_spend', source: 'budget/spend', fields: ['category', 'at'], sort: { field: 'at', dir: 'desc' }, addAt: 'start' },
    ]),
    page('t_categories', 'Categories', [
      { kind: 'metric', id: 'b_k_rent', label: 'Rent', value: 0, format: 'money' },
      { kind: 'metric', id: 'b_k_eating', label: 'Eating out', value: 0, format: 'money' },
      { kind: 'metric', id: 'b_k_groceries', label: 'Groceries', value: 0, format: 'money' },
      { kind: 'metric', id: 'b_k_transport', label: 'Transport', value: 0, format: 'money' },
      { kind: 'metric', id: 'b_k_fun', label: 'Fun', value: 0, format: 'money' },
      { kind: 'metric', id: 'b_k_subs', label: 'Subscriptions', value: 0, format: 'money' },
    ]),
  ],
  face: { value: { minus: [{ setting: 'limit' }, { agg: 'sum', from: 'budget/spend', field: 'amount', window: 'month' }] }, format: 'money', label: 'left', status: true },
  stitches: [{ from: 'groceries/trips', to: 'budget/spend', map: [{ to: 'amount', from: 'total' }, { to: 'at', from: 'at' }, { to: 'note', from: 'store' }, { to: 'category', const: 'c_groceries' }] }],
};
// block values as the server would send them (totals from the category table in §2.3)
const budgetValues = (lunch) => ({
  b_left: { text: lunch ? '$400' : '$412', target: 'left of $1,200', pct: lunch ? 67 : 66, sub: lunch ? 'Was $412 · 11 days to go' : '11 days to go' },
  b_where: { rows: [
    { label: 'Groceries', text: '$142.00 of $200', pct: 71 },
    lunch ? { label: 'Eating out', text: '$177.00 of $150', pct: 85, over_pct: 15, note: '$27 over.' } : { label: 'Eating out', text: '$165.00 of $150', pct: 91, over_pct: 9, note: '$15 over.' },
    { label: 'Transport', text: '$42.00 of $100', pct: 42 },
    { label: 'Subscriptions', text: '$26.47 of $40', pct: 66 },
    { label: 'Rent', text: '$380.00', note: 'No limit' },
    { label: 'Fun', text: '$32.53', note: 'No limit' }] },
  b_subs: { rows: [
    { label: 'Spotify', text: '$11.99', note: 'Renews Sun 22 Nov' },
    { label: 'Hulu', text: '$9.99', note: 'Renews Wed 2 Dec' },
    { label: 'Adobe CC, student', text: '$13.49', note: 'Renews Thu 3 Dec' },
    { label: 'iCloud 50 GB', text: '$2.99', note: 'Renews Wed 9 Dec' }] },
  b_spent: { text: lunch ? '$800.00' : '$788.00', target: '$1,200', pct: lunch ? 67 : 66 },
  b_c_eating: { text: lunch ? '$177.00' : '$165.00', target: '$150', pct: 100, over: lunch ? '$27 over' : '$15 over' },
  b_c_groceries: { text: '$142.00', target: '$200', pct: 71 },
  b_c_transport: { text: '$42.00', target: '$100', pct: 42 },
  b_c_subs: { text: '$26.47', target: '$40', pct: 66 },
  b_k_rent: { text: '$380.00', sub: 'no limit' },
  b_k_eating: { text: lunch ? '$177.00' : '$165.00', sub: lunch ? 'limit $150 · $27 over' : 'limit $150 · $15 over' },
  b_k_groceries: { text: '$142.00', sub: 'limit $200' },
  b_k_transport: { text: '$42.00', sub: 'limit $100' },
  b_k_fun: { text: '$32.53', sub: 'no limit' },
  b_k_subs: { text: '$26.47', sub: 'limit $40' },
});
const appResp = (key, spec, data, values = {}, faceOver = {}, seq = 4100, variant = 'seed') => {
  const ins = instrumented(key, spec, values, variant);
  return { spec: ins.spec, data: ins.data ? { ...data, ...ins.data } : data, values: ins.values, ...(ins.status ? { status: ins.status } : {}),
    faces: { [key]: facesOf(faceOver)[key] }, seq, server_now: SERVER_NOW };
};
write('app.budget', appResp('budget', budgetSpec, { 'budget/spend': spendRows }, budgetValues(false)));
write('app.budget.lunch', appResp('budget', budgetSpec, { 'budget/spend': [...spendRows, LUNCH_ROW] }, budgetValues(true), { budget: { text: '$400' } }, 4101));

// ------------------------------------------------------------------ Groceries (§2.2)
const LISTS = [{ id: 'l_weekly', label: 'Weekly shop' }, { id: 'l_taco', label: 'Taco night', hint: 'Sat 21 Nov' }, { id: 'l_costco', label: 'Costco run', hint: 'Once a month' }];
const open = (list, names) => names.map((n) => {
  const [name, qty] = Array.isArray(n) ? n : [n];
  return rec('i_' + name.toLowerCase().replace(/[^a-z]+/g, '_'), { name, list, status: 'to_buy', usual: 'auto', ...(qty ? { qty } : {}) });
});
const TRIPS = [
  ['05', "Smith's", 41.37, [['Coffee beans', 2.99], ['Butter', 4.79]]], ['09', 'Corner Market', 8.62, [['Chicken thighs', 8.62]]],
  ['10', 'Corner Market', 4.29, [['Greek yogurt', 4.29]]], ['11', "Smith's", 27.15, [['Spinach', 3.29], ['Cheddar', 3.99]]],
  ['12', 'Corner Market', 4.29, [['Eggs', 4.29]]], ['13', 'Corner Market', 7.78, [['Oat milk', 3.49], ['Parmesan', 4.29]]],
  ['14', "Smith's", 45.01, [['Bananas', 1.87], ['Orange juice', 3.69]]], ['15', 'Corner Market', 3.49, [['Hummus', 3.49]]],
];
const tripRows = TRIPS.map(([day, store, total]) => rec('tr_' + day, { store, total: cents(total), at: dt('2026-11-' + day, '17:30') }));
const boughtRows = TRIPS.flatMap(([day, , , items]) => items.map(([name, price]) =>
  rec('ib_' + name.toLowerCase().replace(/[^a-z]+/g, '_'), { name, list: 'l_weekly', status: 'bought', price: cents(price), bought_on: '2026-11-' + day, trip: ['tr_' + day], usual: 'auto' })));
const WEEKLY = open('l_weekly', ['Oat milk', ['Eggs', '1 dozen'], 'Bananas', 'Chicken thighs', ['Rice', '5 lb'], 'Spinach', 'Greek yogurt', 'Coffee beans', 'Coffee filters', 'Tortillas', 'Olive oil', 'Dish soap']);
const TACO = open('l_taco', ['Ground beef', 'Avocados', 'Limes', 'Salsa', 'Shredded cheese']);
const COSTCO = open('l_costco', ['Paper towels', 'Laundry pods', 'Frozen berries', 'Almonds', 'Toilet paper']);
const groceriesSpec = {
  ...meta('groceries'),
  collections: [
    { key: 'items', name: 'Items', titleField: 'name',
      fields: [f('name', 'Item', 'text', { required: true }), f('list', 'List', 'select', { options: LISTS }),
        f('status', 'Status', 'select', { options: [{ id: 'to_buy', label: 'To buy' }, { id: 'bought', label: 'Bought' }] }),
        f('qty', 'Qty', 'text'), f('price', 'Price', 'money'), f('bought_on', 'Bought', 'date'),
        f('trip', 'Trip', 'relation', { target: 'groceries/trips' }),
        f('usual', 'Usual', 'select', { options: [{ id: 'auto', label: 'Auto' }, { id: 'yes', label: 'Yes' }, { id: 'no', label: 'No' }] })] },
    { key: 'trips', name: 'Trips', titleField: 'store', dateField: 'at', amountField: 'total', calendar: true, label: 'Grocery trip',
      fields: [f('store', 'Store', 'text', { required: true }), f('total', 'Total', 'money', { required: true }), f('at', 'When', 'datetime', { required: true })] },
  ],
  tabs: [
    page('t_list', 'List', [
      { kind: 'list', id: 'b_items', source: 'groceries/items', switch: 'list', addAt: 'end', fields: ['qty'],
        where: [{ field: 'status', op: 'eq', value: 'to_buy' }], swipe: { right: 'complete', left: 'delete' } }]),
    page('t_trips', 'Trips', [
      { kind: 'progress', id: 'b_spend', label: 'Grocery spend', value: { agg: 'sum', from: 'groceries/trips', field: 'total', window: 'month' }, target: 20000, format: 'money' },
      { kind: 'list', id: 'b_trips', source: 'groceries/trips', fields: ['at'], sort: { field: 'at', dir: 'desc' } }]),
  ],
  face: { value: { agg: 'count', from: 'groceries/items', window: 'all', where: [{ field: 'status', op: 'eq', value: 'to_buy' }, { field: 'list', op: 'eq', value: 'l_weekly' }] }, format: 'count', label: 'to buy' },
  stitches: [],
};
write('app.groceries', appResp('groceries', groceriesSpec,
  { 'groceries/items': [...WEEKLY, ...TACO, ...COSTCO, ...boughtRows], 'groceries/trips': tripRows },
  { b_spend: { text: '$142.00', target: '$200', pct: 71 } }));

// ------------------------------------------------------------------ *dated (this week and next week, done rows left out)
const D = (date, time, title, app, sub, record_id, extra = {}) => ({ at: time ? dt(date, time) : date, title, sub, app, record_id, ...extra });
const G = { sub: 'Google Calendar', source: 'google' };
const DATED = [
  // this week, Mon 16 to Sun 22 Nov
  D('2026-11-16', '11:50', 'MATH 1210', 'classes', 'Classes', 'c02', { occurrence: '2026-11-16' }),
  D('2026-11-16', '15:00', 'CS 3500', 'classes', 'Classes', 'c03', { occurrence: '2026-11-16' }),
  D('2026-11-17', '09:10', 'ECON 1010', 'classes', 'Classes', 'c01', { occurrence: '2026-11-17' }),
  D('2026-11-18', '11:50', 'MATH 1210', 'classes', 'Classes', 'c02', { occurrence: '2026-11-18' }),
  D('2026-11-18', '15:00', 'CS 3500', 'classes', 'Classes', 'c03', { occurrence: '2026-11-18' }),
  D('2026-11-19', '09:10', 'ECON 1010', 'classes', 'Classes', 'c01', { occurrence: '2026-11-19' }),
  D('2026-11-20', '18:00', 'Pull day', 'workout', 'Workout', 's_pull', { occurrence: '2026-11-20' }),
  D('2026-11-20', '20:00', 'Take out recycling', 'todos', 'To-dos', 't_recycling', { occurrence: '2026-11-20' }),
  D('2026-11-20', '21:00', 'Return library books', 'todos', 'To-dos', 't_library'),
  D('2026-11-21', '10:00', 'Coffee with Maya', 'calendar', 'Calendar', 'e_coffee'),
  D('2026-11-22', null, 'Call home', 'todos', 'To-dos', 't_call_home'),
  D('2026-11-22', null, 'Spotify renews · $11.99', 'subscriptions', 'Subscriptions', 'sub_spotify', { occurrence: '2026-11-22' }),
  // next week, Mon 23 to Sun 29 Nov, before the planner
  D('2026-11-23', '11:50', 'MATH 1210', 'classes', 'Classes', 'c02', { occurrence: '2026-11-23' }),
  D('2026-11-23', '15:00', 'CS 3500', 'classes', 'Classes', 'c03', { occurrence: '2026-11-23' }),
  D('2026-11-23', '18:00', 'Pull day', 'workout', 'Workout', 's_pull', { occurrence: '2026-11-23' }),
  D('2026-11-23', '23:59', 'Start CS 3500 project', 'classes', 'Classes', 'd01'),
  D('2026-11-24', '07:00', 'Leg day', 'workout', 'Workout', 's_legs', { occurrence: '2026-11-24' }),
  D('2026-11-24', '07:30', 'Dentist', 'calendar', G.sub, 'g_dentist', { ends: dt('2026-11-24', '08:30'), source: 'google' }),
  D('2026-11-24', '09:10', 'ECON 1010', 'classes', 'Classes', 'c01', { occurrence: '2026-11-24' }),
  D('2026-11-24', '23:59', 'Homework 11', 'classes', 'Classes', 'd02'),
  D('2026-11-25', '11:50', 'MATH 1210', 'classes', 'Classes', 'c02', { occurrence: '2026-11-25' }),
  D('2026-11-25', '15:00', 'CS 3500', 'classes', 'Classes', 'c03', { occurrence: '2026-11-25' }),
  D('2026-11-25', '17:00', 'Drive home for Thanksgiving', 'calendar', G.sub, 'g_drive', { ends: dt('2026-11-25', '21:00'), source: 'google' }),
  D('2026-11-25', '18:00', 'Push day', 'workout', 'Workout', 's_push', { occurrence: '2026-11-25' }),
  D('2026-11-26', null, 'Thanksgiving at home', 'calendar', G.sub, 'g_thanksgiving', { ends: '2026-11-28', all_day: true, source: 'google' }),
  D('2026-11-27', '18:00', 'Pull day', 'workout', 'Workout', 's_pull', { occurrence: '2026-11-27' }),
  D('2026-11-27', '20:00', 'Take out recycling', 'todos', 'To-dos', 't_recycling', { occurrence: '2026-11-27' }),
  D('2026-11-29', '12:00', 'Back to campus', 'calendar', G.sub, 'g_back', { ends: dt('2026-11-29', '13:00'), source: 'google' }),
];

// ------------------------------------------------------------------ Calendar
const eventRows = [
  rec('e_haircut_aug', { title: 'Haircut', at: dt('2026-08-08', '11:00'), kind: 'barber' }),
  rec('e_haircut_sep', { title: 'Haircut', at: dt('2026-09-12', '11:00'), kind: 'barber' }),
  rec('e_haircut_oct', { title: 'Haircut', at: dt('2026-10-17', '11:00'), kind: 'barber' }),
  rec('e_coffee', { title: 'Coffee with Maya', at: dt('2026-11-21', '10:00') }),
  rec('g_dentist', { title: 'Dentist', at: dt('2026-11-24', '07:30'), ends: dt('2026-11-24', '08:30'), source: 'google', ext_id: 'g1' }),
  rec('g_drive', { title: 'Drive home for Thanksgiving', at: dt('2026-11-25', '17:00'), ends: dt('2026-11-25', '21:00'), source: 'google', ext_id: 'g2' }),
  rec('g_thanksgiving', { title: 'Thanksgiving at home', at: '2026-11-26', ends: '2026-11-28', source: 'google', ext_id: 'g3' }),
  rec('g_back', { title: 'Back to campus', at: dt('2026-11-29', '12:00'), ends: dt('2026-11-29', '13:00'), source: 'google', ext_id: 'g4' }),
];
const calendarSpec = {
  ...meta('calendar'),
  collections: [{ key: 'events', name: 'Events', titleField: 'title', dateField: 'at', calendar: true,
    fields: [f('title', 'Title', 'text', { required: true }), f('at', 'When', 'datetime', { required: true }), f('ends', 'Ends', 'datetime'),
      f('kind', 'Kind', 'select', { options: opts('Doctor', 'Dentist', 'Barber', 'Other') }), f('source', 'Source', 'text')] }],
  tabs: [
    page('t_today', 'Today', [{ kind: 'calendar', id: 'b_today', source: '*dated', window: 'today' }]),
    page('t_week', 'Week', [{ kind: 'calendar', id: 'b_week', source: '*dated', window: 'week' }]),
    page('t_events', 'Events', [{ kind: 'list', id: 'b_events', source: 'calendar/events', fields: ['at', 'kind'], sort: { field: 'at', dir: 'desc' } }]),
  ],
  face: { value: { agg: 'count', from: '*dated', window: 'today' }, format: 'count', label: 'today' },
};
write('app.calendar', appResp('calendar', calendarSpec, { '*dated': DATED, 'calendar/events': eventRows }));

// ------------------------------------------------------------------ To-dos
const todoRows = [
  rec('t_library', { title: 'Return library books', due: dt('2026-11-20', '21:00'), place: 'Marriott Library', done: false }),
  rec('t_recycling', { title: 'Take out recycling', due: dt('2026-11-20', '20:00'), done: false,
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=FR', start: '2026-10-23T20:00', log: ['2026-10-23', '2026-10-30', '2026-11-13'], skip: ['2026-11-06'] } }),
  rec('t_call_home', { title: 'Call home', due: '2026-11-22', done: false }),
  rec('t_maya', { title: 'Pay Maya back for pizza ($14)', done: false }),
  rec('t_devday', { title: 'DevDay demo', due: dt('2026-11-20', '15:00'), place: 'Lassonde Studios', done: true }),
  rec('t_flu', { title: 'Book flu shot', place: 'Student health', done: true }),
];
const todosSpec = {
  ...meta('todos'),
  collections: [{ key: 'todos', name: 'To-dos', titleField: 'title', dateField: 'due', calendar: true,
    fields: [f('title', 'To-do', 'text', { required: true }), f('due', 'Due', 'datetime'), f('place', 'Place', 'text'), f('done', 'Done', 'bool'), f('repeat', 'Repeat', 'repeat')] }],
  tabs: [
    page('t_today', 'Today', [{ kind: 'list', id: 'b_today', source: 'todos/todos', fields: ['due', 'place'], sort: { field: 'due', dir: 'asc' },
      where: [{ field: 'done', op: 'eq', value: false }, { field: 'due', op: 'within', value: 'today' }], swipe: { right: 'complete', left: 'delete' } }]),
    page('t_all', 'All', [{ kind: 'list', id: 'b_all', source: 'todos/todos', fields: ['due', 'place'],
      where: [{ field: 'done', op: 'eq', value: false }], swipe: { right: 'complete', left: 'delete' } }]),
    page('t_done', 'Done', [{ kind: 'list', id: 'b_done', source: 'todos/todos', fields: ['due', 'place'], where: [{ field: 'done', op: 'eq', value: true }] }]),
  ],
  face: { value: { agg: 'count', from: 'todos/todos', window: 'today', where: [{ field: 'done', op: 'eq', value: false }] }, format: 'count', label: 'today' },
};
write('app.todos', appResp('todos', todosSpec, { 'todos/todos': todoRows }));

// ------------------------------------------------------------------ Classes
const classRows = [
  rec('c01', { name: 'ECON 1010', title: 'Principles of Microeconomics', room: 'Kendall 104', time: dt('2026-11-24', '09:10'), meets: 'Tue and Thu 9:10 am',
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20261210T235959', start: '2026-08-25T09:10', log: [], skip: ['2026-11-26'] } }),
  rec('c02', { name: 'MATH 1210', title: 'Calculus I', room: 'JWB 335', time: dt('2026-11-23', '11:50'), meets: 'Mon and Wed 11:50 am',
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959', start: '2026-08-24T11:50', log: [], skip: [] } }),
  rec('c03', { name: 'CS 3500', title: 'Software Practice', room: 'WEB L104', time: dt('2026-11-23', '15:00'), meets: 'Mon and Wed 3:00 pm',
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959', start: '2026-08-24T15:00', log: [], skip: [] } }),
];
const dueRows = [
  rec('d01', { title: 'Start CS 3500 project', kind: 'assignment', at: dt('2026-11-23', '23:59'), class: ['c03'], done: false }),
  rec('d02', { title: 'Homework 11', kind: 'assignment', at: dt('2026-11-24', '23:59'), class: ['c02'], done: false }),
  rec('d03', { title: 'Homework 10', kind: 'assignment', at: dt('2026-11-17', '23:59'), class: ['c02'], done: true }),
];
const classesSpec = {
  ...meta('classes'),
  collections: [
    { key: 'classes', name: 'Classes', titleField: 'name', dateField: 'time', calendar: true,
      fields: [f('name', 'Class', 'text', { required: true }), f('title', 'Title', 'text'), f('room', 'Room', 'text'), f('meets', 'Meets', 'text'), f('time', 'Next', 'datetime'), f('repeat', 'Repeat', 'repeat')] },
    { key: 'due', name: 'Due', label: 'Due date', titleField: 'title', dateField: 'at', calendar: true,
      fields: [f('title', 'Title', 'text', { required: true }), f('kind', 'Kind', 'select', { options: [{ id: 'assignment', label: 'Assignment' }, { id: 'exam', label: 'Exam' }] }),
        f('at', 'Due', 'datetime'), f('class', 'Class', 'relation', { target: 'classes/classes' }), f('done', 'Done', 'bool')] },
  ],
  tabs: [
    page('t_schedule', 'Schedule', [{ kind: 'list', id: 'b_classes', source: 'classes/classes', fields: ['title', 'meets', 'room'] }]),
    page('t_due', 'Due', [{ kind: 'list', id: 'b_due', source: 'classes/due', fields: ['class', 'at'], sort: { field: 'at', dir: 'asc' },
      where: [{ field: 'kind', op: 'eq', value: 'assignment' }], swipe: { right: 'complete' } }]),
    page('t_exams', 'Exams', [{ kind: 'list', id: 'b_exams', source: 'classes/due', fields: ['class', 'at'], sort: { field: 'at', dir: 'asc' }, where: [{ field: 'kind', op: 'eq', value: 'exam' }] }]),
  ],
  face: { value: { agg: 'count', from: 'classes/due', where: [{ field: 'done', op: 'eq', value: false }, { field: 'at', op: 'within', value: '7d' }] }, format: 'count', label: 'due this week' },
};
write('app.classes', appResp('classes', classesSpec, { 'classes/classes': classRows, 'classes/due': dueRows }));

// ------------------------------------------------------------------ Notes
// Eight notes in four notebooks (spec/backend.md §2.3). Only Mon 16 to Thu 19 Nov notes count toward the face (3 this week): the three
// older-than-Monday additions are dated before Mon 16 Nov. A note can sit in several notebooks (`many`). `[[Title]]` in a body is a link
// (resolved by the server when the note is saved; the mock resolves it on read). Links made by hand are the LINKS table at the bottom.
const notebookRows = [
  rec('nb_econ', { name: 'ECON 1010', class: ['c01'] }), rec('nb_math', { name: 'MATH 1210', class: ['c02'] }),
  rec('nb_cs3500', { name: 'CS 3500', class: ['c03'] }), rec('nb_personal', { name: 'Personal' }),
];
const noteRows = [
  rec('n_1', { title: 'Related rates examples', notebook: ['nb_math'], at: dt('2026-11-10', '12:40'),
    body: 'A ladder sliding down a wall, a balloon filling at 5 cm³ a second. Write the relationship, differentiate with respect to time, then plug in. It leans on the [[Chain rule recap]] every time.' }),
  rec('n_2', { title: 'Gift ideas for mom', notebook: ['nb_personal'], at: dt('2026-11-15', '20:15'),
    body: 'A scarf (found one at the thrift shop). A tea sampler. A framed photo from the lake trip.' }),
  rec('n_3', { title: 'Unit testing with mocks', notebook: ['nb_cs3500'], at: dt('2026-11-16', '15:50'),
    body: 'Mock the network call and assert it ran once with the right arguments. Keep one real test per service so the mocks do not drift.' }),
  rec('n_4', { title: 'Dependency injection', notebook: ['nb_cs3500'], at: dt('2026-11-18', '15:55'),
    body: 'Hand a class its dependencies instead of letting it build them. That is what makes the mocks in [[Unit testing with mocks]] possible. Constructor injection first.' }),
  rec('n_5', { title: 'Price elasticity', notebook: ['nb_econ'], at: dt('2026-11-19', '10:30'),
    body: 'Elasticity is the percent change in quantity over the percent change in price. Above 1 the good is elastic. Coffee and textbooks are the class examples.' }),
  recB('n_6', { title: 'Chain rule recap', notebook: ['nb_math'], at: dt('2026-11-09', '11:20'),
    body: "d/dx f(g(x)) = f'(g(x)) · g'(x). Work from the outside in: differentiate the outer function, keep the inside, then multiply by the derivative of the inside. Example: d/dx sin(3x²) = cos(3x²) · 6x." }),
  recB('n_7', { title: 'Finals study plan', notebook: ['nb_math', 'nb_econ'], at: dt('2026-11-15', '10:30'),
    body: 'Math: redo [[Related rates examples]], then Homework 11.\nEcon: reread chapter 5 and the elasticity examples.' }),
  recB('n_8', { title: 'Chicken and rice', notebook: ['nb_personal'], at: dt('2026-11-14', '18:30'),
    body: 'Thighs, rice, spinach, garlic. Bake the thighs at 425 for 25 minutes, rice in the cooker. Serves two with leftovers.' }),
];
const notesSpec = {
  ...meta('notes'),
  collections: [
    { key: 'notebooks', name: 'Notebooks', titleField: 'name', fields: [f('name', 'Notebook', 'text', { required: true }), f('class', 'Class', 'relation', { target: 'classes/classes' })] },
    { key: 'notes', name: 'Notes', titleField: 'title', dateField: 'at',
      fields: [f('title', 'Title', 'text', { required: true }), f('body', 'Note', 'text', { multiline: true }),
        f('notebook', 'Notebook', 'relation', { target: 'notes/notebooks', many: true }), f('at', 'Written', 'datetime', { required: true })] },
  ],
  tabs: [
    page('t_notebooks', 'Notebooks', [{ kind: 'list', id: 'b_notebooks', source: 'notes/notebooks', fields: ['class'] }]),
    page('t_all', 'All notes', [{ kind: 'list', id: 'b_notes', source: 'notes/notes', fields: ['notebook', 'at'], sort: { field: 'at', dir: 'desc' } }]),
  ],
  face: { value: { agg: 'count', from: 'notes/notes', window: 'week' }, format: 'count', label: 'this week' },
};
// `classes/classes` rides along: the notebooks' Class field points into another app, and the client names a relation from the rows it was sent
write('app.notes', appResp('notes', notesSpec, { 'notes/notebooks': notebookRows, 'notes/notes': noteRows, 'classes/classes': classRows }));

// ------------------------------------------------------------------ Subscriptions
const subRows = [
  rec('sub_spotify', { name: 'Spotify', amount: 1199, renews: '2026-11-22', every: 'Monthly on the 22nd' }),
  rec('sub_hulu', { name: 'Hulu', amount: 999, renews: '2026-12-02', every: 'Monthly on the 2nd' }),
  rec('sub_adobe', { name: 'Adobe CC, student', amount: 1349, renews: '2026-12-03', every: 'Monthly on the 3rd' }),
  rec('sub_icloud', { name: 'iCloud 50 GB', amount: 299, renews: '2026-12-09', every: 'Monthly on the 9th' }),
];
const subsSpec = {
  ...meta('subscriptions'),
  collections: [{ key: 'subscriptions', name: 'Subscriptions', titleField: 'name', dateField: 'renews', amountField: 'amount', calendar: true,
    fields: [f('name', 'Name', 'text', { required: true }), f('amount', 'Cost', 'money'), f('renews', 'Renews', 'date'), f('every', 'Repeats', 'text')] }],
  tabs: [
    page('t_subs', 'Subscriptions', [
      { kind: 'metric', id: 'b_total', label: 'A month', value: { agg: 'sum', from: 'subscriptions/subscriptions', field: 'amount' }, format: 'money' },
      { kind: 'list', id: 'b_subs', source: 'subscriptions/subscriptions', fields: ['every'] }]),
    page('t_renewals', 'Renewals', [{ kind: 'list', id: 'b_renewals', source: 'subscriptions/subscriptions', fields: ['renews'], sort: { field: 'renews', dir: 'asc' } }]),
  ],
  face: { value: { agg: 'sum', from: 'subscriptions/subscriptions', field: 'amount' }, format: 'money', label: 'a month' },
};
write('app.subscriptions', appResp('subscriptions', subsSpec, { 'subscriptions/subscriptions': subRows }, { b_total: { text: '$38.46', sub: '4 subscriptions' } }));

// ------------------------------------------------------------------ Workout
const routineRows = [rec('ro_pull', { name: 'Pull', minutes: 45, needs: 'Gym' }), rec('ro_push', { name: 'Push', minutes: 40, needs: 'Gym' }), rec('ro_legs', { name: 'Legs', minutes: 35, needs: 'Gym' })];
const EX = [
  ['ro_pull', 'Pull-ups', 3, 8, 0], ['ro_pull', 'Lat pulldown', 3, 10, 120], ['ro_pull', 'Seated cable row', 3, 12, 100], ['ro_pull', 'Face pulls', 3, 15, 40], ['ro_pull', 'Hammer curl', 3, 12, 25],
  ['ro_push', 'Push-ups', 3, 12, 0], ['ro_push', 'Dumbbell bench', 3, 10, 40], ['ro_legs', 'Goblet squat', 3, 10, 45], ['ro_legs', 'Walking lunges', 3, 12, 0],
];
const exId = (name) => 'ex_' + name.toLowerCase().replace(/[^a-z]+/g, '_');
const exerciseRows = EX.map(([routine, name, sets, reps, weight]) =>
  rec(exId(name), { name, routine: [routine], plan: `${sets}×${reps}` + (weight ? ` at ${weight} lb` : ' bodyweight'), sets, reps, weight }));
const sessionRows = [
  rec('s_pull', { name: 'Pull day', routine: ['ro_pull'], at: dt('2026-11-20', '18:00'), meets: 'Mon and Fri 6:00 pm', done: false,
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=MO,FR', start: '2026-09-01T18:00', log: ['2026-11-16'], skip: ['2026-09-07', '2026-10-12', '2026-10-16'] } }),
  rec('s_legs', { name: 'Leg day', routine: ['ro_legs'], at: dt('2026-11-24', '07:00'), meets: 'Tue 7:00 am', done: false,
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=TU', start: '2026-09-01T07:00', log: ['2026-11-17'], skip: ['2026-10-13'] } }),
  rec('s_push', { name: 'Push day', routine: ['ro_push'], at: dt('2026-11-25', '18:00'), meets: 'Wed 6:00 pm', done: false,
    repeat: { rule: 'FREQ=WEEKLY;BYDAY=WE', start: '2026-09-02T18:00', log: ['2026-11-18'], skip: ['2026-10-14'] } }),
];
const WEEK_SETS = [
  ['16', '18:10', 'Lat pulldown', '3×10', 120], ['16', '18:20', 'Seated cable row', '3×12', 100], ['16', '18:30', 'Face pulls', '3×15', 40], ['16', '18:38', 'Hammer curl', '3×12', 25], ['16', '18:04', 'Pull-ups', '3×8', 0],
  ['17', '07:08', 'Goblet squat', '3×10', 45], ['17', '07:20', 'Walking lunges', '3×12', 0],
  ['18', '18:15', 'Dumbbell bench', '3×10', 40], ['18', '18:05', 'Push-ups', '3×12', 0],
];
const setRows = WEEK_SETS.map(([day, time, name, did, weight], i) =>
  rec('set_' + (i + 1), { exercise: [exId(name)], did, load: weight ? `${weight} lb` : 'Bodyweight', at: dt('2026-11-' + day, time) }));
const workoutSpec = {
  ...meta('workout'),
  collections: [
    { key: 'sessions', name: 'Sessions', titleField: 'name', dateField: 'at', calendar: true,
      fields: [f('name', 'Session', 'text', { required: true }), f('routine', 'Routine', 'relation', { target: 'workout/routines' }), f('at', 'Next', 'datetime'), f('meets', 'Repeats', 'text'), f('done', 'Done', 'bool'), f('repeat', 'Repeat', 'repeat')] },
    { key: 'routines', name: 'Routines', titleField: 'name', fields: [f('name', 'Routine', 'text', { required: true }), f('minutes', 'About', 'number', { unit: 'min' }), f('needs', 'Needs', 'text')] },
    { key: 'exercises', name: 'Exercises', titleField: 'name',
      fields: [f('name', 'Exercise', 'text', { required: true }), f('routine', 'Routine', 'relation', { target: 'workout/routines' }), f('plan', 'Plan', 'text'), f('sets', 'Sets', 'number'), f('reps', 'Reps', 'number'), f('weight', 'Weight', 'number', { unit: 'lb' })] },
    { key: 'sets', name: 'Sets', titleField: 'exercise', dateField: 'at',
      fields: [f('exercise', 'Exercise', 'relation', { target: 'workout/exercises' }), f('did', 'Sets', 'text'), f('load', 'Weight', 'text'), f('at', 'When', 'datetime', { required: true })] },
  ],
  tabs: [
    page('t_today', 'Today', [
      { kind: 'list', id: 'b_today', source: 'workout/sessions', fields: ['at'], where: [{ field: 'at', op: 'within', value: 'today' }] },
      { kind: 'text', id: 'b_plan_h', text: 'Pull routine, about 45 min' },
      { kind: 'list', id: 'b_plan', source: 'workout/exercises', fields: ['plan'], where: [{ field: 'routine', op: 'eq', value: 'ro_pull' }] }]),
    page('t_log', 'Log', [{ kind: 'list', id: 'b_sets', source: 'workout/sets', fields: ['did', 'load'], sort: { field: 'at', dir: 'desc' }, group: 'at' }]),
    page('t_history', 'History', [
      { kind: 'metric', id: 'b_done', label: 'Done since September', value: 0, format: 'count' },
      { kind: 'metric', id: 'b_week', label: 'This week', value: 0, format: 'count' },
      { kind: 'list', id: 'b_series', source: 'workout/sessions', fields: ['meets'] }]),
    page('t_progress', 'Progress', [
      { kind: 'metric', id: 'b_lat', label: 'Lat pulldown', value: 0, format: 'text' },
      { kind: 'metric', id: 'b_volume', label: 'Volume this week', value: 0, format: 'number' }]),
    page('t_routines', 'Routines', [
      { kind: 'list', id: 'b_routines', source: 'workout/routines', fields: ['minutes', 'needs'] },
      { kind: 'list', id: 'b_exercises', source: 'workout/exercises', fields: ['plan'], group: 'routine' }]),
  ],
  face: { value: { agg: 'count', from: 'workout/sessions', window: 'week', where: [{ field: 'done', op: 'eq', value: true }] }, format: 'count', label: 'this week' },
  workflows: [],
};
write('app.workout', appResp('workout', workoutSpec,
  { 'workout/sessions': sessionRows, 'workout/routines': routineRows, 'workout/exercises': exerciseRows, 'workout/sets': setRows },
  { b_done: { text: '41', sub: 'sessions, 5 skipped' }, b_week: { text: '3', sub: 'of 4 planned' }, b_lat: { text: '100 → 120 lb', sub: 'in 8 weeks' }, b_volume: { text: '12,450 lb' } }));

// ------------------------------------------------------------------ Calories
const MEALS = [
  ['16', '08:00', 'Oatmeal and banana', 350, 10, 'breakfast'], ['16', '12:30', 'Turkey sandwich', 520, 28, 'lunch'], ['16', '19:00', 'Pasta with chicken', 780, 42, 'dinner'],
  ['17', '08:15', 'Greek yogurt and granola', 310, 18, 'breakfast'], ['17', '12:40', 'Leftover pasta', 640, 34, 'lunch'], ['17', '19:10', 'Tacos', 820, 38, 'dinner'],
  ['18', '08:05', 'Oatmeal and banana', 350, 10, 'breakfast'], ['18', '13:00', 'Taco Bell burrito', 690, 24, 'lunch'], ['18', '19:20', 'Chicken and rice', 640, 45, 'dinner'],
  ['19', '08:20', 'Eggs and toast', 380, 22, 'breakfast'], ['19', '12:45', 'Union food court rice bowl', 690, 30, 'lunch'], ['19', '19:30', 'Frozen pizza', 900, 36, 'dinner'],
  ['20', '08:10', 'Oatmeal and banana', 350, 10, 'breakfast'], ['20', '12:30', 'Chicken and rice', 640, 45, 'lunch'], ['20', '15:40', 'Greek yogurt', 150, 15, 'snack'],
];
const mealRows = MEALS.map(([day, time, name, calories, protein, meal], i) => rec('m_' + (i + 1), { name, calories, protein, meal, at: dt('2026-11-' + day, time) }));
const foodRows = [rec('fd_1', { name: 'Oatmeal and banana', calories: 350, protein: 10 }), rec('fd_2', { name: 'Chicken and rice', calories: 640, protein: 45 }), rec('fd_3', { name: 'Greek yogurt', calories: 150, protein: 15 })];
const calFields = [f('name', 'Meal', 'text', { required: true }), f('calories', 'Calories', 'number', { unit: 'cal' }), f('protein', 'Protein', 'number', { unit: 'g protein' })];
const caloriesSpec = {
  ...meta('calories'),
  settings: { target: 2200 },
  collections: [
    { key: 'meals', name: 'Meals', titleField: 'name', dateField: 'at',
      fields: [...calFields, f('meal', 'Meal time', 'select', { options: opts('Breakfast', 'Lunch', 'Dinner', 'Snack') }), f('at', 'When', 'datetime', { required: true })] },
    { key: 'foods', name: 'Foods', titleField: 'name', fields: calFields },
  ],
  tabs: [
    page('t_today', 'Today', [
      { kind: 'progress', id: 'b_today', label: 'Today', value: { agg: 'sum', from: 'calories/meals', field: 'calories', window: 'today' }, target: { setting: 'target' }, format: 'number' },
      { kind: 'list', id: 'b_meals_today', source: 'calories/meals', fields: ['meal', 'calories', 'protein'], sort: { field: 'at', dir: 'asc' }, where: [{ field: 'at', op: 'within', value: 'today' }] }]),
    page('t_log', 'Log', [{ kind: 'list', id: 'b_meals', source: 'calories/meals', fields: ['calories', 'protein'], sort: { field: 'at', dir: 'desc' }, group: 'at' }]),
    page('t_foods', 'Foods', [{ kind: 'list', id: 'b_foods', source: 'calories/foods', fields: ['calories', 'protein'] }]),
  ],
  face: { value: { agg: 'sum', from: 'calories/meals', field: 'calories', window: 'today' }, format: 'number', label: 'today' },
};
write('app.calories', appResp('calories', caloriesSpec, { 'calories/meals': mealRows, 'calories/foods': foodRows }, { b_today: { text: '1,140', target: '2,200', pct: 52 } }));

// ------------------------------------------------------------------ Running
const RUNS = [
  ['2026-10-31', '09:00', 'Long run', 'long', 4, 40], ['2026-11-03', '17:30', 'Easy run', 'easy', 3, 30], ['2026-11-07', '09:00', 'Long run', 'long', 4.5, 44],
  ['2026-11-10', '17:30', 'Easy run', 'easy', 3, 29], ['2026-11-12', '16:30', 'Easy run', 'easy', 3.5, 34], ['2026-11-14', '09:00', 'Long run', 'long', 5, 49],
  ['2026-11-17', '17:30', 'Easy run', 'easy', 3, 29], ['2026-11-19', '16:30', 'Easy run', 'easy', 4, 38],
];
const runRows = RUNS.map(([date, time, name, kind, distance, minutes], i) => rec('run_' + (i + 1), { name, kind, distance, minutes, at: dt(date, time), done: true }));
const raceRows = [rec('race_10k', { name: 'Winter 10K', at: dt('2026-12-12', '09:00'), distance: '10K' })];
const runningSpec = {
  ...meta('running'),
  collections: [
    { key: 'runs', name: 'Runs', titleField: 'name', dateField: 'at', calendar: true, label: 'Run',
      fields: [f('name', 'Run', 'text', { required: true }), f('kind', 'Kind', 'select', { options: opts('Easy', 'Long', 'Tempo', 'Intervals', 'Race') }),
        f('distance', 'Distance', 'number', { unit: 'mi' }), f('minutes', 'Time', 'number', { unit: 'min' }), f('at', 'When', 'datetime', { required: true }), f('done', 'Done', 'bool')] },
    { key: 'races', name: 'Races', titleField: 'name', dateField: 'at', calendar: true, label: 'Race',
      fields: [f('name', 'Race', 'text', { required: true }), f('at', 'When', 'datetime'), f('distance', 'Distance', 'text')] },
  ],
  tabs: [
    page('t_week', 'This week', [
      { kind: 'metric', id: 'b_week', label: 'This week', value: { agg: 'sum', from: 'running/runs', field: 'distance', window: 'week' }, format: 'number' },
      { kind: 'list', id: 'b_runs_week', source: 'running/runs', fields: ['at', 'distance', 'minutes'], sort: { field: 'at', dir: 'desc' }, where: [{ field: 'at', op: 'within', value: 'week' }] }]),
    page('t_log', 'Log', [{ kind: 'list', id: 'b_runs', source: 'running/runs', fields: ['at', 'distance', 'minutes'], sort: { field: 'at', dir: 'desc' } }]),
    page('t_races', 'Races', [{ kind: 'list', id: 'b_races', source: 'running/races', fields: ['at', 'distance'] }]),
  ],
  face: { value: { agg: 'sum', from: 'running/runs', field: 'distance', window: 'week', where: [{ field: 'done', op: 'eq', value: true }] }, format: 'number', label: 'mi this week' },
};
write('app.running', appResp('running', runningSpec, { 'running/runs': runRows, 'running/races': raceRows }, { b_week: { text: '7 mi', sub: '2 runs' } }));

// ------------------------------------------------------------------ Cycle
const cycleRows = [rec('cy_1', { start: '2026-09-01', length: 28 }), rec('cy_2', { start: '2026-09-29', length: 28 }), rec('cy_3', { start: '2026-10-27' })];
const DAYS = [['2026-09-01', 'medium', 2], ['2026-09-02', 'heavy', 2], ['2026-09-03', 'light', 3], ['2026-09-29', 'medium', 2], ['2026-09-30', 'heavy', 2], ['2026-10-01', 'light', 3],
  ['2026-10-27', 'medium', 2], ['2026-10-28', 'heavy', 2], ['2026-10-29', 'light', 3]];
const dayRows = DAYS.map(([date, flow, energy], i) => rec('cd_' + (i + 1), { date, flow, energy, ...(energy === 2 ? { symptoms: 'Cramps' } : {}) }));
const cycleSpec = {
  ...meta('cycle'),
  settings: { clair_read: true },
  private: true,
  collections: [
    { key: 'days', name: 'Days', titleField: 'date', dateField: 'date',
      fields: [f('date', 'Day', 'date', { required: true }), f('flow', 'Flow', 'select', { options: opts('None', 'Light', 'Medium', 'Heavy') }), f('symptoms', 'Symptoms', 'text'), f('energy', 'Energy', 'number', { unit: 'energy', unitFirst: true }), f('note', 'Note', 'text')] },
    { key: 'cycles', name: 'Cycles', titleField: 'start', dateField: 'start', fields: [f('start', 'Started', 'date', { required: true }), f('length', 'Length', 'number', { unit: 'days' })] },
  ],
  tabs: [
    page('t_log', 'Log', [{ kind: 'list', id: 'b_days', source: 'cycle/days', fields: ['flow', 'symptoms', 'energy'], sort: { field: 'date', dir: 'desc' } }]),
    page('t_cycles', 'Cycles', [{ kind: 'list', id: 'b_cycles', source: 'cycle/cycles', fields: ['length'], sort: { field: 'start', dir: 'desc' } }]),
  ],
  face: { value: { agg: 'max', from: 'cycle/cycles', field: 'start' }, format: 'text', label: 'last period started' },
};
write('app.cycle', appResp('cycle', cycleSpec, { 'cycle/days': dayRows, 'cycle/cycles': cycleRows }));

// ------------------------------------------------------------------ Meditation
const medRows = [
  rec('med_1', { kind: 'sleep', minutes: 10, at: dt('2026-11-16', '22:30'), mood_before: 2, mood_after: 4 }),
  rec('med_2', { kind: 'breathing', minutes: 5, at: dt('2026-11-18', '07:40'), mood_before: 3, mood_after: 4 }),
  rec('med_3', { kind: 'body_scan', minutes: 10, at: dt('2026-11-19', '22:45'), mood_before: 2, mood_after: 3 }),
];
const meditationSpec = {
  ...meta('meditation'),
  collections: [{ key: 'sessions', name: 'Sessions', titleField: 'kind', dateField: 'at',
    fields: [f('kind', 'Kind', 'select', { options: opts('Breathing', 'Body scan', 'Sleep', 'Walking') }), f('minutes', 'Minutes', 'number', { unit: 'min' }), f('at', 'When', 'datetime', { required: true }), f('mood', 'Mood', 'text')] }],
  tabs: [
    page('t_sessions', 'Sessions', [{ kind: 'list', id: 'b_sessions', source: 'meditation/sessions', fields: ['at', 'minutes', 'mood'], sort: { field: 'at', dir: 'desc' } }]),
    page('t_week', 'This week', [
      { kind: 'metric', id: 'b_min', label: 'This week', value: { agg: 'sum', from: 'meditation/sessions', field: 'minutes', window: 'week' }, format: 'number' },
      { kind: 'metric', id: 'b_count', label: 'Sessions', value: { agg: 'count', from: 'meditation/sessions', window: 'week' }, format: 'count' }]),
  ],
  face: { value: { agg: 'sum', from: 'meditation/sessions', field: 'minutes', window: 'week' }, format: 'number', label: 'min this week' },
};
write('app.meditation', appResp('meditation', meditationSpec, { 'meditation/sessions': medRows }, { b_min: { text: '25 min' }, b_count: { text: '3' } }));

// ==================================================================== scenarios
// A scenario is a scripted Clair run (run.*) and, once its change set is confirmed,
// an effect (effect.*): recorded rows, faces and values that the mock lays over the
// base fixtures. Effects are composed in the order they were confirmed; the mock
// adds and removes recorded rows and never works anything out.
const ev = (delay, event, data) => ({ delay, event, data });
const cs = (id, o) => ({
  id, status: 'basted', version: 1, flagged: false, mode: 'live', kind: 'records',
  source: { kind: 'text', label: 'You typed', at: SERVER_NOW }, ops: [], expanded: [], deltas: [], ...o,
});
const result = (id, seq, faces = {}) => ({ change_set_id: id, server_seq: seq, blocks: [], faces, warnings: [] });
const datedKey = (r) => `${r.record_id}@${r.occurrence ?? r.at}`;
const sample = (run) => run.map((e) => (e.event === 'proposal'
  ? { ...e, data: { change_set: { ...e.data.change_set, mode: 'fixture', source: { ...e.data.change_set.source, kind: 'fixture', label: 'Sample run' } } } } : e));
const fromRule = (run, label) => run.map((e) => (e.event === 'proposal'
  ? { ...e, data: { change_set: { ...e.data.change_set, id: e.data.change_set.id + '_rule', source: { kind: 'workflow', label, at: SERVER_NOW } } } }
  : e)).filter((e) => e.event !== 'offer');

// ------------------------------------------------------------------ lunch ("spent $12 on lunch", base cut line)
const LUNCH_OP = { op: 'insert', ref: 'budget/spend', values: { note: 'Lunch', amount: 1200, category: 'c_eating_out', at: SERVER_NOW } };
write('run.lunch', [
  ev(0, 'status', { text: 'Reading your note…' }),
  ev(900, 'understood', { kind: 'request', summary: 'A $12 lunch. That goes in Budget.' }),
  ev(900, 'proposal', { change_set: cs('cs_lunch', {
    title: 'Lunch', summary: '$12.00 in Eating out.', ops: [LUNCH_OP], expanded: [LUNCH_OP],
    lines: [{ apps: ['budget'], what: 'Lunch · Eating out', val: '$12.00', sub: '$412 → $400 left' }],
    targets: ['budget'], deltas: [{ app: 'budget', before: '$412', after: '$400' }],
    actions: { primary: 'Add to Budget', secondary: 'Review items' },
    review: [{ title: 'Lunch', when: 'Today, 5:45 pm · $12.00', change: 'new', reason: 'Eating out', app: 'budget' }] }) }),
  ev(150, 'done', { status: 'complete', sources: ['budget'], spoken: 'Lunch, twelve dollars. Add to Budget?' }),
]);
write('confirm.lunch', result('cs_lunch', 4101, { budget: { text: '$400', value: 40000, label: 'left' } }));
write('undo.lunch', result('cs_lunch', 4102, { budget: { text: '$412', value: 41200, label: 'left' } }));
write('effect.lunch', {
  credits: -1,
  home: { status: '**$400** left this month. Pull day at **6 pm**.', faces: { budget: { text: '$400' } }, changed: ['budget'] },
  apps: { budget: { add: { 'budget/spend': [LUNCH_ROW] }, values: budgetValues(true), face: { text: '$400', label: 'left' } } },
});

// ------------------------------------------------------------------ planner (clair-agent.md §12.9, backend.md §2.3)
const OFFER_PLAN = {
  kind: 'workflow', app: 'workout', prompt: 'Do this every Sunday at 7 pm?',
  sentence: "Every Sunday at 7:00 pm, plan next week's training",
  trigger: { kind: 'schedule', rule: 'FREQ=WEEKLY;BYDAY=SU', at: '19:00' },
  action: { kind: 'ask_clair', text: 'Plan my training for next week' },
};
const LIFTS = [
  { title: 'Pull day', when: 'Mon 23 Nov 6:00 pm', change: 'kept', reason: 'Free after CS 3500', source: 'Classes', app: 'workout' },
  { title: 'Leg day', when: 'Tue 24 Nov 7:00 am → 5:00 pm', change: 'moved', reason: 'Dentist at 7:30 am', source: 'Google Calendar', app: 'workout' },
  { title: 'Push day', when: 'Wed 25 Nov 6:00 pm → 7:00 am', change: 'moved', reason: 'Drive home at 5:00 pm', source: 'Google Calendar', app: 'workout' },
  { title: 'Pull day', when: 'Fri 27 → Sun 29 Nov 4:00 pm', change: 'moved', reason: 'Back on campus Sun 12:00 pm', source: 'Google Calendar', app: 'workout' },
];
const ALSO = { also: 'shortest session; energy 2 logged on day 1 of your last 3 cycles', also_source: 'Cycle' };
const R4_REVIEW = [
  LIFTS[0], { ...LIFTS[1], ...ALSO }, LIFTS[2],
  { title: 'Easy run', when: 'Thu 26 Nov 8:00 am · 3 mi', change: 'new', reason: 'Away from the gym; a run goes anywhere', source: 'Google Calendar', app: 'running' },
  { title: 'Long run', when: 'Sat 28 Nov 9:00 am · 5.5 mi', change: 'new', reason: '10K on Sat 12 Dec; last long run 5 mi', source: 'Running', app: 'running' },
  LIFTS[3],
  { title: 'Body scan', when: 'Tue 24 Nov 9:30 pm · 10 min', change: 'new', reason: 'After Leg day; 3 sessions logged this week', source: 'Meditation', app: 'todos' },
  { title: 'Oats', when: 'Weekly shop', change: 'new', reason: 'Oatmeal 3 of 5 mornings; not on your list', source: 'Calories', app: 'groceries' },
];
const mv = (record_id, occurrence, value, reason, reason_source) => ({ op: 'move_occurrence', app: 'workout', collection: 'sessions', record_id, occurrence, fields: [{ key: 'at', value }], reason, reason_source });
const LIFT_OPS = [
  { op: 'keep', record_id: 's_pull', occurrence: '2026-11-23', reason: 'Free after CS 3500', reason_source: 'c03' },
  { ...mv('s_legs', '2026-11-24', dt('2026-11-24', '17:00'), 'Dentist at 7:30 am', 'g_dentist') },
  mv('s_push', '2026-11-25', dt('2026-11-25', '07:00'), 'Drive home at 5:00 pm', 'g_drive'),
  mv('s_pull', '2026-11-27', dt('2026-11-29', '16:00'), 'Back on campus Sun 12:00 pm', 'g_back'),
];
const R4_OPS = [
  LIFT_OPS[0], { ...LIFT_OPS[1], also: ALSO.also, also_source: 'cd_7' }, LIFT_OPS[2],
  { op: 'insert', ref: 'running/runs', values: { name: 'Easy run', kind: 'easy', distance: 3, at: dt('2026-11-26', '08:00'), done: false }, reason: 'Away from the gym; a run goes anywhere', reason_source: 'g_thanksgiving' },
  { op: 'insert', ref: 'running/runs', values: { name: 'Long run', kind: 'long', distance: 5.5, at: dt('2026-11-28', '09:00'), done: false }, reason: '10K on Sat 12 Dec; last long run 5 mi', reason_source: 'race_10k' },
  LIFT_OPS[3],
  { op: 'insert', ref: 'todos/todos', values: { title: '10 min body scan', due: dt('2026-11-24', '21:30'), done: false }, reason: 'After Leg day; 3 sessions logged this week', reason_source: 'med_3' },
  { op: 'insert', ref: 'groceries/items', values: { name: 'Oats', list: 'l_weekly', status: 'to_buy' }, reason: 'Oatmeal 3 of 5 mornings; not on your list', reason_source: 'm_13' },
];
const WORKOUT_LINE = { apps: ['workout'], what: 'Pull Mon 6:00 pm · Legs Tue 5:00 pm · Push Wed 7:00 am · Pull Sun 4:00 pm', val: '' };
const PLAN = {
  1: {
    understood: 'Read 4 apps: Calendar, Classes, To-dos and Workout.',
    summary: '4 lifts (1 kept, 3 moved).',
    lines: [WORKOUT_LINE, { apps: ['calendar'], what: '3 sessions move', val: '' }],
    targets: ['workout', 'calendar'], deltas: [], primary: 'Add to 2 apps', review: LIFTS, ops: LIFT_OPS,
    sources: ['calendar', 'classes', 'todos', 'workout'],
  },
  4: {
    understood: 'Read 9 apps: Calendar, Classes, To-dos, Workout, Running, Calories, Cycle, Meditation and Groceries.',
    summary: '4 lifts (1 kept, 3 moved), 2 runs, 1 recovery to-do, 1 grocery item. Mon to Thu you logged 1,650 to 1,970 calories a day (target 2,200).',
    lines: [WORKOUT_LINE,
      { apps: ['running'], what: 'Easy 3 mi Thu 8:00 am · Long 5.5 mi Sat 9:00 am', val: '' },
      { apps: ['todos'], what: '10 min body scan · Tue 9:30 pm', val: '' },
      { apps: ['groceries'], what: 'Oats', val: '', sub: '12 → 13 to buy' },
      { apps: ['calendar'], what: '3 sessions move, 2 runs and 1 to-do added', val: '' }],
    targets: ['workout', 'running', 'todos', 'groceries', 'calendar'], deltas: [{ app: 'groceries', before: '12', after: '13' }],
    primary: 'Add to 5 apps', review: R4_REVIEW, ops: R4_OPS,
    sources: ['calendar', 'classes', 'todos', 'workout', 'running', 'calories', 'cycle', 'meditation', 'groceries'],
  },
};
// rows the confirmed plan writes (backend.md §3, move_occurrence: a skip on the series and a one-off record)
const oneOff = (id, name, routine, date, time, series, occ) => rec(id, { name, routine: [routine], at: dt(date, time), done: false, _moved_from: { record_id: series, occurrence: occ } });
const D_CH = (date, time, title, app, sub, record_id, extra = {}) => ({ ...D(date, time, title, app, sub, record_id, extra), changed: true });
const liftEffect = {
  'workout/sessions': [oneOff('s_legs_1124', 'Leg day', 'ro_legs', '2026-11-24', '17:00', 's_legs', '2026-11-24'),
    oneOff('s_push_1125', 'Push day', 'ro_push', '2026-11-25', '07:00', 's_push', '2026-11-25'),
    oneOff('s_pull_1129', 'Pull day', 'ro_pull', '2026-11-29', '16:00', 's_pull', '2026-11-27')],
};
const liftDated = [
  D_CH('2026-11-24', '17:00', 'Leg day', 'workout', 'Workout', 's_legs_1124'),
  D_CH('2026-11-25', '07:00', 'Push day', 'workout', 'Workout', 's_push_1125'),
  D_CH('2026-11-29', '16:00', 'Pull day', 'workout', 'Workout', 's_pull_1129'),
];
const liftRemoved = ['s_legs@2026-11-24', 's_push@2026-11-25', 's_pull@2026-11-27'];
const r4Rows = {
  runs: [rec('run_easy_1126', { name: 'Easy run', kind: 'easy', distance: 3, at: dt('2026-11-26', '08:00'), done: false }),
    rec('run_long_1128', { name: 'Long run', kind: 'long', distance: 5.5, at: dt('2026-11-28', '09:00'), done: false })],
  todo: rec('t_bodyscan', { title: '10 min body scan', due: dt('2026-11-24', '21:30'), done: false }),
  oats: rec('i_oats', { name: 'Oats', list: 'l_weekly', status: 'to_buy', usual: 'auto' }),
};
const r4Dated = [
  D_CH('2026-11-24', '21:30', '10 min body scan', 'todos', 'To-dos', 't_bodyscan'),
  D_CH('2026-11-26', '08:00', 'Run · Easy run', 'running', 'Running', 'run_easy_1126'),
  D_CH('2026-11-28', '09:00', 'Run · Long run', 'running', 'Running', 'run_long_1128'),
];
for (const rung of [1, 4]) {
  const p = PLAN[rung];
  const card = cs('cs_planner', {
    title: "Next week's training", summary: p.summary, ops: p.ops, expanded: p.ops, lines: p.lines, targets: p.targets, deltas: p.deltas,
    actions: { primary: p.primary, secondary: 'Review items' }, review: rung === 1 ? p.review : p.review,
  });
  const run = [
    ev(0, 'status', { text: 'Reading your week…' }),
    ev(1400, 'understood', { kind: 'request', summary: p.understood }),
    ev(2600, 'status', { text: 'Fitting 4 lifts around your week…' }),
    ev(3200, 'proposal', { change_set: card }),
    ev(120, 'offer', OFFER_PLAN),
    ev(80, 'done', { status: 'complete', sources: p.sources }),
  ];
  write(`run.planner.r${rung}`, run);
  write(`run.planner.r${rung}.sample`, sample(run).map((e) => (e.event === 'status' || e.event === 'understood' ? { ...e, delay: Math.min(e.delay, 300) } : e)));
  write(`run.planner.r${rung}.workflow`, fromRule(run, 'Every Sunday at 7:00 pm'));
  const changed = p.targets;
  write(`confirm.planner.r${rung}`, result('cs_planner', 4110, rung === 4 ? { groceries: { text: '13', value: 13, label: 'to buy' } } : {}));
  write(`undo.planner.r${rung}`, result('cs_planner', 4111, rung === 4 ? { groceries: { text: '12', value: 12, label: 'to buy' } } : {}));
  write(`effect.planner.r${rung}`, {
    credits: -1,
    home: { changed, ...(rung === 4 ? { faces: { groceries: { text: '13' } } } : {}) },
    apps: {
      workout: { add: liftEffect },
      calendar: { add: { '*dated': rung === 4 ? [...liftDated, ...r4Dated] : liftDated }, remove: { '*dated': liftRemoved } },
      ...(rung === 4 ? {
        running: { add: { 'running/runs': r4Rows.runs } },
        todos: { add: { 'todos/todos': [r4Rows.todo] } },
        groceries: { add: { 'groceries/items': [r4Rows.oats] }, face: { text: '13', label: 'to buy' }, status: '**23** to buy across 3 lists. **$142.00** of $200 spent this month.' },
      } : {}),
    },
  });
}
write('run.planner.done', [
  ev(0, 'status', { text: 'Reading your week…' }),
  ev(1600, 'text_delta', { text: 'Next week is already planned. Nothing to move or add.' }),
  ev(80, 'done', { status: 'complete', sources: ['workout', 'calendar'] }),
]);

// ------------------------------------------------------------------ appointment check (clair-agent.md §12.10)
const OFFER_APPT = {
  kind: 'workflow', app: 'calendar', prompt: 'Check every Sunday at 7 pm?',
  sentence: 'Every Sunday at 7:00 pm, check for appointments that are due',
  trigger: { kind: 'schedule', rule: 'FREQ=WEEKLY;BYDAY=SU', at: '19:00' },
  action: { kind: 'ask_clair', text: 'Am I due for any appointments?' },
};
const HAIRCUT_OP = { op: 'insert', ref: 'calendar/events', values: { title: 'Haircut', kind: 'barber', at: dt('2026-11-21', '14:00'), remind: '1d' }, reason: 'Usual 11:00 am is right after Coffee with Maya', reason_source: 'e_coffee' };
const apptRun = [
  ev(0, 'status', { text: 'Checking your calendar…' }),
  ev(900, 'understood', { kind: 'request', summary: 'Read Calendar.' }),
  ev(1500, 'proposal', { change_set: cs('cs_haircut', {
    title: 'Haircut is due', summary: 'You go about every 5 weeks. The last was Sat 17 Oct.', ops: [HAIRCUT_OP], expanded: [HAIRCUT_OP],
    lines: [{ apps: ['calendar'], what: 'Haircut · Sat 21 Nov 2:00 pm · reminder the day before', val: '' }],
    targets: ['calendar'], actions: { primary: 'Add to Calendar', secondary: 'Review items' },
    review: [{ title: 'Haircut', when: 'Sat 21 Nov 2:00 pm · reminder the day before', change: 'new', reason: 'Usual 11:00 am is right after Coffee with Maya', source: 'Calendar', app: 'calendar' }] }) }),
  ev(120, 'offer', OFFER_APPT),
  ev(80, 'done', { status: 'complete', sources: ['calendar'] }),
];
write('run.appointments', apptRun);
write('run.appointments.workflow', fromRule(apptRun, 'Every Sunday at 7:00 pm'));
write('run.appointments.done', [
  ev(0, 'status', { text: 'Checking your calendar…' }),
  ev(1200, 'text_delta', { text: 'Nothing is due. Your next haircut is already on Calendar.' }),
  ev(80, 'done', { status: 'complete', sources: ['calendar'] }),
]);
write('confirm.appointments', result('cs_haircut', 4120, { calendar: { text: '3', value: 3, label: 'today' } }));
write('undo.appointments', result('cs_haircut', 4121, { calendar: { text: '3', value: 3, label: 'today' } }));
write('effect.appointments', {
  credits: -1,
  home: { changed: ['calendar'] },
  apps: { calendar: { add: {
    'calendar/events': [rec('e_haircut_nov', { title: 'Haircut', kind: 'barber', at: dt('2026-11-21', '14:00'), remind: '1d' })],
    '*dated': [D_CH('2026-11-21', '14:00', 'Haircut', 'calendar', 'Calendar', 'e_haircut_nov')] } } },
});

// ------------------------------------------------------------------ described rule and the exam (workflows.md steps 3 and 4)
const EXAM_RULE = {
  sentence: 'When an exam is added to Classes, add a study to-do two days before',
  trigger: { kind: 'row_added', collection: 'classes/due', where: [{ field: 'kind', op: 'eq', value: 'exam' }] },
  action: { kind: 'write_row', collection: 'todos/todos', map: { title: 'Study for {title}', due: { from: 'at', offset: '-2d' } } },
};
write('run.exam-rule', [
  ev(0, 'status', { text: 'Reading your rule…' }),
  ev(1200, 'proposal', { change_set: cs('cs_rule_exam', {
    kind: 'rule', title: 'Add this rule to Classes?', summary: EXAM_RULE.sentence, rule: { app: 'classes', ...EXAM_RULE },
    lines: [{ apps: ['classes'], what: 'Workflows tab', val: '' }, { apps: ['todos'], what: 'gets the study to-dos', val: '' }],
    targets: ['classes'], actions: { primary: 'Turn on', secondary: 'Not now' } }) }),
  ev(80, 'done', { status: 'complete', sources: ['classes', 'todos'] }),
]);
write('confirm.exam-rule', result('cs_rule_exam', 4130));
write('undo.exam-rule', result('cs_rule_exam', 4131));
write('effect.exam-rule', { credits: -1, rules: { classes: [{ id: 'w_exam', on: true, ...EXAM_RULE }] }, home: { changed: ['classes'] } });
const EXAM_ROW = rec('d_midterm2', { title: 'Midterm 2', kind: 'exam', at: dt('2026-12-03', '09:10'), class: ['c01'], done: false });
const STUDY_ROW = rec('t_study_mid2', { title: 'Study for Midterm 2', due: '2026-12-01', done: false, _via: { workflow: 'w_exam' } });
const examCard = (withRule) => cs('cs_exam', {
  title: 'Midterm 2', summary: withRule ? 'ECON 1010, Thu 3 Dec 9:10 am. Your rule adds a study to-do.' : 'ECON 1010, Thu 3 Dec 9:10 am.',
  ops: [{ op: 'insert', ref: 'classes/due', values: EXAM_ROW.properties }],
  expanded: [{ op: 'insert', ref: 'classes/due', values: EXAM_ROW.properties }, ...(withRule ? [{ op: 'insert', ref: 'todos/todos', values: STUDY_ROW.properties }] : [])],
  lines: [{ apps: ['classes'], what: 'Midterm 2 · ECON 1010 · Thu 3 Dec 9:10 am', val: '' },
    ...(withRule ? [{ apps: ['todos'], what: 'Study for Midterm 2 · Tue 1 Dec', val: '', sub: 'by rule' }] : []),
    { apps: ['calendar'], what: withRule ? 'the exam and the to-do' : 'the exam', val: '' }],
  targets: withRule ? ['classes', 'todos', 'calendar'] : ['classes', 'calendar'],
  actions: { primary: withRule ? 'Add to 3 apps' : 'Add to 2 apps', secondary: 'Review items' },
  review: [{ title: 'Midterm 2', when: 'Thu 3 Dec 9:10 am', change: 'new', reason: 'ECON 1010', source: 'Classes', app: 'classes' },
    ...(withRule ? [{ title: 'Study for Midterm 2', when: 'Tue 1 Dec', change: 'new', reason: 'by rule: two days before an exam', source: 'Classes', app: 'todos' }] : [])],
});
for (const [name, withRule] of [['exam', false], ['exam.rule', true]]) {
  write(`run.${name}`, [
    ev(0, 'status', { text: 'Reading your note…' }),
    ev(900, 'understood', { kind: 'request', summary: 'An exam for ECON 1010. That goes in Classes.' }),
    ev(900, 'proposal', { change_set: examCard(withRule) }),
    ev(80, 'done', { status: 'complete', sources: ['classes'] }),
  ]);
  write(`confirm.${name}`, result('cs_exam', 4140));
  write(`undo.${name}`, result('cs_exam', 4141));
  write(`effect.${name}`, {
    credits: -1, home: { changed: withRule ? ['classes', 'todos', 'calendar'] : ['classes', 'calendar'] },
    apps: {
      classes: { add: { 'classes/due': [EXAM_ROW] } },
      calendar: { add: { '*dated': [D_CH('2026-12-03', '09:10', 'Midterm 2', 'classes', 'Classes', 'd_midterm2'),
        ...(withRule ? [D_CH('2026-12-01', null, 'Study for Midterm 2', 'todos', 'To-dos', 't_study_mid2')] : [])] } },
      ...(withRule ? { todos: { add: { 'todos/todos': [STUDY_ROW] } } } : {}),
    },
  });
}

// ------------------------------------------------------------------ plain answers (no card)
const say = (name, status, text, sources = []) => write(`run.${name}`, [ev(0, 'status', { text: status }), ev(1100, 'text_delta', { text }), ev(60, 'done', { status: 'complete', sources })]);
say('google-move', 'Reading your calendar…', "I can't change events from Google Calendar. Move it in Google, and I'll plan around it.", ['calendar']);
say('rule-unsupported', 'Reading your rule…', "Rules can't send email yet. They can add rows to your apps, or ask me to plan something on a schedule.");
say('already-built', 'Reading…', 'You already have that app. Open it from Your apps.');
say('unknown', 'Reading…', 'This is mock data, so only the scripted sentences answer. Try "Spent $12 on lunch" or "Plan my training for next week".');

// ------------------------------------------------------------------ the three builds (clair-agent.md §12.11), on the "before" state
// Each build is one run in two requests (§11): the sentence ends in a card of questions
// (run.build-<key>, done awaiting_input); the answer streams the plan, then the build
// proposal (run.build-<key>.answer). The tapes hold the recording's answers; Calories with
// no number of Sam's (No target, or Skip) has its own tape and effect (build-calories-none).
const ex = (id, props) => ({ ...rec(id, props), example: true });
const opt = (label, description, input) => ({ label, description, ...(input ? { input } : {}) });
const ask = (id, header, text, options, multi = false) => ({ id, header, text, options, multi });
const QUESTIONS = {
  calories: [
    ask('target', 'Daily target', 'Do you want a daily calorie target?', [
      opt('Set a number', 'You choose it; the Today ring fills toward it', { placeholder: 'Calories a day', numeric: true }),
      opt('No target', 'Just totals for the day')]),
    ask('logging', 'Logging', 'How do you log meals?', [
      opt('Type them', 'Name, calories and protein each time'),
      opt('Pick from foods you save', 'Save a food once, then tap it to log it again')], true),
  ],
  running: [
    ask('stopwatch', 'Stopwatch', 'Time runs in the app?', [
      opt('Yes, with a stopwatch', 'Start a run, then add the distance at the end'),
      opt("No, I'll type them after", "Add the distance and time when you're back")]),
    ask('race', 'Race', 'Show the race on Calendar?', [
      opt('Yes', 'Race · 10K on Sat 12 Dec'),
      opt('No', 'Keep it in Running only')]),
  ],
  cycle: [
    ask('log', 'What to log', 'What do you want to log?', [
      opt('Flow', 'None, light, medium or heavy'), opt('Energy', '1 to 5'),
      opt('Symptoms', 'Cramps, headaches, in your words'), opt('Mood', 'In a word')], true),
    ask('read', 'Clair', 'Can Clair read it?', [
      opt('No, keep it private', 'Off on every new Cycle app; you can turn it on later'),
      opt('Yes', 'Clair can use it when you ask, like planning your week')]),
  ],
};
const calNoTarget = {
  plan: [{ app: 'calories', text: 'Today: calories and protein so far, no target' }, { app: 'calories', text: 'Log: meals with calories and protein' }, { app: 'calories', text: 'Foods: save a food once, tap it to log it again' }],
  spec: { ...caloriesSpec, settings: {} },
  exampleValues: { b_ring: { text: '990', target: 'today', pct: 0, sub: 'example' } },
  newValues: { b_ring: { text: '0', target: 'today', pct: 0, sub: 'No daily target' } },
};
const BUILDS = {
  calories: {
    sentence: 'Track what I eat, calories and protein',
    title: 'Make a Calories app?', summary: 'Meals with calories and protein, and foods you save.',
    lines: [{ apps: ['calories'], what: 'new app · Today, Log and Foods', val: '' }],
    plan: [{ app: 'calories', text: 'Today: a ring for calories against 2,200' }, { app: 'calories', text: 'Log: meals with calories and protein' }, { app: 'calories', text: 'Foods: save a food once, tap it to log it again' }],
    spec: { ...caloriesSpec, settings: { target: 2200 } }, // Sam's own number, typed under "Set a number"
    exampleData: { 'calories/meals': [ex('xm_1', { name: 'Oatmeal and banana', calories: 350, protein: 10, meal: 'breakfast', at: dt('2026-11-20', '08:00') }), ex('xm_2', { name: 'Chicken and rice', calories: 640, protein: 45, meal: 'lunch', at: dt('2026-11-20', '12:30') })], 'calories/foods': [] },
    exampleValues: { b_ring: { text: '990', target: 'of 2,200', pct: 45, sub: 'example' } },
    newData: { 'calories/meals': [], 'calories/foods': [] }, newValues: { b_ring: { text: '0', target: 'of 2,200', pct: 0 } },
    face: { text: '0', label: 'today' }, targets: ['calories'],
    variants: { none: calNoTarget },
  },
  running: {
    sentence: "I'm running a 10K on Sat 12 Dec. Track my runs",
    title: 'Make a Running app?', summary: 'Your runs, and your 10K on Sat 12 Dec.',
    lines: [{ apps: ['running'], what: 'new app · This week, Log and Races', val: '' }, { apps: ['calendar'], what: 'Race · 10K, Sat 12 Dec', val: '' }],
    plan: [{ app: 'running', text: 'This week: days to your 10K, and a stopwatch that logs each run' }, { app: 'running', text: 'Log: runs with distance and time' }, { app: 'running', text: 'Races: 10K on Sat 12 Dec' }, { app: 'calendar', text: 'Calendar: Race · 10K on Sat 12 Dec' }],
    spec: runningSpec,
    exampleData: { 'running/runs': [ex('xr_1', { name: 'Easy run', kind: 'easy', distance: 3, minutes: 30, at: dt('2026-11-19', '17:30'), done: true })], 'running/races': [rec('race_new', { name: '10K', at: dt('2026-12-12', '09:00'), distance: '10K' })] },
    exampleValues: { b_race: { title: '10K', text: '22', unit: 'days to go', sub: 'Sat 12 Dec · 9:00 am' }, b_strip: { days: [{ dow: 'M' }, { dow: 'T' }, { dow: 'W' }, { dow: 'T', text: '3 mi', on: true }, { dow: 'F', today: true }, { dow: 'S' }, { dow: 'S' }] } },
    newData: { 'running/runs': [], 'running/races': [rec('race_new', { name: '10K', at: dt('2026-12-12', '09:00'), distance: '10K' })] }, newValues: { b_race: { title: '10K', text: '22', unit: 'days to go', sub: 'Sat 12 Dec · 9:00 am' } },
    face: { text: '0', label: 'mi this week' }, targets: ['running', 'calendar'],
    calendarAdd: [D_CH('2026-12-12', '09:00', 'Race · 10K', 'running', 'Running', 'race_new')],
  },
  cycle: {
    sentence: 'Track my cycle and keep it private',
    title: 'Make a Cycle app?', summary: "A daily log and cycle starts. Private: I won't read it unless you turn that on.",
    lines: [{ apps: ['cycle'], what: 'new app · Log and Cycles · private', val: '' }],
    plan: [{ app: 'cycle', text: 'Month: tap a day to log flow, energy and symptoms' }, { app: 'cycle', text: 'Cycles: when each one started' }, { app: 'cycle', text: "Private: Clair won't read it" }],
    spec: { ...cycleSpec, settings: { clair_read: false } },
    exampleData: { 'cycle/days': [ex('xc_1', { date: '2026-11-20', flow: 'light', energy: 3 })], 'cycle/cycles': [] },
    exampleValues: {}, newData: { 'cycle/days': [], 'cycle/cycles': [] }, newValues: {},
    face: { text: 'None yet', label: 'logged' }, targets: ['cycle'],
  },
};
for (const [key, base] of Object.entries(BUILDS)) {
  const a = APPS.find((x) => x[0] === key);
  const newPatch = { id: key, key, name: a[1], icon: a[2], dye: a[3], face: base.face, changed: true, lastOpened: SERVER_NOW, pinned: false, isNew: true };
  // the sentence: Clair reads it, then asks before building (§7 rule 7). The mock stamps expires_at (24 h) when it plays.
  write(`run.build-${key}`, [
    ev(0, 'status', { text: 'Reading your sentence…' }),
    ev(1100, 'status', { text: "A few questions first, then I'll show you the plan." }),
    ev(260, 'question', { id: `q_build_${key}`, questions: QUESTIONS[key], plan_after: true }),
    ev(60, 'done', { status: 'awaiting_input', sources: [] }),
  ]);
  // the answer: the plan in plain words, then the build proposal it describes (same change set id on every answer)
  for (const [suffix, over] of [['', {}], ...Object.entries(base.variants ?? {}).map(([n, v]) => [`-${n}`, v])]) {
    const b = { ...base, ...over }, effect = `build-${key}${suffix}`;
    write(`run.build-${key}${suffix ? '.' + suffix.slice(1) : '.answer'}`, [
      ev(0, 'status', { text: 'Planning with your answers…' }),
      ev(900, 'plan', { title: a[1], new_app: { key, name: a[1], icon: a[2], dye: a[3] }, lines: b.plan, ...(b.spec.private ? { private: true } : {}) }),
      ev(500, 'status', { text: `Cutting ${b.spec.tabs.length} tabs…` }),
      ev(1500, 'proposal', { change_set: cs(`cs_build_${key}`, {
        kind: 'app', title: b.title, summary: b.summary, lines: b.lines, targets: b.targets,
        ops: [{ op: 'insert', ref: 'apps', values: { key } }], expanded: [],
        actions: { primary: 'Make it' },
        preview: (() => { const r = appResp(key, b.spec, b.exampleData, b.exampleValues, {}, 0, 'preview'); return { spec: r.spec, data: r.data, values: r.values, faces: { [key]: b.face }, seq: 0, server_now: SERVER_NOW }; })() }) }),
      ev(80, 'done', { status: 'complete', sources: [] }),
    ]);
    write(`confirm.${effect}`, result(`cs_build_${key}`, 4150, { [key]: b.face }));
    write(`undo.${effect}`, result(`cs_build_${key}`, 4151));
    write(`app.${key}.new${suffix}`, appResp(key, b.spec, b.newData, b.newValues, { [key]: b.face }, 4100, 'new'));
    write(`effect.${effect}`, {
      credits: -10,
      home: { addApps: [newPatch], changed: b.targets.filter((t) => t !== key) },
      fixtures: { [`/apps/${key}`]: `app.${key}.new${suffix}` },
      apps: b.calendarAdd ? { calendar: { add: { '*dated': b.calendarAdd } } } : {},
    });
  }
}

// ------------------------------------------------------------------ Google Calendar (backend.md §8a)
write('connect', [{ provider: 'google', account_email: 'sam@example.com', last_synced_at: SERVER_NOW, needs_reconnect: false }]);
write('connect.sync', { added: 0, changed: 0, removed: 0, last_synced_at: SERVER_NOW });
write('app.calendar.nogoogle', appResp('calendar', calendarSpec,
  { '*dated': DATED.filter((r) => r.source !== 'google'), 'calendar/events': eventRows.filter((r) => r.properties.source !== 'google') }));



// ==================================================================== instruments (Nov 20, design/DESIGN.md §10)
// Each starter app opens on what you do in it. Specs use the instrument blocks; the
// figures are literals from the seed at DEMO_NOW, as the server would send them.
function instrumented(key, spec, values, variant) {
  const P = (id, title, children) => ({ kind: 'page', id, title, children });
  const E = (f2, op, value) => ({ field: f2, op, value });
  const seed = variant === 'seed';
  const days = (cells) => ({ days: ['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((dow, i) => ({ dow, ...(cells[i] || {}), ...(i === 4 ? { today: true } : {}) })) });
  switch (key) {
    case 'budget': return {
      spec: { ...spec, tabs: [P('t_overview', 'Overview', [
        { kind: 'gauge', id: 'b_left', label: 'Left this month', value: spec.face.value, target: { setting: 'limit' }, format: 'money' },
        { kind: 'bars', id: 'b_where', label: 'Where it went', from: 'budget/spend', by: 'category', value: { agg: 'sum', from: 'budget/spend', field: 'amount', window: 'month' } },
        { kind: 'bars', id: 'b_subs', label: 'Subscriptions · $38.46 a month', from: 'subscriptions/subscriptions', by: 'name', value: { agg: 'sum', from: 'subscriptions/subscriptions', field: 'amount' } },
        { kind: 'list', id: 'b_recent', label: 'Recent', source: 'budget/spend', fields: ['category', 'at'], sort: { field: 'at', dir: 'desc' }, limit: 5 }])] },
      values };
    case 'groceries': return {
      spec: { ...spec, tabs: [P('t_list', 'List', [
        { kind: 'checklist', id: 'b_items', source: 'groceries/items', switch: 'list', fields: ['qty'],
          groups: [{ label: '{option} · {n} to buy', where: [E('status', 'eq', 'to_buy')] },
            { label: 'Bought in the last week · {n}', where: [E('status', 'eq', 'bought'), E('bought_on', 'within', '-7d')], done: true }],
          add: { placeholder: 'Add to {option}', set: { status: 'to_buy' } }, swipe: { right: 'complete', left: 'delete' } },
        { kind: 'progress', id: 'b_spend', label: 'Spent on groceries this month', value: { agg: 'sum', from: 'groceries/trips', field: 'total', window: 'month' }, target: 20000, format: 'money' },
        { kind: 'list', id: 'b_trips', label: 'Trips', source: 'groceries/trips', fields: ['at'], sort: { field: 'at', dir: 'desc' }, limit: 3 }])] },
      values: { b_spend: { text: '$142.00', target: '$200', pct: 71 }, ...values },
      status: seed ? '**22** to buy across 3 lists. **$142.00** of $200 spent this month.' : undefined };
    case 'calendar': return {
      spec: { ...spec, tabs: [P('t_days', 'Calendar', [{ kind: 'days', id: 'b_days', source: '*dated', views: ['day', 'week', 'month'], view: 'week' }])] },
      values, status: seed ? '**3** today. Dates from every app, in one place.' : undefined };
    case 'todos': return {
      spec: { ...spec, tabs: [P('t_todos', 'To-dos', [
        { kind: 'checklist', id: 'b_todos', source: 'todos/todos', fields: ['due', 'place'], due: 'due',
          groups: [{ label: 'Overdue · {n}', where: [E('done', 'eq', false), E('due', 'within', 'past')] },
            { label: 'Today · {today}', where: [E('done', 'eq', false), E('due', 'within', 'today')] },
            { label: 'Coming up', where: [E('done', 'eq', false), E('due', 'within', 'future')] },
            { label: 'Someday', where: [E('done', 'eq', false), E('due', 'empty', true)] },
            { label: 'Done · {n}', where: [E('done', 'eq', true)], done: true, collapsed: true }],
          add: { placeholder: 'Add a to-do, like "email TA Friday"', pinned: true }, swipe: { right: 'complete', left: 'delete' } }])] },
      values, status: seed ? '**2** left today.' : undefined };
    case 'workout': return {
      spec: { ...spec, tabs: [
        P('t_today', 'Today', [
          { kind: 'next', id: 'b_next', source: 'workout/sessions', log: 'workout/sets', fields: ['reps', 'weight'] },
          { kind: 'metric', id: 'b_lifted', label: 'Lifted this week', value: 0, format: 'number' },
          { kind: 'metric', id: 'b_since', label: 'Done since September', value: 0, format: 'count' },
          { kind: 'progress', id: 'b_sessions', label: 'Sessions this week', value: 0, target: 4, format: 'count' },
          { kind: 'strip', id: 'b_strip', label: 'This week', value: { agg: 'count', from: 'workout/sessions', window: 'week' } }]),
        ...spec.tabs.filter((t) => t.id !== 't_today')] },
      values: { ...values,
        b_next: { eyebrow: 'Next up · today 6 pm', meta: '5 exercises · about 45 min', title: 'Pull day', action: 'Start pull day', record_id: 's_pull', occurrence: '2026-11-20', rest: 90,
          steps: [
            { id: 'ex_pull_ups', name: 'Pull-ups', plan: '3 × 8 · bodyweight', sets: 3, reps: 8, weight: 0, unit: 'lb', best: { reps: 8, weight: 0, text: 'best 8 reps' } },
            { id: 'ex_lat_pulldown', name: 'Lat pulldown', plan: '3 × 10', sets: 3, reps: 10, weight: 120, unit: 'lb', best: { reps: 10, weight: 120, text: 'best 120 lb × 10' } },
            { id: 'ex_seated_cable_row', name: 'Seated cable row', plan: '3 × 12', sets: 3, reps: 12, weight: 100, unit: 'lb', best: { reps: 12, weight: 100, text: 'best 100 lb × 12' } },
            { id: 'ex_face_pulls', name: 'Face pulls', plan: '3 × 15', sets: 3, reps: 15, weight: 40, unit: 'lb', best: { reps: 15, weight: 40, text: 'best 40 lb × 15' } },
            { id: 'ex_hammer_curl', name: 'Hammer curl', plan: '3 × 12', sets: 3, reps: 12, weight: 25, unit: 'lb', best: { reps: 12, weight: 25, text: 'best 25 lb × 12' } }] },
        b_lifted: { text: '12,450 lb' }, b_since: { text: '41 sessions' }, b_sessions: { text: '3', target: '4', pct: 75 },
        b_strip: days([{ text: 'Pull', on: true }, { text: 'Legs', on: true }, { text: 'Push', on: true }, {}, { text: '6 pm' }]) },
      status: undefined }; // board Workout: the next-up card and the sessions bar say it
    case 'running': return {
      spec: { ...spec, tabs: [
        P('t_week', 'This week', [
          { kind: 'countdown', id: 'b_race', source: 'running/races' },
          { kind: 'strip', id: 'b_strip', label: 'This week', value: { agg: 'sum', from: 'running/runs', field: 'distance', window: 'week' } },
          { kind: 'timer', id: 'b_run', label: 'Start a run', mode: 'stopwatch', log: 'running/runs', minutesField: 'minutes', kindField: 'kind', after: ['distance'], set: { done: true } },
          { kind: 'list', id: 'b_runs_week', label: 'Runs this week', source: 'running/runs', fields: ['at', 'distance', 'minutes'], sort: { field: 'at', dir: 'desc' }, where: [E('at', 'within', 'week')] }]),
        ...spec.tabs.filter((t) => t.id !== 't_week')] },
      values: seed ? { b_race: { title: 'Winter 10K', text: '22', unit: 'days to go', sub: 'Sat 12 Dec · 9:00 am', note: 'Long runs: 4 → 4.5 → 5 mi' },
        b_strip: days([{}, { text: '3 mi', on: true }, {}, { text: '4 mi', on: true }]), ...values } : values,
      status: seed ? '**7 mi** this week. Winter 10K in **22 days**.' : undefined };
    case 'meditation': return {
      spec: { ...spec,
        collections: [{ ...spec.collections[0], fields: [
          ...spec.collections[0].fields.filter((x) => x.key !== 'mood'),
          { key: 'mood_before', label: 'Mood before', type: 'number', unit: 'mood', unitFirst: true },
          { key: 'mood_after', label: 'Mood after', type: 'number', unit: '→', unitFirst: true }] }],
        tabs: [
          P('t_sit', 'Sit', [
            { kind: 'timer', id: 'b_sit', label: 'Sit', mode: 'countdown', log: 'meditation/sessions', minutesField: 'minutes', kindField: 'kind', presets: [5, 10, 15, 20], moodFields: ['mood_before', 'mood_after'] },
            { kind: 'strip', id: 'b_strip', label: 'This week', value: { agg: 'sum', from: 'meditation/sessions', field: 'minutes', window: 'week' } }]),
          P('t_sessions', 'Sessions', [{ kind: 'list', id: 'b_sessions', source: 'meditation/sessions', fields: ['at', 'minutes', 'mood_before', 'mood_after'], sort: { field: 'at', dir: 'desc' } }])] },
      values: { b_strip: days([{ text: '10', on: true }, {}, { text: '5', on: true }, { text: '10', on: true }]), ...values },
      status: seed ? '**25 min** this week across **3** sessions.' : undefined };
    case 'calories': return {
      spec: { ...spec, tabs: [
        P('t_today', 'Today', [
          { kind: 'ring', id: 'b_ring', label: 'Today', value: spec.face.value, target: { setting: 'target' }, format: 'number' },
          { kind: 'picks', id: 'b_picks', label: 'Again', from: 'calories/foods', log: 'calories/meals', fields: ['name', 'calories', 'protein'] },
          { kind: 'list', id: 'b_meals_today', label: 'Today', source: 'calories/meals', fields: ['meal', 'calories', 'protein'], sort: { field: 'at', dir: 'asc' }, where: [E('at', 'within', 'today')] }]),
        ...spec.tabs.filter((t) => t.id !== 't_today')] },
      values: seed ? { b_ring: { text: '1,140', target: 'of 2,200', pct: 52, sub: '70 g protein' }, ...values } : values,
      status: seed ? '**1,140** of 2,200 today across **3** meals.' : undefined };
    case 'cycle': return {
      spec: { ...spec, tabs: [
        P('t_month', 'Month', [{ kind: 'month', id: 'b_month', source: 'cycle/days', dateField: 'date', mark: 'flow', fields: ['flow', 'energy', 'symptoms'] }]),
        P('t_cycles', 'Cycles', [{ kind: 'list', id: 'b_cycles', source: 'cycle/cycles', fields: ['length'], sort: { field: 'start', dir: 'desc' } }])] },
      values, status: seed ? 'Last period started **Tue 27 Oct**.' : undefined };
    case 'classes': return {
      spec: { ...spec, tabs: [
        P('t_week', 'This week', [{ kind: 'days', id: 'b_week', source: '*dated', views: ['week'], view: 'week', apps: ['classes'] }]),
        P('t_due', 'Due', [{ kind: 'checklist', id: 'b_due', source: 'classes/due', fields: ['class', 'at'], due: 'at',
          groups: [{ label: 'Coming up', where: [E('done', 'eq', false), E('kind', 'eq', 'assignment')] }, { label: 'Done · {n}', where: [E('done', 'eq', true)], done: true, collapsed: true }],
          swipe: { right: 'complete' } }]),
        ...spec.tabs.filter((t) => t.id === 't_exams')] },
      data: { '*dated': DATED.filter((r) => r.app === 'classes') },
      values, status: seed ? '**2** due this week. Next: Start CS 3500 project, **Mon 23 Nov**.' : undefined };
    case 'subscriptions': return {
      spec: { ...spec, tabs: [P('t_subs', 'Subscriptions', [
        { kind: 'gauge', id: 'b_total', label: 'A month', value: spec.face.value, target: 0, format: 'money' },
        { kind: 'list', id: 'b_renewals', label: 'Renewals', source: 'subscriptions/subscriptions', fields: ['every'], sort: { field: 'renews', dir: 'asc' }, due: 'renews' }])] },
      values: { ...values, b_total: { text: '$38.46', target: 'a month · 4 subscriptions' } },
      status: seed ? 'Next: **Spotify** renews **Sun 22 Nov**, $11.99.' : undefined };
    case 'notes': return { spec, values, status: seed ? '**3** notes this week.' : undefined };
    default: return { spec, values };
  }
}
// ------------------------------------------------------------------ Links (Nov 20, spec/backend.md §2, §10)
// Links made by hand ("Link to…"), stored on the record as `_links` (LinkRef: app, ref, id, title). Links typed as [[Title]] in a text field are
// not listed here: the server stores them when the text is saved, and the mock resolves them on read. `_backlinks` are derived, never stored.
// Titles come from the seed rows themselves, so they cannot drift from the rows.
const THRIFT = spendRows.find((r) => r.properties.note === 'Thrift shop').id;
const LINKS = [
  ['n_7', 'd02'], // Finals study plan → Homework 11 (Classes)
  ['n_2', THRIFT], // Gift ideas for mom → the thrift shop spend (Budget)
  ['t_library', 'c01'], // Return library books → ECON 1010 (Classes)
  ['t_call_home', 'n_2'], // Call home → Gift ideas for mom (Notes)
  ['i_chicken_thighs', 'n_8'], // Chicken thighs on Weekly shop → the Chicken and rice note (Notes)
];
{
  const idx = new Map(); // record id → {app, ref, title}
  for (const [key] of APPS) {
    const r = OUTBOX.get('app.' + key);
    for (const c of r.spec.collections) {
      const tf = c.fields.find((x) => x.key === c.titleField);
      if (tf?.type === 'relation') continue; // a title that is another row's title (Workout sets) is not a title to link by
      for (const row of r.data[`${key}/${c.key}`] ?? []) {
        const v = row.properties[c.titleField];
        idx.set(row.id, { app: key, ref: `${key}/${c.key}`, title: tf?.type === 'select' ? tf.options.find((o) => o.id === v)?.label ?? String(v) : String(v) });
      }
    }
  }
  const out = new Map(); // from id → LinkRef[]
  for (const [from, to] of LINKS) {
    if (!idx.has(from)) throw new Error(`link source ${from} is not a seeded record`);
    if (!idx.has(to)) throw new Error(`link target ${to} is not a seeded record`);
    const { app, ref, title } = idx.get(to);
    out.set(from, [...(out.get(from) ?? []), { app, ref, id: to, title }]);
  }
  for (const [name, r] of OUTBOX) {
    if (!name.startsWith('app.') || !r.data) continue;
    for (const rows of Object.values(r.data)) for (const row of rows) if (row.properties && out.has(row.id)) row.properties._links = out.get(row.id);
  }
}

for (const [name, data] of OUTBOX) writeFileSync(join(OUT, name + '.json'), JSON.stringify(data, null, 1) + '\n');
console.log('fixtures written to', OUT);
