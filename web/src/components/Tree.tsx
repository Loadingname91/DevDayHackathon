import { useRef, type KeyboardEvent } from 'react';
import { Icon } from './Icon';

export type TreeItem = { id: string; label: string; meta?: string };
export type TreeGroup = { id: string; label: string; count: number; items: TreeItem[]; /** a line shown while it holds nothing */ empty?: string; /** no options button (a group that is not a real row, like "Unfiled") */ fixed?: boolean };

/**
 * A two-level outline: groups that open and close, and the items inside them (a notebook and its pages). It knows nothing about
 * notes: the caller says what the groups are, which one is open, which item is picked, and what "+" and "···" do. Reusable for
 * any parent → children list (classes → work, lists → items).
 *
 * Keyboard: Up and Down walk every visible row, Right opens a group, Left closes it (or moves from an item to its group),
 * Home and End jump. One row is in the tab order at a time.
 */
export function Tree({ label, groups, open, onToggle, picked, pickedGroup, onPick, onPickGroup, onAdd, addLabel, onMore, moreLabel, empty }: {
  label: string;
  groups: TreeGroup[];
  open: Set<string>;
  onToggle: (group: string) => void;
  /** the item that is open on the page, and the group it was picked under (a page can sit in several) */
  picked?: string | null;
  pickedGroup?: string | null;
  onPick: (item: TreeItem, group: TreeGroup) => void;
  /** a tap on a group's name: open it and (the caller decides) show only its items */
  onPickGroup?: (group: TreeGroup) => void;
  onAdd?: (group: TreeGroup) => void;
  addLabel?: (group: TreeGroup) => string;
  onMore?: (group: TreeGroup) => void;
  moreLabel?: (group: TreeGroup) => string;
  empty?: string;
}) {
  const host = useRef<HTMLUListElement>(null);
  const rows = () => [...(host.current?.querySelectorAll<HTMLElement>('[data-tr]') ?? [])];
  const key = (e: KeyboardEvent<HTMLUListElement>) => {
    const el = (e.target as HTMLElement).closest<HTMLElement>('[data-tr]');
    if (!el || (e.target as HTMLElement) !== el) return;
    const all = rows(), at = all.indexOf(el);
    const go = (i: number) => { const n = all[Math.max(0, Math.min(all.length - 1, i))]; n?.focus(); };
    const g = el.dataset.tr === 'group', id = el.dataset.id ?? '';
    if (e.key === 'ArrowDown') { e.preventDefault(); go(at + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); go(at - 1); }
    else if (e.key === 'Home') { e.preventDefault(); go(0); }
    else if (e.key === 'End') { e.preventDefault(); go(all.length - 1); }
    else if (e.key === 'ArrowRight' && g && !open.has(id)) { e.preventDefault(); onToggle(id); }
    else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      if (g && open.has(id)) onToggle(id);
      else if (!g) host.current?.querySelector<HTMLElement>(`[data-tr="group"][data-id="${CSS.escape(el.dataset.group ?? '')}"]`)?.focus();
    }
  };
  // the group the picked item is drawn under (a page in two notebooks shows under both; the one you came from wins)
  const under = picked ? (groups.find((x) => x.id === pickedGroup && open.has(x.id) && x.items.some((i) => i.id === picked)) ?? groups.find((x) => open.has(x.id) && x.items.some((i) => i.id === picked)))?.id : undefined;
  // roving tabindex: one row is in the tab order, the picked item or else the first group
  const stop = under ? `i:${under}:${picked}` : `g:${groups[0]?.id}`;
  return (
    <ul className="tr" role="tree" aria-label={label} ref={host} onKeyDown={key}>
      {groups.length === 0 && empty && <li className="tr-none" role="none">{empty}</li>}
      {groups.map((g) => {
        const isOpen = open.has(g.id);
        return (
          <li key={g.id} className="tr-g" role="none">
            <div className={`tr-head${pickedGroup === g.id ? ' on' : ''}`}>
              <button type="button" role="treeitem" data-tr="group" data-id={g.id} aria-expanded={isOpen} aria-selected={pickedGroup === g.id && !picked} tabIndex={stop === `g:${g.id}` ? 0 : -1} className="tr-name"
                onClick={() => (onPickGroup ? onPickGroup(g) : onToggle(g.id))}>
                <span className="tr-caret" aria-hidden="true"><Icon name="chev" size={14} sw={2.2} /></span><span className="tr-t">{g.label}</span><span className="tr-n">{g.count}</span>
              </button>
              {onMore && !g.fixed && <button type="button" className="tr-act" aria-label={moreLabel?.(g) ?? `${g.label} options`} onClick={() => onMore(g)}><Icon name="more" size={20} sw={2.4} /></button>}
              {onAdd && <button type="button" className="tr-act" aria-label={addLabel?.(g) ?? `Add to ${g.label}`} onClick={() => onAdd(g)}><Icon name="plus" size={16} sw={2} /></button>}
            </div>
            {isOpen && (
              <ul className="tr-kids" role="group" aria-label={g.label}>
                {g.items.length === 0 && <li className="tr-none" role="none">{g.empty ?? 'Nothing here yet'}</li>}
                {g.items.map((i) => (
                  <li key={i.id} role="none">
                    <button type="button" role="treeitem" data-tr="item" data-id={i.id} data-group={g.id} aria-selected={under === g.id && picked === i.id}
                      tabIndex={stop === `i:${g.id}:${i.id}` ? 0 : -1} className="tr-item" onClick={() => onPick(i, g)}>
                      <Icon name="note" size={16} sw={1.7} /><span className="tr-x"><span className="tr-t">{i.label}</span>{i.meta && <span className="tr-m">{i.meta}</span>}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
