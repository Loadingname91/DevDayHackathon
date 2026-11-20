import { useEffect, useRef, useState, type RefObject } from 'react';

const hasFiles = (dt: DataTransfer | null) => !!dt && Array.from(dt.types ?? []).includes('Files');

/**
 * Drop files on an element, or paste an image into it (Ctrl or Cmd + V in the field). The element is the whole sheet or chat
 * column, so the target is big; `dragging` is true while a file is over it (show `DropHint`). A paste that carries only a
 * picture is taken whole; one that also carries text pastes the text as usual and still attaches the picture. Drag and drop
 * is never the only way in: the Photo and File buttons do the same on every device.
 */
export function useDropPaste(ref: RefObject<HTMLElement | null>, add: (files: File[]) => void, opts: { enabled?: boolean } = {}) {
  const [dragging, setDragging] = useState(false);
  const addRef = useRef(add);
  addRef.current = add;
  const enabled = opts.enabled ?? true;
  const bound = useRef<HTMLElement | null>(null);
  const unbind = useRef<(() => void) | null>(null);

  function bind(el: HTMLElement) {
    let depth = 0;
    const over = (e: DragEvent) => { if (!hasFiles(e.dataTransfer)) return; e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'; };
    const enter = (e: DragEvent) => { if (!hasFiles(e.dataTransfer)) return; e.preventDefault(); depth++; setDragging(true); };
    const leave = (e: DragEvent) => { if (!hasFiles(e.dataTransfer)) return; depth = Math.max(0, depth - 1); if (!depth) setDragging(false); };
    const drop = (e: DragEvent) => {
      if (!hasFiles(e.dataTransfer)) return;
      e.preventDefault(); depth = 0; setDragging(false);
      const files = Array.from(e.dataTransfer?.files ?? []);
      if (files.length) addRef.current(files);
    };
    const paste = (e: ClipboardEvent) => {
      const files = Array.from(e.clipboardData?.files ?? []);
      if (!files.length) return;
      if (!e.clipboardData?.getData('text/plain')) e.preventDefault(); // a bare screenshot has nothing to paste as text
      addRef.current(files);
    };
    const end = () => { depth = 0; setDragging(false); };
    el.addEventListener('dragenter', enter); el.addEventListener('dragover', over); el.addEventListener('dragleave', leave);
    el.addEventListener('drop', drop); el.addEventListener('paste', paste);
    window.addEventListener('dragend', end); window.addEventListener('blur', end);
    return () => {
      el.removeEventListener('dragenter', enter); el.removeEventListener('dragover', over); el.removeEventListener('dragleave', leave);
      el.removeEventListener('drop', drop); el.removeEventListener('paste', paste);
      window.removeEventListener('dragend', end); window.removeEventListener('blur', end);
      setDragging(false);
    };
  }

  // The element may mount after this hook does (a sheet that opens later), so every commit checks which element the ref holds now.
  useEffect(() => {
    const el = enabled ? ref.current : null;
    if (el === bound.current) return;
    unbind.current?.();
    bound.current = el;
    unbind.current = el ? bind(el) : null;
  });
  useEffect(() => () => { unbind.current?.(); unbind.current = null; bound.current = null; }, []);
  return { dragging };
}

/** "Drop to attach": a chalk-dotted veil over the host (give the host `position: relative`). A 120 ms fade, nothing else moves. */
export function DropHint({ show }: { show: boolean }) {
  return <div className="at-drop" data-on={show ? '' : undefined} aria-hidden="true"><span>Drop to attach</span></div>;
}
