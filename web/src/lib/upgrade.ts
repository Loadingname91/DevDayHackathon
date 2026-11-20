import type { AppResponse, PageBlock } from '../api/types';

/**
 * Stopgap until the server emits the `notebook` block for Notes (spec/ui-tech-plan.md §3 "Notebook", log in spec/split.md §7).
 * A Notes app the server still sends as two flat lists (Notebooks, All notes) over `notebooks` and `notes` is shown as the
 * notebook workspace instead. The rows are untouched; only the tabs change. Once the server sends the block this does nothing,
 * and it can be deleted.
 */
export function upgradeApp(a: AppResponse): AppResponse {
  const { spec } = a;
  if (spec.key !== 'notes') return a;
  if (spec.tabs.some((t) => t.children.some((b) => b.kind === 'notebook'))) return a;
  const cols = spec.collections;
  const nb = cols.find((c) => c.key === 'notebooks');
  const notes = cols.find((c) => c.key === 'notes');
  if (!nb || !notes || !notes.fields.some((f) => f.key === 'notebook') || !notes.fields.some((f) => f.key === 'body')) return a;
  const page: PageBlock = {
    kind: 'page', id: 't_notes', title: 'Notes',
    children: [{ kind: 'notebook', id: 'b_notebook', source: 'notes/notebooks', pages: 'notes/notes', link: 'notebook', body: 'body' }],
  };
  const kept = spec.tabs.filter((t) => t.id === 't_workflows' || t.children.every((b) => b.kind === 'workflows')); // rules stay
  return { ...a, spec: { ...spec, tabs: [page, ...kept] } };
}
