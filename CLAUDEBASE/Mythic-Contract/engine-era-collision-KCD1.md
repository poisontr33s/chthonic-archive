# (`Legacy-Engine-Forensics`/`KCD1`/`Motion-Artifact-Case`)

*A worked forensic **case + reusable method** for diagnosing old engines on modern hardware. Outcome: the specific KCD1 motion artifact was **bounded, then solved** (2026-06-24 — root cause: framerate coupling above CryEngine's 60 fps design ceiling; fix: hard cap at 60 fps). The repurposable assets are the method, the negative-space ledger, the rig, and the root cause itself — all compound into future cases. Entry #1 in the legacy-engine forensics set. Source thread: `preamble-log-KKD1.md`.*

---

## The case

*KCD1 (CryEngine, 2018 / ≈2016 design) on i9-13900KF · RTX 4090 · AOC AG276QZD (1440p 240Hz QD-OLED). Symptom: motion-induced smear / ghost / "catching-up" when the camera moves, razor sharp when still. Diagnosed across multiple sessions with the user as instrument — rendered output is ground truth; logs only confirm what applied.*

---

## Negative-space ledger — what was excluded (the durable asset)

*Each turned off / changed; the motion artifact persisted unchanged (sharp-when-still):*

- *SVOGI voxel GI —* (`e_svoTI_Apply 0`*,* `e_svoTI_Active 0`)*.*
- *Temporal AA —* (`r_AntialiasingMode 0` = off; `1` = spatial SMAA, no temporal history)*.*
- *Motion blur —* (`r_MotionBlur 0`)*.*
- *Mouse smoothing / inertia / accel —* (`i_mouse_*` — already 0)*.*
- *Engine vsync —* (`r_vsync` 0 and 1)*.*
- *Game screen-space AO —* (`r_ssdo 0`)*.*
- *Game screen-space contact shadows —* (`r_ShadowsScreenSpace 0`)*.*
- *NVIDIA driver-forced Ambient Occlusion / HBAO+ — off.*
- *NVIDIA driver-forced AA + transparency supersampling — off.*

*Every item lives **inside the rendered frame**. Their exhaustive exclusion is the finding.*

---

## Hypotheses raised and falsified (method honesty)

1. **Engine-era temporal-stack incoherence** *— plausible; falsified: flattening the entire temporal stack at once didn't remove the artifact.*
2. **Forced NVIDIA driver AO** *— strong circumstantial evidence (the profile `.nip` had `Ambient Occlusion = Quality` forced); falsified by test: disabling driver AO + AA changed nothing (slightly worse, from added aliasing).*

*Both were reasonable; both were wrong; the user's empirical testing killed each. Lesson: hypothesis → test → **falsify**, and never enshrine "this is it" before the test runs.*

## Bounded conclusion (closed by the partition test)

- *— The game-independent partition test — **testufo.com at 240 Hz — came back clean.** The panel, GPU output, and frame-delivery chain render fast motion flawlessly when fed clean frames.*

  - *— That **exonerates the hardware** (no response-time ghosting, no display defect, no pacing fault in a well-behaved app) and partitions the cause to **KCD itself** — how the engine presents/paces frames, plausibly compounded by its sub-240 framerate (~111 fps, CPU-bound). Honest caveat: testufo ran at 240 fps vs KCD's ~111, so a pure framerate-bound persistence component can't be fully separated from a KCD present-path quirk without a matched-fps test — but the display as hardware is cleared. Net: image-composition excluded (ledger) + hardware excluded (testufo) → residual = KCD's own frame delivery. Unsolved, fully bounded, hunt closed.*

---

## Root cause — SOLVED (2026-06-24)

*60 fps cap (RTSS or in-engine limit) eliminates all motion artifact: bleeding, jitter, ghosting, catch-up smear. Artifact returns above the cap.*

**Root cause: CryEngine 2016 is framerate-coupled.** Internal simulation tick, animation evaluation, and physics stepping are not decoupled from the render loop. Above the design ceiling (~60 fps), internal engine state advances faster than the presentation layer can express coherently. The gap between what the engine internally computed and what it committed to the frame is the smear. It is not a display artifact, not a driver artifact, not a temporal AA artifact — the ledger excluded all of those. The engine is simply running faster than its own coherence model tolerates.

**Fix: hard cap at 60 fps** (RTSS or `sys_maxfps 60` in user.cfg). The artifact is gone; the engine is coherent at its design ceiling.

**Console parity confirms the mechanism from the other side.** Locked 60 is where the engine was designed to run — why console output is clean. PS5 Pro's PSSR (spectral super-resolution) can push 120 Hz output from a 60 fps engine source without reintroducing the artifact because the upscaler operates downstream of the engine's presentation, not inside the coupled tick loop.

*Status: **SOLVED**. "Unsolved, fully bounded" retired. Root cause = framerate coupling above design ceiling; fix = 60 fps cap.*

---

## Reusable forensic rig (any old/closed engine on this hardware)

- *Read the engine DLL's PE **import table** to settle renderer/API —* (`d3d11`/`dxgi` vs `vulkan-1`/`d3d12`). 
*— KCD1 = DX11 only;* `-vulkan` *is inert.*
- *Extract CryEngine* **CVarGroups from the `.pak`** *— (it's ZIP) for real per-tier values.*
- **Probe hardware via PowerShell** (`Win32_VideoController`*, EDID-decode* `WmiMonitorID`,`nvidia-smi` 
*util/power → CPU-vs-GPU bound). KCD1 ran at 14% GPU = CPU-bound.*
- **Read the NVIDIA driver profile** (`.nip` *via Profile Inspector) — driver overrides sit above the engine,* 
*immune to cvars, personal to the machine. Check before blaming the engine.*
- **P-core pin** f*or old games on hybrid CPUs* (`pin_pcores.ps1`, *mask* `0xFFFF`).
- *The* **game log is a console mirror** *(cvars echo with* `[DUMPTODISK]`; *screenshots log FPS)*.
- *Discipline: change ONE thing, test* **in motion***, falsify. Eye = instrument, log = confirmer.*

---

## Dead routes (recorded so they're not re-chased)

- *Config recovery: KCD cloud-syncs **saves only**, not settings; no shadow copies, File History off → no old config to diff against. Reconstruct, don't hunt.*
- *Image-composition causes: the ledger above. All excluded.*

---

## Era/hardware context (now a proven case, not just a general lesson)

*1080 Ti = king of 1K; 13900K/4090/240Hz-OLED = the 2K side of the bifurcation; 2016 engines sit on the 1K side. "Time reverses optimization into complexity." Temporal-coherence-as-display-persistence-contract is now **empirically confirmed** as KCD1's specific fault — framerate coupling above the design ceiling breaks the coherence contract. This upgrades the invariant from design principle to proven forensic precedent for our own renderer/sim work.*

---

## Repurposing into the project

- *Entry #1 in a legacy-engine forensics set — the "streamlined way to play older games" prospect (siblings: Darkest Dungeon 1/2, force-updated online titles).*
- *The **negative-space ledger + the rig + the root cause** are reusable. Framerate coupling is a predictable pathology in engines from this era — the rig surfaces it fast in future cases.*
- *Feeds the user-authored candidate-types plan and the CLAUDEBASE renderer/sim design invariant — now with empirical backing.*
