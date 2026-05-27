export default function UmekoLung() {
  return (
    <div className="relative flex h-64 w-72 items-center justify-center overflow-hidden rounded-[2rem] border border-umeko-mist/85 bg-alveolar shadow-breath backdrop-blur-sm">
      {/* Albedo Fog Field (Respiratory Medium) */}
      <div className="absolute inset-0 breath-fog animate-mist-drift opacity-90" />

      {/* Bronchial Spine */}
      <div className="absolute z-10 h-40 w-3 rounded-full bg-umeko-silver/80" />

      {/* Twin Alveolar Lobes */}
      <div className="relative z-20 flex items-center gap-6">
        <div className="alveoli-breath flex h-36 w-24 items-center justify-center rounded-[45%] border border-umeko-mist/85 bg-white/70">
          <div className="h-14 w-14 rounded-full bg-umeko-breath/45 animate-breath-cycle" />
        </div>
        <div className="alveoli-breath flex h-36 w-24 items-center justify-center rounded-[45%] border border-umeko-mist/85 bg-white/70">
          <div className="h-14 w-14 rounded-full bg-umeko-breath/45 animate-breath-cycle" />
        </div>
      </div>

      {/* Condensation Veil */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.24),transparent_65%)] mix-blend-soft-light" />
    </div>
  );
}
