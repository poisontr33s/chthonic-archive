export default function OracklaHeart() {
  return (
    <div className="relative flex h-64 w-64 items-center justify-center overflow-hidden rounded-full border-2 border-orackla-crimson/20 bg-orackla-void shadow-pulse">
      {/* Bitumen Flow (Living Oil) */}
      <div className="absolute inset-0 bitumen-flow animate-flow-viscous opacity-80 mix-blend-multiply" />
      
      {/* Visceral Pulse (Heartbeat) */}
      <div className="relative z-10 flex h-32 w-32 items-center justify-center rounded-full bg-orackla-crimson/10 pulse-viscera backdrop-blur-sm">
        <div className="h-16 w-16 rounded-full bg-orackla-pulse/80 shadow-[0_0_30px_rgba(255,69,0,0.6)] animate-pulse-slow" />
      </div>

      {/* Nigredo Overlay (Texture) */}
      <div className="pointer-events-none absolute inset-0 bg-[url('/noise.svg')] opacity-[0.15] mix-blend-overlay" />
    </div>
  );
}
