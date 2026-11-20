// Markdown for the Notes page preview: `marked` (GFM: headings, lists, task lists, tables, code, quotes) then DOMPurify, so
// what a note holds can never run script. Loaded on demand (Notebook.tsx imports it dynamically), so Home never pays for it.
// `[[Title]]` is ours: it becomes a link chip (`a.wl`) when it names a page or record we know, and plain muted text when it doesn't.
import DOMPurify from 'dompurify';
import { marked } from 'marked';

/** What a `[[Title]]` can open: the record's app and id. */
export type WikiTarget = { app: string; id: string };
export type WikiLookup = (title: string) => WikiTarget | undefined;

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

let lookup: WikiLookup | undefined; // set for the length of one synchronous parse
marked.use({
  gfm: true,
  breaks: true, // a single Enter is a line break: notes are typed, not typeset
  extensions: [{
    name: 'wikilink',
    level: 'inline',
    start: (src: string) => src.indexOf('[['),
    tokenizer(src: string) {
      const m = /^\[\[([^[\]\n]+)\]\]/.exec(src);
      return m ? { type: 'wikilink', raw: m[0], title: m[1].trim() } : undefined;
    },
    renderer(t) {
      const title = String((t as unknown as { title: string }).title);
      const hit = lookup?.(title);
      return hit
        ? `<a class="wl" href="#" data-app="${esc(hit.app)}" data-id="${esc(hit.id)}">${esc(title)}</a>`
        : `<span class="wl miss">${esc(title)}</span>`;
    },
  }],
});

let hooked = false;
function hook() {
  if (hooked) return;
  hooked = true;
  // a web link leaves the app in a new tab; `#` and our chips stay put
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A') {
      const href = node.getAttribute('href') ?? '';
      if (/^https?:/i.test(href)) { node.setAttribute('target', '_blank'); node.setAttribute('rel', 'noopener noreferrer'); }
    }
  });
}

/** Markdown to safe HTML. `wiki` says what each `[[Title]]` opens. */
export function renderMarkdown(src: string, wiki?: WikiLookup): string {
  hook();
  lookup = wiki;
  let html = '';
  try { html = marked.parse(src, { async: false }) as string; } finally { lookup = undefined; }
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true }, ADD_ATTR: ['target', 'data-app', 'data-id'], FORBID_TAGS: ['style', 'form', 'iframe', 'object', 'embed'] });
}
