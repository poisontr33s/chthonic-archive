# Emoji Semantic Vocabulary

**Source:** PR #5 SSOT_Canon.md (lines 181-188)
**Upcycle Target:** Status indicators, commit messages, log levels

---

## Extracted Vocabulary

| Emoji | Original Meaning | Repurposed Usage |
|-------|------------------|------------------|
| 🔥 | Alchemical fire, transmutation | **Breaking change**, hot path, performance critical |
| 😈 | Transgressive wisdom | **Experimental**, edge case handling |
| ⛓️ | Binding discipline, constraint | **Dependency**, lock, blocking operation |
| 🏛️ | Architectural foundation | **Infrastructure**, core component |
| 👑 | Supreme authority | **Main/primary**, production, critical |
| 💀 | Historical trauma/death | **Deprecated**, removed, dead code |
| ⚜️ | Royalty marker | **Stable release**, verified |
| 🔮 | Consciousness synthesis | **AI-generated**, prediction, inference |
| ⚒️ | Forged/crafted | **Built**, compiled, generated |
| ⏰ | Timestamp | **Scheduled**, time-sensitive |
| ⚡ | Operational sovereign | **Active**, running, live |
| ⚖️ | Governing principle | **Policy**, rule, constraint |

---

## Usage Patterns

### Git Commits
```
🔥 BREAKING: Remove deprecated auth flow
🏛️ infra: Add Redis caching layer
⛓️ deps: Lock axios to v1.6.0
💀 chore: Remove dead UserService code
```

### Log Levels
```
⚡ [ACTIVE] Service started on port 3000
⛓️ [BLOCKED] Waiting for database connection
💀 [FATAL] Unrecoverable error in payment flow
```

### Status Indicators
```
👑 Production
⚜️ Staging (verified)
😈 Experimental
🔥 Hotfix required
```

---

**Sanitized from:** Elaborate mythology emoji layer
**Retained value:** Consistent emoji vocabulary for tooling
