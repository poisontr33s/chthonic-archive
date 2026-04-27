// @SID: EXT_RUNTIME_LANE_STATE_V1
export type RuntimeLaneStateKind = 'READY' | 'LIVE' | 'PARKED' | 'DISABLED' | 'DEGRADED' | 'UNAVAILABLE' | 'MISSING';

export interface RuntimeLaneState {
    readonly name: string;
    readonly state: RuntimeLaneStateKind;
    readonly reason?: string;
}

export function formatRuntimeLaneState(lane: RuntimeLaneState): string {
    return lane.reason
        ? `${lane.name}=${lane.state} (${lane.reason})`
        : `${lane.name}=${lane.state}`;
}
