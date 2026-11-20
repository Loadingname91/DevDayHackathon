import { usePresence } from '../lib/presence';

/** "just now" / "new": scales in from the left (220), fades out (140). In the app's own dye. */
export function Tag({ show, text = 'just now' }: { show: boolean; text?: string }) {
  const { ref, mounted } = usePresence<HTMLSpanElement>(show);
  return mounted ? <span ref={ref} className="pill now tag-in">{text}</span> : null;
}
