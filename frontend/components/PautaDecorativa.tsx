/** Pauta com notas, só de enfeite, nas telas largas. */
export function PautaDecorativa() {
  return (
    <svg aria-hidden="true" viewBox="0 0 160 40" className="hidden h-10 w-40 text-brand-500 opacity-30 xl:block" fill="none" stroke="currentColor">
      {[10, 16, 22, 28].map((y) => (
        <path key={y} d={`M0 ${y + 4}C40 ${y - 8} 90 ${y + 10} 160 ${y - 2}`} strokeWidth="0.8" />
      ))}
      <g strokeWidth="1.6">
        <path d="M45 26V8l7 5M105 24V7l16-3v17" />
        <g fill="currentColor" stroke="none">
          <ellipse cx="41" cy="27" rx="5" ry="3.5" />
          <ellipse cx="101" cy="25" rx="5" ry="3.5" />
          <ellipse cx="117" cy="22" rx="5" ry="3.5" />
        </g>
      </g>
    </svg>
  );
}
