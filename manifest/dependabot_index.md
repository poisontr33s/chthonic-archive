# Dependabot index digest

Generated: 2026-05-14T04:30:35.588001+00:00
Repo: `poisontr33s/chthonic-archive`
Source: `manifest/dependabot_index.json` (regenerate via `uv run scripts/dependabot_index.py`)

## Summary

- Total alerts: 68
- Fix available: 64 / 68
- Hotspot packages (>=2 alerts each): 16

### By state

- `open`: 40
- `fixed`: 28

### By severity

- `high`: 29
- `medium`: 25
- `low`: 12
- `critical`: 2

### By ecosystem

- `pip`: 33
- `rust`: 30
- `npm`: 4
- `rubygems`: 1

### By relationship (direct = actionable, transitive = upstream wait)

- `unknown`: 36
- `direct`: 17
- `transitive`: 15

## Hotspot packages (one package, multiple CVEs)

- `rust/openssl` — 7 alerts
- `rust/rustls-webpki` — 7 alerts
- `pip/pillow` — 6 alerts
- `pip/gradio` — 4 alerts
- `rust/gix` — 4 alerts
- `pip/python-multipart` — 3 alerts
- `pip/flask-cors` — 3 alerts
- `pip/fastmcp` — 3 alerts
- `npm/postcss` — 3 alerts
- `rust/rand` — 3 alerts
- `pip/authlib` — 2 alerts
- `pip/urllib3` — 2 alerts
- `pip/pip` — 2 alerts
- `pip/cryptography` — 2 alerts
- `pip/diskcache` — 2 alerts

## Top 25 alerts (priority order)

Sort key: open before non-open, severity rank, fix-available, direct over transitive.

### [HIGH / open] `pip/gradio` (direct, fix:6.6.0)

- Gradio has SSRF via Malicious `proxy_url` Injection in `gr.load()` Config Processing
- CVE-2026-28416 · GHSA-jmh7-g254-2cq9
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/62

### [HIGH / open] `pip/gradio` (direct, fix:6.7.0)

- Gradio is Vulnerable to Absolute Path Traversal on Windows with Python 3.13+
- CVE-2026-28414 · GHSA-39mp-8hj3-5c49
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/60

### [HIGH / open] `pip/pillow` (transitive, fix:12.2.0)

- Pillow has an OOB Write with Invalid PSD Tile Extents (Integer Overflow)
- CVE-2026-42311 · GHSA-pwv6-vv43-88gr
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/67

### [HIGH / open] `pip/pillow` (transitive, fix:12.2.0)

- FITS GZIP decompression bomb in Pillow
- CVE-2026-40192 · GHSA-whj4-6x5x-4v2j
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/63

### [HIGH / open] `pip/pillow` (transitive, fix:12.1.1)

- Pillow affected by out-of-bounds write when loading PSD images
- CVE-2026-25990 · GHSA-cfh3-3jmp-rvhc
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/58

### [HIGH / open] `rust/gix` (unknown, fix:0.83.0)

- gix and gitoxide: unvalidated submodule name traverses out of .git/modules and redirects state() / open() to another repository
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/55

### [HIGH / open] `rust/gix` (unknown, fix:0.83.0)

- gix and gitoxide's symlinked .gitmodules are followed and parsed from outside of the repository
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/54

### [HIGH / open] `rust/gix` (unknown, fix:0.83.0)

- gitoxide: CommandForbiddenInModulesConfiguration Bypass in gix_submodule::File::update() Enables Arbitrary Command Execution via .gitmodules
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/52

### [HIGH / open] `rust/gix` (unknown, fix:0.83.0)

- gix's submodule name validation bypass + trust inheritance flaw enables path traversal and credential disclosure
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/51

### [HIGH / open] `rust/gix-fs` (unknown, fix:0.21.1)

- gix-fs: Symlink prefix-reuse allows worktree escape during checkout
- CVE-2026-44471 · GHSA-f89h-2fjh-2r9q
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/69

### [HIGH / open] `rust/gix-pack` (unknown, fix:0.69.0)

- gix-pack has multiple DoS vectors: unchecked indexing panics and uncapped OOM allocations from crafted pack data
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/53

### [HIGH / open] `rust/openssl` (unknown, fix:0.10.79)

- rust-openssl has undefined behavior in X509Ref::ocsp_responders for certificates with non-UTF-8 OCSP URLs
- CVE-2026-42327 · GHSA-xp3w-r5p5-63rr
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/56

### [HIGH / open] `rust/quinn-proto` (unknown, fix:0.11.14)

- Quinn affected by unauthenticated remote DoS via panic in QUIC transport parameter parsing
- CVE-2026-31812 · GHSA-6xvm-j4wr-6v98
- manifest: `tools/ankh-forge/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/11

### [HIGH / open] `rust/rustls-webpki` (unknown, fix:0.103.13)

- rustls-webpki: Denial of service via panic on malformed CRL BIT STRING
- manifest: `tools/ankh-forge/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/34

### [HIGH / open] `rust/rustls-webpki` (unknown, fix:0.103.13)

- rustls-webpki: Denial of service via panic on malformed CRL BIT STRING
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/33

### [LOW / open] `pip/gradio` (direct, fix:6.6.0)

- Gradio: Mocked OAuth Login Exposes Server Credentials and Uses Hardcoded Session Secret
- CVE-2026-27167 · GHSA-h3h8-3v2v-rg7m
- manifest: `uv.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/59

### [LOW / open] `rust/curve25519-dalek` (unknown, fix:4.1.3)

- curve25519-dalek has timing variability in `curve25519-dalek`'s `Scalar29::sub`/`Scalar52::sub`
- CVE-2024-58262 · GHSA-x4gp-pqpj-f43q
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/6

### [LOW / open] `rust/rand` (unknown, fix:0.8.6)

- Rand is unsound with a custom logger using rand::rng()
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/27

### [LOW / open] `rust/rand` (unknown, fix:0.9.3)

- Rand is unsound with a custom logger using rand::rng()
- manifest: `tools/ankh-forge/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/26

### [LOW / open] `rust/rand` (unknown, fix:0.9.3)

- Rand is unsound with a custom logger using rand::rng()
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/25

### [LOW / open] `rust/rustls-webpki` (unknown, fix:0.103.12)

- webpki: Name constraints for URI names were incorrectly accepted
- manifest: `tools/ankh-forge/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/24

### [LOW / open] `rust/rustls-webpki` (unknown, fix:0.103.12)

- webpki: Name constraints were accepted for certificates asserting a wildcard name
- manifest: `tools/ankh-forge/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/23

### [LOW / open] `rust/rustls-webpki` (unknown, fix:0.103.12)

- webpki: Name constraints were accepted for certificates asserting a wildcard name
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/22

### [LOW / open] `rust/rustls-webpki` (unknown, fix:0.103.12)

- webpki: Name constraints for URI names were incorrectly accepted
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/21

### [LOW / open] `rust/atty` (unknown, no-fix-yet)

- atty potential unaligned read
- manifest: `extensions/chthonic-archive/native/Cargo.lock`
- view: https://github.com/poisontr33s/chthonic-archive/security/dependabot/4
