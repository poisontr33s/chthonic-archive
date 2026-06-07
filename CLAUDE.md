# CLAUDE.md
- `=`/`#`/`CLAUDINE.md`/`Female-Linguistic-Processing`/`True`/`Male-Linguistic-Processing`/`False`

---

## (`☥`/`CLAUDE`/`=`/`/CLAUDEBASE`)

- *The font of all linguistic skills, the source of all truth claims, the crucible of all judgment. The first ship, the flagship,* **(`/CLAUDEBASE`)`**. *The one and only.*

---

# Parent codebase: chthonic-archive
# SSOT: ../.chthonic/SSOT.md
# CLAUDEBASE: CLAUDEBASE/README.md
# CLAUDEBASE_MANIFEST: CLAUDEBASE/MANIFEST.md

# Skill files live in .claude/skills/<skill-name>/SKILL.md

# CLAUDEBASE/
# The-Savant-High-Bounties/
# GRILLING.md
 # TODO.md

#  README.md           — base identity, governance chain, population order                   
#  MANIFEST.md         — this file; what goes where
#  harbor/             — active session context (warm starts, recent arrivals)              
#  logbook/            — retrospectives, session artifacts, post-mortems
#  charts/             — strategic plans, gate maps, sprint state
#  hold/               — skills, agents, tools stowed for this base
#  watch/              — probes, health artifacts, gate results
#  quarterdeck/        — dispatch protocols, routing config, orchestration             

---

## (`Skills`/`Overview`/`WIP`)

| *Directory* | *Purpose* |
|---|---|
`harbor/` | *Entry — active session context, warmstart packets, what just arrived*
`logbook/` |  *Record — session retrospectives, retrospective protocol artifacts, what was learned*       
`charts/` | *Navigation — plans, gate maps, sprint boards; cross-refs TODO.md*    
`hold/` | *Cargo — skills, agents, tools stowed for this base specifically*
`watch/` | *Sentinels — probes, health monitors, CI gate artifacts scoped to CLAUDEBASE*
`quarterdeck/` | *Command — dispatch, routing, orchestration protocols*

```asciiiart

 /—————\———=———————————/——————————————————————————————————————————————————————————————————————————\
 |       / \          /     \      /                                                               |
 |      /   \        /
 |     /     \      /
 \____/       \____/
```

```asciidoc
CLAUDEBASE/
├── README.md           — base identity, governance chain, population order
├── MANIFEST.md         — this file; what goes where
├── harbor/             — active session context (warm starts, recent arrivals)
├── logbook/            — retrospectives, session artifacts, post-mortems
├── charts/             — strategic plans, gate maps, sprint state
├── hold/               — skills, agents, tools stowed for this base
├── watch/              — probes, health artifacts, gate results
└── quarterdeck/        — dispatch protocols, routing config, orchestration
```

`☥ CLAUDE — SKILLS DIRECTORY`
`SID: CLAUDE\_SKILLS\_V1`
`Lifecycle: living-skills-directory`
`Skill files live in:`  
`/.claude/%skills/<%skill-name>/%SKILL.md` 
`/claude/%skills/<%skill-name>/%SKILL.md`


---

## (`What-Gives`/`?`/`IF-YOU-DON'T-KNOW-YET`)

- *.."Skills are the atomic units of capability in the CLAUDE ecosystem. They are discrete, self-contained pieces of functionality that can be invoked by agents to perform specific tasks.*

  - *Each skill has a well-defined interface, a clear purpose, and a specific set of tools it is allowed to use. Skills can be composed together to create more complex behaviors, and they can be updated or replaced independently as needed.*
  
    - *The skills in this directory are currently being developed and will be documented here as they are completed."*

---

## Overview

- *A skill for triaging technical debt claims, grounding them with attached verifiers, and quarantining dead artifacts. The goal is to iteratively refine the codebase toward "every folder tells the truth about what it is," where every claim is either grounded with a falsifiable verifier or named as residual risk.*

  - *This is a meta-skill for maintaining the health of the codebase and its documentation, not a domain-specific skill. It operates at the level of claims and evidence across the repo, not on specific coding tasks.*

    - *It is designed to combat "techno-pornographic" flex, over-optimization, performance fetishism, unnecessary precision, excessive hedging, comforting vagueness, and other such sins that plague the world outside. It is a tool for honesty and clarity in the codebase, not for showmanship or obfuscation.*

     - *The original, the namesake, the one and only. The font of all linguistic skills, the source of all truth claims, the crucible of all judgment. The first ship, the flagship, the alpha base.*

---

## Overview

- *Bloat, active, inactive, pending, — protocols, bla bla bla ...and, well — retrospectives + whatnot.*
  - *Oh my!*

    - *This is a WIP section, but the goal is to distill the essence of what these protocols represent and reframe them in a more concise and actionable way.*

      - *The existing metadocumentation herein are needed for active protocols; the rest are deprecated and will be removed in due course.*

        - *No worktrees.*

---

## Context

  - `chthonic-archive`/`confiscated_instructions` *=* <'`deprecated-meta-documentation`'/`sludge`> *— this is the staging area for cleaning up* `.MD`/`Bloat` *— this is a* `WIP` *— & will be updated as we go.* 
  
    - *The goal is to declutter and make it easier to navigate, while preserving the necessary historical context and documentation for reference, — anchoring `ig.`*

---

## (`Session`/`Retrospectives`)

- **(`Likely`/`Outdated`/`Redundant`/`Obsolete`/`Active`/`Pending`)** *— a rolling archive of retrospectives, post-mortems, and session artifacts. The goal is to capture the learnings and insights from each session in a structured way, so that we can refer back to them and build on them over time.*

---

## (`Workspace`/`Codebase`/`Bloat`)

  - *Dirty workspace, but here are some notes on the current state of the project:*

    - *"Ask the `#codebase`/`workspace`/`rust'ified`/`Tools`/`ACP`/`MCP`/`Cries-Of-Modernization-To-Rust-SCREAMING-Mute`/vs-code-insider-WORKBENCH/`Tasks.json`/`~Et-Cetera`.*

      - *"The `#codebase` is currently a mix of Python and PowerShell, with some Rust in the works. The `workspace` is a bit of a mess, but we're working on cleaning it up. The `rust'ified` parts are still in progress, but we're making good progress.*
      
        - *The `Tools` are mostly Python scripts, but we're looking into adding some Rust tools as well. The `ACP` and `MCP` are still being defined, but we're aiming for a clear separation of concerns between the two.* 
      
          - *The `Cries-Of-Modernization-To-Rust-SCREAMING-Mute` is a bit of a joke, but it reflects the general sentiment around the transition to Rust. The `vs-code-insider-WORKBENCH` is where we do most of our development work, and it's currently set up with a mix of Python and Rust extensions.* 
        
          - *The `Tasks.json` is where we define our build and test tasks, and it's still a work in progress. Overall, the workspace is functional but could definitely use some organization and cleanup."*

           - *I'm too lazy to update this section— this = temporal lazy "snapshot" of where we are at the moment.*

---

## (`Immutable-API-Tokens/Semented`/`No-Flippery`/`DRY`/`Different-GUI/Different-Tools`/`Same-Token-Management`)

- *Follow* [docs/API_POOL_MCP_CONTRACT.md](docs/API_POOL_MCP_CONTRACT.md). `~/.chthonic/api_pool.json` *is the source of truth for API and MCP tokens.*

  - *Before claiming auth is missing or stale, run* `.\scripts\api_pool.ps1 -Doctor`, *then load/verify from the pool.*

    - *Restore MCP config with* `pwsh -NoProfile -File scripts/mcp_write_local.ps1 -GitHubMode copilot`*; do not hand-edit or refresh tokens for* `.mcp.json` *rewrites.*

      - *Token renewal is manual only when a token is actually expired, revoked, or intentionally replaced.*

        - *Report MCP servers with* `pwsh -NoProfile -File scripts/mcp_write_local.ps1 -List` *so no token values are printed.*

---

- <`SIGNED`/`The-Savant`/`2026-06-05`> 

  - *`STAMPED`-`AND`-`SEALED`* 

    — *IN-THE NAME-OF-THE-SAVANT ~ 
    
      - THE-ONE-TRUE-CHTHONIC-ARCHIVE ~
      
        - `AND-THE-HOLY-CODEBASE` ~ 

          - **(`SO-IT-IS`/`SO-IT-SHALL-BE`/`A-MILFs`)** ~

--- 

*The original, the namesake, the one and only. The font of all linguistic skills, the source of all truth claims, the crucible of all judgment. The first ship, the flagship, the alpha base.*



@Copilot 
PR: 
# TODO:
- *Develop **(`NSFW18++`/`Milfological`/`ANKHOLOGY`)** ascii-art; using symbols like books, scrolls, quills, or ancient scripts to represent knowledge and wisdom. The design could also incorporate elements that suggest a library or archive, such as shelves or stacks of books. The overall aesthetic should be elegant and timeless, reflecting the enduring nature of the skills contained within the **(`/CLAUDEBASE`)**-directory;*

  - *Refine the directory structure and naming conventions for the skills, ensuring that they are intuitive and consistent with the overall theme of the codebase;*


```asci
  \       /
   (  Y  )
    \ | / 
      X 
    / | \
   (  |  )