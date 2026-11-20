import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { dyeOf, RM, sleep, STAGGER, stitchIn, T } from '../lib/motion';
import { clearPeek, peekSinking, useStore } from '../lib/store';
import { Icon } from './Icon';
import { Roll } from './Roll';
import { Tag } from './Tag';

/**
 * Apps that changed but can't be seen creep up above the bar: their tiles rise from
 * behind it (T.layout, 40 ms apart), a stitch sews around each, the number rolls and
 * "just now" scales in; after a beat they sink (T.stateOut) and the receipt capsule rises out of the bar as they
 * fold into it: it is released 80 ms before the sink ends (peekSinking). Three at most, then "+N".
 * Undo raises them the same way with the seam pulling out and the numbers rolling back.
 * Reduced motion: they fade in, the values swap, they fade out.
 */
export function Peek() {
  const p = useStore((s) => s.peek);
  const apps = useStore((s) => s.home?.apps) ?? [];
  const [vals, setVals] = useState<Record<string, string>>({});
  const [landed, setLanded] = useState<Record<string, boolean>>({});
  const [on, setOn] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // rise on the frame the tiles mount: commit the sunk state, then flip the class (no double rAF)
  useLayoutEffect(() => {
    if (!p) return;
    ref.current?.getBoundingClientRect();
    setOn(true);
  }, [p?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!p) return;
    let alive = true;
    const shown = p.items.slice(0, 3);
    setVals(Object.fromEntries(p.items.map((i) => [i.app, i.from])));
    setLanded({});
    (async () => {
      await sleep(RM() ? T.fb : T.layout + STAGGER[Math.min(shown.length - 1, 2)]);
      if (!alive || !ref.current) return;
      const tiles = [...ref.current.querySelectorAll('.peek-tile')];
      await stitchIn({
        els: tiles.map((el) => ({ el, color: dyeOf(el) })),
        reverse: p.reverse,
        alive: () => alive,
        onLand: (i) => {
          const it = shown[i];
          if (!it) return;
          setVals((v) => ({ ...v, [it.app]: it.to }));
          if (!p.reverse) setLanded((l) => ({ ...l, [it.app]: true }));
        },
      });
      await sleep(p.reverse ? T.land : T.hold);
      if (!alive) return;
      setOn(false);
      await sleep(RM() ? 0 : T.stateOut - 80);
      if (alive) peekSinking(p.id); // the capsule overlaps the last 80 ms of the sink
      await sleep(RM() ? T.fb : 80);
      if (alive) clearPeek(p.id);
    })();
    return () => { alive = false; };
  }, [p?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!p) return null;
  const shown = p.items.slice(0, 3), more = p.items.length - shown.length;
  return (
    <div ref={ref} className={`peek ${on ? 'on' : ''}`} role="status" aria-label={`${p.reverse ? 'Put back' : 'Updated'}: ${p.items.map((i) => apps.find((a) => a.key === i.app)?.name ?? i.app).join(', ')}`}>
      {shown.map((it, i) => {
        const a = apps.find((x) => x.key === it.app);
        return (
          <span key={it.app} className="peek-tile" data-dye={a?.dye} style={{ transitionDelay: on ? `${STAGGER[Math.min(i, 2)]}ms` : '0ms' }}>
            <span className="top"><Icon name={a?.icon ?? 'app'} size={18} /><Tag show={!!landed[it.app]} /></span>
            <span className="name">{a?.name ?? it.app}</span>
            <span className="face"><Roll text={vals[it.app] ?? it.from} className="num" /><span className="unit">{a?.face.label}</span></span>
          </span>
        );
      })}
      {more > 0 && <span className="peek-more">+{more}</span>}
    </div>
  );
}
