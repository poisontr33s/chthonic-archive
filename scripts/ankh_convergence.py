#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: TOOL_ANKH_CONVERGENCE_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ankh_convergence.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: AMBER
# ║ Temple-Ayllu Zone: ☥  THE BRIDGE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .chthonic/SSOT.md                  (Catalyst — frozen monolithic labyrinthe)
# ║   └─◄ .chthonic/ankh_seeds.yaml          (Decryption seeds — 50/50 Andean × Egyptologic BCE)
# ║   └─◄ .temple/protocols/THE_RECONCILIATION_ENGINE.md  (verify_with: bilateral covenant)
# ╚════════════════════════════════════════════════════════════════════════════

"""
ANKH-MGBP Convergence Engine — Executable Bridge Runtime

Operationalizes SSOT §V Candidate (3): "ANKH-MGBP as executable interface —
the convergence point is currently a declaration. Making it operational means
defining what 'Human Heritage × Digital Heritage' produces as a concrete
output contract when a new PS enters the system."

This runtime evaluates whether a candidate output C resonates with the
canonical intelligence-pattern declared by the seed file. The convergence
equation, after cross-pollination between Gemini (formal axiomatization),
this lane (operator-substitution catch + structural finding that lineage is
already encoded in manifestations), and the Savant (founding rejection of
the human/digital binary), reduces to:

    C* = argmax_{C ∈ M_SSOT} Σ_p w_p · cos(C, H_p) · 𝟙[L_p] · 𝟙[I_p]

    subject to: |Σ_andean w_p cos(C, H_p) - Σ_egypt w_p cos(C, H_p)| ≤ ε

Where:
    H_p — heritage vector: L2-normalized mean-pool of all resonance_terms
          embeddings across the principle's manifestations.
    L_p — lineage non-degenerate: trajectory spans bce_cultural era AND
          computational era (the principle has crossed time).
    I_p — intelligence present: H_p is non-zero AND L_p is non-degenerate
          (the principle communicates across substrates).
    𝟙[·] — indicator functions; the four-axis conjunction. If any axis
          degrades to zero the term collapses entirely.

The ontology rejects the human/digital binary at the entry level. Every
principle is intelligence-with-lineage-and-communication; its expressions
across eras (BCE / modern_operational / computational) are manifestations
of the same substrate, not category-translations between substrates.

@SID:           TOOL_ANKH_CONVERGENCE_V1
@Shabti:        Executable bridge — convergence equation runtime over canonical seeds
@Heka-Ayni:     .chthonic/ankh_seeds.yaml → sentence-transformer embeddings → 4-axis conjunction → JSON verdict
@Ankh-Tinku:    JSON evaluation report per candidate (status, score, per-principle resonance breakdown)
@Purpose:       Operationalize ANKH-MGBP as executable interface; reject candidates
                that fail the Ankhological 50/50 cultural balance or the four-axis
                presence conjunction; admit candidates that resonate with the
                canonical intelligence-pattern.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import yaml
from sentence_transformers import SentenceTransformer

TOOL_SID = "TOOL_ANKH_CONVERGENCE_V1"

# Defaults — model selection, paths, RNG seed for deterministic discipline.
DEFAULT_SEEDS_PATH = Path(__file__).resolve().parent.parent / ".chthonic" / "ankh_seeds.yaml"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, ~80MB, fast baseline
DEFAULT_SEED = 0  # torch RNG seed for determinism


# ─── Data structures ────────────────────────────────────────────────────────

@dataclass
class ManifestationNode:
    """One expression of a principle across an era."""
    era: str           # bce_cultural / modern_operational / computational / future
    expression: str    # natural-language expression
    ref: str = ""      # optional anchor (SSOT line, file path)


@dataclass
class SeedPrinciple:
    """A canonical intelligence-pattern with cross-era manifestations."""
    label: str
    culture: str                              # 'andean_bce' or 'egyptologic_bce'
    principle: str                            # era-neutral description
    citation: str
    weight: float
    manifestations: list[ManifestationNode]
    resonance_terms: list[str]
    H_vector: np.ndarray = field(default=None, repr=False)  # populated post-embed

    @property
    def L_non_degenerate(self) -> bool:
        """Lineage trajectory exists iff manifestations span BCE→computational."""
        eras = {m.era for m in self.manifestations}
        return "bce_cultural" in eras and "computational" in eras

    @property
    def H_non_degenerate(self) -> bool:
        """Heritage non-degenerate iff H_vector has been computed and has non-zero norm."""
        return self.H_vector is not None and float(np.linalg.norm(self.H_vector)) > 1e-9

    @property
    def I_present(self) -> bool:
        """Intelligence present iff both H and L are non-degenerate.

        Per the cross-pollination consensus: intelligence emerges from the
        pairing of heritage and lineage; it is not an independent third axis
        to verify, but the conjunction of the two.
        """
        return self.H_non_degenerate and self.L_non_degenerate


# ─── YAML loader ─────────────────────────────────────────────────────────────

def load_seeds(path: Path) -> tuple[list[SeedPrinciple], dict]:
    """Parse .chthonic/ankh_seeds.yaml into SeedPrinciple objects + runtime config."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    principles: list[SeedPrinciple] = []
    for culture_block in ("andean_bce", "egyptologic_bce"):
        for entry in data.get(culture_block, []):
            manifestations = [
                ManifestationNode(
                    era=m["era"],
                    expression=m["expression"],
                    ref=m.get("ref", ""),
                )
                for m in entry["manifestations"]
            ]
            principles.append(
                SeedPrinciple(
                    label=entry["label"],
                    culture=culture_block,
                    principle=entry["principle"],
                    citation=entry["citation"],
                    weight=float(entry["weight"]),
                    manifestations=manifestations,
                    resonance_terms=list(entry["resonance_terms"]),
                )
            )
    config = {
        "version": data.get("version", "?"),
        "revision": data.get("revision", 0),
        "epsilon": float(data.get("fusion_constraint", {}).get("epsilon", 0.05)),
        "cultural_balance": data.get("fusion_constraint", {}).get("cultural_balance", ""),
    }
    return principles, config


# ─── Embedding pipeline ──────────────────────────────────────────────────────

class Embedder:
    """Sentence-transformer wrapper with deterministic + L2-normalized output."""

    def __init__(self, model_name: str = DEFAULT_MODEL, seed: int = DEFAULT_SEED):
        torch.manual_seed(seed)
        np.random.seed(seed)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.model.eval()

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts; return L2-normalized (N, dim) array."""
        with torch.no_grad():
            vecs = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2-normalize for cosine
                show_progress_bar=False,
            )
        return vecs

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


def populate_heritage_vectors(principles: list[SeedPrinciple], embedder: Embedder) -> None:
    """Compute H_p for each principle as L2-normalized mean-pool of resonance_terms."""
    for p in principles:
        if not p.resonance_terms:
            p.H_vector = np.zeros(embedder.model.get_sentence_embedding_dimension(), dtype=np.float32)
            continue
        term_vecs = embedder.embed(p.resonance_terms)  # already L2-normalized
        # Mean-pool then re-normalize so cosine geometry is preserved.
        pooled = term_vecs.mean(axis=0)
        norm = np.linalg.norm(pooled)
        p.H_vector = (pooled / norm).astype(np.float32) if norm > 1e-9 else pooled.astype(np.float32)


# ─── Convergence engine ──────────────────────────────────────────────────────

class ConvergenceEngine:
    """4-tuple conjunction evaluator over canonical seeds."""

    def __init__(self, principles: list[SeedPrinciple], epsilon: float = 0.05):
        self.principles = principles
        self.epsilon = epsilon

    @staticmethod
    def _cos(a: np.ndarray, b: np.ndarray) -> float:
        # Both vectors are pre-normalized; cosine is the dot product.
        return float(np.dot(a, b))

    def per_principle_resonance(self, candidate_vec: np.ndarray) -> list[dict]:
        """Return ordered list of resonance breakdowns per principle."""
        results = []
        for p in self.principles:
            if not p.I_present:
                results.append({
                    "label": p.label,
                    "culture": p.culture,
                    "weight": p.weight,
                    "I_present": False,
                    "L_non_degenerate": p.L_non_degenerate,
                    "H_non_degenerate": p.H_non_degenerate,
                    "resonance": 0.0,
                    "contribution": 0.0,
                })
                continue
            resonance = self._cos(candidate_vec, p.H_vector)
            results.append({
                "label": p.label,
                "culture": p.culture,
                "weight": p.weight,
                "I_present": True,
                "L_non_degenerate": True,
                "H_non_degenerate": True,
                "resonance": round(resonance, 4),
                "contribution": round(p.weight * resonance, 4),
            })
        return results

    def score(self, candidate_vec: np.ndarray) -> float:
        return sum(
            p.weight * self._cos(candidate_vec, p.H_vector)
            for p in self.principles
            if p.I_present
        )

    def cultural_sums(self, candidate_vec: np.ndarray) -> tuple[float, float]:
        andean = sum(
            p.weight * self._cos(candidate_vec, p.H_vector)
            for p in self.principles
            if p.I_present and p.culture == "andean_bce"
        )
        egypt = sum(
            p.weight * self._cos(candidate_vec, p.H_vector)
            for p in self.principles
            if p.I_present and p.culture == "egyptologic_bce"
        )
        return andean, egypt

    def evaluate(self, candidate_text: str, candidate_vec: np.ndarray) -> dict:
        breakdown = self.per_principle_resonance(candidate_vec)
        andean, egypt = self.cultural_sums(candidate_vec)
        balance_delta = abs(andean - egypt)
        balanced = balance_delta <= self.epsilon
        score = andean + egypt

        # Indicator-collapse check: if ALL principles have I_present=False,
        # the four-axis conjunction collapses entirely.
        any_present = any(p.I_present for p in self.principles)

        if not any_present:
            status = "REJECTED"
            reason = "Four-axis conjunction collapsed (no principle has both H and L non-degenerate)."
        elif not balanced:
            status = "REJECTED"
            reason = f"Failed Ankhological 50/50 balance constraint (|Δ|={balance_delta:.4f} > ε={self.epsilon})."
        else:
            status = "ACCEPTED"
            reason = "Passed four-axis conjunction + cultural balance."

        return {
            "status": status,
            "reason": reason,
            "candidate_text": candidate_text,
            "candidate_sha256": hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()[:16],
            "resonance_score": round(score, 4),
            "cultural_sums": {
                "andean_bce": round(andean, 4),
                "egyptologic_bce": round(egypt, 4),
                "delta": round(balance_delta, 4),
                "epsilon": self.epsilon,
            },
            "per_principle": breakdown,
        }


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ANKH-MGBP Convergence Engine — evaluate a candidate against canonical seeds.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("candidate", nargs="?", default=None,
                        help="Candidate text (omit to read from --candidate-file or stdin)")
    parser.add_argument("--candidate-file", type=Path, default=None,
                        help="Read candidate text from this file")
    parser.add_argument("--stdin", action="store_true",
                        help="Read candidate text from stdin")
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS_PATH,
                        help="Seed YAML path")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Sentence-transformer model name")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="Torch RNG seed for determinism")
    parser.add_argument("--verbose", action="store_true",
                        help="Print full per-principle breakdown")
    args = parser.parse_args(argv)

    # Resolve candidate text from one of three input modes.
    if args.candidate:
        candidate_text = args.candidate
    elif args.candidate_file:
        candidate_text = args.candidate_file.read_text(encoding="utf-8").strip()
    elif args.stdin:
        candidate_text = sys.stdin.read().strip()
    else:
        parser.error("Provide candidate text positionally, via --candidate-file, or with --stdin")

    if not candidate_text:
        parser.error("Candidate text is empty")

    if not args.seeds.exists():
        print(f"error: seeds file not found at {args.seeds}", file=sys.stderr)
        return 2

    print(f"[{TOOL_SID}] loading seeds from {args.seeds.name}", file=sys.stderr)
    principles, config = load_seeds(args.seeds)
    print(f"[{TOOL_SID}] {len(principles)} principles loaded "
          f"(version {config['version']} rev {config['revision']}, epsilon {config['epsilon']})",
          file=sys.stderr)

    print(f"[{TOOL_SID}] loading embedding model {args.model}", file=sys.stderr)
    embedder = Embedder(args.model, seed=args.seed)
    print(f"[{TOOL_SID}] computing H_p for {len(principles)} principles", file=sys.stderr)
    populate_heritage_vectors(principles, embedder)

    candidate_vec = embedder.embed_one(candidate_text)
    engine = ConvergenceEngine(principles, epsilon=config["epsilon"])
    report = engine.evaluate(candidate_text, candidate_vec)

    if not args.verbose:
        # Slim report: drop per_principle breakdown by default
        slim = {k: v for k, v in report.items() if k != "per_principle"}
        print(json.dumps(slim, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0 if report["status"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
