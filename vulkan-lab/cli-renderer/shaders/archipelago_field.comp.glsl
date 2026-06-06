#version 460
// @SID: ARCHIPELAGO_FIELD_COMP_V0
// L−5 · THE SEAM — islands SSBO → inverse-distance field over a lat/lon grid → field SSBO.
//
// One invocation per grid cell. The cell's lat/lon is interpolated from the bounding
// box (push constants); the field value is the Shepard inverse-distance-weighted mean
// of the island seeds. This is the barometer's geography made into a continuous field
// on the GPU — the first rung of the ladder: barometer → SSBO → compute → (host) ascii.
//
// Binding contract:
//   set=0 binding=0  SSBO  IslandBuf  readonly   — Island{lat,lon,elev,seed}[]
//   set=0 binding=1  SSBO  FieldBuf   writeonly  — float field[W*H], row-major, row 0 = north
//   push_constant    { uint count, W, H; float minLat, maxLat, minLon, maxLon }

layout(local_size_x = 64) in;

struct Island { float lat; float lon; float elev; float seed; };

layout(set = 0, binding = 0) readonly  buffer IslandBuf { Island islands[]; };
layout(set = 0, binding = 1) writeonly buffer FieldBuf  { float  field[];   };

layout(push_constant) uniform Push {
    uint  count;
    uint  W;
    uint  H;
    float minLat;
    float maxLat;
    float minLon;
    float maxLon;
} pc;

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx >= pc.W * pc.H) return;

    uint cx = idx % pc.W;
    uint cy = idx / pc.W;

    // Cell centre → lat/lon. Row 0 = north (maxLat); col 0 = west (minLon).
    float fx  = (pc.W > 1u) ? float(cx) / float(pc.W - 1u) : 0.0;
    float fy  = (pc.H > 1u) ? float(cy) / float(pc.H - 1u) : 0.0;
    float lon = mix(pc.minLon, pc.maxLon, fx);
    float lat = mix(pc.maxLat, pc.minLat, fy);

    // Inverse-distance weighting (Shepard, power 2). eps avoids /0 atop an island.
    float num = 0.0;
    float den = 0.0;
    for (uint i = 0u; i < pc.count; ++i) {
        float dlat = lat - islands[i].lat;
        float dlon = lon - islands[i].lon;
        float d2   = dlat * dlat + dlon * dlon + 1e-6;
        float w    = 1.0 / d2;
        num += w * islands[i].seed;
        den += w;
    }
    field[idx] = (den > 0.0) ? num / den : 0.0;
}
