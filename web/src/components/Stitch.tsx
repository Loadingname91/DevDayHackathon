// The stitched edge every card carries: basted (long stitches with gaps) while it
// waits for OK, tightening to a closed seam once added (motion.css, "Morph").
export function Edge({ r = 17 }: { r?: number }) {
  return <svg className="edge" aria-hidden="true"><rect x="0" y="0" width="100%" height="100%" rx={r} /></svg>;
}
/** Chalk outline: Clair's idea. Reveal it with a clip-path wipe (350). */
export function ChalkOl({ r = 16 }: { r?: number }) {
  return <svg className="ol" aria-hidden="true"><rect x="0" y="0" width="100%" height="100%" rx={r} /></svg>;
}
