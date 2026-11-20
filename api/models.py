"""Contract models: every body that crosses the seam between `web/` and `api/`.

Sources, in order of authority (spec/split.md §2): spec/backend.md §10, §5, §7, §2 intro;
spec/ui-tech-plan.md §3 and §4; spec/clair-agent.md §2; spec/workflows.md "Engine v1".
Where the spec is silent the shapes follow web/src/api/types.ts ("assumed" fields), and
each such choice is logged in spec/split.md §7.

Conventions (backend.md §2): money is integer cents; datetimes are ISO 8601 with offset;
dates are YYYY-MM-DD. Field names are the wire names (camelCase where the contract uses it);
Python keywords use an alias (`from_` is sent as `from`).
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal, Union

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Model(BaseModel):
    """Closed object: unknown keys are a contract bug, not something to ignore."""

    model_config = ConfigDict(extra='forbid', populate_by_name=True)


# ---------------------------------------------------------------------------
# Scalars and shared names
# ---------------------------------------------------------------------------

Scalar = Union[str, int, float, bool]
CollectionRef = Annotated[
    str, Field(description='"<app key>/<collection key>" ("groceries/items"), or "*dated" (backend.md §3)')
]
DateOrDatetime = Annotated[str, Field(description='YYYY-MM-DD, or ISO 8601 datetime with offset')]
Dye = Literal['butter', 'sage', 'sea glass', 'apricot', 'chambray', 'lavender', 'pear', 'blush', 'linen']
Print = Literal['solid', 'gingham', 'stripe', 'dot']
Format = Literal['money', 'count', 'number', 'duration', 'text']
ChangeSetStatus = Literal['basted', 'stitched', 'undone', 'dismissed']


# ---------------------------------------------------------------------------
# Formula grammar (backend.md §6, ui-tech-plan.md §3)
# ---------------------------------------------------------------------------

class Filter(Model):
    """`within` takes today, week, past, future, 7d, -7d (72h server only); `empty` ignores `value`."""

    field: str
    op: Literal['eq', 'ne', 'lt', 'gt', 'within', 'empty']
    value: Scalar


class WindowDays(Model):
    """The last N days up to now (backend.md §6)."""

    days: int = Field(ge=1)


class Query(Model):
    agg: Literal['sum', 'count', 'avg', 'min', 'max', 'last']
    from_: CollectionRef = Field(alias='from')
    field: str | None = None
    where: list[Filter] | None = None
    window: Literal['today', 'week', 'month', 'all'] | WindowDays | None = None


class SettingTerm(Model):
    """A value from the app's `settings` (`{setting: "limit"}`)."""

    setting: str


class OptionLimitRef(Model):
    field: str
    option: str


class OptionLimitTerm(Model):
    """The `limit` stored on a select option (backend.md §6)."""

    limit: OptionLimitRef


Term = Union[int, float, Query, SettingTerm, OptionLimitTerm]


class Minus(Model):
    """One level only, never recursive."""

    minus: tuple[Term, Term]


Value = Union[Term, Minus]


# ---------------------------------------------------------------------------
# AppSpec: collections and fields (ui-tech-plan.md §3 + backend.md §2 intro)
# ---------------------------------------------------------------------------

class Option(Model):
    """A select option. Records store `id`; `hint` is display only; `limit` in cents (Budget categories)."""

    id: str
    label: str
    hint: str | None = None
    limit: int | None = None


class FieldSpec(Model):
    """A collection field. `relation` needs `target`; `formula` needs `op`, `a`, `b` (backend.md §6)."""

    key: str
    label: str
    type: Literal['text', 'number', 'money', 'date', 'datetime', 'bool', 'select', 'relation', 'formula', 'repeat', 'file']
    options: list[Option] | None = None
    required: bool | None = None
    target: CollectionRef | None = None
    unit: str | None = Field(None, description='Display unit for number fields ("mi", "min")')
    unitFirst: bool | None = Field(None, description='"energy 2" rather than "2 energy"')
    op: Literal['add', 'sub', 'mul', 'div'] | None = None
    a: str | float | None = None
    b: str | float | None = None
    output: Format | None = None
    many: bool | None = Field(None, description='relation: a record may point at several targets (a note in several notebooks). Default one; the value is an array of record ids either way')
    multiline: bool | None = Field(None, description='text: a textarea; `[[Title]]` in it links to that record (backend.md section 5)')


class Collection(Model):
    """Data, not UI. Stored as a collection block under the page (backend.md §2)."""

    id: str | None = Field(None, description='The collection block id; sent by the server, used by /collections/{id}/options and POST /records')
    key: str
    name: str
    fields: list[FieldSpec]
    titleField: str
    dateField: str | None = None
    amountField: str | None = None
    calendar: bool | None = None
    label: str | None = Field(None, description='Singular name on Calendar rows ("Grocery trip")')
    datedTitle: str | None = Field(None, description='Title template for this collection\'s Calendar rows, e.g. "{name} renews · {amount}"')


# ---------------------------------------------------------------------------
# AppSpec: blocks (ui-tech-plan.md §3, base blocks + instruments + workflows)
# ---------------------------------------------------------------------------

class Sort(Model):
    field: str
    dir: Literal['asc', 'desc']


class Swipe(Model):
    right: Literal['complete'] | None = None
    left: Literal['delete'] | None = None


class ViewBase(Model):
    id: str
    source: CollectionRef
    fields: list[str] | None = None
    where: list[Filter] | None = None
    sort: Sort | None = None
    group: str | None = None
    swipe: Swipe | None = None
    switch: str | None = None
    addAt: Literal['start', 'end'] | None = None
    label: str | None = None
    limit: int | None = None
    due: str | None = None


class TextBlock(Model):
    kind: Literal['text']
    id: str
    text: str


class MetricBlock(Model):
    kind: Literal['metric']
    id: str
    label: str
    value: Value
    format: Format
    compare: Value | None = None


class ProgressBlock(Model):
    kind: Literal['progress']
    id: str
    label: str
    value: Value
    target: Value
    format: Format


class ListBlock(ViewBase):
    kind: Literal['list']


class TableBlock(ViewBase):
    kind: Literal['table']


class CalendarBlock(ViewBase):
    kind: Literal['calendar']
    window: Literal['today', 'week'] | None = None


class FormBlock(Model):
    kind: Literal['form']
    id: str
    collection: CollectionRef
    fields: list[str]
    submit: str


class ChartBlock(Model):
    kind: Literal['chart']
    id: str
    type: Literal['bar', 'line']
    from_: CollectionRef = Field(alias='from')
    x: str
    y: Query
    window: Literal['week', 'month']


class WorkflowsBlock(Model):
    """The rules tab; the server adds it as a last tab named Workflows (workflows.md)."""

    kind: Literal['workflows']
    id: str


class GaugeLink(Model):
    app: str
    text: str


class GaugeBlock(Model):
    kind: Literal['gauge']
    id: str
    label: str
    value: Value
    target: Value
    format: Format
    link: GaugeLink | None = None


class BarsBlock(Model):
    kind: Literal['bars']
    id: str
    label: str
    from_: CollectionRef = Field(alias='from')
    by: str
    value: Query


class RingBlock(Model):
    kind: Literal['ring']
    id: str
    label: str
    value: Value
    target: Value
    format: Format


class CountdownBlock(Model):
    kind: Literal['countdown']
    id: str
    source: CollectionRef


class StripBlock(Model):
    kind: Literal['strip']
    id: str
    label: str
    value: Query


class PicksBlock(Model):
    kind: Literal['picks']
    id: str
    label: str
    from_: CollectionRef = Field(alias='from')
    log: CollectionRef
    fields: list[str]


class ChecklistGroup(Model):
    """Label tokens: {today}, {n}, {option}."""

    label: str
    where: list[Filter]
    done: bool | None = None
    collapsed: bool | None = None


class ChecklistAdd(Model):
    placeholder: str
    set: dict[str, Scalar] | None = None
    pinned: bool | None = None


class ChecklistBlock(Model):
    kind: Literal['checklist']
    id: str
    source: CollectionRef
    fields: list[str] | None = None
    switch: str | None = None
    due: str | None = None
    groups: list[ChecklistGroup]
    add: ChecklistAdd | None = None
    swipe: Swipe | None = None


DayView = Literal['day', 'week', 'month']


class DaysBlock(Model):
    kind: Literal['days']
    id: str
    source: CollectionRef
    views: list[DayView]
    view: DayView
    apps: list[str] | None = None


class NextBlock(Model):
    kind: Literal['next']
    id: str
    source: CollectionRef
    log: CollectionRef
    fields: list[str]


class TimerBlock(Model):
    kind: Literal['timer']
    id: str
    label: str
    mode: Literal['countdown', 'stopwatch']
    log: CollectionRef
    minutesField: str
    kindField: str | None = None
    presets: list[int] | None = None
    moodFields: tuple[str, str] | None = None
    after: list[str] | None = None
    set: dict[str, Scalar] | None = None


class MonthBlock(Model):
    kind: Literal['month']
    id: str
    source: CollectionRef
    dateField: str
    mark: str
    fields: list[str]


class NotebookBlock(Model):
    """A notes workspace: a tree of `source` rows (notebooks) with the `pages` rows in them; `link` is the pages' (many) relation
    to `source` and `body` their multiline text (ui-tech-plan.md section 3 "Notebook")."""

    kind: Literal['notebook']
    id: str
    source: CollectionRef
    pages: CollectionRef
    link: str
    body: str


LeafBlock = Annotated[
    Union[
        TextBlock, MetricBlock, ProgressBlock, ListBlock, TableBlock, CalendarBlock, FormBlock, ChartBlock,
        WorkflowsBlock, GaugeBlock, BarsBlock, RingBlock, CountdownBlock, StripBlock, PicksBlock,
        ChecklistBlock, DaysBlock, NextBlock, TimerBlock, MonthBlock, NotebookBlock,
    ],
    Field(discriminator='kind'),
]


class PageBlock(Model):
    """A tab. Pages don't nest."""

    kind: Literal['page']
    id: str
    title: str
    children: list[LeafBlock]


# ---------------------------------------------------------------------------
# Rules (spec/workflows.md, Engine v1)
# ---------------------------------------------------------------------------

class ScheduleTrigger(Model):
    kind: Literal['schedule']
    rule: str = Field(description='RRULE subset, weekly or daily ("FREQ=WEEKLY;BYDAY=SU")')
    at: str = Field(pattern=r'^\d{2}:\d{2}$', description='Time of day in the workspace zone, "19:00"')


class RowAddedTrigger(Model):
    kind: Literal['row_added']
    collection: CollectionRef
    where: list[Filter] | None = None


class FieldChangedTrigger(Model):
    kind: Literal['field_changed']
    collection: CollectionRef
    field: str
    to: Scalar
    where: list[Filter] | None = None


Trigger = Annotated[Union[ScheduleTrigger, RowAddedTrigger, FieldChangedTrigger], Field(discriminator='kind')]


class AskClairAction(Model):
    kind: Literal['ask_clair']
    text: str


class MapDate(Model):
    """A date taken from the triggering row's field, moved by an offset ("-2d", "3h")."""

    from_: str = Field(alias='from')
    offset: str = Field(pattern=r'^-?\d+[dh]$')


class WriteRowAction(Model):
    """`map` values: fixed text, "{field}" templates from the triggering row, or a MapDate."""

    kind: Literal['write_row']
    collection: CollectionRef
    map: dict[str, Union[MapDate, Scalar]]


Action = Annotated[Union[AskClairAction, WriteRowAction], Field(discriminator='kind')]


class Workflow(Model):
    id: str
    sentence: str
    on: bool
    trigger: Trigger
    action: Action
    runs: str | None = Field(None, description='Server-worded run line, "ran 2 times this week · last run Sun 7:00 pm"')
    next_run: AwareDatetime | None = Field(None, description='Only once scheduled firing (ladder step 5) is deployed')


# ---------------------------------------------------------------------------
# AppSpec
# ---------------------------------------------------------------------------

class StitchMap(Model):
    to: str
    from_: str | None = Field(None, alias='from')
    const: Scalar | None = None


class Stitch(Model):
    """Declared on the receiving app (backend.md §5)."""

    from_: CollectionRef = Field(alias='from')
    to: CollectionRef
    map: list[StitchMap]
    where: list[Filter] | None = None
    on: Literal['insert', 'occurrence'] | None = Field(None, description='Default insert; occurrence fires on each passed occurrence')


class FaceSpec(Model):
    value: Value
    format: Format
    label: str
    status: bool | None = None


class AppSpec(Model):
    """The app as the renderer draws it. `id` is the page block id; `key` is the slug."""

    v: Literal[1]
    id: str
    key: str
    name: str
    icon: str
    dye: Dye
    print: Print | None = None
    private: bool | None = None
    settings: dict[str, Scalar | None] | None = None
    collections: list[Collection]
    tabs: list[PageBlock]
    face: FaceSpec
    stitches: list[Stitch] | None = None
    workflows: list[Workflow] | None = None
    version: int | None = Field(None, description='The page block version; send it back as base_version on PATCH /apps/{id}')


class NewAppSpec(AppSpec):
    """`POST /apps`: the server assigns the page block id."""

    id: str | None = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Data on the wire: records, blocks, dated rows, faces, values
# ---------------------------------------------------------------------------

class Record(Model):
    """A record block as `GET /apps/{id}` sends it. `properties` keys starting with `_` are system data (`_via`)."""

    id: str
    position: str
    version: int
    properties: dict[str, Any]
    example: bool | None = Field(None, description='A sample row in a build preview; never saved')


class Block(Model):
    """Any stored block (backend.md §2.1), as command results and /sync send changed blocks."""

    id: str
    block_type: Literal['page', 'collection', 'record']
    parent_id: str | None
    collection_id: str | None
    position: str
    version: int
    properties: dict[str, Any]
    deleted_at: AwareDatetime | None = None


class Dated(Model):
    """A row of the virtual `*dated` source (backend.md §3, §8a)."""

    at: DateOrDatetime
    title: str
    sub: str
    app: str
    record_id: str
    occurrence: date | None = None
    ends: DateOrDatetime | None = None
    all_day: bool | None = None
    source: str | None = Field(None, description='"google" for imported events (read-only)')
    changed: bool | None = Field(None, description='Touched by the last change ("just now")')


class Face(Model):
    """A computed face (backend.md §5, §7). `value` is the raw number (cents for money)."""

    text: str
    label: str
    value: int | float | None = None


class BarRow(Model):
    label: str
    text: str
    pct: int | None = None
    over_pct: int | None = None
    note: str | None = None


class StripDay(Model):
    dow: str
    text: str | None = None
    on: bool | None = None
    today: bool | None = None


class Best(Model):
    reps: int
    weight: float
    text: str


class Step(Model):
    id: str
    name: str
    plan: str
    sets: int
    reps: int
    weight: float
    unit: str
    best: Best | None = None


class BlockValue(Model):
    """`values[block.id]`: what the server computed for a metric, progress or instrument block (backend.md §10)."""

    text: str | None = None
    sub: str | None = None
    target: str | None = None
    pct: int | None = None
    over: str | None = None
    over_pct: int | None = None
    title: str | None = None
    unit: str | None = None
    note: str | None = None
    rows: list[BarRow] | None = None
    days: list[StripDay] | None = None
    eyebrow: str | None = None
    meta: str | None = None
    action: str | None = None
    record_id: str | None = None
    occurrence: date | None = None
    rest: int | None = Field(None, description='Seconds between sets')
    steps: list[Step] | None = None
    link: str | None = None


class Patch(Model):
    """An app on Home (`GET /home`, `GET /apps`)."""

    id: str
    key: str
    name: str
    icon: str
    dye: Dye
    print: Print | None = None
    face: Face
    changed: bool
    lastOpened: AwareDatetime | None
    pinned: bool
    isNew: bool | None = None


class AppDetail(Model):
    """`GET /apps/{id}`, and a build card's `preview` (seq 0)."""

    spec: AppSpec
    data: dict[str, list[Union[Record, Dated]]] = Field(description='Keyed by CollectionRef; "*dated" holds Dated rows')
    faces: dict[str, Face]
    values: dict[str, BlockValue] | None = None
    status: str | None = Field(None, description='The app sentence; ** marks figures')
    seq: int
    server_now: AwareDatetime


# ---------------------------------------------------------------------------
# Change sets and cards (ui-tech-plan.md §4, backend.md §5, §10)
# ---------------------------------------------------------------------------

class Via(Model):
    app: str | None = None
    record_id: str | None = None
    workflow: str | None = None


class OpReasons(Model):
    reason: str | None = None
    reason_source: str | None = None
    also: str | None = None
    also_source: str | None = None
    via: Via | None = Field(None, description='Set on ops the server derived in `expanded` (stitch or rule)')


class InsertOp(OpReasons):
    op: Literal['insert']
    ref: CollectionRef
    values: dict[str, Any]
    record_id: str | None = Field(None, description='Temp name ("new:trip") other ops in the set may reference')


class UpdateOp(OpReasons):
    op: Literal['update']
    rowId: str
    values: dict[str, Any]


class DeleteOp(OpReasons):
    op: Literal['delete']
    rowId: str


class FieldValue(Model):
    key: str
    value: str


class MoveOccurrenceOp(OpReasons):
    """backend.md §3: skip one occurrence of a series and insert a one-off at the new date."""

    op: Literal['move_occurrence']
    app: str | None = None
    collection: str | None = None
    record_id: str
    occurrence: date
    fields: list[FieldValue]


class KeepOp(OpReasons):
    """A planned occurrence shown as kept; writes nothing (clair-agent.md §12.9 `keep: true`)."""

    op: Literal['keep']
    record_id: str
    occurrence: date


RowOp = Annotated[Union[InsertOp, UpdateOp, DeleteOp, MoveOccurrenceOp, KeepOp], Field(discriminator='op')]


class ChangeSource(Model):
    kind: Literal['text', 'voice', 'photo', 'file', 'insight', 'checkin', 'workflow', 'gesture', 'template', 'sweep', 'undo', 'seed']
    label: str
    at: AwareDatetime


class CardLine(Model):
    apps: list[str]
    what: str
    val: str
    sub: str | None = None


class Delta(Model):
    app: str
    before: str
    after: str


class CardActions(Model):
    primary: str
    secondary: str | None = None


class ReviewRow(Model):
    """One row of Review items, worded by the server."""

    title: str
    when: str
    change: Literal['kept', 'moved', 'new', 'changed', 'removed']
    reason: str | None = None
    source: str | None = None
    also: str | None = None
    also_source: str | None = None
    app: str


class RuleDraft(Model):
    """A rule card's rule (kind `rule`); Turn on saves it."""

    app: str
    sentence: str
    trigger: Trigger
    action: Action


class ChangeSet(Model):
    """ui-tech-plan.md §4 `Proposal`. `lines`, `expanded`, `targets`, `deltas`, `actions` are computed by the server on every read."""

    id: str
    status: ChangeSetStatus
    source: ChangeSource
    mode: Literal['live', 'fixture'] = 'live'
    title: str
    summary: str | None = None
    ops: list[RowOp]
    lines: list[CardLine]
    expanded: list[RowOp]
    targets: list[str]
    deltas: list[Delta]
    actions: CardActions
    flagged: bool = False
    version: int
    kind: Literal['records', 'app', 'rule'] = 'records'
    review: list[ReviewRow] | None = None
    preview: AppDetail | None = Field(None, description='kind app: the new app as it would open')
    rule: RuleDraft | None = Field(None, description='kind rule: the rule Turn on saves')


class ChangeSetCard(Model):
    kind: Literal['change_set']
    change_set: ChangeSet


class CheckinItem(Model):
    text: str
    app: str


class CheckinCard(Model):
    kind: Literal['checkin']
    id: str
    title: str
    items: list[CheckinItem]
    change_set: ChangeSet | None = None


class KeepCard(Model):
    kind: Literal['keep']


Card = Annotated[Union[ChangeSetCard, CheckinCard, KeepCard], Field(discriminator='kind')]


class ChangeSetPatch(Model):
    """`PATCH /change-sets/{id}` (Review items)."""

    ops: list[RowOp]
    version: int


# ---------------------------------------------------------------------------
# Command result (backend.md §5)
# ---------------------------------------------------------------------------

class ChangedSince(Model):
    block_id: str
    field: str
    now: Any
    was: Any


class ChangedSinceWarning(Model):
    changed_since: ChangedSince


class SupersededWarning(Model):
    superseded: str


Warning = Union[ChangedSinceWarning, SupersededWarning]


class CommandResult(Model):
    change_set_id: str
    server_seq: int
    blocks: list[Block]
    faces: dict[str, Face]
    warnings: list[Warning]


# ---------------------------------------------------------------------------
# Home and sync (backend.md §10, §7)
# ---------------------------------------------------------------------------

class Insight(Model):
    id: str
    text: str
    apps: list[str]
    proposal: ChangeSet | None = None


class Home(Model):
    greeting: str
    status: str
    needsOk: list[Card]
    nextUp: list[Dated]
    noticed: Insight | None = None
    apps: list[Patch]
    seq: int
    server_now: AwareDatetime


class SyncResponse(Model):
    seq: int
    epoch: int
    server_now: AwareDatetime
    blocks: list[Block]
    change_sets: list[ChangeSet]
    faces: dict[str, Face]
    touched_apps: list[str]


# ---------------------------------------------------------------------------
# System, me, workspace, credits (backend.md §10, §8)
# ---------------------------------------------------------------------------

class Health(Model):
    ok: bool
    db: bool
    version: str


class User(Model):
    id: str
    display_name: str | None
    email: str | None = None


ReadLevel = Literal['full', 'field_names', 'none']


class WorkspaceSettings(Model):
    pins: list[str]
    credits_monthly: int
    notes_enabled: bool


class Workspace(Model):
    id: str
    tz: str
    epoch: int
    read_level: ReadLevel = 'full'
    settings: WorkspaceSettings


class Credits(Model):
    granted: int
    spent: int
    left: int
    resets: date | None = None


class BootstrapRequest(Model):
    tz: str | None = None


class BootstrapResponse(Model):
    user: User
    is_anonymous: bool
    workspace: Workspace
    credits: Credits


class Me(BootstrapResponse):
    server_now: AwareDatetime


class MePatch(Model):
    display_name: str | None = None


class MePatchResponse(Model):
    user: User
    workspace: Workspace


class SettingsPatch(Model):
    tz: str | None = None
    read_level: ReadLevel | None = None
    pins: list[str] | None = None


class SettingsResponse(Model):
    workspace: Workspace


class Usage(Model):
    period: str = Field(description='"2026-11"')
    granted: int
    spent: int
    left: int


# ---------------------------------------------------------------------------
# Google connection (backend.md §8a)
# ---------------------------------------------------------------------------

class ConnectStart(Model):
    url: str = Field(description='Google\'s consent URL; the client navigates the whole page there. In fixture mode '
                                 '(DEMO_GCAL_FIXTURE=1) a site path, "/app/calendar?connected=google"')
    connected: bool | None = Field(None, description='True when the connection was made by this call (fixture mode): '
                                                     'there is no consent page to visit')


class Connection(Model):
    provider: Literal['google']
    account_email: str
    last_synced_at: AwareDatetime | None
    needs_reconnect: bool


class ConnectSyncResult(Model):
    added: int
    changed: int
    removed: int
    last_synced_at: AwareDatetime


# ---------------------------------------------------------------------------
# Apps, collections, records, templates, workflows: request bodies (backend.md §10)
# ---------------------------------------------------------------------------

class AppCreate(Model):
    spec: NewAppSpec


class AppUpdate(Model):
    spec: AppSpec
    base_version: int


class Dependent(Model):
    app: str
    what: str


class OptionCreate(Model):
    field: str
    label: str


class OptionRename(Model):
    field: str
    label: str


class OptionDelete(Model):
    field: str
    items: str | None = Field(None, pattern=r'^(move:.+|delete)$', description='"move:<option_id>" or "delete"')


class RecordCreate(Model):
    collection_id: str = Field(description='Collection block id (or "app/collection" ref until ids ship)')
    fields: dict[str, Any]
    before_id: str | None = None
    after_id: str | None = None


class RecordUpdate(Model):
    fields: dict[str, Any]
    base_version: int


class RecordMove(Model):
    before_id: str | None = None
    after_id: str | None = None
    list: str | None = None


class RecordComplete(Model):
    occurrence: date | None = None
    minutes: int | None = None


class RecordSkip(Model):
    occurrence: date


class TemplatesApply(Model):
    templates: list[str]


class WorkflowCreate(Model):
    sentence: str
    trigger: Trigger
    action: Action


class WorkflowPatch(Model):
    on: bool


class RunStarted(Model):
    run_id: str


# ---------------------------------------------------------------------------
# Clair (clair-agent.md §2)
# ---------------------------------------------------------------------------

class TurnContext(Model):
    app: str
    collection: str | None = None
    record_id: str | None = None


class NewTurn(Model):
    thread_id: str | None = None
    run_id: str | None = Field(None, description='Client-made UUID; becomes agent_runs.id (polling fallback)')
    text: str | None = None
    transcript: str | None = None
    voice: bool = False
    images: list[str] = Field(default_factory=list, description='Storage paths, never file bodies')
    files: list[str] = Field(default_factory=list, description='Storage paths, never file bodies')
    context: TurnContext | None = None


class CardAnswer(Model):
    choices: list[str]
    other: str | None = None


class Answer(Model):
    """One question: `choices` (+ `other`). A card: `answers` keyed by question id. `skip`: "use your best guess"."""

    question_id: str
    choices: list[str] | None = None
    other: str | None = None
    answers: dict[str, CardAnswer] | None = None
    skip: bool | None = None


class AnswerTurn(Model):
    thread_id: str
    run_id: str | None = None
    answer: Answer


class FixtureTurn(Model):
    """Use sample: a recorded run replayed through the real pipeline, marked "sample"."""

    fixture: Literal['planner', 'receipt', 'fridge', 'lunch']
    run_id: str | None = None


ClairTurnRequest = Union[AnswerTurn, FixtureTurn, NewTurn]


class StatusData(Model):
    text: str


class UnderstoodData(Model):
    kind: str
    summary: str
    items: list[str] | None = None


class QuestionOption(Model):
    id: str
    label: str
    hint: str | None = None


class SingleQuestion(Model):
    """One menu question (clair-agent.md §2, the fridge)."""

    id: str
    text: str
    options: list[QuestionOption]
    multi: bool
    other: bool | None = Field(None, description='false hides the Other field')
    expires_at: AwareDatetime | None = None


class CardOptionInput(Model):
    placeholder: str
    numeric: bool | None = None


class CardOption(Model):
    label: str
    description: str | None = None
    input: CardOptionInput | None = Field(None, description='Only on single-select questions: the option takes a typed value')


class CardQuestion(Model):
    id: str
    header: str
    text: str
    options: list[CardOption] = Field(min_length=2, max_length=4)
    multi: bool
    other: bool | None = Field(None, description='false hides the Other row')


class QuestionCard(Model):
    """A card of 1 to 3 questions (clair-agent.md §2, §7 rule 7; the build questions)."""

    id: str
    questions: list[CardQuestion] = Field(min_length=1, max_length=3)
    plan_after: bool | None = Field(None, description='A `plan` event follows the answers')
    expires_at: AwareDatetime | None = None


QuestionData = Union[SingleQuestion, QuestionCard]


class NoteData(Model):
    text: str
    note_id: str | None = Field(None, description='For the chip Undo (DELETE /clair/notes/{id})')


class ProposalData(Model):
    change_set: ChangeSet


class OfferData(Model):
    """Held by the client until the change set is confirmed; Turn on posts it to /apps/{app}/workflows."""

    kind: Literal['workflow']
    app: str
    sentence: str
    trigger: Trigger
    action: Action
    prompt: str | None = Field(None, description='"Do this every Sunday at 7 pm?"')


class TextDeltaData(Model):
    text: str


class DoneData(Model):
    status: Literal['complete', 'awaiting_input', 'error']
    sources: list[str]
    spoken: str | None = None
    message: str | None = Field(None, description='Plain message for status error')


class StatusEvent(Model):
    event: Literal['status']
    data: StatusData


class UnderstoodEvent(Model):
    event: Literal['understood']
    data: UnderstoodData


class QuestionEvent(Model):
    event: Literal['question']
    data: QuestionData


class NoteEvent(Model):
    event: Literal['note']
    data: NoteData


class ProposalEvent(Model):
    event: Literal['proposal']
    data: ProposalData


class OfferEvent(Model):
    event: Literal['offer']
    data: OfferData


class PlanNewApp(Model):
    key: str
    name: str
    icon: str
    dye: Dye


class PlanLine(Model):
    app: str | None = None
    text: str


class PlanData(Model):
    """`plan` (clair-agent.md §2, §11): sent just before a build's `proposal`; the client holds the proposal behind it."""

    title: str
    new_app: PlanNewApp | None = None
    lines: list[PlanLine]
    private: bool | None = None


class PlanEvent(Model):
    event: Literal['plan']
    data: PlanData


class TextDeltaEvent(Model):
    event: Literal['text_delta']
    data: TextDeltaData


class DoneEvent(Model):
    event: Literal['done']
    data: DoneData


ClairEvent = Annotated[
    Union[StatusEvent, UnderstoodEvent, QuestionEvent, NoteEvent, PlanEvent, ProposalEvent, OfferEvent, TextDeltaEvent, DoneEvent],
    Field(discriminator='event'),
]


class RunEvents(Model):
    """`GET /clair/runs/{id}/events?after=n`: the polling fallback."""

    events: list[ClairEvent]
    last: int = Field(description='Index of the last event returned; pass as `after` next time')
    done: bool


class Thread(Model):
    id: str
    started_at: AwareDatetime
    last_at: AwareDatetime


class ThreadMessage(Model):
    role: Literal['user', 'clair']
    text: str
    at: AwareDatetime
    change_set_id: str | None = None


class LatestThread(Model):
    thread: Thread
    messages: list[ThreadMessage]


class Note(Model):
    id: str
    text: str
    kind: Literal['preference', 'fact']
    app: str | None = None
    created_at: AwareDatetime | None = None


# ---------------------------------------------------------------------------
# Search, join codes
# ---------------------------------------------------------------------------

class LinkRef(Model):
    """One end of a link between two records, in any app (backend.md section 2). `title` is the other record's title field, filled
    by the server; "(deleted)" for a deleted record. In `_backlinks`, `via` is the relation field that points here ("notebook")."""

    app: str
    ref: CollectionRef
    id: str
    title: str
    via: str | None = None


class SearchHit(Model):
    """A record that matched. `snippet` tells rows with the same title apart (amount and day for a spend, the time for an event,
    the first line of a note); it may be empty."""

    app: str
    ref: CollectionRef
    collection: str = Field(description='The collection key ("notes" in "notes/notes")')
    id: str
    title: str
    snippet: str
    updated: AwareDatetime | None = Field(None, description='When the record last changed')


class SearchResponse(Model):
    hits: list[SearchHit]


class LinkTarget(Model):
    ref: CollectionRef | None = Field(None, description='The target\'s collection; checked against the record when sent')
    id: str


class LinkCreate(Model):
    """`POST /records/{id}/links`: the target as `to: {ref, id}` (what the client sends) or as a bare `target_id`."""

    to: LinkTarget | None = None
    target_id: str | None = None


class JoinCode(Model):
    code: str
    expires_at: AwareDatetime


class JoinRedeem(Model):
    code: str


class JoinRedeemed(Model):
    email: str
    token_hash: str


# ---------------------------------------------------------------------------
# Error bodies (backend.md §10 "Status codes")
# ---------------------------------------------------------------------------

class ErrorBody(Model):
    error: str


class Issue(Model):
    loc: list[str | int]
    msg: str


class ValidationErrorBody(Model):
    """422: structural or semantic validation (backend.md §5 steps 3 and 4)."""

    error: str
    issues: list[Issue]


class StatusConflict(Model):
    """409 on a change-set transition: the current status."""

    error: str = 'status'
    status: ChangeSetStatus


class Conflict(Model):
    """409 for the other cases: version mismatch, items remain (`count`), dependents of an app, thread busy, rule off."""

    error: str
    count: int | None = None
    dependents: list[Dependent] | None = None
    version: int | None = None
