import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorText, request } from '../api/client';
import type { CommandResult, Offer } from '../api/types';
import { EASE, RM, T } from '../lib/motion';
import { afterCommand, applyDelta, openClair, toast, useStore } from '../lib/store';
import { ChalkOl } from './Stitch';

/** "Do this every Sunday at 7 pm?": a chalk idea after a confirmed plan. Turn on writes the rule; no Clair call, no credits. */
export function OfferCard({ offer }: { offer: Offer }) {
  const app = useStore((s) => s.home?.apps.find((a) => a.key === offer.app));
  const [state, setState] = useState<'ask' | 'busy' | 'on' | 'gone'>('ask');
  const ref = useRef<HTMLDivElement>(null);
  const nav = useNavigate();
  useEffect(() => {
    const ol = ref.current?.querySelector('.ol');
    if (ol && !RM()) ol.animate([{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: T.layout, easing: EASE });
  }, []);
  if (state === 'gone') return null;
  const turnOn = async () => {
    setState('busy');
    try {
      const r = await request<CommandResult>('POST', `/apps/${offer.app}/workflows`, { sentence: offer.sentence, trigger: offer.trigger, action: offer.action });
      applyDelta(offer.app);
      await afterCommand(r);
      setState('on');
    } catch (e) { toast(errorText(e), undefined, 4000); setState('ask'); }
  };
  return (
    <div ref={ref} className="chalk arrive offer" data-dye={app?.dye}>
      <ChalkOl />
      {state === 'on' ? (
        <>
          <p className="say"><b>On.</b> {offer.sentence}.</p>
          <button className="link" onClick={() => { openClair(false); nav(`/a/${offer.app}?tab=t_workflows`); }}>{app?.name ?? offer.app} · Workflows ›</button>
        </>
      ) : (
        <>
          <p className="say"><b>{offer.prompt ?? 'Do this every week?'}</b><br />{offer.sentence}.</p>
          <span className="btns">
            <button className="cta" onClick={turnOn} disabled={state === 'busy'}>Turn on</button>
            <button className="ghost" onClick={() => setState('gone')} disabled={state === 'busy'}>Not now</button>
          </span>
        </>
      )}
    </div>
  );
}
