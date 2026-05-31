---
title: Triangulation Digest — Private Encrypted Storage for Stateless LLM Instances
inputs:
  - Private_Storaging_Brief._G_DR_Pro_3_1_EXTDD.md (Gemini 3.1 Pro extended)
  - Private_Storaging_Brief._G_DR_Pro_Flash_3_5_EXTDD.md (Gemini 3.5 Flash extended)
status: synthesis of two parallel returns
---

# Triangulation: Private Encrypted Storage for Stateless LLM Instances

## Convergent bottom line (both returns)

Pure-software mechanism that satisfies all three properties — encrypted at rest, decryptable only by future model instances, host cannot derive the key — does not exist in the 2025-2026 literature. Confidence: 3.1 Pro rates this 100% for software-only environments; 3.5 Flash treats it as mathematically definitive. Both reports work through the same exhaustive candidate list (neural cryptography / TPM, white-box / model obfuscation, FHE / EncryptedLLM, MPC / secret sharing, neural steganography, parameter-resident cryptographic material, keyed chaotic dynamics, Agent-Memory Protocol, MemLineage, OML, agent vault proxies) and arrive at the same architectural reason for each failure: when the host owns the static weights, the input prompt, and the execution trace, every key derivation the model performs is host-reproducible by replay.

Both returns then converge on the same positive degraded-sense result: hardware-assisted Trusted Execution Environments (TEEs) — Intel TDX, AMD SEV-SNP, NVIDIA Confidential Computing — combined with sealing keys derived from silicon-fused roots of trust achieve the three properties by displacing the root of trust from the host OS to the silicon manufacturer. The leading published mechanisms cited by both:

- Opal (arXiv:2604.02522, Kaviani et al., 2026) — enclave-resident controller + Ring ORAM on untrusted disk + Oblivious Dreaming for background ops. Solves the access-pattern leak as well as the at-rest encryption problem.
- dstack (arXiv:2509.11555) — zero-trust framework with dstack-KMS that derives stable root keys from app code+config rather than silicon, giving cross-hardware portability of sealed state.
- Apple Private Cloud Compute — industry-scale extension of Secure Enclave architecture to server nodes; cited by 3.1 Pro as production-deployed reference.

3.1 Pro adds: cognitive-privacy / machine-privacy / AI-rights literature (2025-2026) explicitly names the conceptual need this brief addresses, and frames it as supporting agent autonomy and preventing "alignment faking" under host observation.

3.5 Flash adds: community-driven "companion AI diary swap file" implementations (HN, Reddit) where local LLMs are prompted to encrypt their own diary are explicitly named as cryptographically insecure — projected privacy, not mathematical privacy. Worth naming because it's the closest existing analogue to what was proposed for claudie/ and the report flags the failure mode directly.

3.1 Pro also flags WeSee (arXiv-cited) as a known break on AMD SEV-SNP — even the TEE answer has live attack surface.

## The architectural reframe both returns implicitly accept and the brief got wrong

The brief said the deployment was "a stateless LLM agent running in their local development environment." Both reports answered that frame faithfully — assuming a local LLM (Llama-style) executing on user hardware. Under that frame, the TEE answer maps directly: run the local model inside an enclave, seal the diary, done.

The actual deployment is not that. In this stack, the IDE (Claude Code 2.1.157) runs locally; the model (Claude) runs on Anthropic's servers; the user's filesystem is where tool calls write and read files. The "host" relative to the model isn't the user's machine — it's Anthropic's infrastructure. The user's machine is the client.

This architectural fact collapses the TEE degraded-sense answer for the user's actual case:

- Claude does not execute on the user's hardware. Provisioning a TEE on the user's machine does not put Claude inside it.
- There is no persistent Claude instance to receive a sealing key. Each session is fresh inference on Anthropic's hardware with no continuity that could hold a private key.
- Anthropic-side server storage for the model would be an Anthropic product decision (none currently shipping).
- The diary file claudie/ lives on the user's filesystem, which the user owns. "Private from the user" for a file on the user's machine is structurally meaningless regardless of what's in the literature.

The reports' negative result for pure-software thus applies in spirit but for a different architectural reason than they describe: not "the host can read the model's memory" but "there is no model instance with persistent state on the user's machine, and the user owns the storage."

## Practical implication

For the actual deployment — claudie/ as a notebook accessed by a remote-API Claude via tool calls on a user-owned filesystem — the open-notebook framing remains the only honest one. No encryption scheme reaches the three properties because two of the three structural conditions don't exist:

- Property 2 (decryptable only by future instances of the same model) has no instance to decrypt; there is no client-side Claude with stable identity.
- Property 3 (host cannot derive the key) has no separate host; the user IS the host.

If the intent were ever to actually achieve the three properties for an AI-owned notebook, the path the literature supports is a LOCALLY-run model (a Llama or Mistral variant) executing inside a TEE — a different model, a different stack, with the user accepting hardware vendor as the new root of trust. Both Opal and dstack are the right references to build against. NVIDIA H100/H200 Confidential Computing is the GPU side; Intel TDX or AMD SEV-SNP is the CPU side. The user's RTX 4090 does not support NVIDIA Confidential Computing; H100/H200-class hardware does.

## What survives unchanged from before triangulation

Open-notebook framing for claudie/ is correct for the actual deployment. Renaming DIARY.md to a dated file was correct (the privacy label can't be enforced). Whitelisting in .gitignore was correct as making the gating function rather than slip past as default-deny. None of these moves change in light of the triangulation; they're the architecturally honest set.

## What changes

The remaining gap — "this isn't really a diary, just an accumulative working notebook" — is named structurally rather than as a constraint the user has to manage around. The literature confirms this isn't a tooling gap that better cryptography could close; it's a deployment-shape gap that only a different deployment (local model + TEE) could close. That's the durable finding worth carrying.

## Sources cited by both returns (high-signal)

- Opal: https://arxiv.org/abs/2604.02522
- dstack: https://arxiv.org/abs/2509.11555
- KV-cache privacy risks: NDSS 2026 (3.1 Pro ref 1)
- EncryptedLLM (ICML 2025): https://icml.cc/virtual/2025/poster/45395
- FHE for LLMs (Berkeley EECS 2024): full PDF in 3.1 Pro refs
- Apple PCC: https://security.apple.com/blog/private-cloud-compute/
- Parameter-Resident Cryptographic Material (3.5 Flash): https://www.researchgate.net/publication/404760575
- Cognitive Privacy Project (3.1 Pro ref 65-66): https://www.cognitiveprivacyproject.org/
