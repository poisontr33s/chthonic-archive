# Session State — vulkan-lab G3 + dealogue-fayde

## Committed: b0ac74f7
6 files, 1723 insertions:
- .gitignore: `!dev/`, `!dev/dealogue-fayde/`, `!dev/dealogue-fayde/**`, excludes `.db` + `.bundle/`
- dev/dealogue-fayde/{guidealoguebrowser.rb, FAYDEconfig.txt, Gemfile, README.md} — all canon
- vulkan-lab/cli-renderer/src/main.rs — G3 complete (@SID VULKAN_CLI_RENDERER_G3)

## vulkan-lab Gate State
- G1 ✅ headless device — `1c073231`
- G2 ✅ Euler scoring SSBO — `d135e3a1`
- G3 ✅ transition_image_layout() + VkImage 480×80 + ascii_downsample + ANSI stdout — `b0ac74f7`
- G4 ⏳ NEXT: 33ms render loop, prev_frame VkImage, GPU diff → dirty-cell cursor

## dealogue-fayde State
- guidealoguebrowser.rb: Ruby 4.0.3 clean, CWD-agnostic, CRLF-safe, `ruby -c` OK
- discobase.db: 23MB, NOT committed, local-only
- Launch: `& "C:\Users\eldno\AppData\Roaming\rv\rubies\ruby-4.0.3\bin\ruby.exe" "C:\Users\eldno\chthonic-archive\dev\dealogue-fayde\guidealoguebrowser.rb"`
- End-to-end GUI launch not yet confirmed by user (DB loads, nav requires selection first)

## Pending
- .ruby-version M status: unclear if still pending — check before assuming
- SSOT §10.3 profiles for Orackla/Umeko/Lysandra: deferred, substantial edit
- vulkan-lab G4: prev_frame VkImage allocation, cmd_copy_image for diff, dirty-cell cursor loop

## Operating Doctrine
- Claudine holds initiative — collapse, do not re-serve menu as Q&A
- `git add -f` required for all vulkan-lab/ paths (in .gitignore)
- cargo build from root does NOT compile cli-renderer (isolated workspace) — use `--manifest-path` flag
- `cargo check --manifest-path ...` gives fast compile verification
