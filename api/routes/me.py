"""`GET /me` (backend.md §10, §8). Credits come from `usage_ledger` for the current month."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends

from .. import db
from ..auth import Member, current_member
from ..models import Credits, Me, User, Workspace, WorkspaceSettings
from ..settings import settings

router = APIRouter(tags=['me'])

SPENDS = ('chat', 'photo', 'build')


def server_now(tz: str) -> datetime:
    """Server time in the workspace zone; pinned to DEMO_NOW when it is set (backend.md §2.2)."""
    if settings().demo_now:
        return datetime.fromisoformat(settings().demo_now).astimezone(ZoneInfo(tz))
    return datetime.now(ZoneInfo(tz))


def month_start(now: datetime) -> date:
    return now.date().replace(day=1)


def next_month(d: date) -> date:
    return d.replace(year=d.year + (d.month == 12), month=d.month % 12 + 1)


def credits(conn, workspace_id, monthly: int, now: datetime) -> Credits:
    period = month_start(now)
    rows = conn.execute('select kind, coalesce(sum(credits), 0) as n from usage_ledger '
                        'where workspace_id = %s and period = %s group by kind', (workspace_id, period)).fetchall()
    by = {r['kind']: int(r['n']) for r in rows}
    granted = by.get('grant', 0) + by.get('topup', 0) or monthly
    spent = -sum(by.get(k, 0) for k in SPENDS) - by.get('refund', 0)
    return Credits(granted=granted, spent=max(spent, 0), left=granted - max(spent, 0), resets=next_month(period))


def load_me(m: Member) -> Me:
    with db.connect() as conn:
        w = conn.execute('select id, tz, epoch, read_level, settings from workspaces where id = %s', (m.workspace_id,)).fetchone()
        mem = conn.execute('select display_name from workspace_members where workspace_id = %s and user_id = %s',
                           (m.workspace_id, m.user.id)).fetchone()
        s = w['settings'] or {}
        now = server_now(w['tz'])
        monthly = int(s.get('credits_monthly', 50))
        cr = credits(conn, m.workspace_id, monthly, now)
    return Me(
        user=User(id=str(m.user.id), display_name=mem and mem['display_name'], email=m.user.email),
        is_anonymous=m.user.is_anonymous,
        workspace=Workspace(id=str(w['id']), tz=w['tz'], epoch=w['epoch'], read_level=w['read_level'],
                            settings=WorkspaceSettings(pins=[str(p) for p in s.get('pins', [])], credits_monthly=monthly,
                                                       notes_enabled=bool(s.get('notes_enabled', True)))),
        credits=cr,
        server_now=now,
    )


@router.get('/me', response_model=Me, operation_id='get_me')
def get_me(m: Member = Depends(current_member)) -> Me:
    return load_me(m)
