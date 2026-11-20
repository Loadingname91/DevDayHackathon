import { useFresh } from '../lib/fresh';
import { usePresence } from '../lib/presence';

/**
 * "just now" / "new" / "just changed": scales in from the left (220), fades out (140). In the app's own dye.
 * Pass `id` for a "just changed" marker so it lets go on its own after FRESH_MS (lib/fresh.ts); "new" tags omit it.
 */
export function Tag({ show, text = 'just now', id }: { show: boolean; text?: string; id?: string }) {
  const live = useFresh(id, show);
  const { ref, mounted } = usePresence<HTMLSpanElement>(show && live);
  return mounted ? <span ref={ref} className="pill now tag-in">{text}</span> : null;
}

/** The small dot version of the marker (Bar pins, Home's small patches); same expiry and exit as Tag. */
export function Notch({ show, id, className }: { show: boolean; id: string; className: string }) {
  const live = useFresh(id, show);
  const { ref, mounted } = usePresence<HTMLSpanElement>(show && live);
  return mounted ? <span ref={ref} className={className} aria-hidden="true" /> : null;
}
