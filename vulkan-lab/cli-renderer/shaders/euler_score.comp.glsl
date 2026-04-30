#version 460
// @SID: EULER_SCORE_COMP_V0
// Gate 2: Euler scoring compute shader
// f(task) = weight * exp(KAPPA * staleness_days) * 0.5 * (1 + sin(phase_angle))
//
// Closes: GPU-parallel scoring for all tasks in one dispatch
// Scales: 64 tasks = 1 workgroup invocation. 64,000 tasks = 1000 workgroups, same clock.
// Binding contract:
//   set=0 binding=0  SSBO  TaskBuf   readonly   — task structs uploaded by host
//   set=0 binding=1  SSBO  ScoreBuf  writeonly  — f32 scores written by shader
//   set=0 binding=2  SSBO  CountBuf  readonly   — uint task_count (guard against overrun)

layout(local_size_x = 64) in;

struct Task {
    float weight;          // base weight 1..10
    float staleness_days;  // days since last touched or added
    float phase_angle;     // TAG_PHASE circular mean (radians, 0..2pi)
    float _pad;            // std430 alignment
};

layout(set = 0, binding = 0) readonly  buffer TaskBuf  { Task  tasks[];       };
layout(set = 0, binding = 1) writeonly buffer ScoreBuf { float scores[];      };
layout(set = 0, binding = 2) readonly  buffer CountBuf { uint  task_count;    };

const float KAPPA = 0.07; // staleness exponent — matches todo_roulette.ts

void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i >= task_count) return;

    Task t = tasks[i];

    // Euler score formula — identical to TypeScript implementation
    scores[i] = t.weight
              * exp(KAPPA * t.staleness_days)
              * 0.5 * (1.0 + sin(t.phase_angle));
}
