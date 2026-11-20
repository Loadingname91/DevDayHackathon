/** The quilt mark: four 9 px patches (Main and Laptop boards). Colours live in CSS (.logo-mark). */
export function LogoMark() {
  return (
    <svg className="logo-mark" width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <rect x="1" y="1" width="9" height="9" rx="2" /><rect x="12" y="1" width="9" height="9" rx="2" />
      <rect x="1" y="12" width="9" height="9" rx="2" /><rect x="12" y="12" width="9" height="9" rx="2" />
    </svg>
  );
}
