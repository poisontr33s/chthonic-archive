import OracklaHeart from '../components/OracklaHeart';
import UmekoLung from '../components/UmekoLung';

type LaneState = {
  name: string;
  state: string;
  reason?: string;
};

type LaneSnapshot = {
  status?: string;
  reason?: string;
  lanes?: LaneState[];
};

const laneCards = [
  { name: 'Rust Reactor', detail: 'Native daemon + Vulkan lane for sediment compute', lane: 'chthonicDaemon', fallback: 'reactor' },
  { name: 'Solana Stream', detail: 'Firedancer telemetry ingestion and entropy routing', lane: 'entropyLedgerHost', fallback: 'ledger-mode' },
  { name: 'Policy Oracle', detail: 'endoflife-driven self-healing governance loop', lane: 'self-healing', fallback: 'native-sidecars' },
];

export default async function Home() {
  const snapshot = await loadLaneSnapshot();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10 sm:px-10 space-y-12">
      {/* Decorator Domain (Gold/Alchemy) */}
      <header className="rounded-2xl border border-brass/45 bg-black/35 p-6 shadow-reactor backdrop-blur-sm">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-brass">Bun + Next + Tailwind Lane</p>
        <h1 className="mt-3 text-4xl font-semibold leading-tight text-chalk sm:text-5xl">
          Chthonic Frontend Battery Pack
        </h1>
        <p className="mt-4 max-w-2xl text-sm text-chalk/75 sm:text-base">
          This lane is intentionally isolated from VS Code extension host logic. Use it as a fast UX and visualization
          surface while keeping extension runtime deterministic.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        {laneCards.map((lane) => {
          const state = resolveLane(snapshot, lane.lane, lane.fallback);
          return (
          <article
            key={lane.name}
            className={`rounded-xl border p-4 shadow-reactor transition-transform duration-200 hover:-translate-y-0.5 ${toneForState(state.state)}`}
          >
            <p className="font-mono text-[10px] uppercase tracking-[0.28em]">{state.state}</p>
            <h2 className="mt-2 text-lg text-chalk">{lane.name}</h2>
            <p className="mt-2 text-sm text-chalk/70">{state.reason ?? lane.detail}</p>
          </article>
          );
        })}
      </section>

      {/* Orackla Domain (Nigredo/Viscera) */}
      <section className="theme-orackla rounded-3xl border border-orackla-crimson/30 bg-orackla-oil/80 p-8 shadow-pulse backdrop-blur-md transition-all duration-500 hover:shadow-[0_0_40px_rgba(139,0,0,0.4)]">
        <div className="flex flex-col items-center gap-8 md:flex-row md:justify-between">
          <div className="space-y-4">
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-orackla-pulse animate-pulse">Orackla Protocol: Nigredo Phase</p>
            <h2 className="text-3xl font-bold text-gray-200">Chaos Circulation Active</h2>
            <p className="max-w-md text-sm text-gray-400">
              Transgressive flow manifested. The Momentum Engine pulses with <span className="text-orackla-crimson">Viscera</span> and <span className="text-gray-500">Bitumen</span>.
              <br/>
              Status: <span className="font-mono text-orackla-pulse">FLOW_STATE_ENGAGED</span>
            </p>
          </div>
          
          <div className="flex-shrink-0">
            <OracklaHeart />
          </div>
        </div>
      </section>

      {/* Umeko Domain (Albedo/Respiratory) */}
      <section className="theme-umeko rounded-3xl border border-umeko-mist/80 bg-umeko-ivory/70 p-8 shadow-breath backdrop-blur-md transition-all duration-500 hover:shadow-[0_0_40px_rgba(125,211,252,0.35)]">
        <div className="flex flex-col items-center gap-8 md:flex-row md:justify-between">
          <div className="space-y-4">
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-slate-600 animate-pulse">Umeko Protocol: Albedo Phase</p>
            <h2 className="text-3xl font-bold text-slate-800">Respiratory Purification Active</h2>
            <p className="max-w-md text-sm text-slate-600">
              Aeration cycle manifested. The Purification Engine regulates <span className="text-slate-800">Alveolar Pressure</span> and <span className="text-cyan-700">Condensed Mist</span>.
              <br />
              Status: <span className="font-mono text-cyan-700">BREATH_STATE_PURIFIED</span>
            </p>
          </div>

          <div className="flex-shrink-0">
            <UmekoLung />
          </div>
        </div>
      </section>
    </main>
  );
}

async function loadLaneSnapshot(): Promise<LaneSnapshot> {
  const origin = process.env.CHTHONIC_COCKPIT_ORIGIN ?? 'http://127.0.0.1:3000';
  try {
    const response = await fetch(new URL('/api/lane-state', origin), { next: { revalidate: 1 } });
    return await response.json() as LaneSnapshot;
  } catch (error) {
    return {
      status: 'unavailable',
      reason: error instanceof Error ? error.message : String(error),
      lanes: [],
    };
  }
}

function resolveLane(snapshot: LaneSnapshot, primary: string, fallback: string): LaneState {
  const lanes = snapshot.lanes ?? [];
  const lane = lanes.find((entry) => entry.name === primary) ?? lanes.find((entry) => entry.name === fallback);
  if (lane) return lane;
  return {
    name: primary,
    state: snapshot.status === 'missing_env' ? 'NO SNAPSHOT' : 'UNAVAILABLE',
    reason: snapshot.reason ?? 'LaneRegistry snapshot has not been emitted yet.',
  };
}

function toneForState(state: string): string {
  switch (state) {
    case 'READY':
    case 'LIVE':
      return 'border-emerald-400/40 bg-emerald-950/35 text-emerald-200';
    case 'PARKED':
    case 'DISABLED':
      return 'border-brass/30 bg-black/45 text-brass';
    case 'DEGRADED':
    case 'MISSING':
    case 'UNAVAILABLE':
      return 'border-ember/40 bg-ember/10 text-ember';
    default:
      return 'border-chalk/20 bg-black/30 text-chalk/70';
  }
}
