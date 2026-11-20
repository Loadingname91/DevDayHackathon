import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  type Attachment, ATTACH_ONLY_TEXT, prepareImage, revokeThumbs, type Thumb, toRequest, uid, upload, UploadError, uploadMessage, validate,
} from '../../lib/attachments';

export { revokeThumbs, type Thumb };

export type AttachmentsApi = {
  list: Attachment[];
  /** Adds files (a picker, a drop, a paste): classified, checked, prepared and uploaded one by one. */
  add: (files: FileList | File[] | null | undefined) => void;
  remove: (id: string) => void;
  /** An upload that failed goes again (the prepared picture is kept). */
  retry: (id: string) => void;
  /** Empties the tray (a cancelled turn, or a send that failed to start). */
  clear: () => void;
  /**
   * Empties the tray after a send and hands the thumbnails to the turn: their object URLs are no longer revoked here, so the
   * understanding line can still draw them. The turn revokes them with `revokeThumbs` when it goes.
   */
  take: () => Thumb[];
  /** The uploaded ones as thumbnails, without emptying the tray: read before a send, then `take()` once it went. */
  peek: () => Thumb[];
  /** Something is still being prepared or uploaded. */
  busy: boolean;
  /** An upload failed and has not been retried or removed: sending would drop it silently, so Send waits. */
  stuck: boolean;
  /** Nothing is in flight and nothing is stuck: Send may go. */
  ready: boolean;
  /** At least one attachment would go with the turn. */
  hasSendable: boolean;
  /** The tray is full (5). */
  full: boolean;
  /** One plain line (a role="status" under the tray): "Up to 5 per message". Clears itself. */
  notice: string | null;
  /** The turn's `images` and `files`. */
  request: () => { images: string[]; files: string[] };
  /** What to send as `text` when the field is empty. */
  fallbackText: string;
};

const NOTICE_MS = 4000;

/**
 * State for the attachments of one Clair turn. A picture is prepared (scaled to 1568 px) and then uploaded at once, so by the
 * time Sam has typed the sentence it is already in Storage; `ready` says when Send may go. Unmounting aborts the work in flight
 * and revokes every object URL. `workspaceId` comes from `GET /me` (`me.workspace.id`).
 */
export function useAttachments(opts: { workspaceId?: string } = {}): AttachmentsApi {
  const [list, setList] = useState<Attachment[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const listRef = useRef(list);
  listRef.current = list;
  const ws = useRef(opts.workspaceId);
  ws.current = opts.workspaceId;
  const alive = useRef(false);
  const aborts = useRef(new Map<string, AbortController>());
  const queue = useRef<Promise<void>>(Promise.resolve()); // pictures are prepared one at a time: five 12 MP bitmaps at once is 240 MB
  const urls = useRef(new Set<string>());
  const noticeTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const patch = useCallback((id: string, p: Partial<Attachment>) => {
    if (!alive.current) return;
    setList((l) => l.map((a) => (a.id === id ? { ...a, ...p } : a)));
  }, []);

  const say = useCallback((text: string) => {
    setNotice(text);
    clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(null), NOTICE_MS);
  }, []);

  const forget = useCallback((a: Attachment | undefined, later = 0) => {
    aborts.current.get(a?.id ?? '')?.abort();
    aborts.current.delete(a?.id ?? '');
    const url = a?.preview;
    if (url) setTimeout(() => { URL.revokeObjectURL(url); urls.current.delete(url); }, later); // a tile fading out still draws it
  }, []);

  useEffect(() => {
    alive.current = true;
    const pending = aborts.current, held = urls.current;
    return () => {
      alive.current = false;
      clearTimeout(noticeTimer.current);
      pending.forEach((c) => c.abort());
      pending.clear();
      held.forEach((u) => URL.revokeObjectURL(u));
      held.clear();
    };
  }, []);

  const send = useCallback(async (id: string, ac: AbortController) => {
    const a = listRef.current.find((x) => x.id === id);
    if (!a || !alive.current) return;
    patch(id, { state: 'uploading', error: undefined, retry: undefined });
    try {
      const path = await upload(a, ws.current);
      if (ac.signal.aborted) return;
      patch(id, { state: 'uploaded', path });
    } catch (e) {
      if (ac.signal.aborted) return;
      const err = e instanceof UploadError ? e : new UploadError('network');
      patch(id, { state: 'error', error: uploadMessage(err), retry: true });
    } finally {
      aborts.current.delete(id);
    }
  }, [patch]);

  const add = useCallback((files: FileList | File[] | null | undefined) => {
    const incoming = Array.from(files ?? []);
    if (!incoming.length) return;
    const made: { att: Attachment; file: File }[] = [];
    for (const v of validate(listRef.current, incoming)) {
      if (!v.tile) { say(v.error); continue; } // the sixth: a line, no tile
      const base = { id: uid(), name: v.file.name || 'Photo', size: v.file.size };
      if (!v.kind) { made.push({ file: v.file, att: { ...base, kind: 'text', mime: v.file.type, state: 'error', error: v.error } }); continue; }
      made.push({ file: v.file, att: { ...base, kind: v.kind, mime: v.mime, state: v.kind === 'image' ? 'preparing' : 'ready', blob: v.kind === 'image' ? undefined : v.file } });
    }
    if (!made.length) return;
    const atts = made.map((m) => m.att);
    listRef.current = [...listRef.current, ...atts]; // `send` reads it before React has rendered
    setList((l) => [...l, ...atts]);
    for (const { att: a, file } of made) {
      if (a.state === 'error') continue;
      const ac = new AbortController();
      aborts.current.set(a.id, ac);
      if (a.kind !== 'image') { void send(a.id, ac); continue; }
      queue.current = queue.current.then(async () => {
        if (ac.signal.aborted || !alive.current) return;
        try {
          const p = await prepareImage(file, ac.signal);
          if (ac.signal.aborted || !alive.current) return;
          const preview = URL.createObjectURL(p.blob);
          urls.current.add(preview);
          const prepared = { blob: p.blob, preview, w: p.w, h: p.h, prep: p.ms, size: p.blob.size, mime: 'image/jpeg' };
          listRef.current = listRef.current.map((x) => (x.id === a.id ? { ...x, ...prepared } : x));
          patch(a.id, { ...prepared, state: 'ready' });
          await send(a.id, ac);
        } catch {
          if (ac.signal.aborted) return;
          patch(a.id, { state: 'error', error: "Couldn't open that photo. Try another." });
          aborts.current.delete(a.id);
        }
      });
    }
  }, [patch, say, send]);

  const remove = useCallback((id: string) => {
    forget(listRef.current.find((a) => a.id === id), 300);
    setList((l) => l.filter((a) => a.id !== id));
  }, [forget]);

  const retry = useCallback((id: string) => {
    const a = listRef.current.find((x) => x.id === id);
    if (!a || a.state !== 'error' || !a.retry) return;
    const ac = new AbortController();
    aborts.current.set(id, ac);
    void send(id, ac);
  }, [send]);

  const clear = useCallback(() => {
    listRef.current.forEach((a) => forget(a, 300));
    setList([]);
    setNotice(null);
  }, [forget]);

  const peek = useCallback((): Thumb[] => listRef.current.filter((a) => a.state === 'uploaded').map((a) => ({ kind: a.kind, name: a.name, url: a.preview })), []);

  const take = useCallback((): Thumb[] => {
    const out = peek();
    for (const a of listRef.current) {
      if (a.preview && out.some((t) => t.url === a.preview)) urls.current.delete(a.preview); // the turn owns it now
      else forget(a, 300);
      aborts.current.delete(a.id);
    }
    setList([]);
    setNotice(null);
    return out;
  }, [forget, peek]);

  return useMemo(() => {
    const busy = list.some((a) => a.state === 'preparing' || a.state === 'uploading' || a.state === 'ready');
    const stuck = list.some((a) => a.state === 'error' && a.retry);
    return {
      list, add, remove, retry, clear, take, peek, busy, stuck, ready: !busy && !stuck,
      hasSendable: list.some((a) => a.state === 'uploaded'),
      full: list.length >= 5, notice,
      request: () => toRequest(listRef.current),
      fallbackText: ATTACH_ONLY_TEXT,
    };
  }, [list, add, remove, retry, clear, take, peek, notice]);
}
