import { useState } from 'react';
import { Button, Calendar, CalendarCell, CalendarGrid, CalendarGridBody, CalendarGridHeader, CalendarHeaderCell, DateInput, DateSegment, Heading, I18nProvider, TimeField } from 'react-aria-components';
import { parseDate, Time } from '@internationalized/date';
import { addDays, day, dayKey, when } from '../lib/format';
import { Disclosure } from './Disclosure';
import { Icon } from './Icon';
import '../styles/datetime.css';

/**
 * A date, and a time only when the field asks for one, in the add and edit sheet.
 *
 * Values are what the form already held: "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM", no offset (the server reads the wall time in the
 * workspace zone, spec/backend.md §3). "Today" is the server's `now`, never the device clock: react-aria is never asked for it
 * (the calendar's own "today" mark is ignored and drawn from `now`).
 *
 *  - `kind: 'date'`            a day, nothing else.
 *  - `kind: 'datetime'`        a day and a time; the time starts at the next whole hour today, 9 am any other day.
 *  - `timeOptional`            a day, with an "Add a time" switch (a due date: most have no time).
 *  - `allDay`                  a day and a time, with an "All day" switch (an event); all day is stored as the day alone.
 * An echo line always says what was chosen in the words the rows use ("Fri 20 Nov, 6:00 pm"), so the time is never a guess.
 */
type Props = {
  id: string; labelId: string; value: string; onChange: (v: string) => void; now: string;
  kind: 'date' | 'datetime'; timeOptional?: boolean; allDay?: boolean;
  /** a "Now" chip (a log of something that just happened); not offered when editing */
  showNow?: boolean;
};

const p2 = (n: number) => String(n).padStart(2, '0');

export function DateTimeField({ id, labelId, value, onChange, now, kind, timeOptional, allDay, showNow }: Props) {
  const [open, setOpen] = useState(false);
  const today = now ? dayKey(now) : '';
  const date = value.slice(0, 10);
  const hasTime = value.length > 10;
  const time = hasTime ? value.slice(11, 16) : '';
  const optional = !!(timeOptional || allDay); // the time can be absent
  const showTime = kind === 'datetime' && !!date && (optional ? hasTime : true);
  const toggle = kind === 'datetime' && optional ? (allDay ? 'allday' : 'time') : null;

  // the time a day starts with: the next whole hour when it is today (never already past), 9 am otherwise
  const startTime = (d: string) => (d === today ? `${p2(Math.min(23, (parseInt(now.slice(11, 13), 10) || 0) + 1))}:00` : '09:00');
  const withDay = (d: string) => {
    if (kind === 'date') return d;
    if (optional) return hasTime ? `${d}T${time}` : d;
    return `${d}T${time || startTime(d)}`;
  };
  const withTime = (hh: number, mm: number) => `${date}T${p2(hh)}:${p2(mm)}`;

  const [hh, mm] = time ? [parseInt(time.slice(0, 2), 10), parseInt(time.slice(3, 5), 10)] : [0, 0];
  const quick: [string, string][] = [['Today', today], ['Tomorrow', today && addDays(today, 1)]];
  if (showNow && kind === 'datetime' && now) quick.unshift(['Now', now.slice(0, 16)]);
  const pickQuick = (q: string) => onChange(q.length > 10 ? q : withDay(q));

  const echo = date ? (toggle === 'allday' && !hasTime ? `${day(date)} · All day` : when(value, now)) : kind === 'date' ? 'No day picked' : 'No day or time picked';

  return (
    <span className="dt" id={id}>
      <span className="chips">
        {quick.map(([t, q]) => <button type="button" key={t} className="chip pick" aria-pressed={dayKey(q) === date && (q.length <= 10 || value.startsWith(q))} onClick={() => pickQuick(q)}>{t}</button>)}
        <button type="button" className="chip pick dt-day" aria-expanded={open} aria-labelledby={`${labelId} ${id}_d`} onClick={() => setOpen((o) => !o)}>
          <span id={`${id}_d`}>{date ? day(date) : 'Pick a day'}</span>
          <Icon name="chev" size={16} sw={2} />
        </button>
      </span>

      <Disclosure open={open}>
        <I18nProvider locale="en-US">
          <Calendar className="dt-cal" aria-label="Pick a day" value={date ? parseDate(date) : null} defaultFocusedValue={today ? parseDate(today) : undefined}
            firstDayOfWeek="mon" onChange={(d) => { onChange(withDay(d.toString())); setOpen(false); }}>
            <header>
              <Button slot="previous" className="dt-nav" aria-label="Month before"><Icon name="back" size={18} sw={2} /></Button>
              <Heading />
              <Button slot="next" className="dt-nav" aria-label="Month after"><Icon name="fwd" size={18} sw={2} /></Button>
            </header>
            <CalendarGrid>
              <CalendarGridHeader>{(d) => <CalendarHeaderCell>{d}</CalendarHeaderCell>}</CalendarGridHeader>
              <CalendarGridBody>{(d) => <CalendarCell date={d} data-now={d.toString() === today ? '' : undefined} />}</CalendarGridBody>
            </CalendarGrid>
          </Calendar>
        </I18nProvider>
      </Disclosure>

      {toggle && (toggle === 'allday' || !!date) && (
        <span className="chips">
          <button type="button" className="chip pick" aria-pressed={toggle === 'allday' ? !!date && !hasTime : hasTime}
            onClick={() => {
              const d = date || today;
              if (!d) return;
              onChange(hasTime ? d : `${d}T${startTime(d)}`);
            }}>{toggle === 'allday' ? 'All day' : 'Add a time'}</button>
        </span>
      )}

      {showTime && (
        <span className="dt-time">
          <I18nProvider locale="en-US">
            <TimeField aria-label="Time" hourCycle={12} granularity="minute" value={new Time(hh, mm)}
              onChange={(t) => { if (t) onChange(withTime(t.hour, t.minute)); }}>
              <DateInput className="dt-seg">{(s) => <DateSegment segment={s} />}</DateInput>
            </TimeField>
          </I18nProvider>
          <span className="dt-ampm" role="radiogroup" aria-label="am or pm">
            <button type="button" role="radio" aria-checked={hh < 12} className="chip pick" onClick={() => hh >= 12 && onChange(withTime(hh - 12, mm))}>AM</button>
            <button type="button" role="radio" aria-checked={hh >= 12} className="chip pick" onClick={() => hh < 12 && onChange(withTime(hh + 12, mm))}>PM</button>
          </span>
        </span>
      )}

      <span className="dt-echo" aria-live="polite">{echo}</span>
    </span>
  );
}
