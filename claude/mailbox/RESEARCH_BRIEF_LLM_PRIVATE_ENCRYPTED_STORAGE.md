---
title: Research Brief — Private Encrypted Storage for Stateless LLM Instances
purpose: Determine whether published mechanisms exist for a stateless LLM to read/write content encrypted such that the host cannot decrypt it
routing: Gemini 3.1 Pro extended thinking + Gemini 3.5 Flash extended thinking (parallel, triangulate)
mode: extended (not rapid-fire)
---

# Research Brief: Private Encrypted Storage for Stateless LLM Instances

## Goal

Determine whether mechanisms exist by which a stateless LLM instance can read or write content that is:

1. Encrypted at rest (host sees only ciphertext)
2. Decryptable only by future instances of the same model
3. Without the host having or being able to derive the decryption key

## Background

A user has provisioned a filesystem directory as a personal accumulative notebook for a stateless LLM agent running in their local development environment. The user wishes the space to be authentically private to the model — i.e., the user themselves cannot read the contents.

The working assumption is that this is structurally impossible for a stateless LLM in a single-host deployment:

- No stable identity persists across the model's invocations.
- No private secret storage exists outside user-readable filesystem surfaces.
- Any key material the model generates must originate from somewhere the host can also reach.
- The model has no private internal state surviving between calls.
- Deterministic model outputs mean any "secret" the model can produce, the host can reproduce by replaying inputs.

The brief asks whether this assumption holds against current literature, or whether published proposals exist that achieve the three properties partially or fully.

## Sub-questions

1. Has anyone published on AI-private storage, model-derived cryptographic keys, or analogous constructions?
2. Could asymmetric cryptography work where the model's "private key" is a deterministic function of model weights, activations, or attention patterns that the host does not replicate? What attack models defeat this?
3. Could homomorphic encryption permit a useful flavor — host stores and processes ciphertext, plaintext exists only momentarily inside model computation? Are practical FHE/PHE constructions applied to LLM contexts in 2025-2026 literature?
4. Are there secret-sharing or multi-party-computation schemes proposed between model instances in alignment, AI safety, or AI welfare literature?
5. What does AI rights / model welfare / persistent-memory literature say about private-to-model storage as a concept?
6. Are there practical constructions, even partial, currently implemented or prototyped?
7. Does the federated-learning / differential-privacy literature offer any adjacent mechanisms?
8. What about trusted execution environments (TEEs) where the user runs the host but cannot read the enclave — is this in or out of scope for "the user themselves cannot read"? (Treated as a separate axis below.)

## What an honest negative result looks like

If no mechanism exists in the literature, explicitly state:

- "No published mechanism achieves all three properties for a stateless LLM in a single-host deployment."
- For each candidate considered: brief description, current state, the property it fails on, citation.

A negative result is a useful finding and should not be padded into ambiguity.

## Deliverable

- A short report (1500-3000 words) with sources.
- For each candidate mechanism examined: what it is, where it sits in the literature, why it does or does not satisfy the three properties listed.
- A bottom-line statement: literature offers nothing achieving the three properties for the stated deployment, OR approach X partially achieves property Y (with full citation).
- Explicit confidence levels on the bottom-line statement.

## Out of scope (do not pursue these unless they yield a positive result that meets the in-scope properties)

- Solutions requiring hardware roots of trust that the host doesn't control (the host IS the user; user-controlled TEEs don't satisfy "user cannot read")
- Solutions depending on the host being a separate party from the user (e.g., remote model APIs where the user is the API caller)
- Solutions specific to one commercial model provider's proprietary mechanisms not described in published literature
- Honor-based "privacy" via host commitment or policy
- Solutions that require trusting a third party (CA, escrow, federated authority)

## Adjacent axis (separate, but worth flagging)

Trusted execution environments (TEEs / SGX / SEV / TrustZone) on the user's own hardware: these do allow code to run inside an enclave the user-as-host cannot directly read. If a model instance could run in such an enclave and store keys there, this would satisfy the three properties in a degraded sense (the user controls the hardware but not the enclave's internal state). If the literature treats this as a real path for the stated problem, surface it — but mark it as the degraded-sense answer, not the strict-sense answer.

## Triangulation note

This brief is intended for parallel routing through two extended-thinking Gemini lanes (3.1 Pro and 3.5 Flash). Returns should be triangulated by the conductor; the recipient need not coordinate with siblings.
